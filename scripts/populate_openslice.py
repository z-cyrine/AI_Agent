import httpx
import sys
import os
import json

# Ajout du chemin pour importer tes settings
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import settings
from scripts.ingest_catalog import get_openslice_token # On réutilise ta fonction d'auth

def create_remote_service(token: str, service_data: dict):
    url = f"{settings.openslice_base_url}/tmf-api/serviceCatalogManagement/v4/serviceSpecification"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Structure TMF633 minimale pour OpenSlice
    payload = {
        "name": service_data["name"],
        "description": service_data["description"],
        "lifecycleStatus": "Active",
        "isBundle": False,
        "category": service_data["metadata"].get("category", "General"),
        # On ajoute les caractéristiques par défaut pour que l'Agent 3 puisse mapper
        "serviceSpecCharacteristic": [
            {"name": "vCPU", "valueType": "integer", "serviceSpecCharacteristicValue": [{"value": "2", "isDefault": True}]},
            {"name": "RAM_GB", "valueType": "integer", "serviceSpecCharacteristicValue": [{"value": "4", "isDefault": True}]},
            {"name": "Location", "valueType": "string", "serviceSpecCharacteristicValue": [{"value": "Paris", "isDefault": True}]}
        ]
    }

    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=10.0)
        if response.status_code in [201, 200]:
            print(f"✅ Service créé : {service_data['name']} (ID: {response.json().get('id')})")
        else:
            print(f"❌ Erreur pour {service_data['name']}: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erreur de connexion : {e}")

def main():
    print("🚀 Début de l'injection dans OpenSlice réel...")
    token = get_openslice_token()
    
    services_to_add = [
        {
            "name": "Edge_AR_Content_Provider",
            "description": "Serveur de contenu pour réalité augmentée (AR) optimisé pour le rendu Edge à basse latence.",
            "metadata": { "category": "XR", "type": "AR" }
        },
        {
            "name": "Mixed_Reality_Collab_Hub",
            "description": "Plateforme de collaboration pour réalité mixte (MR) permettant le partage d'hologrammes multi-utilisateurs.",
            "metadata": { "category": "XR", "type": "MR" }
        },
        {
            "name": "VR_Simulation_Core",
            "description": "Moteur de simulation haute fidélité pour environnements de réalité virtuelle (VR) immersive.",
            "metadata": { "category": "XR", "type": "VR" }
        },
        {
            "name": "5G_Slice_Paris_Region",
            "description": "Connectivité 5G ultra-rapide couvrant l'Île-de-France (Paris) avec garantie de latence < 5ms.",
            "metadata": { "category": "Network", "location": "Paris" }
        },
        {
            "name": "HD_Video_Streaming_Standard",
            "description": "Service de diffusion vidéo classique pour contenu multimédia standard sur le web.",
            "metadata": { "category": "Entertainment" }
        },
        {
            "name": "Legacy_4G_LTE_Access",
            "description": "Accès réseau mobile 4G LTE standard pour smartphones et tablettes.",
            "metadata": { "category": "Network" }
        }
    ]

    for svc in services_to_add:
        create_remote_service(token, svc)

if __name__ == "__main__":
    main()