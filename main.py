"""
Point d'entrée principal du framework IBN Agentic AI

Ce script orchestre les Agents 1 et 2 (Cyrine):
- Agent 1: Interprétation du langage naturel → Intent structuré (JSON Agnostique)
- Agent 2: Sélection sémantique de services via RAG

Usage:
    python main.py --query "I need XR applications..."
    python main.py --interactive
"""
import argparse
import sys
from typing import Optional

from agents.agent1_interpreter import IntentInterpreterAgent
from agents.agent2_selector import ServiceSelectorAgent
from schemas.intent import Intent
from config import settings


def run_pipeline(user_query: str, top_k: int = 3, min_score: float = 0.5):
    """
    Exécute le pipeline complet des Agents 1 et 2
    
    Args:
        user_query: Requête utilisateur en langage naturel
        top_k: Nombre de services à retourner
        min_score: Score minimum de pertinence
    """
    print("\n" + "="*80)
    print("PIPELINE AGENTS 1 & 2 - INTENT-BASED NETWORKING")
    print("="*80 + "\n")
    
    # =============================
    # Agent 1: Interprétation
    # =============================
    print("🤖 AGENT 1: INTERPRÉTEUR (Intent Planner)")
    print("-" * 80)
    print(f"Requête utilisateur:\n{user_query}\n")
    
    try:
        agent1 = IntentInterpreterAgent()
        intent = agent1.interpret(user_query)
        
        print("\n✅ Intention structurée générée (JSON Agnostique):")
        print(intent.model_dump_json(indent=2, exclude_none=True))
        
    except Exception as e:
        print(f"\n❌ Erreur Agent 1: {e}")
        return None
    
    # =============================
    # Agent 2: Sélection de services
    # =============================
    print("\n" + "="*80)
    print("🤖 AGENT 2: SÉLECTEUR (Service Broker)")
    print("-" * 80)
    
    try:
        agent2 = ServiceSelectorAgent()
        
        # Vérifier que la collection n'est pas vide
        if agent2.collection.count() == 0:
            print("⚠️  La base de services est vide!")
            print("   Exécutez d'abord: python scripts/ingest_catalog.py --mock")
            return intent, []
        
        # Sélection des services
        services = agent2.select_services(intent, top_k=top_k, min_score=min_score)
        
        if services:
            print(f"\n✅ {len(services)} service(s) sélectionné(s):\n")
            for i, svc in enumerate(services, 1):
                print(f"{i}. {svc['name']}")
                print(f"   UUID: {svc['id']}")
                print(f"   Score: {svc['score']}")
                print(f"   Catégorie: {svc['metadata'].get('category', 'N/A')}")
                print(f"   Description: {svc['description'][:150]}...")
                print()
        else:
            print("\n⚠️  Aucun service correspondant trouvé")
        
        return intent, services
        
    except Exception as e:
        print(f"\n❌ Erreur Agent 2: {e}")
        import traceback
        traceback.print_exc()
        return intent, []


def interactive_mode():
    """Mode interactif pour tester le pipeline"""
    print("\n" + "="*80)
    print("MODE INTERACTIF - AGENTS 1 & 2")
    print("="*80)
    print("Tapez 'quit' ou 'exit' pour quitter\n")
    
    while True:
        try:
            user_input = input("\n💬 Votre requête: ")
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Au revoir!")
                break
            
            if not user_input.strip():
                continue
            
            run_pipeline(user_input)
            
        except KeyboardInterrupt:
            print("\n\n👋 Au revoir!")
            break
        except Exception as e:
            print(f"\n❌ Erreur: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline IBN Agentic AI - Agents 1 & 2 (Cyrine)"
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Requête utilisateur en langage naturel"
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Mode interactif"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Nombre de services à retourner (défaut: 3)"
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.5,
        help="Score minimum de pertinence (0-1, défaut: 0.5)"
    )
    parser.add_argument(
        "--example",
        action="store_true",
        help="Exécuter avec l'exemple XR du contexte"
    )
    
    args = parser.parse_args()
    
    # Mode exemple
    if args.example:
        example_query = """I need a network composed of three XR applications: an augmented reality content server,
a mixed reality collaboration platform, and a virtual reality simulation engine. Each application
requires 4 vCPUs and 2 gigabytes (GB) of memory. All XR applications are interconnected
using 5 GB/s links. The clients are connected through a 5G network located in the Nice area
and tolerate a maximum latency of 5 ms."""
        
        run_pipeline(example_query, top_k=args.top_k, min_score=args.min_score)
    
    # Mode interactif
    elif args.interactive:
        interactive_mode()
    
    # Mode requête unique
    elif args.query:
        run_pipeline(args.query, top_k=args.top_k, min_score=args.min_score)
    
    # Afficher l'aide si aucun argument
    else:
        parser.print_help()
        print("\n💡 Exemples d'utilisation:")
        print('   python main.py --example')
        print('   python main.py --query "I need a low-latency 5G service"')
        print('   python main.py --interactive')


if __name__ == "__main__":
    main()
