import sys
import os
from datetime import datetime

# On s'assure que Python regarde dans le dossier courant
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# IMPORT CORRIGÉ : dossier.fichier
from mcp.openslice_client import OpenSliceClient

def format_date(date_str):
    """Formate une date ISO en format lisible"""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime("%d/%m/%Y %H:%M:%S")
    except:
        return date_str

def list_orders_summary():
    """Affiche un résumé de tous les ordres"""
    print("Connexion au serveur OpenSlice...")
    client = OpenSliceClient()
    
    try:
        # Authentification (Keycloak port 8080)
        client.authenticate()
        
        # Récupération des ordres via l'API (osscapi port 13082)
        url = f"{client.base_url}/tmf-api/serviceOrdering/v4/serviceOrder"
        response = client.client.get(url, headers=client._get_headers())
        response.raise_for_status()
        
        orders = response.json()
        
        print(f"\nConnexion réussie ! {len(orders)} ordre(s) trouvé(s).\n")
        
        # Compter par statut
        status_count = {}
        for o in orders:
            state = o.get('state', 'UNKNOWN')
            status_count[state] = status_count.get(state, 0) + 1
        
        print("RÉSUMÉ PAR STATUT:")
        print("-" * 40)
        for status, count in sorted(status_count.items()):
            emoji_map = {
                "COMPLETED": "[OK]",
                "INPROGRESS": "[EN COURS]",
                "ACKNOWLEDGED": "[RECONNU]"
            }
            emoji = emoji_map.get(status, "[?]")
            print(f"{emoji} {status:<20} : {count}")
        
        print(f"\n{'ID':<40} | {'STATUT':<15} | {'EXTERNE ID':<20}")
        print("-" * 80)
        
        for o in sorted(orders, key=lambda x: x.get('state', ''), reverse=True):
            order_id = o.get('id', 'N/A')[:37] + ".."
            state = o.get('state', 'N/A')
            ext_id = o.get('externalId', 'N/A')[:20]
            print(f"{order_id:<40} | {state:<15} | {ext_id:<20}")
            
    except Exception as e:
        print(f"Erreur lors de la récupération : {e}")
    finally:
        client.close()


def show_order_details(order_id):
    """Affiche les détails complets d'un ordre"""
    print(f"Récupération des détails de l'ordre {order_id[:8]}...")
    client = OpenSliceClient()
    
    try:
        client.authenticate()
        
        url = f"{client.base_url}/tmf-api/serviceOrdering/v4/serviceOrder/{order_id}"
        response = client.client.get(url, headers=client._get_headers())
        response.raise_for_status()
        
        order = response.json()
        
        print("\n" + "="*80)
        print("DÉTAILS DE L'ORDRE")
        print("="*80)
        
        print(f"\n[ID]              : {order.get('id', 'N/A')}")
        print(f"[External ID]     : {order.get('externalId', 'N/A')}")
        print(f"[État FINAL]      : {order.get('state', 'N/A')}")
        print(f"[Priorité]        : {order.get('priority', 'N/A')}")
        print(f"[Date création]   : {format_date(order.get('orderDate', 'N/A'))}")
        print(f"[Date démarrage]  : {format_date(order.get('startDate', 'N/A'))}")
        print(f"[Date complétion] : {format_date(order.get('completionDate', 'N/A'))}")
        
        # Afficher l'historique des statuts
        if order.get('note'):
            print(f"\n[HISTORIQUE DES STATUTS]:")
            print("-" * 80)
            for note in sorted(order['note'], key=lambda x: x.get('date', ''), reverse=True):
                date = format_date(note.get('date', 'N/A'))
                author = note.get('author', 'unknown')
                text = note.get('text', 'N/A')
                print(f"  {date} | {author:<30} | {text}")
        
        # Afficher les items de l'ordre
        items = order.get('serviceOrderItem') or order.get('orderItem')
        if items:
            print(f"\n[SERVICES COMMANDÉS]:")
            print("-" * 80)
            for item in items:
                service = item.get('service', {})
                print(f"  • {service.get('name', 'Sans nom')}")
                print(f"    - Action: {item.get('action', 'N/A')}")
                print(f"    - Qty: {item.get('quantity', '1')}")
        else:
            print(f"\n[SERVICES COMMANDÉS]: Aucun item trouvé")
        
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        client.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--detail":
        # Mode détail : afficher un ordre spécifique
        if len(sys.argv) > 2:
            show_order_details(sys.argv[2])
        else:
            print("Utilisation: python check_orders.py --detail <order_id>")
    else:
        # Mode résumé : lister tous les ordres
        list_orders_summary()
        print("\nPour voir les détails d'un ordre: python check_orders.py --detail <order_id>")