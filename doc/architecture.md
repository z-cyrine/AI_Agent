# Architecture du pipeline IBN

## Vue d'ensemble

Le systeme est un pipeline multi-agents orchestre par LangGraph. Chaque agent est un noeud
du graphe d'etat. L'etat partage (`AgentState`) circule de noeud en noeud et est enrichi
a chaque etape.

---

## Le graphe LangGraph

Le graphe est construit dans `orchestrator.py` via la fonction `create_workflow()`.

### Noeuds du graphe

| Noeud        | Fonction Python           | Role                                               |
|--------------|---------------------------|----------------------------------------------------|
| agent1       | `agent1_node()`           | Interpretation NLP -> intention JSON               |
| agent2       | `agent2_node()`           | Recherche RAG dans ChromaDB                        |
| agent3       | `agent3_node()`           | Generation de l'ordre TMF641                       |
| agent4       | `agent4_node()`           | Validation de l'ordre TMF641                       |
| confirm      | `user_confirmation_node()`| Demande de confirmation a l'utilisateur            |
| user_input   | `user_input_node()`       | Saisie d'une nouvelle requete (reformulation)      |
| submit       | `submit_to_openslice()`   | Soumission via MCP -> OpenSlice                    |

### Flux principal

```
START
  |
agent1 --> agent2 --> agent3 --> agent4
                          ^          |
                          |    is_valid=False et retry < 3
                          +----------+  (retour agent3)
                                     |
                               is_valid=True
                                     |
                                  confirm
                                /    |    \
                    user_approved  retry  stopped
                          |          |        |
                        submit   user_input   END
                          |          |
                         END      agent1  (nouvelle requete)
```

### Routage conditionnel

**Apres Agent 4** — fonction `should_retry_translation()` :

- `is_valid=True` -> noeud `confirm`
- `is_valid=False` et `validation_retry_count < 3` -> retour noeud `agent3`
- `validation_retry_count >= 3` -> `END` (abandon)

**Apres confirmation** — fonction `should_submit_retry_or_stop()` :

- `user_approved=True` -> noeud `submit`
- `user_wants_to_retry=True` et `user_retry_count < 3` -> noeud `user_input`
- sinon -> `END` (arret)

---

## L'etat partage : AgentState

Defini dans `orchestrator.py` comme `TypedDict`. Toutes les cles sont passees de noeud
en noeud. Chaque noeud retourne un `dict` avec uniquement les cles qu'il modifie.

```python
class AgentState(TypedDict):
    # Entree
    user_query: str

    # Agent 1
    intent: Optional[Intent]
    intent_errors: List[str]

    # Agent 2
    selected_services: List[Dict[str, Any]]
    selection_errors: List[str]

    # Agent 3
    service_order: Optional[ServiceOrder]
    translation_errors: List[str]

    # Agent 4
    is_valid: bool
    validation_errors: List[str]
    validation_retry_count: int

    # Confirmation utilisateur
    user_approved: bool
    user_wants_to_retry: bool
    user_retry_count: int
    non_interactive_mode: bool    

    # Resultat final
    openslice_response: Optional[Dict[str, Any]]
    final_status: str
```

---

## Flux de donnees

```
Requete texte (str)
       |
       v
  [Agent 1]
  LLM (Llama 3.3 70B / Groq)
  Sortie : Intent (Pydantic)
       |
       | intent.sub_intents[].description
       v
  [Agent 2]
  ChromaDB (sentence-transformers embeddings)
  1 requete semantique par sous-intention
  Sortie : List[Dict] — services selectionnes avec score, id, metadata
       |
       | intent + selected_services
       v
  [Agent 3]
  LLM (Llama 3.3 70B / Groq)
  Sortie : ServiceOrder (Pydantic TMF641)
       |
       v
  [Agent 4]
  MCPClient.validate_service_order()
  Validation Pydantic schema + regles metier
  Sortie : (is_valid: bool, errors: List[str])
       |
       v
  [Confirmation]
  Streamlit UI ou terminal
       |
       v
  [Submit]
  MCPClient.submit_service_order()
  -> OpenSliceClient.submit_order() -> API REST TMF641
  Sortie : order_id (str)
```

---

## Couche MCP

La communication entre les agents et OpenSlice est abstraite par une couche MCP locale.

```
Agent / Orchestrateur
        |
        v
   MCPClient (mcp/mcp_client.py)
        |  appel par nom d'outil
        v
   OpenSliceMCPServer (mcp/openslice_mcp_server.py)
        |  dispatch vers le handler
        v
   OpenSliceClient (mcp/openslice_client.py)
        |  HTTP REST
        v
   OpenSlice API (TMF633 / TMF641 / TMF638)
```

Voir [mcp.md](mcp.md) pour le detail des outils et ressources exposes.

---

## Schemas de donnees

### Intent (schemas/intent.py)

Produit par Agent 1, consomme par Agent 2 et Agent 3.

```
Intent
  |- intent_id : str (optionnel)
  |- type      : str ("simple_service" | "composite_service")
  |- location  : str (optionnel — ville)
  |- qos       : Dict (optionnel — max_latency, min_bandwidth, ...)
  |- sub_intents : List[SubIntent]
       |- domain      : str (ex: "cloud", "ran", "database")
       |- description : str (requete semantique pour ChromaDB)
       |- requirements: Dict (exigences libres)
```

### ServiceOrder (schemas/tmf641.py)

Produit par Agent 3, valide par Agent 4, soumis a OpenSlice.

```
ServiceOrder
  |- externalId : str (= intent_id)
  |- priority   : str
  |- description: str
  |- state      : ServiceOrderStateType
  |- serviceOrderItem : List[ServiceOrderItem]
       |- id     : str
       |- action : ServiceOrderItemActionType ("add")
       |- service: Service
            |- name                : str
            |- serviceSpecification: ServiceSpecificationRef
                 |- id : str (UUID du service dans OpenSlice)
            |- serviceCharacteristic: List[ServiceCharacteristic]
                 |- name     : str
                 |- value    : Any
```
