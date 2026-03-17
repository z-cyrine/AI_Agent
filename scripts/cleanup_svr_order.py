import httpx
import sys
import os

# Ajout du chemin pour importer tes réglages
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import settings
from scripts.ingest_catalog import get_openslice_token

def cleanup():
    print("🧹 Nettoyage des Service Orders dans OpenSlice...")
    token = get_openslice_token()
    
    # URL de base pour les ordres de service
    base_url = f"{settings.openslice_base_url}/tmf-api/serviceOrdering/v4/serviceOrder"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        # 1. Lister tous les ordres existants
        response = httpx.get(base_url, headers=headers, timeout=10.0)
        response.raise_for_status()
        orders = response.json()

        if not orders:
            print("✨ Aucun ordre à supprimer.")
            return

        print(f"🔍 {len(orders)} ordre(s) trouvé(s). Début de la suppression...")

        # 2. Supprimer chaque ordre
        for order in orders:
            order_id = order.get('id')
            if not order_id: continue

            del_url = f"{base_url}/{order_id}"
            del_resp = httpx.delete(del_url, headers=headers, timeout=10.0)
            
            if del_resp.status_code in [200, 204]:
                print(f"✅ Ordre supprimé : {order_id}")
            else:
                print(f"⚠️ Échec suppression {order_id}: {del_resp.status_code}")

        print("\n✅ Nettoyage terminé.")

    except Exception as e:
        print(f"❌ Erreur lors du nettoyage : {e}")

if __name__ == "__main__":
    cleanup()