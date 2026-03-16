"""
Test complet du pipeline avec intégration MCP

Teste le pipeline end-to-end : Agent1 → Agent2 → Agent3 → Agent4 → Submit (via MCP)

Usage:
    python scripts/test_pipeline_mcp.py
    python scripts/test_pipeline_mcp.py --verbose
"""
import sys
import json
import argparse
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator import create_workflow, AgentState
from datetime import datetime


def print_section(title: str):
    """Affiche un titre de section"""
    print(f"\n{'='*80}")
    print(f"{'🧪 ' if '🧪' not in title else ''}{title}")
    print(f"{'='*80}")


def print_step(step_num: int, agent_name: str, status: str):
    """Affiche une étape du pipeline"""
    icon = "✅" if status == "success" else "⚠️ " if status == "warning" else "❌"
    print(f"\n{icon} Étape {step_num}: {agent_name} - {status.upper()}")


def test_pipeline(user_query: str, verbose: bool = False):
    """
    Teste le pipeline complet avec MCP
    
    Args:
        user_query: Requête utilisateur en langage naturel
        verbose: Mode verbeux pour plus de détails
    """
    print_section("TEST COMPLET DU PIPELINE - AVEC INTÉGRATION MCP")
    
    print(f"\n📝 Requête utilisateur:")
    print(f"   {user_query[:100]}...")
    
    # Créer le workflow
    print("\n🚀 Initialisation du workflow LangGraph...")
    try:
        app = create_workflow()
        print("   ✅ Workflow créé avec succès")
    except Exception as e:
        print(f"   ❌ Erreur lors de la création du workflow: {e}")
        return False
    
    # État initial
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
        non_interactive_mode=False,
        openslice_response=None,
        final_status="pending"
    )
    
    # Exécuter le workflow
    print("\n" + "="*80)
    print("🔄 EXÉCUTION DU PIPELINE")
    print("="*80)
    
    try:
        result = app.invoke(initial_state)
        
        # Afficher les résultats
        print_section("RÉSULTATS DU PIPELINE")
        
        print("\n📊 RÉSUMÉ:")
        print(f"  Statut final        : {result['final_status']}")
        print(f"  Ordre valide        : {'✅ OUI' if result['is_valid'] else '❌ NON'}")
        print(f"  Nombre de retries   : {result['validation_retry_count']}")
        
        # Résultats Agent 1
        print("\n[Agent 1 - Interpreter]")
        if result['intent']:
            print(f"  ✅ Intention générée: {result['intent'].intent_id}")
            print(f"     Type: {result['intent'].type}")
            print(f"     Sous-intentions: {len(result['intent'].sub_intents)}")
        else:
            print(f"  ❌ Erreurs: {result['intent_errors']}")
        
        # Résultats Agent 2
        print("\n[Agent 2 - Selector]")
        if result['selected_services']:
            print(f"  ✅ {len(result['selected_services'])} service(s) sélectionné(s)")
            for i, svc in enumerate(result['selected_services'][:3], 1):
                name = svc.get('name', 'Unknown')
                print(f"     {i}. {name}")
        else:
            if result['selection_errors']:
                print(f"  ❌ Erreurs: {result['selection_errors']}")
            else:
                print(f"  ⚠️  Aucun service sélectionné")
        
        # Résultats Agent 3
        print("\n[Agent 3 - Translator]")
        if result['service_order']:
            print(f"  ✅ Ordre TMF641 généré: {result['service_order'].externalId}")
            print(f"     Items: {len(result['service_order'].serviceOrderItem)}")
        else:
            if result['translation_errors']:
                print(f"  ❌ Erreurs: {result['translation_errors']}")
            else:
                print(f"  ⚠️  Pas d'ordre généré")
        
        # Résultats Agent 4 (avec MCP)
        print("\n[Agent 4 - Validator] (via MCP)")
        if result['validation_errors']:
            print(f"  ❌ Erreurs de validation:")
            for error in result['validation_errors']:
                print(f"     - {error}")
        else:
            print(f"  ✅ Validation réussie (aucune erreur)")
        
        # Résultats Submit (via MCP)
        print("\n[Submit] (via MCP)")
        if result['openslice_response']:
            response = result['openslice_response']
            status = response.get('status', 'unknown')
            if status == 'success':
                print(f"  ✅ Ordre soumis avec succès")
                print(f"     Order ID: {response.get('order_id', '?')}")
                print(f"     État: {response.get('order_state', '?')}")
            else:
                print(f"  ❌ Erreur lors de la soumission")
                print(f"     Message: {response.get('message', '?')}")
        else:
            print(f"  ❌ Aucune réponse OpenSlice")
        
        # Affichage détaillé si verbose
        if verbose:
            print("\n" + "="*80)
            print("📋 DÉTAILS COMPLETS")
            print("="*80)
            
            if result['intent']:
                print("\n[Intention - Détails]")
                print(json.dumps(
                    result['intent'].model_dump(exclude_none=True),
                    indent=2,
                    default=str
                )[:500])
            
            if result['service_order']:
                print("\n[ServiceOrder TMF641 - Détails]")
                print(json.dumps(
                    result['service_order'].model_dump(exclude_none=True),
                    indent=2,
                    default=str
                )[:500])
        
        # Statut final
        print("\n" + "="*80)
        success = (
            result['final_status'] in ['submitted', 'success'] and
            result['openslice_response'] and
            result['openslice_response'].get('status') == 'success'
        )
        
        if success:
            print("✅ PIPELINE RÉUSSI - ORDRE SOUMIS À OPENSLICE")
        else:
            print("⚠️  PIPELINE COMPLÉTÉ AVEC DES AVERTISSEMENTS")
        print("="*80 + "\n")
        
        return success
    
    except Exception as e:
        print(f"\n❌ ERREUR LORS DE L'EXÉCUTION DU PIPELINE:")
        print(f"   {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Point d'entrée du test"""
    parser = argparse.ArgumentParser(description="Test du pipeline avec MCP")
    parser.add_argument(
        "--query",
        type=str,
        default="I need XR applications with 5G connectivity in Nice",
        help="Requête utilisateur"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Mode verbeux"
    )
    parser.add_argument(
        "--example",
        action="store_true",
        help="Utiliser l'exemple XR complexe"
    )
    
    args = parser.parse_args()
    
    # Sélectionner la requête
    if args.example:
        query = """I need a network composed of three XR applications: an augmented reality content server,
a mixed reality collaboration platform, and a virtual reality simulation engine. Each application
requires 4 vCPUs and 2 gigabytes (GB) of memory. All XR applications are interconnected
using 5 GB/s links. The clients are connected through a 5G network located in the Nice area
and tolerate a maximum latency of 5 ms."""
    else:
        query = args.query
    
    # Lancer le test
    success = test_pipeline(query, verbose=args.verbose)
    
    # Code de sortie
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
