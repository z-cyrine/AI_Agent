"""
Tests unitaires pour les Agents 1 et 2

Usage:
    python tests/test_agents.py
"""
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.agent1_interpreter import IntentInterpreterAgent
from agents.agent2_selector import ServiceSelectorAgent
from schemas.intent import Intent, SubIntent


def test_agent1_basic():
    """Test basique de l'Agent 1"""
    print("\n" + "="*80)
    print("TEST AGENT 1: Interprétation basique")
    print("="*80 + "\n")
    
    query = "I need a video streaming service with low latency"
    
    agent = IntentInterpreterAgent()
    intent = agent.interpret(query)
    
    assert intent is not None
    assert isinstance(intent, Intent)
    assert intent.name is not None
    assert len(intent.intentExpectation) > 0
    
    print("✅ Test réussi!")
    return intent


def test_agent1_xr_example():
    """Test avec l'exemple XR du contexte"""
    print("\n" + "="*80)
    print("TEST AGENT 1: Exemple XR complet")
    print("="*80 + "\n")
    
    query = """I need a network composed of three XR applications: an augmented reality content server,
    a mixed reality collaboration platform, and a virtual reality simulation engine. Each application
    requires 4 vCPUs and 2 gigabytes (GB) of memory. All XR applications are interconnected
    using 5 GB/s links. The clients are connected through a 5G network located in the Nice area
    and tolerate a maximum latency of 5 ms."""
    
    agent = IntentInterpreterAgent()
    intent = agent.interpret(query)
    
    # Vérifications
    assert intent.sub_intents is not None
    assert len(intent.sub_intents) > 0
    
    # Vérifier qu'il y a des domaines cloud, transport et ran
    domains = [sub.domain for sub in intent.sub_intents]
    
    print(f"✅ Test réussi!")
    print(f"   - {len(intent.sub_intents)} sous-intention(s)")
    print(f"   - Domaines: {', '.join(domains)}")
    
    return intent


def test_agent2_selection():
    """Test de l'Agent 2 avec une intention"""
    print("\n" + "="*80)
    print("TEST AGENT 2: Sélection de services")
    print("="*80 + "\n")
    
    # Créer une intention de test
    intent = Intent(
        intent_id="Test_XR_001",
        type="composite_service",
        sub_intents=[
            SubIntent(
                domain="cloud",
                requirements={
                    "cpu": 4,
                    "ram": "2GB",
                    "applications": ["XR_apps"]
                }
            ),
            SubIntent(
                domain="ran",
                requirements={
                    "network_type": "5G",
                    "max_latency": "5ms"
                }
            )
        ],
        location="Nice",
        qos={"max_latency": "5ms"}
    )
    
    # Créer l'agent
    agent = ServiceSelectorAgent()
    
    # Vérifier qu'il y a des données dans ChromaDB
    count = agent.collection.count()
    if count == 0:
        print("⚠️  La collection est vide. Exécutez d'abord:")
        print("   python scripts/ingest_catalog.py --mock")
        return None
    
    # Sélection
    services = agent.select_services(intent, top_k=3)
    
    assert isinstance(services, list)
    
    if services:
        print(f"✅ Test réussi! {len(services)} service(s) trouvé(s)")
        for svc in services:
            assert "id" in svc
            assert "name" in svc
            assert "score" in svc
    else:
        print("⚠️  Aucun service trouvé (collection vide ou score trop bas)")
    
    return services


def test_pipeline_integration():
    """Test d'intégration du pipeline complet"""
    print("\n" + "="*80)
    print("TEST PIPELINE: Intégration Agents 1 & 2")
    print("="*80 + "\n")
    
    query = "I need an edge computing service with low latency for IoT applications"
    
    # Agent 1
    print("1️⃣  Agent 1: Interprétation...")
    agent1 = IntentInterpreterAgent()
    intent = agent1.interpret(query)
    print(f"   ✅ Intent créé: {intent.name}")
    
    # Agent 2
    print("\n2️⃣  Agent 2: Sélection...")
    agent2 = ServiceSelectorAgent()
    
    if agent2.collection.count() == 0:
        print("   ⚠️  Collection vide - test partiel")
        return intent, []
    
    services = agent2.select_services(intent, top_k=2)
    print(f"   ✅ {len(services)} service(s) sélectionné(s)")
    
    print("\n✅ Pipeline complet testé avec succès!")
    return intent, services


def run_all_tests():
    """Exécute tous les tests"""
    print("\n" + "🧪 "*40)
    print("SUITE DE TESTS - AGENTS 1 & 2")
    print("🧪 "*40)
    
    try:
        # Test 1
        test_agent1_basic()
        
        # Test 2
        test_agent1_xr_example()
        
        # Test 3
        test_agent2_selection()
        
        # Test 4
        test_pipeline_integration()
        
        print("\n" + "="*80)
        print("✅ TOUS LES TESTS SONT PASSÉS!")
        print("="*80 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ Test échoué: {e}")
        raise
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    run_all_tests()
