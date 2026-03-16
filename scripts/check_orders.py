import sys
import os

# On s'assure que Python regarde dans le dossier courant
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# IMPORT CORRIGÉ : dossier.fichier
from mcp.openslice_client import OpenSliceClient

def list_orders():
    print("🔍 Connexion au serveur OpenSlice...")
    client = OpenSliceClient()
    
    try:
        # Authentification (Keycloak port 8080)
        client.authenticate()
        
        # Récupération des ordres via l'API (osscapi port 13082)
        url = f"{client.base_url}/tmf-api/serviceOrdering/v4/serviceOrder"
        response = client.client.get(url, headers=client._get_headers())
        response.raise_for_status()
        
        orders = response.json()
        
        print(f"\n✅ Connexion réussie ! {len(orders)} ordre(s) trouvé(s).\n")
        print(f"{'ID':<40} | {'STATUT':<15} | {'NOM (EXTERNAL ID)'}")
        print("-" * 80)
        
        for o in orders:
            order_id = o.get('id', 'N/A')
            state = o.get('state', 'N/A')
            ext_id = o.get('externalId', 'N/A')
            print(f"{order_id:<40} | {state:<15} | {ext_id}")
            
    except Exception as e:
        print(f"❌ Erreur lors de la récupération : {e}")
    finally:
        client.close()

if __name__ == "__main__":
    list_orders()