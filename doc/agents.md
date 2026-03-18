# Description des agents

Le pipeline est compose de quatre agents specialises. Chaque agent est una classe Python
independante instanciee dans le noeud LangGraph correspondant.

---

## Agent 1 — Interpreteur (IntentInterpreterAgent)

**Fichier** : `agents/agent1_interpreter.py`  
**Classe** : `IntentInterpreterAgent`  
**Noeud LangGraph** : `agent1_node()`

### Role

Transformer toute requete en langage naturel en une intention structuree au format JSON.
L'agent decompose la requete en sous-intentions par domaine (reseau, application, stockage,
etc.) et extrait les exigences explicitement mentionnees.

### Technologie

- LLM : Llama 3.3 70B via API Groq (`langchain-openai`, pointant sur l'endpoint Groq)
- Validation de sortie : Pydantic (`Intent`, `SubIntent`)

### Entree / Sortie

```
Entree  : user_query (str) — requete en langage naturel
Sortie  : intent (Intent) — intention structuree Pydantic
```

### Format de sortie

```json
{
  "intent_id": "XR_Service_Nice_001",
  "type": "composite_service",
  "sub_intents": [
    {
      "domain": "applications",
      "description": "extended reality XR augmented reality application hosting",
      "requirements": { "type": "XR" }
    },
    {
      "domain": "connectivity",
      "description": "5G mobile radio access network with low latency",
      "requirements": { "type": "5G" }
    }
  ],
  "location": "Nice",
  "qos": null
}
```

### Regles de generation (prompt)

- Extraire uniquement les informations explicitement mentionnees dans la requete
- Ne jamais inventer de valeurs numeriques (latence, memoire, CPU) si non specifiees
- Pour les termes vagues ("rapide", "scalable") : utiliser des booleens (`high_performance: true`)
- La localisation va dans le champ `location` de l'Intent, pas dans les sous-intentions
- Le champ `description` de chaque sous-intention est formule en anglais, en langage naturel
  riche en mots cles, car il sert de requete pour la recherche vectorielle de l'Agent 2

### Initialisation

```python
agent = IntentInterpreterAgent(
    llm_model="llama-3.3-70b-versatile",
    temperature=0.0                       
)
intent = agent.interpret(user_query)
```

---

## Agent 2 — Selecteur RAG (ServiceSelectorAgent)

**Fichier** : `agents/agent2_selector.py`  
**Classe** : `ServiceSelectorAgent`  
**Noeud LangGraph** : `agent2_node()`

### Role

Selectionner les services du catalogue les plus pertinents pour chaque sous-intention,
en utilisant une recherche semantique (Retrieval Augmented Generation) sur ChromaDB.

### Technologie

- Base vectorielle : ChromaDB (persistee dans `data/chroma_db/`)
- Modele d'embeddings : `sentence-transformers/all-MiniLM-L6-v2`
- Metrique de similarite : distance cosinus (convertie en score 0-1 par `1 / (1 + distance)`)

### Entree / Sortie

```
Entree  : intent (Intent) — sortie de l'Agent 1
Sortie  : selected_services (List[Dict]) — un service par sous-intention
```

### Logique de selection

Pour chaque sous-intention de l'intention :

1. La description de la sous-intention (`sub_intent.description`) est utilisee comme requete
   de recherche. Si absente, une requete est construite a partir du domaine et des exigences.
2. ChromaDB retourne `top_k=3` candidats par sous-intention.
3. Le meilleur candidat (score le plus eleve) non deja assigne est selectionne.
4. Les candidats restants sont passes dans le champ `alternatives` pour l'Agent 4.

Format d'un service selectionne :

```python
{
    "id": "uuid-du-service",
    "name": "Nom du service",
    "score": 0.87,              # similarite cosinus (0 a 1)
    "description": "...",       # document indexe dans ChromaDB
    "metadata": {...},          # metadonnees OpenSlice
    "domain": "cloud",          # domaine de la sous-intention associee
    "alternatives": [...]       # autres candidats pour Agent 4
}
```

### Initialisation

```python
agent = ServiceSelectorAgent(
    persist_directory="./data/chroma_db",       # optionnel
    embedding_model="sentence-transformers/...", # optionnel
    collection_name="openslice_services"         # optionnel
)
services = agent.select_services(intent, top_k=3, min_score=0.5)
```

### Pre-requis

La collection ChromaDB (`openslice_services`) doit etre alimentee avant le premier appel.
Voir `scripts/ingest_catalog.py`.

---

## Agent 3 — Traducteur TMF641 (ServiceTranslatorAgent)

**Fichier** : `agents/agent3_translator.py`  
**Classe** : `ServiceTranslatorAgent`  
**Noeud LangGraph** : `agent3_node()`

### Role

Generer un ordre de service conforme au standard TMF641 a partir des services selectionnes
et de l'intention de l'utilisateur. L'agent est appele aussi bien lors du premier passage
que lors des retries apres une validation echouee.

### Technologie

- LLM : Llama 3.3 70B via API Groq (`langchain-groq`)
- Validation de sortie : Pydantic (`ServiceOrder`)

### Entree / Sortie

```
Entree  : intent (Intent) + selected_services (List[Dict])
Sortie  : service_order (ServiceOrder) — ordre TMF641 valide Pydantic
```

### Regles de generation (prompt)

- **Cardinalite stricte** : exactement un `serviceOrderItem` par service dans la liste.
  Ni plus, ni moins.
- L'`id` de chaque item utilise l'UUID du service fourni par l'Agent 2.
- L'action est toujours `"add"`.
- L'`externalId` est l'`intent_id` de l'intention.
- Les caracteristiques (`serviceCharacteristic`) sont mappees depuis le champ `constraints`
  du service selectionne.

### Format de sortie attendu (prompt)

```json
{
    "externalId": "intent-001",
    "priority": "normal",
    "description": "Order based on intent intent-001",
    "serviceOrderItem": [
        {
            "id": "1",
            "action": "add",
            "service": {
                "name": "Nom du service",
                "serviceSpecification": { "id": "uuid-du-service" },
                "serviceCharacteristic": [
                    {"name": "vCPU", "value": {"value": "4"}}
                ]
            }
        }
    ]
}
```

---

## Agent 4 — Validateur (ServiceValidatorAgent)

**Fichier** : `agents/agent4_validator.py`  
**Classe** : `ServiceValidatorAgent`  
**Noeud LangGraph** : `agent4_node()`

### Role

Verifier la conformite de l'ordre de service TMF641 avant soumission. L'agent appelle le
serveur MCP local qui effectue la validation cote client.

### Technologie

- Client MCP local : `MCPClient(mode="local")`
- Outil MCP utilise : `validate_service_order`

### Entree / Sortie

```
Entree  : service_order (ServiceOrder) — sortie de l'Agent 3
Sortie  : (is_valid: bool, errors: List[str])
```

### Logique de validation (dans OpenSliceMCPServer)

L'outil MCP `validate_service_order` effectue les verifications suivantes :

- Presence d'au moins un `serviceOrderItem`
- Chaque item possede un `id` et une `action`
- Chaque service possede une `serviceSpecification` avec un `id` non vide
- Les avertissements (non bloquants) sont loggues mais ne font pas echouer la validation

### Comportement en cas d'echec

Si `is_valid=False`, l'orchestrateur retourne au noeud `agent3` pour regenerer l'ordre
(maximum 3 tentatives, comptees via `validation_retry_count`).

### Initialisation

```python
agent = ServiceValidatorAgent()
is_valid, errors = agent.validate(service_order)
```
