import sys
import os
import json
from datetime import datetime

# On s'assure que Python regarde dans le dossier courant
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from mcp.openslice_client import OpenSliceClient
except ImportError:
    print("❌ Erreur : Impossible de trouver 'mcp.openslice_client'.")
    sys.exit(1)

def format_date(date_str):
    if not date_str or date_str == 'N/A': return 'N/A'
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime("%d/%m/%Y %H:%M:%S")
    except: return date_str

def show_order_details_absolute_truth(order_id):
    """Affiche les détails et force l'inspection du JSON brut si besoin"""
    print(f"🔍 Inspection profonde de l'ordre {order_id[:8]}...")
    client = OpenSliceClient()
    
    try:
        client.authenticate()
        
        url = f"{client.base_url}/tmf-api/serviceOrdering/v4/serviceOrder/{order_id}"
        response = client.client.get(url, headers=client._get_headers())
        response.raise_for_status()
        
        order = response.json()
        
        print("\n" + "="*80)
        print(f"📊 RAPPORT D'INSPECTION : {order.get('externalId', 'SANS NOM')}")
        print("="*80)
        
        print(f"[ID Technique] : {order.get('id')}")
        print(f"[État]        : {order.get('state')}")
        
        # --- LA VÉRITÉ EST ICI ---
        # On teste toutes les clés de collection possibles
        items = order.get('orderItem') or order.get('serviceOrderItem')
        
        if items and len(items) > 0:
            print(f"\n✅ {len(items)} ITEM(S) TROUVÉ(S) :")
            print("-" * 40)
            for i, item in enumerate(items, 1):
                svc = item.get('service', {})
                name = svc.get('name') or item.get('name') or "Inconnu"
                action = item.get('action', 'add')
                print(f"  {i}. {name} [Action: {action}]")
        else:
            print("\n❌ AUCUN ITEM DANS LES CLÉS CLASSIQUES.")
            print("\n--- DEBUG : ANALYSE DU JSON BRUT REÇU ---")
            # On affiche le JSON complet mais proprement indenté pour que tu puisses 
            # lire s'il y a des données cachées ailleurs (ex: dans 'orderRelationship')
            print(json.dumps(order, indent=2))
            print("--- FIN DU DEBUG ---")

        print("\n" + "="*80)
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
    finally:
        client.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Si on passe --detail ou juste l'ID
        target_id = sys.argv[2] if sys.argv[1] == "--detail" else sys.argv[1]
        show_order_details_absolute_truth(target_id)
    else:
        print("Usage: python scripts/check_orders.py <order_id>")