"""
Script d'ingestion du catalogue OpenSlice (TMF633) dans ChromaDB

Ce script:
1. Se connecte à l'API OpenSlice TMF633 (Service Catalog Management)
2. Récupère toutes les ServiceSpecifications
3. Génère des embeddings pour chaque service
4. Stocke les vecteurs dans ChromaDB pour la recherche sémantique

Usage:
    python scripts/ingest_catalog.py
    python scripts/ingest_catalog.py --clear  # Efface d'abord la collection
"""
import argparse
import sys
import os
from typing import List, Dict, Any
import httpx
from tqdm import tqdm

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.agent2_selector import ServiceSelectorAgent
from config import settings


def get_openslice_token() -> str:
    """
    Obtient un token d'authentification pour OpenSlice
    
    Returns:
        str: Token JWT
    """
    auth_url = f"{settings.openslice_base_url}/auth/realms/openslice/protocol/openid-connect/token"
    
    data = {
        "username": settings.openslice_username,
        "password": settings.openslice_password,
        "grant_type": "password",
        "client_id": "admin-cli"
    }
    
    try:
        response = httpx.post(auth_url, data=data, timeout=30.0)
        response.raise_for_status()
        token = response.json()["access_token"]
        print("✅ Authentification OpenSlice réussie")
        return token
    except httpx.HTTPStatusError as e:
        print(f"❌ Erreur d'authentification: {e}")
        print(f"   URL: {auth_url}")
        print(f"   Vérifiez les credentials dans .env")
        raise
    except Exception as e:
        print(f"❌ Erreur de connexion à OpenSlice: {e}")
        print(f"   URL: {auth_url}")
        print(f"   OpenSlice est-il démarré?")
        raise


def fetch_service_specifications(token: str) -> List[Dict[str, Any]]:
    """
    Récupère toutes les ServiceSpecifications du catalogue OpenSlice (TMF633)
    
    Args:
        token: Token JWT d'authentification
        
    Returns:
        List[Dict]: Liste des ServiceSpecifications
    """
    # API TMF633: Service Catalog Management
    catalog_url = f"{settings.openslice_base_url}/tmf-api/serviceCatalogManagement/v4/serviceSpecification"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    try:
        print(f"📡 Récupération des services depuis: {catalog_url}")
        response = httpx.get(catalog_url, headers=headers, timeout=60.0)
        response.raise_for_status()
        
        services = response.json()
        
        # Gestion de la pagination si nécessaire
        if isinstance(services, dict) and "serviceSpecification" in services:
            services = services["serviceSpecification"]
        
        print(f"✅ {len(services)} ServiceSpecification(s) récupérée(s)")
        return services
        
    except httpx.HTTPStatusError as e:
        print(f"❌ Erreur HTTP {e.response.status_code}: {e}")
        print(f"   URL: {catalog_url}")
        raise
    except Exception as e:
        print(f"❌ Erreur lors de la récupération: {e}")
        raise


def create_service_document(service_spec: Dict[str, Any]) -> str:
    """
    Crée un document textuel à partir d'une ServiceSpecification
    pour l'embedding et la recherche sémantique
    
    Args:
        service_spec: ServiceSpecification OpenSlice
        
    Returns:
        str: Document textuel enrichi
    """
    parts = []
    
    # Nom du service
    if "name" in service_spec:
        parts.append(f"Service: {service_spec['name']}")
    
    # Description
    if "description" in service_spec:
        parts.append(f"Description: {service_spec['description']}")
    
    # Catégorie
    if "category" in service_spec:
        parts.append(f"Category: {service_spec['category']}")
    
    # Version
    if "version" in service_spec:
        parts.append(f"Version: {service_spec['version']}")
    
    # Caractéristiques du service
    if "serviceSpecCharacteristic" in service_spec:
        char_names = [char.get("name", "") for char in service_spec["serviceSpecCharacteristic"]]
        if char_names:
            parts.append(f"Characteristics: {', '.join(char_names)}")
    
    # Type de service
    if "serviceType" in service_spec:
        parts.append(f"Type: {service_spec['serviceType']}")
    
    # Tags ou mots-clés
    if "tags" in service_spec:
        parts.append(f"Tags: {', '.join(service_spec['tags'])}")
    
    return " | ".join(parts)


def extract_metadata(service_spec: Dict[str, Any]) -> Dict[str, str]:
    """
    Extrait les métadonnées importantes d'une ServiceSpecification
    
    Args:
        service_spec: ServiceSpecification OpenSlice
        
    Returns:
        Dict: Métadonnées clés-valeurs (seulement des strings pour ChromaDB)
    """
    metadata = {}
    
    # Informations de base
    if "name" in service_spec:
        metadata["name"] = str(service_spec["name"])
    
    if "category" in service_spec:
        metadata["category"] = str(service_spec["category"])
    
    if "version" in service_spec:
        metadata["version"] = str(service_spec["version"])
    
    if "lifecycleStatus" in service_spec:
        metadata["status"] = str(service_spec["lifecycleStatus"])
    
    if "serviceType" in service_spec:
        metadata["type"] = str(service_spec["serviceType"])
    
    # Nombre de caractéristiques
    if "serviceSpecCharacteristic" in service_spec:
        metadata["num_characteristics"] = str(len(service_spec["serviceSpecCharacteristic"]))
    
    return metadata


def ingest_catalog(clear_existing: bool = False):
    """
    Pipeline complet d'ingestion du catalogue OpenSlice dans ChromaDB
    
    Args:
        clear_existing: Si True, efface la collection existante avant l'ingestion
    """
    print("\n" + "="*80)
    print("INGESTION DU CATALOGUE OPENSLICE (TMF633 → ChromaDB)")
    print("="*80 + "\n")
    
    # 1. Initialiser l'agent de sélection (= ChromaDB)
    print("1️⃣  Initialisation de ChromaDB...")
    agent = ServiceSelectorAgent()
    
    # Effacer la collection si demandé
    if clear_existing:
        print("🗑️  Suppression de la collection existante...")
        agent.client.delete_collection(name=agent.collection_name)
        agent.collection = agent.client.create_collection(
            name=agent.collection_name,
            embedding_function=agent.embedding_function,
            metadata={"description": "OpenSlice Service Catalog"}
        )
        print("✅ Collection réinitialisée")
    
    # 2. Authentification OpenSlice
    print("\n2️⃣  Authentification OpenSlice...")
    try:
        token = get_openslice_token()
    except Exception:
        print("\n⚠️  IMPOSSIBLE DE SE CONNECTER À OPENSLICE")
        print("    Pour tester sans OpenSlice, vous pouvez créer des services de test:")
        print("    python scripts/ingest_catalog.py --mock")
        return
    
    # 3. Récupération des ServiceSpecifications
    print("\n3️⃣  Récupération du catalogue TMF633...")
    try:
        service_specs = fetch_service_specifications(token)
    except Exception:
        print("\n⚠️  IMPOSSIBLE DE RÉCUPÉRER LE CATALOGUE")
        return
    
    if not service_specs:
        print("\n⚠️  Aucune ServiceSpecification trouvée dans OpenSlice")
        print("    Créez d'abord des services dans l'interface OpenSlice")
        return
    
    # 4. Ingestion dans ChromaDB
    print(f"\n4️⃣  Ingestion de {len(service_specs)} service(s) dans ChromaDB...")
    
    ids = []
    documents = []
    metadatas = []
    
    for service_spec in tqdm(service_specs, desc="Traitement"):
        # UUID du service (clé primaire)
        service_id = service_spec.get("id") or service_spec.get("uuid")
        if not service_id:
            print(f"⚠️  Service sans ID ignoré: {service_spec.get('name', 'Unknown')}")
            continue
        
        # Document textuel pour l'embedding
        document = create_service_document(service_spec)
        
        # Métadonnées
        metadata = extract_metadata(service_spec)
        
        ids.append(service_id)
        documents.append(document)
        metadatas.append(metadata)
    
    # Batch insertion dans ChromaDB
    if ids:
        agent.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        print(f"\n✅ {len(ids)} service(s) ingéré(s) avec succès!")
    
    # 5. Statistiques finales
    print("\n" + "="*80)
    print("STATISTIQUES FINALES:")
    print("="*80)
    stats = agent.get_collection_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    print("="*80 + "\n")


def create_mock_services():
    """Crée des services de test pour valider le système sans OpenSlice"""
    print("\n📦 Création de services de test (mode mock)...\n")
    
    agent = ServiceSelectorAgent()
    
    # Effacer la collection existante
    agent.client.delete_collection(name=agent.collection_name)
    agent.collection = agent.client.create_collection(
        name=agent.collection_name,
        embedding_function=agent.embedding_function,
        metadata={"description": "Mock OpenSlice Service Catalog"}
    )
    
    # Services de test
    mock_services = [
        {
            "id": "mock-xr-service-001",
            "name": "XR Application Bundle",
            "description": "Extended Reality service bundle for AR, VR, and MR applications with low latency 5G connectivity and edge computing resources",
            "category": "XR",
            "type": "5G Edge Service",
            "num_characteristics": "5"
        },
        {
            "id": "mock-video-streaming-002",
            "name": "4K Video Streaming Service",
            "description": "High-definition video streaming service with CDN and adaptive bitrate for residential customers",
            "category": "Video",
            "type": "Streaming",
            "num_characteristics": "4"
        },
        {
            "id": "mock-iot-platform-003",
            "name": "IoT Platform Service",
            "description": "Industrial IoT platform with device management, data ingestion, and analytics for smart city applications",
            "category": "IoT",
            "type": "Platform",
            "num_characteristics": "6"
        },
        {
            "id": "mock-edge-compute-004",
            "name": "Edge Computing Service",
            "description": "Low-latency edge computing infrastructure for compute-intensive applications near the network edge",
            "category": "Edge",
            "type": "Compute",
            "num_characteristics": "3"
        },
        {
            "id": "mock-5g-slice-005",
            "name": "5G Network Slice - eMBB",
            "description": "Enhanced Mobile Broadband 5G network slice with high throughput and low latency for mobile applications",
            "category": "5G",
            "type": "Network Slice",
            "num_characteristics": "7"
        }
    ]
    
    ids = []
    documents = []
    metadatas = []
    
    for service in mock_services:
        ids.append(service["id"])
        
        # Document textuel
        doc = f"Service: {service['name']} | Description: {service['description']} | Category: {service['category']} | Type: {service['type']}"
        documents.append(doc)
        
        # Métadonnées
        metadata = {
            "name": service["name"],
            "category": service["category"],
            "type": service["type"],
            "num_characteristics": service["num_characteristics"],
            "status": "active"
        }
        metadatas.append(metadata)
    
    # Insertion
    agent.collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    
    print(f"✅ {len(ids)} services de test créés!\n")
    
    # Afficher les stats
    stats = agent.get_collection_stats()
    print("="*80)
    print("STATISTIQUES:")
    print("="*80)
    for key, value in stats.items():
        print(f"{key}: {value}")
    print("="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Ingestion du catalogue OpenSlice (TMF633) dans ChromaDB"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Efface la collection existante avant l'ingestion"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Crée des services de test sans se connecter à OpenSlice"
    )
    
    args = parser.parse_args()
    
    if args.mock:
        create_mock_services()
    else:
        ingest_catalog(clear_existing=args.clear)


if __name__ == "__main__":
    main()
