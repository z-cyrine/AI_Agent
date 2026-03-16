"""
Pipeline IBN Complet avec Orchestrateur LangGraph

Rôle: Orchestrer les 4 agents avec gestion des cycles et erreurs via LangGraph.
Utilise le protocole MCP pour la communication standardisée.

Flux:
    User Query → Agent1 → Agent2 → Agent3 → Agent4 → Submit (MCP) → OpenSlice
    
    Si validation échoue: Retry Agent3 (max 3x)
"""
import argparse
import sys
import json
from typing import Optional
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import create_workflow, AgentState
from config import settings


def print_section(title: str):
    """Affiche un titre de section"""
    print(f"\n{'='*80}")
    print(f"🎯 {title}")
    print(f"{'='*80}")


def print_subsection(title: str):
    """Affiche un sous-titre"""
    print(f"\n{'-'*80}")
    print(f"   {title}")
    print(f"{'-'*80}")


def run_complete_pipeline(user_query: str, verbose: bool = False) -> dict:
    """
    Exécute le pipeline COMPLET avec orchestrateur LangGraph
    
    Args:
        user_query: Requête utilisateur en langage naturel
        verbose: Afficher les détails
        
    Returns:
        Résultats du pipeline
    """
    print_section("PIPELINE IBN COMPLET - ORCHESTRATEUR LANGGRAPH")
    
    print(f"\n📝 Requête utilisateur:")
    print(f"   {user_query[:100]}{'...' if len(user_query) > 100 else ''}")
    
    # ==========================================
    # Créer le workflow
    # ==========================================
    print_subsection("Initialisation du Workflow LangGraph")
    try:
        app = create_workflow()
        print("✅ Workflow LangGraph créé")
    except Exception as e:
        print(f"❌ Erreur création workflow: {e}")
        return {"error": str(e)}
    
    # ==========================================
    # État initial
    # ==========================================
    initial_state = AgentState(
        user_query=user_query,
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
    
    # ==========================================
    # Exécuter le pipeline
    # ==========================================
    print_subsection("Exécution du Pipeline")
    try:
        result = app.invoke(initial_state)
    except Exception as e:
        print(f"❌ Erreur exécution pipeline: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
    
    # ==========================================
    # Afficher les résultats
    # ==========================================
    print_section("RÉSULTATS DU PIPELINE")
    
    print("\n📊 RÉSUMÉ EXÉCUTION:")
    print(f"  Statut final        : {result['final_status']}")
    print(f"  Ordre valide        : {'✅ OUI' if result['is_valid'] else '❌ NON'}")
    print(f"  Nombre de retries   : {result['validation_retry_count']}/3")
    
    # Résultats Agent 1
    print("\n[AGENT 1 - INTERPRÉTEUR]")
    if result['intent']:
        print(f"  ✅ Intention générée: {result['intent'].intent_id}")
        print(f"     Type: {result['intent'].type}")
        print(f"     Sous-intentions: {len(result['intent'].sub_intents)}")
        if verbose and result['intent'].requirements:
            print(f"     Requirements: {len(result['intent'].requirements)}")
    else:
        print(f"  ❌ Erreurs: {result['intent_errors']}")
    
    # Résultats Agent 2
    print("\n[AGENT 2 - SÉLECTEUR]")
    if result['selected_services']:
        print(f"  ✅ {len(result['selected_services'])} service(s) sélectionné(s)")
        for i, svc in enumerate(result['selected_services'][:3], 1):
            name = svc.get('name', 'Unknown')
            score = svc.get('score', 'N/A')
            print(f"     {i}. {name} (score: {score})")
        if len(result['selected_services']) > 3:
            print(f"     ... et {len(result['selected_services']) - 3} autre(s)")
    else:
        if result['selection_errors']:
            print(f"  ⚠️  {result['selection_errors'][0]}")
        else:
            print(f"  ⚠️  Aucun service sélectionné")
    
    # Résultats Agent 3
    print("\n[AGENT 3 - TRADUCTEUR]")
    if result['service_order']:
        print(f"  ✅ Ordre TMF641 généré: {result['service_order'].externalId}")
        print(f"     Items: {len(result['service_order'].serviceOrderItem)}")
        print(f"     Priority: {result['service_order'].priority}")
    else:
        if result['translation_errors']:
            print(f"  ❌ Erreurs: {result['translation_errors'][0]}")
        else:
            print(f"  ⚠️  Pas d'ordre généré")
    
    # Résultats Agent 4 (avec MCP)
    print("\n[AGENT 4 - VALIDATEUR] (via MCP)")
    if result['is_valid']:
        print(f"  ✅ Validation réussie")
    else:
        if result['validation_errors']:
            print(f"  ❌ Erreurs de validation:")
            for error in result['validation_errors'][:3]:
                print(f"     - {error}")
            if len(result['validation_errors']) > 3:
                print(f"     ... et {len(result['validation_errors']) - 3} autre(s)")
        else:
            print(f"  ⚠️  Pas d'erreur spécifique")
    
    # Résultats Submit (via MCP)
    print("\n[SUBMIT] (via MCP)")
    if result['openslice_response']:
        response = result['openslice_response']
        status = response.get('status', 'unknown')
        if status == 'success':
            print(f"  ✅ Ordre soumis avec succès")
            print(f"     Order ID: {response.get('order_id', '?')}")
            print(f"     État: {response.get('order_state', '?')}")
        else:
            print(f"  ⚠️  Statut MCP: {status}")
            if response.get('message'):
                print(f"     Message: {response.get('message')}")
    else:
        print(f"  ⚠️  Pas de réponse OpenSlice")
    
    # Résultats User Confirmation
    print("\n[USER CONFIRMATION]")
    if result['user_approved']:
        print(f"  ✅ Ordre accepté par l'utilisateur")
    else:
        print(f"  ❌ Ordre rejeté par l'utilisateur")
        if result.get('user_wants_to_retry'):
            print(f"  🔄 L'utilisateur veut recommencer ({result['user_retry_count']}/3)")
        else:
            print(f"  ⛔ L'utilisateur a arrêté le pipeline")
    
    # Détails si verbose
    if verbose:
        print_section("DÉTAILS COMPLETS (MODE VERBEUX)")
        
        if result['intent']:
            print("\n[Intention - Structure Complète]")
            intent_dict = result['intent'].model_dump(exclude_none=True)
            print(json.dumps(intent_dict, indent=2, default=str)[:500])
        
        if result['service_order']:
            print("\n[ServiceOrder TMF641 - Structure Complète]")
            order_dict = result['service_order'].model_dump(exclude_none=True)
            print(json.dumps(order_dict, indent=2, default=str)[:500])
        
        if result['openslice_response']:
            print("\n[Réponse OpenSlice]")
            print(json.dumps(result['openslice_response'], indent=2, default=str)[:500])
    
    # Résumé final
    print_section("RÉSUMÉ FINAL")
    
    success = (
        result['final_status'] in ['submitted', 'success'] and
        result.get('openslice_response') and
        result['openslice_response'].get('status') == 'success'
    )
    
    if success:
        print("✅ PIPELINE RÉUSSI - ORDRE SOUMIS À OPENSLICE")
    elif result['final_status'] == 'user_cancelled':
        print("⛔ PIPELINE ANNULÉ PAR L'UTILISATEUR")
        print("   - L'utilisateur a choisi de quitter pendant la saisie de la nouvelle requête")
    elif result['user_wants_to_retry'] and result['user_retry_count'] >= 3:
        print("⛔ PIPELINE ARRÊTÉ - TROP DE TENTATIVES")
        print(f"   - Nombre maximum de reformulations atteint ({result['user_retry_count']}/3)")
    elif result['user_approved'] == False and result['user_wants_to_retry'] == False:
        print("⛔ PIPELINE ARRÊTÉ - UTILISATEUR A REJETÉ L'ORDRE")
        print("   - L'utilisateur n'a pas accepté l'ordre généré")
    elif result['is_valid'] and result['service_order']:
        print("⚠️  PIPELINE PARTIELLEMENT RÉUSSI")
        print("   - Ordre généré et valide")
        print("   - Soumission à OpenSlice échouée (vérifier OpenSlice)")
    elif result['service_order']:
        print("⚠️  PIPELINE COMPLÉTÉ AVEC AVERTISSEMENTS")
        print(f"   - Validation échouée ({result['validation_retry_count']} retries)")
    else:
        print("❌ PIPELINE ÉCHOUÉ")
        if result['intent_errors']:
            print(f"   - Erreur Agent 1: {result['intent_errors'][0]}")
        elif result['selection_errors']:
            print(f"   - Erreur Agent 2: {result['selection_errors'][0]}")
        elif result['translation_errors']:
            print(f"   - Erreur Agent 3: {result['translation_errors'][0]}")
    
    print()
    return result


def interactive_mode():
    """Mode interactif pour tester le pipeline"""
    print_section("MODE INTERACTIF - ORCHESTRATEUR LANGGRAPH")
    print("\nTapez 'quit' ou 'exit' pour quitter\n")
    
    while True:
        try:
            user_input = input("\n💬 Votre requête: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Au revoir!")
                break
            
            if not user_input:
                continue
            
            run_complete_pipeline(user_input, verbose=False)
            
        except KeyboardInterrupt:
            print("\n\n👋 Au revoir!")
            break
        except Exception as e:
            print(f"\n❌ Erreur: {e}")


def test_complete_application():
    """Test complet de l'application"""
    print_section("TEST COMPLET DE L'APPLICATION")
    
    tests = [
        {
            "name": "Test Simple - 5G Service",
            "query": "I need a 5G network service in Nice"
        },
        {
            "name": "Test Complexe - XR avec 5G",
            "query": "I need XR applications with 5G connectivity in Nice"
        },
        {
            "name": "Test Très Complexe - Multi-services",
            "query": """I need a network composed of three XR applications: 
an augmented reality content server, a mixed reality collaboration platform, 
and a virtual reality simulation engine. Each application requires 4 vCPUs and 
2 gigabytes of memory. All XR applications are interconnected using 5 GB/s links. 
The clients are connected through a 5G network located in the Nice area 
and tolerate a maximum latency of 5 ms."""
        }
    ]
    
    results = []
    for i, test in enumerate(tests, 1):
        print(f"\n\n{'='*80}")
        print(f"TEST {i}/{len(tests)}: {test['name']}")
        print(f"{'='*80}")
        
        result = run_complete_pipeline(test['query'], verbose=False)
        results.append({
            "test": test['name'],
            "success": result.get('final_status') == 'submitted' and result.get('openslice_response', {}).get('status') == 'success',
            "result": result
        })
    
    # Résumé des tests
    print_section("RÉSUMÉ DES TESTS")
    
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"\n✅ Tests réussis: {passed}/{total}")
    
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"  {status}: {result['test']}")
    
    print(f"\n{'='*80}\n")
    
    return passed == total


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline IBN Agentic AI - Orchestrateur LangGraph Complet"
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
        "--verbose",
        "-v",
        action="store_true",
        help="Mode verbeux (affiche les détails complets)"
    )
    parser.add_argument(
        "--example",
        action="store_true",
        help="Exécuter avec l'exemple XR du contexte"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Exécuter les tests complets de l'application"
    )
    
    args = parser.parse_args()
    
    # Mode test complet
    if args.test:
        success = test_complete_application()
        sys.exit(0 if success else 1)
    
    # Mode exemple
    elif args.example:
        example_query = """I need a network composed of three XR applications: 
an augmented reality content server, a mixed reality collaboration platform, 
and a virtual reality simulation engine. Each application requires 4 vCPUs and 
2 gigabytes of memory. All XR applications are interconnected using 5 GB/s links. 
The clients are connected through a 5G network located in the Nice area 
and tolerate a maximum latency of 5 ms."""
        
        run_complete_pipeline(example_query, verbose=args.verbose)
    
    # Mode interactif
    elif args.interactive:
        interactive_mode()
    
    # Mode requête unique
    elif args.query:
        run_complete_pipeline(args.query, verbose=args.verbose)
    
    # Afficher l'aide si aucun argument
    else:
        parser.print_help()
        print("\n💡 Exemples d'utilisation:")
        print('   python main.py --example')
        print('   python main.py --query "I need a low-latency 5G service"')
        print('   python main.py --interactive')
        print('   python main.py --test')
        print('   python main.py --example --verbose')


if __name__ == "__main__":
    main()
