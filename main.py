import argparse
import sys
import json
from typing import Optional

from agents.agent1_interpreter import IntentInterpreterAgent
from agents.agent2_selector import ServiceSelectorAgent
from agents.agent3_translator import ServiceTranslatorAgent  # Ton Agent 3
from agents.agent4_validator import ServiceValidatorAgent    # Ton Agent 4
from schemas.intent import Intent
from config import settings

def run_pipeline(user_query: str, top_k: int = 3, min_score: float = 0.5):
    """
    Exécute le pipeline complet des Agents 1, 2, 3 et 4
    """
    print("\n" + "="*80)
    print("PIPELINE COMPLET IBN - AGENTS 1, 2, 3 & 4")
    print("="*80 + "\n")
    
    # ==========================================
    # Agent 1: Interprétation (Cyrine)
    # ==========================================
    print("🤖 AGENT 1: INTERPRÉTEUR (Intent Planner)")
    print("-" * 80)
    try:
        agent1 = IntentInterpreterAgent()
        intent = agent1.interpret(user_query)
        print("\n✅ Intention structurée générée.")
    except Exception as e:
        print(f"\n❌ Erreur Agent 1: {e}")
        return None
    
    # ==========================================
    # Agent 2: Sélection (Cyrine)
    # ==========================================
    print("\n" + "="*80)
    print("🤖 AGENT 2: SÉLECTEUR (Service Broker)")
    print("-" * 80)
    try:
        agent2 = ServiceSelectorAgent()
        services = agent2.select_services(intent, top_k=top_k, min_score=min_score)
        
        if not services:
            print("\n⚠️ Aucun service correspondant trouvé dans ChromaDB.")
            return intent, []
    except Exception as e:
        print(f"\n❌ Erreur Agent 2: {e}")
        return intent, []

    # ==========================================
    # Agent 3: Traduction TMF641 (Sarra)
    # ==========================================
    print("\n" + "="*80)
    print("🤖 AGENT 3: TRADUCTEUR (TMF641 Mapper)")
    print("-" * 80)
    try:
        agent3 = ServiceTranslatorAgent()
        # Traduction de l'intent et des services sélectionnés en ServiceOrder
        service_order = agent3.translate(intent, services)
        print("\n✅ Ordre de service TMF641 généré.")
    except Exception as e:
        print(f"\n❌ Erreur Agent 3: {e}")
        return intent, services

    # ==========================================
    # Agent 4: Validation QA (Sarra)
    # ==========================================
    print("\n" + "="*80)
    print("🤖 AGENT 4: VALIDATEUR (Quality Assurance)")
    print("-" * 80)
    try:
        agent4 = ServiceValidatorAgent()
        is_valid, validation_errors = agent4.validate(service_order)
        
        if is_valid:
            print("\n✅ VALIDATION RÉUSSIE : L'ordre est conforme au standard TMF641.")
            print("\n--- RÉSULTAT FINAL (JSON TMF641) ---")
            print(service_order.model_dump_json(indent=2))
        else:
            print(f"\n❌ ÉCHEC DE VALIDATION : {validation_errors}")
    except Exception as e:
        print(f"\n❌ Erreur Agent 4: {e}")

    return intent, services, service_order

# ... (garder les fonctions interactive_mode et main() telles quelles)


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
