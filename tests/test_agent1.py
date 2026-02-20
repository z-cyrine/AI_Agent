#!/usr/bin/env python3
"""
Script de test rapide pour Agent 1 - Mode interactif
Usage: python test_quick.py
"""

from agents.agent1_interpreter import IntentInterpreterAgent

def main():
    print("=" * 70)
    print("🧪 TEST RAPIDE - Agent 1 Interpreter")
    print("=" * 70)
    
    # Demander la requête à l'utilisateur
    query = input("\n📝 Entrez votre requête: ").strip()
    
    if not query:
        print("❌ Requête vide!")
        return
    
    print("=" * 70)
    print("🧪 TEST RAPIDE - Agent 1 Interpreter")
    print("=" * 70)
    print(f"\n📝 Requête: {query}")
    print("🤖 Analyse en cours...\n")
    
    # Initialiser l'agent et interpréter
    agent = IntentInterpreterAgent()
    intent = agent.interpret(query)
    
    # Afficher le résultat
    print("✅ Résultat:")
    print(f"   Intent ID: {intent.intent_id}")
    print(f"   Type: {intent.type}")
    print(f"   Sous-intentions: {len(intent.sub_intents)}")
    
    for i, sub in enumerate(intent.sub_intents, 1):
        print(f"\n   [{i}] Domaine: {sub.domain}")
        print(f"       Requirements: {sub.requirements}")
    
    if intent.location:
        print(f"\n🌍 Location: {intent.location}")
    if intent.qos:
        print(f"⚡ QoS: {intent.qos}")
    
    print("\n📄 JSON complet:")
    print(intent.model_dump_json(indent=2))
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
