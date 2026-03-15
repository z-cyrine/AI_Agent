"""
Orchestrateur LangGraph pour le pipeline complet.

Role : Orchestrer les 4 agents avec gestion des cycles et erreurs.
Utilise le protocole MCP pour communiquer avec OpenSlice.
"""
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END

from agents.agent1_interpreter import IntentInterpreterAgent
from agents.agent2_selector import ServiceSelectorAgent
from agents.agent3_translator import ServiceTranslatorAgent
from agents.agent4_validator import ServiceValidatorAgent
from mcp.mcp_client import MCPClient
from schemas.intent import Intent
from schemas.tmf641 import ServiceOrder


# ============================================================
# ETAT PARTAGE ENTRE TOUS LES NOEUDS
# ============================================================

class AgentState(TypedDict):
    """
    Etat qui circule dans le graphe LangGraph.
    Chaque noeud lit cet etat et le met a jour avant de le passer au suivant.
    """
    # Entree utilisateur
    user_query: str

    # Agent 1 : intention structuree
    intent: Optional[Intent]
    intent_errors: List[str]

    # Agent 2 : services selectionnes
    selected_services: List[Dict[str, Any]]
    selection_errors: List[str]

    # Agent 3 : ordre de service TMF641
    service_order: Optional[ServiceOrder]
    translation_errors: List[str]

    # Agent 4 : validation
    is_valid: bool
    validation_errors: List[str]
    validation_retry_count: int

    # Resultat final
    openslice_response: Optional[Dict[str, Any]]
    final_status: str


# ============================================================
# NOEUDS DU GRAPHE
# ============================================================

def agent1_node(state: AgentState) -> dict:
    """
    Noeud Agent 1 : Interpretation.
    Transforme la requete en langage naturel en intention structuree (JSON).
    """
    print("\n[Agent 1] Interpretation de la requete...")

    try:
        agent = IntentInterpreterAgent()
        intent = agent.interpret(state["user_query"])

        print(f"[Agent 1] Intention generee : {intent.intent_id}")
        return {
            "intent": intent,
            "intent_errors": []
        }

    except Exception as e:
        print(f"[Agent 1] Erreur : {e}")
        return {
            "intent": None,
            "intent_errors": [str(e)]
        }


def agent2_node(state: AgentState) -> dict:
    """
    Noeud Agent 2 : Selection de services via RAG.
    Interroge ChromaDB pour trouver les services correspondant a l'intention.
    """
    print("\n[Agent 2] Selection des services...")

    if not state["intent"]:
        return {
            "selected_services": [],
            "selection_errors": ["Aucune intention recue de l'Agent 1"]
        }

    try:
        agent = ServiceSelectorAgent()
        services = agent.select_services(state["intent"])

        print(f"[Agent 2] {len(services)} service(s) selectionne(s)")
        return {
            "selected_services": services,
            "selection_errors": []
        }

    except Exception as e:
        print(f"[Agent 2] Erreur : {e}")
        return {
            "selected_services": [],
            "selection_errors": [str(e)]
        }


def agent3_node(state: AgentState) -> dict:
    """
    Noeud Agent 3 : Traduction en ordre TMF641.
    Genere le ServiceOrder a partir de l'intention et des services selectionnes.
    Appele aussi bien la premiere fois que lors d'un retry apres validation echouee.
    """
    print("\n[Agent 3] Generation de l'ordre TMF641...")

    if not state["intent"] or not state["selected_services"]:
        return {
            "service_order": None,
            "translation_errors": ["Intention ou services manquants"]
        }

    try:
        agent = ServiceTranslatorAgent()
        service_order = agent.translate(state["intent"], state["selected_services"])

        print(f"[Agent 3] Ordre genere : {service_order.externalId}")
        return {
            "service_order": service_order,
            "translation_errors": []
        }

    except Exception as e:
        print(f"[Agent 3] Erreur : {e}")
        return {
            "service_order": None,
            "translation_errors": [str(e)]
        }


def agent4_node(state: AgentState) -> dict:
    """
    Noeud Agent 4 : Validation de l'ordre TMF641.
    Verifie la conformite du ServiceOrder avant soumission via MCP.
    Incremente le compteur de retry a chaque appel.
    """
    print("\n[Agent 4] Validation de l'ordre...")

    if not state["service_order"]:
        return {
            "is_valid": False,
            "validation_errors": ["Aucun ordre de service a valider"],
            "validation_retry_count": state["validation_retry_count"] + 1
        }

    try:
        agent = ServiceValidatorAgent()
        is_valid, errors = agent.validate(state["service_order"])

        if is_valid:
            print("[Agent 4] Validation reussie")
        else:
            print(f"[Agent 4] Validation echouee : {errors}")

        return {
            "is_valid": is_valid,
            "validation_errors": errors,
            "validation_retry_count": state["validation_retry_count"] + 1
        }

    except Exception as e:
        print(f"[Agent 4] Erreur : {e}")
        return {
            "is_valid": False,
            "validation_errors": [str(e)],
            "validation_retry_count": state["validation_retry_count"] + 1
        }


def submit_to_openslice(state: AgentState) -> dict:
    """
    Noeud final : Soumission de l'ordre a OpenSlice via MCP.
    Utilise l'outil MCP "submit_service_order" pour assurer une communication standardisee.
    """
    print("\n[Submit] Soumission de l'ordre a OpenSlice via MCP...")

    try:
        mcp_client = MCPClient(mode="local")
        
        # Convertir l'ordre en JSON
        order_json = state["service_order"].model_dump_json(exclude_none=True)
        
        # Soumettre via l'outil MCP
        result = mcp_client.submit_service_order(order_json)
        mcp_client.close()

        if result.get("status") == "success":
            order_id = result.get("order_id", "inconnu")
            print(f"[Submit] Ordre soumis avec succes -- ID : {order_id}")
            return {
                "openslice_response": result,
                "final_status": "submitted"
            }
        else:
            print(f"[Submit] Erreur lors de la soumission : {result.get('message')}")
            return {
                "openslice_response": result,
                "final_status": "submission_failed"
            }

    except Exception as e:
        print(f"[Submit] Erreur lors de la soumission : {e}")
        return {
            "openslice_response": None,
            "final_status": "submission_failed"
        }


# ============================================================
# ROUTAGE CONDITIONNEL
# ============================================================

def should_retry_translation(state: AgentState) -> str:
    """
    Fonction de routage apres l'Agent 4.

    Retourne :
      - "submit"  : validation OK, on soumet a OpenSlice
      - "retry"   : validation KO mais retry_count < 3, on repasse par Agent 3
      - "error"   : trop de retries, on abandonne
    """
    if state["is_valid"]:
        return "submit"
    elif state["validation_retry_count"] < 3:
        print(f"[Routage] Retry {state['validation_retry_count']}/3 -- Retour a l'Agent 3")
        return "retry"
    else:
        print("[Routage] Trop de retries -- Abandon")
        return "error"


# ============================================================
# CONSTRUCTION DU GRAPHE
# ============================================================

def create_workflow():
    """
    Cree et compile le graphe LangGraph complet.

    Flux :
      START -> Agent1 -> Agent2 -> Agent3 -> Agent4 -> ?
                                     ^           |
                                     |    (retry)|
                                     +-----------+
                                         (submit) -> OpenSlice (via MCP) -> END
                                         (error)                         -> END
    """
    workflow = StateGraph(AgentState)

    # Ajout des noeuds
    workflow.add_node("agent1", agent1_node)
    workflow.add_node("agent2", agent2_node)
    workflow.add_node("agent3", agent3_node)
    workflow.add_node("agent4", agent4_node)
    workflow.add_node("submit", submit_to_openslice)

    # Flux sequentiel
    workflow.set_entry_point("agent1")
    workflow.add_edge("agent1", "agent2")
    workflow.add_edge("agent2", "agent3")
    workflow.add_edge("agent3", "agent4")

    # Routage conditionnel apres Agent 4
    workflow.add_conditional_edges(
        "agent4",
        should_retry_translation,
        {
            "retry":  "agent3",  # boucle de correction
            "submit": "submit",  # validation OK
            "error":  END        # trop de retries
        }
    )

    # Fin apres soumission
    workflow.add_edge("submit", END)

    return workflow.compile()


# ============================================================
# TEST DIRECT
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TEST -- Orchestrateur LangGraph avec MCP")
    print("=" * 60)

    app = create_workflow()

    initial_state = AgentState(
        user_query="I need XR applications with 5G connectivity in Nice",
        intent=None,
        intent_errors=[],
        selected_services=[],
        selection_errors=[],
        service_order=None,
        translation_errors=[],
        is_valid=False,
        validation_errors=[],
        validation_retry_count=0,
        openslice_response=None,
        final_status="pending"
    )

    result = app.invoke(initial_state)

    print("\n" + "=" * 60)
    print("RESULTAT FINAL")
    print("=" * 60)
    print(f"Statut         : {result['final_status']}")
    print(f"Ordre valide   : {result['is_valid']}")
    print(f"Retries        : {result['validation_retry_count']}")

    if result["openslice_response"]:
        print(f"Statut MCP     : {result['openslice_response'].get('status')}")
        if result['openslice_response'].get('status') == 'success':
            print(f"ID OpenSlice   : {result['openslice_response'].get('order_id')}")

    if result["validation_errors"]:
        print(f"Erreurs        : {result['validation_errors']}")