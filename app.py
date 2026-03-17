"""
Interface Streamlit avec Confirmation Interactive

En mode Mock : auto-approbation
En mode OpenSlice : demande RÉELLE de confirmation à l'utilisateur
"""

import streamlit as st
import json
import time
from datetime import datetime
from typing import Dict, Any

# Configuration de la page
st.set_page_config(
    page_title="IBN Pipeline - Live Demo",
    page_icon="🚀",
    layout="wide"
)

# ============================================================
# CSS - Cached pour éviter le retraitement à chaque rerun
# ============================================================

@st.cache_data
def get_css():
    return """
<style>
    /* Fonts loaded async via link preload in HTML */
    .main { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
    
    /* Reduce top padding */
    .block-container { padding-top: 1rem !important; }
    
    /* JSON viewer compact */
    [data-testid="stJson"] {
        line-height: 1.2 !important;
        font-size: 0.8rem !important;
    }
    [data-testid="stJson"] * {
        line-height: 1.2 !important;
    }
    
    /* Override Streamlit primary button - Classy blue */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
        border: none !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.35) !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #818cf8 0%, #6366f1 100%) !important;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.45) !important;
        transform: translateY(-1px);
    }
    .stButton > button[kind="primary"]:active {
        transform: translateY(0);
    }
    
    /* Secondary button style */
    .stButton > button:not([kind="primary"]) {
        background: rgba(99, 102, 241, 0.1) !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        color: #a5b4fc !important;
    }
    .stButton > button:not([kind="primary"]):hover {
        background: rgba(99, 102, 241, 0.2) !important;
        border-color: rgba(99, 102, 241, 0.5) !important;
    }
    
    /* Text area styling */
    .stTextArea textarea {
        border-radius: 12px !important;
        padding: 16px !important;
        line-height: 1.6 !important;
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        background: rgba(15, 23, 42, 0.6) !important;
    }
    .stTextArea textarea:focus {
        border-color: rgba(99, 102, 241, 0.5) !important;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.15) !important;
    }
    
    /* Header - Compact & Clean */
    .main-header {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(79, 70, 229, 0.1) 100%);
        backdrop-filter: blur(10px);
        padding: 1rem 1.5rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(99, 102, 241, 0.2);
        position: relative;
    }
    .main-header h1 { 
        margin: 0; 
        font-size: 1.4rem; 
        font-weight: 600;
        background: linear-gradient(135deg, #a5b4fc 0%, #818cf8 50%, #6366f1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.3px;
    }
    
    /* Pipeline container with vertical line */
    .pipeline-container {
        position: relative;
        padding-left: 20px;
    }
    .pipeline-container::before {
        content: '';
        position: absolute;
        left: 8px;
        top: 20px;
        bottom: 20px;
        width: 2px;
        background: linear-gradient(180deg, rgba(99, 102, 241, 0.4) 0%, rgba(79, 70, 229, 0.2) 100%);
        border-radius: 2px;
    }
    
    /* Agent Card */
    .agent-card {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.6rem;
        margin-left: 12px;
        border: 1px solid rgba(99, 102, 241, 0.1);
        border-left: 3px solid #475569;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
    }
    /* Connector dot */
    .agent-card::before {
        content: '';
        position: absolute;
        left: -20px;
        top: 50%;
        transform: translateY(-50%);
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #475569;
        border: 2px solid #1e293b;
        transition: all 0.3s ease;
    }
    
    .agent-card.pending { 
        border-left-color: #475569; 
        opacity: 0.5;
    }
    .agent-card.pending::before {
        background: #475569;
    }
    
    .agent-card.running { 
        border-left-color: #6366f1; 
        background: linear-gradient(145deg, rgba(99, 102, 241, 0.1) 0%, rgba(79, 70, 229, 0.05) 100%);
        box-shadow: 0 0 25px rgba(99, 102, 241, 0.15);
        opacity: 1;
        transform: translateX(4px);
    }
    .agent-card.running::before {
        background: #6366f1;
        box-shadow: 0 0 10px rgba(99, 102, 241, 0.6);
        animation: pulse-dot 1.5s ease-in-out infinite;
    }
    @keyframes pulse-dot {
        0%, 100% { box-shadow: 0 0 5px rgba(99, 102, 241, 0.4); }
        50% { box-shadow: 0 0 15px rgba(99, 102, 241, 0.8); }
    }
    
    .agent-card.completed { 
        border-left-color: #10b981; 
        opacity: 1; 
    }
    .agent-card.completed::before {
        background: #10b981;
    }
    
    .agent-card.error { 
        border-left-color: #ef4444; 
        opacity: 1; 
    }
    .agent-card.error::before {
        background: #ef4444;
    }
    
    .agent-card.waiting { 
        border-left-color: #6366f1; 
        background: linear-gradient(145deg, rgba(99, 102, 241, 0.08) 0%, rgba(79, 70, 229, 0.04) 100%);
        box-shadow: 0 0 20px rgba(99, 102, 241, 0.1);
        opacity: 1;
    }
    .agent-card.waiting::before {
        background: #6366f1;
    }
    
    .agent-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 4px;
    }
    .agent-icon {
        font-size: 1.1rem;
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        background: linear-gradient(145deg, rgba(99, 102, 241, 0.15) 0%, rgba(79, 70, 229, 0.1) 100%);
        border: 1px solid rgba(99, 102, 241, 0.2);
    }
    .agent-name {
        font-weight: 600;
        font-size: 0.9rem;
        color: #e2e8f0;
    }
    .agent-status {
        font-size: 0.75rem;
        color: #94a3b8;
        margin-left: auto;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .agent-status.running { color: #818cf8; }
    .agent-status.completed { color: #10b981; }
    .agent-status.error { color: #ef4444; }
    .agent-status.waiting { color: #818cf8; }
    
    .agent-desc {
        color: #94a3b8;
        font-size: 0.78rem;
        margin-left: 48px;
        margin-bottom: 6px;
        line-height: 1.4;
    }
    
    /* Output box */
    .agent-output {
        background: rgba(15, 23, 42, 0.8);
        border-radius: 8px;
        padding: 10px 12px;
        margin-top: 8px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        line-height: 1.5;
        color: #cbd5e1;
        max-height: 150px;
        overflow-y: auto;
        border: 1px solid rgba(99, 102, 241, 0.1);
    }
    .output-line { margin: 2px 0; }
    .output-key { color: #818cf8; }
    .output-value { color: #34d399; }
    .output-label { color: #a5b4fc; font-weight: 500; }
    .output-error { color: #f87171; }
    .output-success { color: #34d399; }
    
    /* Spinner - blue theme */
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .spinner {
        display: inline-block;
        width: 12px;
        height: 12px;
        border: 2px solid #6366f1;
        border-top-color: transparent;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
        margin-right: 6px;
        vertical-align: middle;
    }
    
    /* Banners */
    .success-banner {
        background: linear-gradient(145deg, rgba(16, 185, 129, 0.12) 0%, rgba(5, 150, 105, 0.08) 100%);
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 1.2rem;
        border-radius: 12px;
        color: #34d399;
        text-align: center;
        margin: 1rem 0;
    }
    .success-banner h3 { margin: 0 0 0.3rem 0; font-size: 1rem; }
    .success-banner p { margin: 0; font-size: 0.85rem; opacity: 0.85; }
    
    .cancelled-banner {
        background: linear-gradient(145deg, rgba(251, 191, 36, 0.12) 0%, rgba(245, 158, 11, 0.08) 100%);
        border: 1px solid rgba(251, 191, 36, 0.3);
        padding: 1.2rem;
        border-radius: 12px;
        color: #fbbf24;
        text-align: center;
        margin: 1rem 0;
    }
    
    /* Section titles */
    .section-title {
        color: #a5b4fc;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .section-title::after {
        content: '';
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, rgba(99, 102, 241, 0.3), transparent);
    }
    
    /* Expanders - Blue theme like agent cards */
    .streamlit-expanderHeader,
    [data-testid="stExpander"] > div:first-child,
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] > details > summary {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%) !important;
        border: 1px solid rgba(59, 130, 246, 0.1) !important;
        border-left: 3px solid #3b82f6 !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
        padding: 1rem 1.2rem !important;
    }
    [data-testid="stExpander"],
    [data-testid="stExpander"] > details {
        background: transparent !important;
        border: none !important;
    }
    [data-testid="stExpander"] > div:first-child:hover,
    [data-testid="stExpander"] summary:hover,
    [data-testid="stExpander"] > details > summary:hover {
        border-color: rgba(59, 130, 246, 0.3) !important;
        border-left-color: #60a5fa !important;
        background: linear-gradient(145deg, rgba(59, 130, 246, 0.1) 0%, rgba(37, 99, 235, 0.05) 100%) !important;
    }
    .streamlit-expanderContent,
    [data-testid="stExpander"] > div:last-child,
    [data-testid="stExpander"] > details > div {
        background: rgba(15, 23, 42, 0.85) !important;
        border: 1px solid rgba(59, 130, 246, 0.15) !important;
        border-left: 3px solid rgba(59, 130, 246, 0.3) !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
        margin-top: -4px !important;
    }
    
    /* Info boxes - Sober dark theme like agent cards */
    .stAlert,
    [data-testid="stAlert"],
    div[data-baseweb="notification"] {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%) !important;
        border: 1px solid rgba(71, 85, 105, 0.3) !important;
        border-left: 3px solid #475569 !important;
        border-radius: 10px !important;
        color: #94a3b8 !important;
    }
    .stAlert p,
    [data-testid="stAlert"] p {
        color: #94a3b8 !important;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(30, 41, 59, 0.5);
        border-radius: 8px 8px 0 0;
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-bottom: none;
        color: #94a3b8;
        padding: 10px 20px;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(99, 102, 241, 0.1);
        color: #a5b4fc;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(99, 102, 241, 0.15) !important;
        border-color: rgba(99, 102, 241, 0.3) !important;
        color: #a5b4fc !important;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        background: #6366f1 !important;
    }
    
    /* Hide Streamlit stuff */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    header {visibility: hidden;}
</style>
"""

st.markdown(get_css(), unsafe_allow_html=True)

# ============================================================
# Imports du projet - Lazy loading pour accélérer le démarrage
# ============================================================

# Note: config et orchestrator sont importés au moment de l'exécution
# pour éviter le délai de chargement au démarrage

# ============================================================
# État de session
# ============================================================

def init_state():
    defaults = {
        "agents_state": {
            "agent1": {"status": "pending", "output": None},
            "agent2": {"status": "pending", "output": None},
            "agent3": {"status": "pending", "output": None},
            "agent4": {"status": "pending", "output": None},
            "confirm": {"status": "pending", "output": None},
            "submit": {"status": "pending", "output": None},
        },
        "is_running": False,
        "pipeline_result": None,  # Résultat après Agent 4
        "awaiting_confirmation": False,  # En attente de décision utilisateur
        "user_decision": None,  # "accept" ou "reject"
        "final_result": None,
        "show_rejected_message": False,  # Afficher le message après rejet
        "trigger_run": False,  # Flag pour déclencher le pipeline
        "saved_query": "",  # Sauvegarde de la requête
        "raw_json_outputs": {  # JSON bruts des agents
            "agent1_intent": None,
            "agent2_services": None,
            "agent3_order": None,
            "agent4_validation": None,
            "submit_response": None,
        },
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ============================================================
# Fonctions d'affichage
# ============================================================

def render_agent_html(agent_id: str, name: str, icon: str, description: str) -> str:
    state = st.session_state.agents_state[agent_id]
    status = state["status"]
    output = state["output"]
    
    if status == "pending":
        status_html = '<span class="agent-status">⏳ En attente</span>'
    elif status == "running":
        status_html = '<span class="agent-status running"><span class="spinner"></span>En cours...</span>'
    elif status == "completed":
        status_html = '<span class="agent-status completed">Terminé</span>'
    elif status == "error":
        status_html = '<span class="agent-status error">❌ Erreur</span>'
    elif status == "waiting":
        status_html = '<span class="agent-status waiting">🔵 En attente de votre décision</span>'
    else:
        status_html = f'<span class="agent-status">{status}</span>'
    
    output_html = ""
    if output and status in ["completed", "error", "running", "waiting"]:
        lines = []
        for key, value in output.items():
            if isinstance(value, list):
                lines.append(f'<div class="output-line"><span class="output-label">{key}:</span></div>')
                for item in value[:4]:
                    if isinstance(item, dict):
                        item_str = " | ".join([f'{k}: {v}' for k, v in item.items()])
                        lines.append(f'<div class="output-line">  → {item_str}</div>')
                    else:
                        lines.append(f'<div class="output-line">  → <span class="output-value">{item}</span></div>')
                if len(value) > 4:
                    lines.append(f'<div class="output-line">  ... +{len(value)-4} autres</div>')
            elif isinstance(value, dict):
                lines.append(f'<div class="output-line"><span class="output-label">{key}:</span></div>')
                for k, v in value.items():
                    lines.append(f'<div class="output-line">  <span class="output-key">{k}:</span> <span class="output-value">{v}</span></div>')
            elif "error" in key.lower() or "❌" in str(value):
                lines.append(f'<div class="output-line"><span class="output-error">{key}: {value}</span></div>')
            elif "✅" in str(value) or "success" in key.lower():
                lines.append(f'<div class="output-line"><span class="output-success">{key}: {value}</span></div>')
            else:
                lines.append(f'<div class="output-line"><span class="output-key">{key}:</span> <span class="output-value">{value}</span></div>')
        
        output_html = f'<div class="agent-output">{"".join(lines)}</div>'
    
    return f"""
    <div class="agent-card {status}">
        <div class="agent-header">
            <div class="agent-icon">{icon}</div>
            <div class="agent-name">{name}</div>
            {status_html}
        </div>
        <div class="agent-desc">{description}</div>
        {output_html}
    </div>
    """

def update_display(placeholders: dict):
    agents = [
        ("agent1", "Agent 1 - Interpréteur", "🧠", "Transforme le langage naturel → Intention JSON"),
        ("agent2", "Agent 2 - Sélecteur RAG", "🔍", "Recherche sémantique dans ChromaDB"),
        ("agent3", "Agent 3 - Traducteur", "📝", "Génère l'ordre TMF641"),
        ("agent4", "Agent 4 - Validateur", "✅", "Valide via MCP"),
        ("confirm", "Confirmation", "👤", "Approbation de l'ordre"),
        ("submit", "Soumission", "🚀", "Envoi vers OpenSlice"),
    ]
    
    for agent_id, name, icon, desc in agents:
        html = render_agent_html(agent_id, name, icon, desc)
        placeholders[agent_id].markdown(html, unsafe_allow_html=True)

# ============================================================
# Exécution du pipeline - Phase 1 (jusqu'à validation)
# ============================================================

def run_pipeline_phase1(user_query: str, placeholders: dict):
    """Exécute le pipeline jusqu'à la validation (sans soumettre)"""
    from orchestrator import create_workflow, AgentState
    
    # Reset
    for aid in st.session_state.agents_state:
        st.session_state.agents_state[aid] = {"status": "pending", "output": None}
    update_display(placeholders)
    
    try:
        # Agent 1 - Running
        st.session_state.agents_state["agent1"]["status"] = "running"
        st.session_state.agents_state["agent1"]["output"] = {"traitement": "Analyse de la requête..."}
        update_display(placeholders)
        
        workflow = create_workflow()
        
        # ⚠️ non_interactive_mode=True pour éviter le input() bloquant dans le terminal
        initial_state = AgentState(
            user_query=user_query,
            intent=None, intent_errors=[],
            selected_services=[], selection_errors=[],
            service_order=None, translation_errors=[],
            is_valid=False, validation_errors=[],
            validation_retry_count=0,
            user_approved=False,  # On ne soumet PAS encore
            user_wants_to_retry=False,
            user_retry_count=0,
            non_interactive_mode=True,  # Skip le input() terminal - confirmation via UI
            openslice_response=None,
            final_status="pending"
        )
        
        result = workflow.invoke(initial_state)
        
        # ===== Mise à jour Agent 1 =====
        if result.get("intent"):
            intent = result["intent"]
            # Afficher TOUTES les sous-intentions
            sub_intents_info = [{"domain": si.domain, "desc": si.description} for si in intent.sub_intents]
            st.session_state.agents_state["agent1"]["status"] = "completed"
            st.session_state.agents_state["agent1"]["output"] = {
                "intent_id": intent.intent_id,
                "type": intent.type,
                "location": intent.location or "N/A",
                "qos": str(intent.qos) if intent.qos else "N/A",
                "nb_sous_intentions": len(intent.sub_intents),
                "sous_intentions": sub_intents_info
            }
            # Stocker le JSON brut de l'intent
            st.session_state.raw_json_outputs["agent1_intent"] = intent.model_dump(mode='json')
        else:
            st.session_state.agents_state["agent1"]["status"] = "error"
            st.session_state.agents_state["agent1"]["output"] = {"erreur": str(result.get("intent_errors", ["?"]))}
            st.session_state.raw_json_outputs["agent1_intent"] = {"errors": result.get("intent_errors", [])}
        update_display(placeholders)
        time.sleep(0.2)
        
        # ===== Mise à jour Agent 2 =====
        st.session_state.agents_state["agent2"]["status"] = "running"
        update_display(placeholders)
        time.sleep(0.3)
        
        if result.get("selected_services"):
            svcs = result["selected_services"]
            # Afficher TOUS les services avec plus de détails
            svc_list = [{"nom": s.get("name", "?"), "id": s.get("id", "?"), "score": round(s.get("score", 0), 3)} for s in svcs]
            st.session_state.agents_state["agent2"]["status"] = "completed"
            st.session_state.agents_state["agent2"]["output"] = {
                "nb_services": f"{len(svcs)} service(s)",
                "services": svc_list
            }
            # Stocker le JSON brut des services sélectionnés
            st.session_state.raw_json_outputs["agent2_services"] = svcs
        else:
            st.session_state.agents_state["agent2"]["status"] = "completed"
            st.session_state.agents_state["agent2"]["output"] = {"warning": "⚠️ Aucun service trouvé"}
            st.session_state.raw_json_outputs["agent2_services"] = []
        update_display(placeholders)
        time.sleep(0.2)
        
        # ===== Mise à jour Agent 3 =====
        st.session_state.agents_state["agent3"]["status"] = "running"
        update_display(placeholders)
        time.sleep(0.3)
        
        if result.get("service_order"):
            order = result["service_order"]
            # Afficher TOUS les items
            items = [{"service": item.service.name or "N/A", "action": str(item.action.value) if hasattr(item.action, 'value') else str(item.action)} for item in order.serviceOrderItem]
            st.session_state.agents_state["agent3"]["status"] = "completed"
            st.session_state.agents_state["agent3"]["output"] = {
                "order_id": order.externalId,
                "nb_items": len(order.serviceOrderItem),
                "priority": order.priority,
                "items": items
            }
            # Stocker le JSON brut de l'ordre TMF641
            st.session_state.raw_json_outputs["agent3_order"] = order.model_dump(mode='json', exclude_none=True)
        else:
            st.session_state.agents_state["agent3"]["status"] = "error"
            st.session_state.agents_state["agent3"]["output"] = {"erreur": str(result.get("translation_errors", []))}
            st.session_state.raw_json_outputs["agent3_order"] = {"errors": result.get("translation_errors", [])}
        update_display(placeholders)
        time.sleep(0.2)
        
        # ===== Mise à jour Agent 4 =====
        st.session_state.agents_state["agent4"]["status"] = "running"
        update_display(placeholders)
        time.sleep(0.3)
        
        if result.get("is_valid"):
            st.session_state.agents_state["agent4"]["status"] = "completed"
            st.session_state.agents_state["agent4"]["output"] = {
                "résultat": "[OK] VALIDE",
                "erreurs": "0",
                "retries": str(result.get("validation_retry_count", 0))
            }
            # Stocker le résultat de validation
            st.session_state.raw_json_outputs["agent4_validation"] = {
                "is_valid": True,
                "validation_errors": [],
                "retry_count": result.get("validation_retry_count", 0)
            }
        else:
            errs = result.get("validation_errors", [])
            st.session_state.agents_state["agent4"]["status"] = "completed" if not errs else "error"
            st.session_state.agents_state["agent4"]["output"] = {
                "résultat": "[WARN] Avertissements" if not errs else "[ERROR] Erreurs",
                "détails": errs if errs else ["Aucune"]
            }
            st.session_state.raw_json_outputs["agent4_validation"] = {
                "is_valid": False,
                "validation_errors": errs,
                "retry_count": result.get("validation_retry_count", 0)
            }
        update_display(placeholders)
        
        # Stocker le résultat pour la phase 2
        st.session_state.pipeline_result = result
        return True
        
    except Exception as e:
        import traceback
        st.session_state.agents_state["agent1"]["status"] = "error"
        st.session_state.agents_state["agent1"]["output"] = {"erreur": str(e), "trace": traceback.format_exc()[:300]}
        update_display(placeholders)
        return False

# ============================================================
# Exécution du pipeline - Phase 2 (soumission)
# ============================================================

def run_pipeline_phase2_submit(placeholders: dict):
    """Soumet l'ordre après confirmation utilisateur"""
    from mcp.mcp_client import MCPClient
    
    result = st.session_state.pipeline_result
    if not result or not result.get("service_order"):
        return False
    
    # Confirmation acceptée
    st.session_state.agents_state["confirm"]["status"] = "completed"
    st.session_state.agents_state["confirm"]["output"] = {
        "décision": "ACCEPTÉ par l'utilisateur",
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }
    update_display(placeholders)
    time.sleep(0.2)
    
    # Soumission
    st.session_state.agents_state["submit"]["status"] = "running"
    st.session_state.agents_state["submit"]["output"] = {"envoi": "Soumission en cours..."}
    update_display(placeholders)
    
    try:
        from config import settings
        mcp_client = MCPClient()
        order_json = result["service_order"].model_dump(mode='json', exclude_none=True)
        response = mcp_client.call_tool("submit_service_order", service_order_json=json.dumps(order_json))
        
        if response.get("status") == "success":
            st.session_state.agents_state["submit"]["status"] = "completed"
            st.session_state.agents_state["submit"]["output"] = {
                "statut": "SOUMIS",
                "order_id": response.get("order_id", "N/A"),
                "state": response.get("order_state", "ACKNOWLEDGED"),
                "mode": "MOCK" if settings.openslice_mock_mode else "OpenSlice"
            }
            st.session_state.final_result = {"success": True, "response": response}
            # Stocker la réponse JSON brute
            st.session_state.raw_json_outputs["submit_response"] = response
        else:
            st.session_state.agents_state["submit"]["status"] = "error"
            st.session_state.agents_state["submit"]["output"] = {
                "statut": "❌ ÉCHEC",
                "message": response.get("message", "?")
            }
            st.session_state.final_result = {"success": False, "response": response}
            # Stocker la réponse d'erreur
            st.session_state.raw_json_outputs["submit_response"] = response
        
        update_display(placeholders)
        return True
        
    except Exception as e:
        st.session_state.agents_state["submit"]["status"] = "error"
        st.session_state.agents_state["submit"]["output"] = {"erreur": str(e)}
        update_display(placeholders)
        return False

# ============================================================
# INTERFACE PRINCIPALE
# ============================================================

# Header
st.markdown("""
<div class="main-header">
    <h1>🌐  Agentic AI Framework for Intent-Based Network Service Management</h1>
</div>
""", unsafe_allow_html=True)

# Tabs pour organiser l'interface
tab_pipeline, tab_json, tab_orders = st.tabs(["Pipeline", "Sorties JSON", "Ordres OpenSlice"])

with tab_pipeline:
    # Layout
    col_input, col_pipeline = st.columns([1, 1.5])

    with col_input:
        st.markdown('<div class="section-title">Votre Intention</div>', unsafe_allow_html=True)
        
        user_query = st.text_area(
            "Décrivez votre besoin",
            value="I need a network composed of three XR applications: an augmented reality content server, a mixed reality collaboration platform, and a virtual reality simulation engine. Each application requires 4 vCPUs and 2 gigabytes (GB) of memory. The clients are connected through a 5G network located in the Nice area and tolerate a maximum latency of 5 ms.",
            height=150,
            label_visibility="collapsed",
            disabled=st.session_state.is_running or st.session_state.awaiting_confirmation
        )
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            run_btn = st.button(
                "Lancer", 
                type="primary", 
                use_container_width=True, 
                disabled=st.session_state.is_running or st.session_state.awaiting_confirmation
            )
            # Quand le bouton est cliqué, déclencher le run via session_state
            if run_btn and user_query.strip():
                st.session_state.trigger_run = True
                st.session_state.saved_query = user_query
                st.session_state.show_rejected_message = False
        with col_btn2:
            reset_btn = st.button("Reset", use_container_width=True)
            if reset_btn:
                for k in ["agents_state", "is_running", "pipeline_result", "awaiting_confirmation", "user_decision", "final_result", "show_rejected_message", "trigger_run", "saved_query", "raw_json_outputs"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.rerun()

    with col_pipeline:
        st.markdown('<div class="section-title">Progression en Temps Réel</div>', unsafe_allow_html=True)
        
        # Placeholders
        placeholders = {}
        for aid in ["agent1", "agent2", "agent3", "agent4"]:
            placeholders[aid] = st.empty()
        
        # Placeholder pour confirm
        placeholders["confirm"] = st.empty()
        
        # Container pour les boutons de confirmation (s'affiche DANS le flux après confirm)
        confirm_buttons_container = st.container()
        
        # Placeholder pour submit
        placeholders["submit"] = st.empty()
        
        update_display(placeholders)
        
        # Boutons de confirmation DANS le container (apparaît juste après la carte confirm)
        if st.session_state.awaiting_confirmation and st.session_state.pipeline_result:
            with confirm_buttons_container:
                col_spacer1, col_accept, col_reject, col_spacer2 = st.columns([0.5, 2, 2, 0.5])
                with col_accept:
                    if st.button("Accepter", type="primary", use_container_width=True):
                        st.session_state.user_decision = "accept"
                        st.session_state.awaiting_confirmation = False
                        st.rerun()
                with col_reject:
                    if st.button("Rejeter", use_container_width=True):
                        st.session_state.user_decision = "reject"
                        st.session_state.awaiting_confirmation = False
                        st.rerun()
        
        result_container = st.empty()
        
        # ============================================================
        # Logique d'exécution - DANS LE CONTEXTE DES PLACEHOLDERS
        # ============================================================
        
        # Phase 1 : Lancer le pipeline (déclenché par trigger_run)
        if st.session_state.trigger_run and st.session_state.saved_query.strip():
            st.session_state.trigger_run = False  # Reset immédiatement pour éviter la boucle
            st.session_state.is_running = True
            st.session_state.user_decision = None
            st.session_state.final_result = None
            
            success = run_pipeline_phase1(st.session_state.saved_query, placeholders)
            
            st.session_state.is_running = False
            
            if success and st.session_state.pipeline_result:
                from config import settings
                # En mode Mock : auto-confirmation
                if settings.openslice_mock_mode:
                    st.session_state.agents_state["confirm"]["status"] = "completed"
                    st.session_state.agents_state["confirm"]["output"] = {
                        "mode": "Auto-approbation (Mock)",
                        "résultat": "APPROUVÉ automatiquement"
                    }
                    update_display(placeholders)
                    time.sleep(0.2)
                    
                    # Soumettre directement
                    run_pipeline_phase2_submit(placeholders)
                    
                    if st.session_state.final_result and st.session_state.final_result.get("success"):
                        result_container.markdown("""
                        <div class="success-banner">
                            <h3>Pipeline Terminé!</h3>
                            <p>L'ordre a été soumis (mode Mock)</p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    # En mode OpenSlice : demander confirmation
                    st.session_state.awaiting_confirmation = True
                    
                    # Construire l'output avec le résumé de l'ordre
                    order = st.session_state.pipeline_result.get("service_order")
                    confirm_output = {
                        "statut": "🔵 EN ATTENTE de votre décision",
                        "action": "Acceptez ou rejetez ci-dessous",
                    }
                    if order:
                        confirm_output["order_id"] = order.externalId
                        confirm_output["nb_items"] = len(order.serviceOrderItem)
                        confirm_output["priorité"] = order.priority
                        services_list = []
                        for item in order.serviceOrderItem[:5]:
                            svc_name = item.service.name or 'N/A'
                            action = item.action.value if hasattr(item.action, 'value') else item.action
                            services_list.append(f"{svc_name} ({action})")
                        confirm_output["services"] = services_list
                    
                    st.session_state.agents_state["confirm"]["status"] = "waiting"
                    st.session_state.agents_state["confirm"]["output"] = confirm_output
                    update_display(placeholders)
                    st.rerun()
        
        # Phase 2 : Traiter la décision utilisateur
        if st.session_state.user_decision == "accept" and st.session_state.pipeline_result:
            run_pipeline_phase2_submit(placeholders)
            st.session_state.user_decision = None
            
            if st.session_state.final_result and st.session_state.final_result.get("success"):
                result_container.markdown("""
                <div class="success-banner">
                    <h3>Pipeline Terminé!</h3>
                    <p>L'ordre a été soumis avec succès à OpenSlice</p>
                </div>
                """, unsafe_allow_html=True)
        
        elif st.session_state.user_decision == "reject":
            # Réinitialiser les états pour permettre une nouvelle requête
            st.session_state.user_decision = None
            st.session_state.pipeline_result = None
            st.session_state.awaiting_confirmation = False
            st.session_state.is_running = False
            st.session_state.show_rejected_message = True
            
            # Réinitialiser tous les agents pour la prochaine exécution
            for aid in st.session_state.agents_state:
                st.session_state.agents_state[aid] = {"status": "pending", "output": None}
            
            st.rerun()
        
        # Afficher le message de rejet persistant
        if st.session_state.get("show_rejected_message", False):
            result_container.markdown("""
            <div class="cancelled-banner">
                <h3>⚠️ Ordre Rejeté</h3>
                <p>L'ordre n'a pas été soumis - Saisissez une nouvelle requête et relancez le pipeline</p>
            </div>
            """, unsafe_allow_html=True)

# ============================================================
# Tab JSON Outputs
# ============================================================

with tab_json:
    st.markdown('<div class="section-title">📝 Outputs JSON des Agents</div>', unsafe_allow_html=True)
    st.markdown('<p style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 1rem;">JSON complet généré par chaque agent. Cliquez sur ▶ pour déplier.</p>', unsafe_allow_html=True)
    
    json_cols = st.columns(2)

    with json_cols[0]:
        with st.expander("🧠 Agent 1 - Intent JSON", expanded=True):
            if st.session_state.raw_json_outputs.get("agent1_intent"):
                st.json(st.session_state.raw_json_outputs["agent1_intent"], expanded=True)
            else:
                st.info("⏳ Exécutez le pipeline pour voir l'output")
        
        with st.expander("📝 Agent 3 - Service Order TMF641", expanded=True):
            if st.session_state.raw_json_outputs.get("agent3_order"):
                st.json(st.session_state.raw_json_outputs["agent3_order"], expanded=True)
            else:
                st.info("⏳ Exécutez le pipeline pour voir l'output")

    with json_cols[1]:
        with st.expander("🔍 Agent 2 - Services RAG", expanded=True):
            if st.session_state.raw_json_outputs.get("agent2_services"):
                st.json(st.session_state.raw_json_outputs["agent2_services"], expanded=True)
            else:
                st.info("⏳ Exécutez le pipeline pour voir l'output")
        
        with st.expander("✅ Agent 4 - Validation MCP", expanded=True):
            if st.session_state.raw_json_outputs.get("agent4_validation"):
                st.json(st.session_state.raw_json_outputs["agent4_validation"], expanded=True)
            else:
                st.info("⏳ Exécutez le pipeline pour voir l'output")

    # Ligne séparée pour Submit Response
    with st.expander("🚀 Réponse Soumission (OpenSlice)", expanded=True):
        if st.session_state.raw_json_outputs.get("submit_response"):
            st.json(st.session_state.raw_json_outputs["submit_response"], expanded=True)
        else:
            st.info("⏳ Soumettez un ordre pour voir la réponse")

# ============================================================
# Tab Orders - Affichage de tous les ordres OpenSlice
# ============================================================

with tab_orders:
    st.markdown('<div class="section-title"> Liste des Ordres OpenSlice</div>', unsafe_allow_html=True)
    
    # Afficher l'endpoint + bouton sur la même ligne
    from config import settings
    api_endpoint_path = "/tmf-api/serviceOrdering/v4/serviceOrder"
    api_endpoint = f"{settings.openslice_base_url}{api_endpoint_path}"
    
    col_endpoint, col_btn = st.columns([4, 1])
    with col_endpoint:
        st.markdown(f"""
        <div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%); 
                    border-radius: 8px; padding: 0.6rem 1rem;
                    border: 1px solid rgba(99, 102, 241, 0.2); display: flex; align-items: center; gap: 1rem;">
            <span style="color: #a5b4fc; font-weight: 600; white-space: nowrap;">🔗 Endpoint API</span>
            <code style="color: #34d399; background: rgba(16, 185, 129, 0.1); padding: 5px 10px; 
                         border-radius: 6px; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; white-space: nowrap;">
                GET {api_endpoint_path}
            </code>
        </div>
        """, unsafe_allow_html=True)
    with col_btn:
        fetch_btn = st.button("Charger les ordres", type="primary", use_container_width=True)
    
    # Initialiser l'état pour les ordres
    if "orders_list" not in st.session_state:
        st.session_state.orders_list = None
    if "orders_error" not in st.session_state:
        st.session_state.orders_error = None
    if "orders_loading" not in st.session_state:
        st.session_state.orders_loading = False
    
    if fetch_btn:
        st.session_state.orders_loading = True
        st.session_state.orders_error = None
        
        try:
            from mcp.openslice_client import OpenSliceClient
            
            with st.spinner("🔍 Connexion et récupération des ordres..."):
                client = OpenSliceClient()
                client.authenticate()
                
                if client.mock_mode:
                    # Mode Mock : générer des données de démo
                    st.session_state.orders_list = [
                        {
                            "id": "mock-order-001",
                            "externalId": "XR-Network-Demo-001",
                            "state": "acknowledged",
                            "orderDate": "2025-03-15T10:30:00Z",
                            "priority": "1",
                            "description": "XR Applications Network Order (Mock)"
                        },
                        {
                            "id": "mock-order-002",
                            "externalId": "5G-Slice-Nice-002",
                            "state": "inProgress",
                            "orderDate": "2025-03-14T14:45:00Z",
                            "priority": "2",
                            "description": "5G Network Slice - Nice Area (Mock)"
                        },
                        {
                            "id": "mock-order-003",
                            "externalId": "VR-Collaboration-003",
                            "state": "completed",
                            "orderDate": "2025-03-10T09:00:00Z",
                            "priority": "1",
                            "description": "VR Collaboration Platform (Mock)"
                        }
                    ]
                else:
                    # Mode réel : appel API
                    url = f"{client.base_url}/tmf-api/serviceOrdering/v4/serviceOrder"
                    response = client.client.get(url, headers=client._get_headers())
                    response.raise_for_status()
                    st.session_state.orders_list = response.json()
                
                client.close() if hasattr(client, 'close') and client.client else None
                
        except Exception as e:
            st.session_state.orders_error = str(e)
            st.session_state.orders_list = None
        
        st.session_state.orders_loading = False
        st.rerun()
    
    # Affichage des résultats
    if st.session_state.orders_error:
        st.error(f"❌ Erreur lors de la récupération : {st.session_state.orders_error}")
    
    elif st.session_state.orders_list is not None:
        orders = st.session_state.orders_list
        
        if orders:
            state_colors = {
                "acknowledged": "#fbbf24",
                "inProgress": "#60a5fa",
                "completed": "#10b981",
                "failed": "#ef4444",
                "cancelled": "#6b7280"
            }
            
            rows_html = ""
            for i, order in enumerate(orders):
                order_id = order.get('id', 'N/A')
                ext_id = order.get('externalId', order.get('description', 'N/A'))
                state = order.get('state', 'N/A')
                order_date = order.get('orderDate', order.get('requestedStartDate', order.get('@baseType', 'N/A')))
                date_short = order_date[:10] if isinstance(order_date, str) and len(order_date) >= 10 else 'N/A'
                color = state_colors.get(state, "#94a3b8")
                id_display = f"{str(order_id)[:32]}..." if len(str(order_id)) > 32 else order_id
                row_bg = "rgba(99,102,241,0.04)" if i % 2 == 0 else "transparent"

                rows_html += f"""<tr style="background:{row_bg}; border-bottom:1px solid rgba(99,102,241,0.08);">
                    <td style="padding:9px 14px; color:#e2e8f0; font-weight:500;">{ext_id}</td>
                    <td style="padding:9px 14px; color:#64748b; font-size:0.78rem; font-family:'JetBrains Mono',monospace;">{id_display}</td>
                    <td style="padding:9px 14px;"><span style="color:{color}; font-weight:500;">● {state}</span></td>
                    <td style="padding:9px 14px; color:#94a3b8;">{date_short}</td>
                </tr>"""
            
            st.markdown(f"""<div style="margin-top:0.75rem; border-radius:10px; overflow:hidden; border:1px solid rgba(99,102,241,0.2);">
            <table style="width:100%; border-collapse:collapse; font-size:0.84rem;">
                <thead>
                    <tr style="background:rgba(99,102,241,0.12);">
                        <th style="padding:10px 14px; color:#a5b4fc; font-weight:600; text-align:left;">External ID</th>
                        <th style="padding:10px 14px; color:#a5b4fc; font-weight:600; text-align:left;">ID</th>
                        <th style="padding:10px 14px; color:#a5b4fc; font-weight:600; text-align:left;">État</th>
                        <th style="padding:10px 14px; color:#a5b4fc; font-weight:600; text-align:left;">Date</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table></div>""", unsafe_allow_html=True)
            
            with st.expander("📄 JSON brut", expanded=False):
                st.json(orders)
        else:
            st.info("📭 Aucun ordre trouvé dans OpenSlice")
    else:
        pass
