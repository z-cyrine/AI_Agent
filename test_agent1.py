"""
Test simple de l'Agent 1 (Interpréteur d'intentions)
Usage: python test_agent1.py
"""

from agents.agent1_interpreter import IntentInterpreterAgent

def test_simple():
    """Test avec une intention simple"""
    print("=" * 70)
    print("🧪 TEST 1: Intention Simple")
    print("=" * 70)
    
    agent = IntentInterpreterAgent()
    query = "I need a database"
    
    print(f"\n📝 Requête: {query}")
    print("🤖 Analyse en cours...\n")
    
    intent = agent.interpret(query)
    
    print("✅ Résultat:")
    print(f"   Intent ID: {intent.intent_id}")
    print(f"   Type: {intent.type}")
    print(f"   Sous-intentions: {len(intent.sub_intents)}")
    for i, sub in enumerate(intent.sub_intents, 1):
        print(f"\n   [{i}] Domaine: {sub.domain}")
        print(f"       Requirements: {sub.requirements}")
    
    print("\n📄 JSON complet:")
    print(intent.model_dump_json(indent=2))


def test_complex():
    """Test avec une intention complexe"""
    print("\n" + "=" * 70)
    print("🧪 TEST 2: Intention Complexe")
    print("=" * 70)
    
    agent = IntentInterpreterAgent()
    query = "je veux déployer une application web avec une base postgres de 32GB RAM, un frontend React, et un backend FastAPI avec 8 cores"
    
    print(f"\n📝 Requête: {query}")
    print("🤖 Analyse en cours...\n")
    
    intent = agent.interpret(query)
    
    print("✅ Résultat:")
    print(f"   Intent ID: {intent.intent_id}")
    print(f"   Type: {intent.type}")
    print(f"   Sous-intentions: {len(intent.sub_intents)}")
    for i, sub in enumerate(intent.sub_intents, 1):
        print(f"\n   [{i}] Domaine: {sub.domain}")
        print(f"       Requirements: {sub.requirements}")
    
    print("\n📄 JSON complet:")
    print(intent.model_dump_json(indent=2))


def test_custom():
    """Test avec votre propre requête"""
    print("\n" + "=" * 70)
    print("🧪 TEST 3: Votre Requête")
    print("=" * 70)
    
    agent = IntentInterpreterAgent()
    query = input("\n📝 Entrez votre requête: ")
    
    print("🤖 Analyse en cours...\n")
    
    intent = agent.interpret(query)
    
    print("✅ Résultat:")
    print(f"   Intent ID: {intent.intent_id}")
    print(f"   Type: {intent.type}")
    print(f"   Sous-intentions: {len(intent.sub_intents)}")
    for i, sub in enumerate(intent.sub_intents, 1):
        print(f"\n   [{i}] Domaine: {sub.domain}")
        print(f"       Requirements: {sub.requirements}")
    
    if intent.location:
        print(f"\n🌍 Location globale: {intent.location}")
    if intent.qos:
        print(f"⚡ QoS global: {intent.qos}")
    
    print("\n📄 JSON complet:")
    print(intent.model_dump_json(indent=2))


if __name__ == "__main__":
    try:
        # Test 1: Simple
        test_simple()
        
        # Test 2: Complexe
        test_complex()
        
        # Test 3: Personnalisé
        choice = input("\n❓ Voulez-vous tester votre propre requête? (o/n): ")
        if choice.lower() == 'o':
            test_custom()
        
        print("\n" + "=" * 70)
        print("🎉 TESTS TERMINÉS")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrompus")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
