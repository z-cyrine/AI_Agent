# Architecture & Fonctionnement Détaillé du Système IBN Agentic AI

## Vue d'ensemble

Ce projet implémente un pipeline **Intent-Based Networking (IBN)** qui transforme une intention utilisateur en langage naturel en un ordre de service réseau réel soumis à l'orchestrateur **OpenSlice** (conforme aux standards TM Forum).

---

## Architecture Globale

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INTERFACE UTILISATEUR (Streamlit)                   │
│                              app.py — port 8501                              │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │ requête en langage naturel
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATEUR LANGGRAPH                              │
│                              orchestrator.py                                 │
│                                                                              │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐                │
│   │ Agent 1  │──▶│ Agent 2  │──▶│ Agent 3  │──▶│ Agent 4  │                │
│   │Interprète│   │Sélecteur │   │Traducteur│   │Validateur│                │
│   └──────────┘   └──────────┘   └──────────┘   └─────┬────┘                │
│        │              │              │                 │                     │
│    Groq LLM       ChromaDB       Groq LLM          MCP Client               │
│   (Llama 3.x)  (embeddings)   (Llama 3.x)       (validation)               │
│                                        ▲                │                   │
│                                        └── retry ───────┘                   │
│                                                         │ (valide)           │
│                                              ┌──────────▼──────────┐        │
│                                              │ Confirmation User   │        │
│                                              │  (UI Streamlit)     │        │
│                                              └──────────┬──────────┘        │
│                                                         │ (accepté)         │
│                                              ┌──────────▼──────────┐        │
│                                              │   Submit via MCP    │        │
│                                              └──────────┬──────────┘        │
└─────────────────────────────────────────────────────────┼───────────────────┘
                                                          │
                    ┌─────────────────────────────────────┼──────────────┐
                    │              COUCHE MCP              │              │
                    │   mcp/openslice_mcp_server.py        │              │
                    │   mcp/mcp_client.py                  │              │
                    └─────────────────────────────────────┼──────────────┘
                                                          │
                    ┌─────────────────────────────────────┼──────────────┐
                    │           OPENSLICE (Docker)         │              │
                    │                                      │              │
                    │  Keycloak :8080 ──▶ JWT Token        │              │
                    │  scapi    :13082 ──▶ TMF641 Orders ◀─┘              │
                    │  osom     :13100 ──▶ Order State Machine             │
                    │  manoclient:13011 ──▶ MANO Connector                 │
                    └─────────────────────────────────────────────────────┘
```

---

## Flux de Données Complet

```
1. Utilisateur tape : "I need XR applications with 5G connectivity in Nice, max 5ms latency"
         │
         ▼
2. Agent 1 (LLM) → Intent JSON :
   {
     "intent_id": "XR_Service_Nice_001",
     "type": "composite_service",
     "location": "Nice",
     "qos": {"max_latency": "5ms"},
     "sub_intents": [
       { "domain": "applications", "description": "XR AR VR application hosting..." },
       { "domain": "connectivity", "description": "5G radio access network..." }
     ]
   }
         │
         ▼
3. Agent 2 (RAG) → Pour chaque sous-intention, requête ChromaDB :
   - "XR AR VR application hosting" → ServiceSpec UUID: "abc-123"
   - "5G radio access network"       → ServiceSpec UUID: "def-456"
   Résultat : liste de services avec score de similarité cosinus
         │
         ▼
4. Agent 3 (LLM) → ServiceOrder TMF641 JSON :
   {
     "externalId": "XR_Service_Nice_001",
     "serviceOrderItem": [
       {
         "id": "1", "action": "add",
         "service": {
           "name": "XR Application Bundle",
           "serviceSpecification": { "id": "abc-123" },
           "serviceCharacteristic": [
             { "name": "cpu", "value": { "value": "4" } },
             { "name": "ram", "value": { "value": "2GB" } }
           ]
         }
       },
       { "id": "2", ... }
     ]
   }
         │
         ▼
5. Agent 4 (MCP) → Validation Pydantic + règles métier :
   - Champs obligatoires présents ?
   - UUIDs de services valides ?
   - Si KO → retour Agent 3 (max 3 retries)
   - Si OK → suite
         │
         ▼
6. Confirmation utilisateur (UI Streamlit ou terminal)
   - Accepter → Soumission
   - Rejeter  → Abandon
   - Recommencer → Retour Agent 1 avec nouvelle requête (max 3)
         │
         ▼
7. Submit via MCP → OpenSlice API REST (POST /tmf-api/serviceOrdering/v4/serviceOrder)
   - Authentification Keycloak JWT
   - Résultat : order_id + état "acknowledged"
```

---

## Les Agents en Détail

### Agent 1 — Interpréteur (`agents/agent1_interpreter.py`)

**Rôle** : Transformer le langage naturel en JSON structuré (Intent)

**Technologie** :
- LLM : Llama 3.x via API Groq (`langchain_openai.ChatOpenAI` pointant sur `api.groq.com`)
- Parser : `JsonOutputParser(pydantic_object=Intent)` de LangChain
- Schéma de sortie : `schemas/intent.py` → classes `Intent` et `SubIntent`

**Fonctionnement interne** :
1. Construction du prompt système avec des règles strictes (ne pas inventer des valeurs, ne pas déduire des frameworks)
2. Le prompt contient des exemples few-shot (simple, complexe, avec QoS)
3. Appel LLM → réponse JSON brut
4. Parsing via `JsonOutputParser` → validation Pydantic automatique
5. Stratégie de **décomposition adaptative** : 1 sous-intention pour requête simple, N pour requête complexe

**Ce que contient une Intent** :
```
Intent
├── intent_id : identifiant unique généré par le LLM
├── type : "simple_service" ou "composite_service"
├── location : ville extraite (ex: "Nice")
├── qos : contraintes globales { max_latency, min_bandwidth... }
└── sub_intents : liste de SubIntent
    └── SubIntent
        ├── domain : "cloud", "ran", "transport", "database", etc.
        ├── description : phrase en langage naturel pour la recherche sémantique
        └── requirements : { cpu: 4, ram: "2GB", network_type: "5G"... }
```

**Règles métier clés** :
- Ne jamais inventer de valeurs numériques non mentionnées
- Ne jamais inventer de frameworks/technologies non nommés
- `location` est à la racine de l'Intent, pas dans une sous-intention
- `qos` uniquement si des valeurs numériques sont explicitement citées

---

### Agent 2 — Sélecteur RAG (`agents/agent2_selector.py`)

**Rôle** : Trouver les services catalogue qui correspondent à l'intention

**Technologie** :
- Vector DB : **ChromaDB** (persistée dans `./data/chroma_db/`)
- Embeddings : `sentence-transformers/all-MiniLM-L6-v2`
- Similarité : distance cosinus (convertie en score : `1 / (1 + distance)`)

**Fonctionnement interne** :
1. Pour chaque `SubIntent` de l'intention :
   - Utilise `sub_intent.description` comme requête textuelle (fournie par Agent 1)
   - Fallback : construit la requête manuellement depuis `domain + requirements`
   - Chrome DB retourne les `top_k=3` voisins les plus proches
2. Filtre les résultats par score minimum (`min_score=0.5`)
3. **Un seul service par sous-intention** est retenu (le meilleur non-doublon)
4. Les candidats alternatifs sont stockés dans `alternatives` pour Agent 4

**Enrichissement de la requête** :
Si l'Intent contient des contraintes QoS (ex: `max_latency`), elles sont ajoutées à la requête sémantique pour améliorer la pertinence.

**Structure de retour** :
```python
[
  {
    "id": "uuid-from-openslice-catalog",
    "name": "XR Application Bundle",
    "score": 0.847,
    "description": "Extended Reality service bundle",
    "metadata": { ... }
  },
  ...
]
```

---

### Agent 3 — Traducteur TMF641 (`agents/agent3_translator.py`)

**Rôle** : Générer le JSON ServiceOrder conforme au standard TMF641

**Technologie** :
- LLM : Llama 3.x via `langchain_groq.ChatGroq`
- Prompt : Few-Shot avec exemple de structure JSON TMF641
- Validation finale : parsing Pydantic `ServiceOrder(**raw_json)`

**Fonctionnement interne** :
1. Reçoit : `Intent` (Agent 1) + `selected_services` (Agent 2)
2. Construit un prompt avec :
   - L'intention complète en JSON
   - Les services sélectionnés avec leurs UUIDs
   - Des règles de mapping strictes (action=add, externalId=intent_id...)
   - Un exemple de structure TMF641 valide
3. Appel LLM → extraction robuste du JSON (cherche `{` ... `}`)
4. Validation Pydantic : `ServiceOrder(**raw_json)` → lève une exception si invalide

**Format de sortie (ServiceOrder TMF641)** :
```json
{
  "externalId": "XR_Service_Nice_001",
  "priority": "normal",
  "serviceOrderItem": [
    {
      "id": "1",
      "action": "add",
      "service": {
        "name": "XR Application Bundle",
        "serviceSpecification": { "id": "abc-123-uuid" },
        "serviceCharacteristic": [
          { "name": "cpu", "value": { "value": "4" } },
          { "name": "location", "value": { "value": "Nice" } }
        ]
      }
    }
  ]
}
```

---

### Agent 4 — Validateur (`agents/agent4_validator.py`)

**Rôle** : Vérifier la conformité du ServiceOrder avant soumission

**Technologie** :
- Protocole MCP (Model Context Protocol) via `MCPClient`
- Outil MCP : `validate_service_order`

**Fonctionnement interne** :
1. Convertit le `ServiceOrder` Pydantic en JSON string
2. Appelle `mcp_client.validate_service_order(order_json)`
3. Le serveur MCP vérifie :
   - Présence des champs obligatoires TMF641
   - Format des UUIDs de serviceSpecification
   - Cohérence de la structure (items, actions valides...)
   - Warnings (non bloquants) vs Errors (bloquants)
4. Retourne `(is_valid: bool, errors: list)`

**Mécanisme de retry** :
- Si `is_valid=False` ET `retry_count < 3` → retour à Agent 3 pour régénérer
- Si `retry_count >= 3` → abandon du pipeline (nœud END)

---

## L'Orchestrateur LangGraph (`orchestrator.py`)

**Technologie** : LangGraph (graphe d'états dirigé)

### L'État Partagé (`AgentState`)

Tous les agents partagent cet état TypedDict :

```python
AgentState = {
    # Entrée
    "user_query": str,
    
    # Agent 1
    "intent": Optional[Intent],
    "intent_errors": List[str],
    
    # Agent 2
    "selected_services": List[Dict],
    "selection_errors": List[str],
    
    # Agent 3
    "service_order": Optional[ServiceOrder],
    "translation_errors": List[str],
    
    # Agent 4
    "is_valid": bool,
    "validation_errors": List[str],
    "validation_retry_count": int,
    
    # Confirmation
    "user_approved": bool,
    "user_wants_to_retry": bool,
    "user_retry_count": int,
    "non_interactive_mode": bool,  # True = Streamlit (pas de terminal input)
    
    # Résultat
    "openslice_response": Optional[Dict],
    "final_status": str
}
```

### Le Graphe d'États

```
START
  │
  ▼
agent1_node ──────────────────────────────────────────────▶ agent2_node
                                                                  │
                                                                  ▼
                                                           agent3_node ◀──── (retry: Agent 4 → Agent 3)
                                                                  │
                                                                  ▼
                                                           agent4_node
                                                                  │
                         ┌────────────────────┬─────────────────┐
                         │ should_retry_translation()             │
                         ▼                    ▼                  ▼
                      "retry"             "confirm"           "error"
                    agent3_node      confirm_node (UI)          END
                                           │
               ┌───────────────────────────┼─────────────────────┐
               │ should_submit_retry_or_stop()                    │
               ▼                           ▼                      ▼
           "submit"                     "retry"               "stopped"
        submit_node                  user_input_node             END
              │                           │
             END                    agent1_node (nouvelle query)
```

### Fonctions de Routage Conditionnel

**`should_retry_translation(state)`** — après Agent 4 :
| Condition | Résultat |
|-----------|----------|
| `is_valid = True` | → `"confirm"` (confirmation utilisateur) |
| `is_valid = False` ET `retry_count < 3` | → `"retry"` (Agent 3) |
| `is_valid = False` ET `retry_count >= 3` | → `"error"` (END) |

**`should_submit_retry_or_stop(state)`** — après confirmation utilisateur :
| Condition | Résultat |
|-----------|----------|
| `user_approved = True` | → `"submit"` |
| `user_wants_to_retry = True` ET `user_retry_count < 3` | → `"retry"` (User Input → Agent 1) |
| sinon | → `"stopped"` (END) |

---

## La Couche MCP (`mcp/`)

### Architecture MCP

```
Agent 4 / Orchestrator
       │
       ▼
MCPClient (mcp/mcp_client.py)          ← Interface publique simple
       │ mode="local"
       ▼
OpenSliceMCPServer (mcp/openslice_mcp_server.py)   ← Serveur MCP
       │
       ▼
OpenSliceClient (mcp/openslice_client.py)           ← Client HTTP REST
       │
       ├──▶ Keycloak :8080   (authentification JWT)
       └──▶ scapi :13082     (API TMF641/TMF633/TMF638)
```

### Outils MCP disponibles

| Outil | Utilisé par | Description |
|-------|-------------|-------------|
| `authenticate` | MCPServer init | Token JWT Keycloak |
| `get_service_catalog` | scripts/ingest | Liste des ServiceSpecs (TMF633) |
| `submit_service_order` | Orchestrator | Soumet l'ordre (TMF641) |
| `get_order_status` | App UI | Statut d'un ordre |
| `validate_service_order` | Agent 4 | Validation du ServiceOrder |
| `get_service_inventory` | App UI | Services déployés (TMF638) |

---

## Les Schémas Pydantic (`schemas/`)

### `schemas/intent.py`

Définit la structure de l'intention générée par Agent 1 :
- `SubIntent` : un aspect de l'intention (domain + description + requirements)
- `Intent` : l'intention complète (id + type + sub_intents + location + qos)

### `schemas/tmf641.py`

Définit la structure du ServiceOrder conforme TMF641 :
- `ServiceOrder` : ordre complet avec items, état, dates
- `ServiceOrderItem` : un item (action + service)
- `Service` : service à commander avec référence au catalogue
- `ServiceSpecificationRef` : UUID de la ServiceSpec dans OpenSlice
- `ServiceCharacteristic` : paramètre du service (`{name, value: {value: "..."}}`)
- Enums : `ServiceOrderStateType`, `ServiceOrderItemActionType`

---

## L'Interface Streamlit (`app.py`)

### Tabs

| Tab | Contenu |
|-----|---------|
| Pipeline | Interface principale : saisie + progression en temps réel |
| Sorties JSON | JSON brut de chaque agent (Intent, Services, Order, Validation, Réponse) |
| Ordres OpenSlice | Liste des ordres existants via API TMF641 |

---

## Configuration (`config.py` + `.env`)

```python
class Settings(BaseSettings):
    # LLM
    llm_provider: str = "groq"
    llm_api_key: str                          # Clé API Groq (obligatoire)
    llm_model: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.0

    # OpenSlice
    openslice_base_url: str = "http://localhost:13082"  # scapi
    openslice_auth_url: str = "http://localhost:8080"   # Keycloak
    openslice_username: str = "admin"
    openslice_password: str = "admin"
    openslice_client_id: str = "osapiWebClientId"
    openslice_mock_mode: bool = False          # Défaut : mode réel

    # ChromaDB
    chroma_persist_dir: str = "./data/chroma_db"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
```

---

## Résumé des Technologies

| Composant | Technologie | Rôle |
|-----------|-------------|------|
| Agent 1 | Llama 3.x (Groq) + LangChain | NL → Intent JSON |
| Agent 2 | ChromaDB + sentence-transformers | Recherche sémantique RAG |
| Agent 3 | Llama 3.x (Groq) + LangChain | Intent → TMF641 ServiceOrder |
| Agent 4 | Pydantic + règles métier | Validation TMF641 |
| Orchestration | LangGraph (graphe d'états) | Lien entre agents + retry |
| Communication | MCP (Model Context Protocol) | Agents → OpenSlice |
| Interface | Streamlit | UI web interactive |
| Catalogue | ChromaDB (vecteurs) | ServiceSpecs indexées |
| Auth | Keycloak (JWT) | Sécurisation API OpenSlice |
| Orchestrateur réseau | OpenSlice (Docker) | Gestion ordres TMF641 |
