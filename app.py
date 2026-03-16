"""
Interface Streamlit pour le Pipeline IBN Agentic AI
Permet à l'utilisateur de :
- Rédiger son intention
- Suivre le pipeline en temps réel
- Mettre son feedback
- Voir la liste de ses ordres
"""

import streamlit as st
import json
from datetime import datetime
from pathlib import Path
import pandas as pd
import os
from queue import Queue
import threading
import time

# Désactiver les inputs interactifs pendant Streamlit
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'

from orchestrator import create_workflow, AgentState, context as orch_context
from mcp.mcp_client import MCPClient

# ============================================================
# CONFIGURATION STREAMLIT
# ============================================================

st.set_page_config(
    page_title="Pipeline IBN - Interface Utilisateur",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.2rem;
        font-weight: bold;
    }
    .step-success {
        background-color: #d4edda;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #28a745;
        margin: 10px 0;
    }
    .step-error {
        background-color: #f8d7da;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #dc3545;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# GESTION DE L'ÉTAT SESSION
# ============================================================

if "pipeline_history" not in st.session_state:
    st.session_state.pipeline_history = []

if "current_order" not in st.session_state:
    st.session_state.current_order = None

if "current_result" not in st.session_state:
    st.session_state.current_result = None

if "pipeline_running" not in st.session_state:
    st.session_state.pipeline_running = False

if "step_updates" not in st.session_state:
    st.session_state.step_updates = []

if "feedback_received" not in st.session_state:
    st.session_state.feedback_received = False

if "user_feedback" not in st.session_state:
    st.session_state.user_feedback = None

if "awaiting_feedback" not in st.session_state:
    st.session_state.awaiting_feedback = False

# ============================================================
# CALLBACKS POUR LA COMMUNICATION
# ============================================================

def on_step_complete(step_name: str, result: dict):
    """Callback appelé quand une étape se termine"""
    st.session_state.step_updates.append({
        "step": step_name,
        "result": result,
        "timestamp": datetime.now()
    })
    print(f"[Streamlit] Step {step_name} completed")

def get_feedback_from_user(state: AgentState) -> dict:
    """Callback pour obtenir le feedback utilisateur"""
    print(f"[Streamlit] Attente du feedback utilisateur...")
    
    # Marquer que nous attendons le feedback
    st.session_state.awaiting_feedback = True
    st.session_state.feedback_received = False
    
    # Attendre que l'utilisateur clique sur un bouton
    # Le rerun de Streamlit va afficher les boutons
    max_wait = 300  # 30 secondes maximum
    wait_count = 0
    
    while wait_count < max_wait:
        if st.session_state.user_feedback is not None:
            feedback = st.session_state.user_feedback
            st.session_state.user_feedback = None  # Réinitialiser
            print(f"[Callback] Feedback reçu: {feedback}")
            return feedback
        
        time.sleep(0.1)
        wait_count += 1
    
    # Timeout - retourner une valeur par défaut
    print(f"[Callback] Timeout - aucun feedback reçu")
    return {
        "user_approved": False,
        "user_wants_to_retry": False,
        "user_retry_count": state["user_retry_count"]
    }

# Enregistrer les callbacks
orch_context.register_step_callback(on_step_complete)
orch_context.register_feedback_callback(get_feedback_from_user)

# ============================================================
# PAGE PRINCIPALE
# ============================================================

st.title("🚀 Pipeline IBN - Interface Utilisateur")
st.markdown("Orchestration intelligente des services réseau et cloud")

# Créer les onglets
tab1, tab2, tab3 = st.tabs(["📝 Nouvelle Intention", "📊 Suivi Pipeline", "📋 Historique Ordres"])

# ============================================================
# ONGLET 1 : NOUVELLE INTENTION
# ============================================================

with tab1:
    st.header("📝 Rédiger votre Intention")
    st.markdown("""
    Décrivez ce que vous souhaitez déployer en langage naturel.
    
    **Exemples :**
    - "I need a web server with database in Nice"
    - "Deploy an e-commerce platform with PostgreSQL and React"
    - "Smart city IoT platform with sensors"
    """)
    
    # Zone de texte pour la requête
    user_query = st.text_area(
        label="Votre intention",
        placeholder="Décrivez votre besoin...",
        height=150,
        key="user_intention"
    )
    
    # Boutons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Lancer le Pipeline", key="launch_btn"):
            if not user_query.strip():
                st.error("❌ Veuillez entrer une intention")
            else:
                st.session_state.current_order = {
                    "id": f"order_{datetime.now().timestamp()}",
                    "query": user_query,
                    "created_at": datetime.now().isoformat(),
                }
                st.session_state.pipeline_running = True
                st.session_state.step_updates = []
                st.session_state.awaiting_feedback = False
                st.session_state.feedback_received = False
                st.rerun()
    
    with col2:
        if st.button("🔄 Réinitialiser", key="reset_btn"):
            st.session_state.current_order = None
            st.session_state.current_result = None
            st.session_state.pipeline_running = False
            st.session_state.step_updates = []
            st.rerun()

# ============================================================
# ONGLET 2 : SUIVI PIPELINE
# ============================================================

with tab2:
    st.header("📊 Suivi du Pipeline")
    
    if st.session_state.current_order is None:
        st.info("💡 Aucun pipeline en cours. Allez à l'onglet '📝 Nouvelle Intention' pour commencer.")
    else:
        st.subheader("🎯 Intention")
        st.write(st.session_state.current_order["query"])
        
        # Lancer le pipeline en arrière-plan
        if st.session_state.pipeline_running:
            # Créer deux colonnes : une pour le pipeline, une pour les mises à jour
            progress_col = st.empty()
            updates_col = st.empty()
            feedback_col = st.empty()
            
            with progress_col.container():
                st.info("⏳ Exécution du pipeline en cours...")
            
            # Thread pour exécuter le pipeline
            def run_pipeline():
                try:
                    app = create_workflow()
                    
                    initial_state = AgentState(
                        user_query=st.session_state.current_order["query"],
                        intent=None,
                        intent_errors=[],
                        selected_services=[],
                        selection_errors=[],
                        service_order=None,
                        translation_errors=[],
                        is_valid=False,
                        validation_errors=[],
                        validation_retry_count=0,
                        user_approved=False,
                        user_wants_to_retry=False,
                        user_retry_count=0,
                        openslice_response=None,
                        final_status="pending"
                    )
                    
                    result = app.invoke(initial_state)
                    st.session_state.current_result = result
                    st.session_state.pipeline_running = False
                    st.session_state.awaiting_feedback = False
                    
                except Exception as e:
                    st.error(f"❌ Erreur: {e}")
                    st.session_state.pipeline_running = False
            
            # Lancer le pipeline dans un thread
            pipeline_thread = threading.Thread(target=run_pipeline, daemon=True)
            pipeline_thread.start()
            
            # Afficher les mises à jour en temps réel
            while st.session_state.pipeline_running or st.session_state.awaiting_feedback:
                with updates_col.container():
                    st.subheader("📡 Progression")
                    for update in st.session_state.step_updates:
                        step = update["step"]
                        if "error" in step.lower():
                            st.markdown(f"""
                            <div class="step-error">
                            <strong>❌ {step}</strong>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div class="step-success">
                            <strong>✅ {step}</strong>
                            </div>
                            """, unsafe_allow_html=True)
                
                # Afficher les boutons de feedback si en attente
                if st.session_state.awaiting_feedback:
                    with feedback_col.container():
                        st.subheader("🎯 Votre Feedback")
                        st.info("📋 Veuillez valider l'ordre avant de continuer")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if st.button("✅ Accepter et Soumettre", key="accept_btn_live"):
                                st.session_state.user_feedback = {
                                    "user_approved": True,
                                    "user_wants_to_retry": False,
                                    "user_retry_count": 0
                                }
                                st.success("✅ Ordre accepté !")
                        
                        with col2:
                            if st.button("❌ Rejeter et Arrêter", key="reject_btn_live"):
                                st.session_state.user_feedback = {
                                    "user_approved": False,
                                    "user_wants_to_retry": False,
                                    "user_retry_count": 0
                                }
                                st.warning("❌ Ordre rejeté")
                        
                        with col3:
                            if st.button("🔄 Recommencer", key="retry_btn_live"):
                                st.session_state.user_feedback = {
                                    "user_approved": False,
                                    "user_wants_to_retry": True,
                                    "user_retry_count": 1
                                }
                                st.info("🔄 Recommençons...")
                
                time.sleep(0.2)
            
            # Pipeline terminé - afficher les résultats finaux
            st.rerun()
        
        # Afficher les résultats si disponibles
        if st.session_state.current_result:
            result = st.session_state.current_result
            
            st.divider()
            
            # Indicateurs de progression
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if result["intent"]:
                    st.success("✅ Agent 1")
                else:
                    st.error("❌ Agent 1")
            
            with col2:
                if result["selected_services"]:
                    st.success("✅ Agent 2")
                else:
                    st.error("❌ Agent 2")
            
            with col3:
                if result["service_order"]:
                    st.success("✅ Agent 3")
                else:
                    st.error("❌ Agent 3")
            
            with col4:
                if result["is_valid"]:
                    st.success("✅ Agent 4")
                else:
                    st.error("❌ Agent 4")
            
            st.divider()
            
            # Détails Agent 1
            with st.expander("🔴 Agent 1 - Interpréteur", expanded=True):
                if result["intent"]:
                    st.success("✅ Intention structurée")
                    st.json(result["intent"].model_dump(exclude_none=True))
                else:
                    st.error(f"❌ {result['intent_errors']}")
            
            # Détails Agent 2
            with st.expander("🟠 Agent 2 - Sélecteur"):
                if result["selected_services"]:
                    st.success(f"✅ {len(result['selected_services'])} service(s)")
                    for svc in result["selected_services"]:
                        st.write(f"• {svc.get('name')}")
                else:
                    st.error(f"❌ {result['selection_errors']}")
            
            # Détails Agent 3
            with st.expander("🟡 Agent 3 - Traducteur"):
                if result["service_order"]:
                    st.success("✅ ServiceOrder généré")
                    st.json(result["service_order"].model_dump(exclude_none=True))
                else:
                    st.error(f"❌ {result['translation_errors']}")
            
            # Détails Agent 4
            with st.expander("🟢 Agent 4 - Validateur"):
                if result["is_valid"]:
                    st.success("✅ Validation OK")
                else:
                    st.error(f"❌ {result['validation_errors']}")
            
            st.divider()
            
            # FEEDBACK UTILISATEUR
            st.subheader("🎯 Votre Feedback")
            
            if result["final_status"] == "pending" or (result["is_valid"] and not result["user_approved"]):
                st.info("📋 Veuillez valider l'ordre avant de continuer")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("✅ Accepter et Soumettre", key="accept_btn"):
                        st.session_state.user_feedback = {
                            "user_approved": True,
                            "user_wants_to_retry": False,
                            "user_retry_count": result.get("user_retry_count", 0)
                        }
                        st.session_state.feedback_received = True
                        st.rerun()
                
                with col2:
                    if st.button("❌ Rejeter et Arrêter", key="reject_btn"):
                        st.session_state.user_feedback = {
                            "user_approved": False,
                            "user_wants_to_retry": False,
                            "user_retry_count": result.get("user_retry_count", 0)
                        }
                        st.session_state.feedback_received = True
                        st.rerun()
                
                with col3:
                    if st.button("🔄 Recommencer", key="retry_btn"):
                        st.session_state.user_feedback = {
                            "user_approved": False,
                            "user_wants_to_retry": True,
                            "user_retry_count": result.get("user_retry_count", 0) + 1
                        }
                        st.session_state.feedback_received = True
                        st.rerun()
            
            elif result["user_approved"] and result["final_status"] != "submitted":
                st.success("✅ Soumission en cours...")
                try:
                    mcp_client = MCPClient(mode="local")
                    order_json = result["service_order"].model_dump_json(exclude_none=True)
                    submit_result = mcp_client.submit_service_order(order_json)
                    mcp_client.close()
                    
                    result["openslice_response"] = submit_result
                    if submit_result.get("status") == "success":
                        result["final_status"] = "submitted"
                        st.success("✅ Ordre soumis!")
                        st.write(f"**Order ID:** {submit_result.get('order_id')}")
                    else:
                        st.error("❌ Erreur soumission")
                    
                    st.session_state.current_result = result
                except Exception as e:
                    st.error(f"❌ Erreur: {e}")
            
            elif result["final_status"] == "submitted":
                st.success("✅ PIPELINE RÉUSSI")
                if result.get("openslice_response"):
                    st.write(f"**Order ID:** {result['openslice_response'].get('order_id')}")
            
            elif result["final_status"] == "user_rejected":
                st.warning("⛔ Ordre rejeté")

# ============================================================
# ONGLET 3 : HISTORIQUE
# ============================================================

with tab3:
    st.header("📋 Historique des Ordres")
    
    try:
        from mcp.openslice_client import OpenSliceClient
        client = OpenSliceClient()
        client.authenticate()
        url = f"{client.base_url}/tmf-api/serviceOrdering/v4/serviceOrder"
        import httpx
        response = httpx.get(url, headers=client._get_headers())
        
        if response.status_code == 200:
            orders = response.json()
            if orders:
                st.success(f"✅ {len(orders)} ordre(s) trouvé(s)")
                for order in orders:
                    st.write(f"- {order.get('externalId')} ({order.get('state')})")
            else:
                st.info("📭 Aucun ordre")
        
        client.close()
    except Exception as e:
        st.error(f"❌ Erreur: {e}")

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.title("⚙️ Configuration")
    st.markdown("""
    ### Pipeline IBN Agentic AI
    
    4 Agents IA spécialisés pour :
    - Interpréter les requêtes
    - Sélectionner les services
    - Générer les ordres TMF641
    - Valider et soumettre
    """)
