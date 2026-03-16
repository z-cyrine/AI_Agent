"""
Orchestrateur LangGraph pour le pipeline complet.

Role : Orchestrer les 4 agents avec gestion des cycles et erreurs.
Utilise le protocole MCP pour communiquer avec OpenSlice.
"""
from typing import TypedDict, List, Dict, Any, Optional, Callable
from langgraph.graph import StateGraph, END
from datetime import datetime

from agents.agent1_interpreter import IntentInterpreterAgent
from agents.agent2_selector import ServiceSelectorAgent
from agents.agent3_translator import ServiceTranslatorAgent
from agents.agent4_validator import ServiceValidatorAgent
from mcp.mcp_client import MCPClient
from schemas.intent import Intent
from schemas.tmf641 import ServiceOrder
from config import settings


# ============================================================
# CONTEXTE GLOBAL POUR CALLBACKS UI
# ============================================================

class PipelineContext:
    """
    Contexte global pour les callbacks de l'interface utilisateur.
    Permet de suivre la progression du pipeline en temps réel.
    """
    
    def __init__(self):
        self._step_callback: Optional[Callable] = None
        self._feedback_callback: Optional[Callable] = None
        self._progress_callback: Optional[Callable] = None
        self.mock_mode: bool = settings.openslice_mock_mode
    
    def register_step_callback(self, callback: Callable[[str, str, Dict[str, Any]], None]):
        """
        Enregistre un callback appelé à chaque étape du pipeline.
        
        Args:
            callback(agent_name, status, details): Fonction appelée avec
                - agent_name: Nom de l'agent (agent1, agent2, etc.)
                - status: "started", "completed", "error"
                - details: Dictionnaire avec les détails de l'étape
        """
        self._step_callback = callback
    
    def register_feedback_callback(self, callback: Callable[["AgentState"], Dict[str, Any]]):
        """
        Enregistre un callback pour obtenir le feedback utilisateur.
        
        Args:
            callback(state): Fonction appelée pour obtenir le feedback
                - Retourne: {"user_approved": bool, "user_wants_to_retry": bool, ...}
        """
        self._feedback_callback = callback
    
    def register_progress_callback(self, callback: Callable[[str, float], None]):
        """
        Enregistre un callback pour la progression globale.
        
        Args:
            callback(message, progress): Fonction appelée avec
                - message: Message de progression
                - progress: Pourcentage (0.0 à 1.0)
        """
        self._progress_callback = callback
    
    def notify_step(self, agent_name: str, status: str, details: Dict[str, Any] = None):
        """Notifie le callback d'une étape"""
        if self._step_callback:
            try:
                self._step_callback(agent_name, status, details or {})
            except Exception as e:
                print(f"[Context] Erreur callback step: {e}")
    
    def notify_progress(self, message: str, progress: float):
        """Notifie le callback de progression"""
        if self._progress_callback:
            try:
                self._progress_callback(message, progress)
            except Exception as e:
                print(f"[Context] Erreur callback progress: {e}")
    
    def get_user_feedback(self, state: "AgentState") -> Dict[str, Any]:
        """Obtient le feedback utilisateur via callback"""
        if self._feedback_callback:
            try:
                return self._feedback_callback(state)
            except Exception as e:
                print(f"[Context] Erreur callback feedback: {e}")
        return None
    
    def reset(self):
        """Remet à zéro les callbacks"""
        self._step_callback = None
        self._feedback_callback = None
        self._progress_callback = None


# Instance globale du contexte
context = PipelineContext()


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

    # Confirmation utilisateur (NEW)
    user_approved: bool              # True = accepté, False = rejeté
    user_wants_to_retry: bool        # True = recommencer, False = arrêt
    user_retry_count: int            # Compte les reformulations (max 3)
    non_interactive_mode: bool       # True = skip terminal input() - pour Streamlit/tests

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
    context.notify_step("agent1", "started", {"query": state["user_query"][:100]})
    context.notify_progress("Agent 1: Interprétation de l'intention...", 0.1)

    try:
        agent = IntentInterpreterAgent()
        intent = agent.interpret(state["user_query"])

        print(f"[Agent 1] Intention generee : {intent.intent_id}")
        context.notify_step("agent1", "completed", {
            "intent_id": intent.intent_id,
            "type": intent.type,
            "sub_intents_count": len(intent.sub_intents),
            "location": intent.location
        })
        context.notify_progress("Agent 1: Intention structurée générée", 0.2)
        
        return {
            "intent": intent,
            "intent_errors": []
        }

    except Exception as e:
        print(f"[Agent 1] Erreur : {e}")
        context.notify_step("agent1", "error", {"error": str(e)})
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
    context.notify_step("agent2", "started", {"intent_id": state["intent"].intent_id if state["intent"] else None})
    context.notify_progress("Agent 2: Recherche sémantique des services...", 0.3)

    if not state["intent"]:
        context.notify_step("agent2", "error", {"error": "Aucune intention"})
        return {
            "selected_services": [],
            "selection_errors": ["Aucune intention recue de l'Agent 1"]
        }

    try:
        agent = ServiceSelectorAgent()
        services = agent.select_services(state["intent"])

        print(f"[Agent 2] {len(services)} service(s) selectionne(s)")
        context.notify_step("agent2", "completed", {
            "services_count": len(services),
            "services": [{"name": s.get("name"), "id": s.get("id")} for s in services[:5]]
        })
        context.notify_progress("Agent 2: Services sélectionnés", 0.4)
        
        return {
            "selected_services": services,
            "selection_errors": []
        }

    except Exception as e:
        print(f"[Agent 2] Erreur : {e}")
        context.notify_step("agent2", "error", {"error": str(e)})
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
    context.notify_step("agent3", "started", {"services_count": len(state["selected_services"])})
    context.notify_progress("Agent 3: Génération de l'ordre TMF641...", 0.5)

    if not state["intent"] or not state["selected_services"]:
        context.notify_step("agent3", "error", {"error": "Données manquantes"})
        return {
            "service_order": None,
            "translation_errors": ["Intention ou services manquants"]
        }

    try:
        agent = ServiceTranslatorAgent()
        service_order = agent.translate(state["intent"], state["selected_services"])

        print(f"[Agent 3] Ordre genere : {service_order.externalId}")
        context.notify_step("agent3", "completed", {
            "external_id": service_order.externalId,
            "items_count": len(service_order.serviceOrderItem),
            "priority": service_order.priority
        })
        context.notify_progress("Agent 3: Ordre TMF641 généré", 0.6)
        
        return {
            "service_order": service_order,
            "translation_errors": []
        }

    except Exception as e:
        print(f"[Agent 3] Erreur : {e}")
        context.notify_step("agent3", "error", {"error": str(e)})
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
    context.notify_step("agent4", "started", {"retry_count": state["validation_retry_count"]})
    context.notify_progress("Agent 4: Validation de l'ordre...", 0.7)

    if not state["service_order"]:
        context.notify_step("agent4", "error", {"error": "Pas d'ordre"})
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
            context.notify_step("agent4", "completed", {"is_valid": True, "errors": []})
            context.notify_progress("Agent 4: Validation réussie ✓", 0.8)
        else:
            print(f"[Agent 4] Validation echouee : {errors}")
            context.notify_step("agent4", "completed", {"is_valid": False, "errors": errors})

        return {
            "is_valid": is_valid,
            "validation_errors": errors,
            "validation_retry_count": state["validation_retry_count"] + 1
        }

    except Exception as e:
        print(f"[Agent 4] Erreur : {e}")
        context.notify_step("agent4", "error", {"error": str(e)})
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
    mode_label = "MOCK" if context.mock_mode else "OPENSLICE"
    context.notify_step("submit", "started", {"mode": mode_label})
    context.notify_progress(f"Soumission à {mode_label}...", 0.9)

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
            context.notify_step("submit", "completed", {
                "order_id": order_id,
                "order_state": result.get("order_state", "ACKNOWLEDGED"),
                "mode": mode_label
            })
            context.notify_progress("Pipeline terminé avec succès!", 1.0)
            return {
                "openslice_response": result,
                "final_status": "submitted"
            }
        else:
            print(f"[Submit] Erreur lors de la soumission : {result.get('message')}")
            context.notify_step("submit", "error", {"error": result.get('message')})
            return {
                "openslice_response": result,
                "final_status": "submission_failed"
            }

    except Exception as e:
        print(f"[Submit] Erreur lors de la soumission : {e}")
        context.notify_step("submit", "error", {"error": str(e)})
        return {
            "openslice_response": None,
            "final_status": "submission_failed"
        }


def user_confirmation_node(state: AgentState) -> dict:
    """
    Noeud 5 : Confirmation utilisateur avec 3 options
    - y : accepter et soumettre
    - n : rejeter et arrêter
    - r : rejeter et recommencer avec une nouvelle requête
    """
    print("\n[USER CONFIRMATION] Verification de l'ordre avant soumission...")
    
    # Mode non-interactif (Streamlit UI) - skip l'input() terminal
    # La confirmation sera gérée par l'UI externe
    if state.get("non_interactive_mode", False):
        print("[USER CONFIRMATION] Mode non-interactif: skip input() - confirmation via UI")
        # On retourne l'état actuel sans modifier user_approved
        # L'UI Streamlit récupérera le résultat et gèrera la confirmation
        return {
            "user_approved": state.get("user_approved", False),
            "user_wants_to_retry": False,
            "user_retry_count": state.get("user_retry_count", 0)
        }
    
    # Auto-approbation si déjà pré-approuvé
    if state.get("user_approved", False):
        print("[USER CONFIRMATION] Approbation automatique activée")
        return {
            "user_approved": True,
            "user_wants_to_retry": False,
            "user_retry_count": state["user_retry_count"]
        }
    
    if not state["service_order"]:
        return {
            "user_approved": False,
            "user_wants_to_retry": False,
            "user_retry_count": state["user_retry_count"]
        }
    
    order = state["service_order"]
    
    # Afficher le résumé
    print("\n" + "="*80)
    print("[RESUME DETAILLE DE L'ORDRE A SOUMETTRE]")
    print("="*80)
    print(f"\n[ID Externe]          : {order.externalId}")
    print(f"[Nombre d'items]      : {len(order.serviceOrderItem)}")
    print(f"[Priorite]            : {order.priority}")
    print(f"[Description]         : {order.description or 'N/A'}")
    
    # Afficher l'intention source si disponible
    if state["intent"]:
        print(f"\n[INTENTION SOURCE]:")
        print(f"   ID: {state['intent'].intent_id}")
        print(f"   Type: {state['intent'].type}")
        if state['intent'].location:
            print(f"   Localisation: {state['intent'].location}")
        if state['intent'].qos:
            print(f"   QoS: {state['intent'].qos}")
    
    print(f"\n[SERVICES A COMMANDER]:")
    print("-" * 80)
    
    for i, item in enumerate(order.serviceOrderItem, 1):
        service = item.service
        spec_id = service.serviceSpecification.id if service.serviceSpecification else "N/A"
        
        print(f"\n  {i}. {service.name or 'Service sans nom'}")
        print(f"     |- Action: {item.action}")
        print(f"     |- Quantity: {item.quantity}")
        print(f"     |- ServiceSpec ID: {spec_id}")
        
        # Afficher les caractéristiques si disponibles
        if service.serviceCharacteristic:
            print(f"     |-- Caracteristiques:")
            for char in service.serviceCharacteristic:
                char_name = char.name
                char_value = char.value
                
                # Afficher la valeur proprement (gérer les dicts imbriqués)
                if isinstance(char_value, dict) and 'value' in char_value:
                    char_value = char_value['value']
                
                print(f"        * {char_name}: {char_value}")
        else:
            print(f"     |-- Caracteristiques: Aucune")
    
    print("\n" + "="*80)
    print("\nOptions:")
    print("  (y) Accepter et soumettre l'ordre")
    print("  (n) Rejeter et arrêter le pipeline")
    print("  (r) Rejeter et recommencer avec une nouvelle requête")
    print("="*80)
    
    # Demander la confirmation
    while True:
        try:
            response = input("\n[CONFIRMATION] Que voulez-vous faire ? (y/n/r) : ").strip().lower()
            
            if response in ['y', 'yes', 'oui']:
                print("[USER CONFIRMATION] [OK] Ordre accepte - Passage a la soumission")
                return {
                    "user_approved": True,
                    "user_wants_to_retry": False,
                    "user_retry_count": state["user_retry_count"]
                }
            
            elif response in ['n', 'no', 'non']:
                print("[USER CONFIRMATION] [ERREUR] Ordre rejete - Arret du pipeline")
                return {
                    "user_approved": False,
                    "user_wants_to_retry": False,
                    "user_retry_count": state["user_retry_count"]
                }
            
            elif response in ['r', 'retry', 'recommencer']:
                print("[USER CONFIRMATION] [INFO] Recommençons avec une nouvelle requête")
                return {
                    "user_approved": False,
                    "user_wants_to_retry": True,
                    "user_retry_count": state["user_retry_count"] + 1
                }
            
            else:
                print("[AVERTISSEMENT] Veuillez repondre par 'y', 'n' ou 'r'")
        
        except KeyboardInterrupt:
            print("\n[USER CONFIRMATION] [AVERTISSEMENT] Annulation par Ctrl+C")
            return {
                "user_approved": False,
                "user_wants_to_retry": False,
                "user_retry_count": state["user_retry_count"]
            }
        except EOFError:
            # Mode non-interactif (tests)
            print("[USER CONFIRMATION] Mode non-interactif: approbation automatique")
            return {
                "user_approved": True,
                "user_wants_to_retry": False,
                "user_retry_count": state["user_retry_count"]
            }


def user_input_node(state: AgentState) -> dict:
    """
    Noeud intermédiaire : Demande une nouvelle requête à l'utilisateur
    Utilisé quand l'utilisateur choisit "recommencer" (r)
    
    Réinitialise tous les champs pour préparer une nouvelle itération
    """
    print("\n[USER INPUT] Entrez votre nouvelle requête:")
    
    while True:
        try:
            new_query = input("\n[ENTREE] Nouvelle requête (ou 'quit' pour quitter) : ").strip()
            
            if new_query.lower() in ['quit', 'exit', 'q']:
                print("[USER INPUT] [ARRET] Annulation par l'utilisateur")
                return {
                    "user_query": state["user_query"],  # Garder l'ancienne requête
                    "user_wants_to_retry": False,  # Arrêter le pipeline
                    "user_retry_count": state["user_retry_count"],
                    "intent": None,
                    "intent_errors": [],
                    "selected_services": [],
                    "selection_errors": [],
                    "service_order": None,
                    "translation_errors": [],
                    "is_valid": False,
                    "validation_errors": [],
                    "validation_retry_count": 0,
                    "user_approved": False,
                    "openslice_response": None,
                    "final_status": "user_cancelled"
                }
            
            if not new_query:
                print("[AVERTISSEMENT] Veuillez entrer une requête non vide")
                continue
            
            print(f"[USER INPUT] [OK] Nouvelle requête acceptée")
            print(f"   {new_query[:80]}{'...' if len(new_query) > 80 else ''}")
            
            # Retourner la nouvelle requête ET réinitialiser les champs des agents précédents
            return {
                "user_query": new_query,  # NOUVELLE requête
                "user_wants_to_retry": True,
                "user_retry_count": state["user_retry_count"],
                "intent": None,
                "intent_errors": [],
                "selected_services": [],
                "selection_errors": [],
                "service_order": None,
                "translation_errors": [],
                "is_valid": False,
                "validation_errors": [],
                "validation_retry_count": 0,
                "user_approved": False,
                "openslice_response": None,
                "final_status": "pending"
            }
        
        except KeyboardInterrupt:
            print("\n[USER INPUT] [AVERTISSEMENT] Annulation par Ctrl+C")
            return {
                "user_query": state["user_query"],
                "user_wants_to_retry": False,
                "user_retry_count": state["user_retry_count"],
                "intent": None,
                "intent_errors": [],
                "selected_services": [],
                "selection_errors": [],
                "service_order": None,
                "translation_errors": [],
                "is_valid": False,
                "validation_errors": [],
                "validation_retry_count": 0,
                "user_approved": False,
                "openslice_response": None,
                "final_status": "user_cancelled"
            }
        except EOFError:
            # Mode non-interactif
            print("[USER INPUT] Mode non-interactif: arret")
            return {
                "user_query": state["user_query"],
                "user_wants_to_retry": False,
                "user_retry_count": state["user_retry_count"],
                "intent": None,
                "intent_errors": [],
                "selected_services": [],
                "selection_errors": [],
                "service_order": None,
                "translation_errors": [],
                "is_valid": False,
                "validation_errors": [],
                "validation_retry_count": 0,
                "user_approved": False,
                "openslice_response": None,
                "final_status": "user_cancelled"
            }


# ============================================================
# ROUTAGE CONDITIONNEL
# ============================================================

def should_retry_translation(state: AgentState) -> str:
    """
    Fonction de routage apres l'Agent 4.

    Retourne :
      - "confirm" : validation OK, aller à la confirmation utilisateur
      - "retry"   : validation KO mais retry_count < 3, on repasse par Agent 3
      - "error"   : trop de retries, on abandonne
    """
    if state["is_valid"]:
        return "confirm"  # Aller à la confirmation utilisateur
    elif state["validation_retry_count"] < 3:
        print(f"[Routage] Retry {state['validation_retry_count']}/3 -- Retour a l'Agent 3")
        return "retry"
    else:
        print("[Routage] Trop de retries -- Abandon")
        return "error"


def should_submit_retry_or_stop(state: AgentState) -> str:
    """
    Fonction de routage apres la confirmation utilisateur.
    
    Retourne :
      - "submit"  : utilisateur accepte l'ordre
      - "retry"   : utilisateur veut recommencer (retour à Agent 1)
      - "stopped" : utilisateur arrête définitivement
    """
    if state["user_approved"]:
        return "submit"  # Aller au Submit
    
    elif state["user_wants_to_retry"] and state["user_retry_count"] < 3:
        print(f"[Routage] Retry utilisateur {state['user_retry_count']}/3 -- Retour à User Input")
        return "retry"  # Retour à User Input
    
    else:
        print("[Routage] Pipeline arrêté par l'utilisateur")
        return "stopped"  # Arrêt définitif


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
                                         (confirm) -> UserConfirmation -> ?
                                         (submit) -> OpenSlice (via MCP) -> END
                                         (error)                         -> END
                                         (stopped)                       -> END
                                         (retry)                         -> UserInput -> Agent1
    """
    workflow = StateGraph(AgentState)

    # Ajout des noeuds
    workflow.add_node("agent1", agent1_node)
    workflow.add_node("agent2", agent2_node)
    workflow.add_node("agent3", agent3_node)
    workflow.add_node("agent4", agent4_node)
    workflow.add_node("submit", submit_to_openslice)
    workflow.add_node("confirm", user_confirmation_node)
    workflow.add_node("user_input", user_input_node)

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
            "confirm": "confirm", # validation OK
            "error":  END        # trop de retries
        }
    )

    # Confirmation utilisateur
    workflow.add_conditional_edges(
        "confirm",
        should_submit_retry_or_stop,
        {
            "submit": "submit",  # utilisateur accepte
            "retry": "user_input",   # utilisateur veut recommencer
            "stopped": END       # utilisateur arrête
        }
    )

    # Flux après User Input
    workflow.add_edge("user_input", "agent1")

    # Fin apres soumission
    workflow.add_edge("submit", END)

    return workflow.compile()


# ============================================================
# TEST DIRECT
# ============================================================

# if __name__ == "__main__":
#     print("=" * 60)
#     print("TEST -- Orchestrateur LangGraph avec MCP")
#     print("=" * 60)

#     app = create_workflow()

#     initial_state = AgentState(
#         user_query="I need XR applications with 5G connectivity in Nice",
#         intent=None,
#         intent_errors=[],
#         selected_services=[],
#         selection_errors=[],
#         service_order=None,
#         translation_errors=[],
#         is_valid=False,
#         validation_errors=[],
#         validation_retry_count=0,
#         user_approved=False,
#         user_wants_to_retry=False,
#         user_retry_count=0,
#         openslice_response=None,
#         final_status="pending"
#     )

#     result = app.invoke(initial_state)

#     print("\n" + "=" * 60)
#     print("RESULTAT FINAL")
#     print("=" * 60)
#     print(f"Statut         : {result['final_status']}")
#     print(f"Ordre valide   : {result['is_valid']}")
#     print(f"Retries        : {result['validation_retry_count']}")

#     if result["openslice_response"]:
#         print(f"Statut MCP     : {result['openslice_response'].get('status')}")
#         if result['openslice_response'].get('status') == 'success':
#             print(f"ID OpenSlice   : {result['openslice_response'].get('order_id')}")

#     if result["validation_errors"]:
#         print(f"Erreurs        : {result['validation_errors']}")