"""
Agent 2: Le Sélecteur (Service Broker)

Rôle: Sélection sémantique de services via RAG (Retrieval Augmented Generation)
Technologie: ChromaDB + sentence-transformers
Responsable: Cyrine
"""
import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

from schemas.intent import Intent
from config import settings


class ServiceSelectorAgent:
    """
    Agent 2: Sélectionne les services appropriés à partir d'une intention structurée
    utilisant une recherche sémantique (RAG) sur le catalogue OpenSlice
    
    Architecture:
    - Base de données vectorielle: ChromaDB
    - Modèle d'embeddings: sentence-transformers (all-MiniLM-L6-v2)
    - Recherche par similarité cosinus
    
    Exemple d'utilisation:
    ```python
    # Initialisation
    agent = ServiceSelectorAgent()
    
    # Sélection de services pour une intention
    intent = Intent(...)
    results = agent.select_services(intent, top_k=3)
    
    for result in results:
        print(f"Service: {result['name']}")
        print(f"UUID: {result['id']}")
        print(f"Score: {result['score']}")
    ```
    """
    
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        embedding_model: Optional[str] = None,
        collection_name: str = "openslice_services"
    ):
        """
        Initialise l'agent de sélection de services
        
        Args:
            persist_directory: Répertoire de persistance ChromaDB
            embedding_model: Nom du modèle d'embeddings
            collection_name: Nom de la collection ChromaDB
        """
        self.persist_directory = persist_directory or settings.chroma_persist_dir
        self.embedding_model_name = embedding_model or settings.embedding_model
        self.collection_name = collection_name
        
        # Créer le répertoire si nécessaire
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialiser le modèle d'embeddings
        print(f"📦 Chargement du modèle d'embeddings: {self.embedding_model_name}")
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        
        # Fonction d'embedding pour ChromaDB
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.embedding_model_name
        )
        
        # Initialiser ChromaDB
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Obtenir ou créer la collection
        try:
            self.collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            print(f"✅ Collection '{self.collection_name}' chargée ({self.collection.count()} services)")
        except Exception:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "OpenSlice Service Catalog"}
            )
            print(f"✅ Collection '{self.collection_name}' créée (vide)")
    
    def _intent_to_query(self, intent: Intent) -> str:
        """
        Convertit une intention en requête textuelle pour la recherche
        
        Args:
            intent: Intention structurée avec sous-intentions
            
        Returns:
            str: Requête textuelle optimisée pour la recherche sémantique
        """
        query_parts = []
        
        # Type de service
        if intent.type:
            query_parts.append(intent.type.replace("_", " "))
        
        # Localisation globale
        if intent.location:
            query_parts.append(f"location: {intent.location}")
        
        # QoS global
        if intent.qos:
            for key, value in intent.qos.items():
                query_parts.append(f"{key}: {value}")
        
        # Parcourir les sous-intentions par domaine
        for sub_intent in intent.sub_intents:
            # Nom du domaine
            query_parts.append(f"{sub_intent.domain} domain")
            
            # Exigences du domaine
            for key, value in sub_intent.requirements.items():
                if isinstance(value, list):
                    query_parts.append(f"{key}: {', '.join(str(v) for v in value)}")
                else:
                    query_parts.append(f"{key}: {value}")
        
        # Joindre toutes les parties
        query = " ".join(query_parts)
        
        print(f"🔍 Requête de recherche: {query[:200]}...")
        return query
    
    def select_services(
        self,
        intent: Intent,
        top_k: int = 5,
        min_score: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Sélectionne les services les plus pertinents pour une intention
        
        Args:
            intent: Intention structurée avec sous-intentions
            top_k: Nombre maximum de résultats à retourner
            min_score: Score de similarité minimum (0-1)
            
        Returns:
            List[Dict]: Liste des services sélectionnés avec leurs métadonnées
            
        Format de retour:
        [
            {
                "id": "uuid-service-spec",
                "name": "XR Service Bundle",
                "description": "...",
                "score": 0.87,
                "metadata": {...}
            },
            ...
        ]
        """
        if self.collection.count() == 0:
            print("⚠️  La collection est vide. Exécutez d'abord le script d'ingestion.")
            return []
        
        # Convertir l'intention en requête
        query = self._intent_to_query(intent)
        
        # Recherche dans ChromaDB
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["metadatas", "documents", "distances"]
        )
        
        # Formater les résultats
        services = []
        
        if results and results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                # ChromaDB retourne des distances (plus proche = plus petit)
                # Convertir en score de similarité (0-1, plus grand = meilleur)
                distance = results['distances'][0][i]
                score = 1 / (1 + distance)  # Normalisation
                
                # Filtrer par score minimum
                if score < min_score:
                    continue
                
                service = {
                    "id": results['ids'][0][i],
                    "score": round(score, 3),
                    "description": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {}
                }
                
                # Extraire le nom depuis les métadonnées
                if results['metadatas'] and results['metadatas'][0][i]:
                    service["name"] = results['metadatas'][0][i].get('name', 'Unknown Service')
                
                services.append(service)
            
            print(f"✅ {len(services)} services trouvés (score >= {min_score})")
            for svc in services:
                print(f"   - {svc['name']} (score: {svc['score']})")
        else:
            print("⚠️  Aucun service trouvé")
        
        return services
    
    def get_best_service(self, intent: Intent) -> Optional[Dict[str, Any]]:
        """
        Retourne le service le plus pertinent pour une intention
        
        Args:
            intent: Intention structurée
            
        Returns:
            Dict: Service sélectionné ou None si aucun service trouvé
        """
        services = self.select_services(intent, top_k=1)
        return services[0] if services else None
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Retourne des statistiques sur la collection de services"""
        return {
            "name": self.collection_name,
            "count": self.collection.count(),
            "embedding_model": self.embedding_model_name,
            "persist_directory": self.persist_directory
        }


# Fonction utilitaire pour tests
def test_agent():
    """Teste l'agent de sélection avec une intention exemple"""
    from schemas.intent import SubIntent
    
    # Créer une intention de test
    intent = Intent(
        intent_id="XR_Test_001",
        type="composite_service",
        sub_intents=[
            SubIntent(
                domain="cloud",
                requirements={
                    "cpu": 4,
                    "ram": "2GB",
                    "applications": ["AR_server", "VR_engine"]
                }
            ),
            SubIntent(
                domain="ran",
                requirements={
                    "network_type": "5G",
                    "location": "Nice",
                    "max_latency": "5ms"
                }
            )
        ],
        location="Nice",
        qos={"max_latency": "5ms"}
    )
    
    # Initialiser l'agent
    agent = ServiceSelectorAgent()
    
    # Afficher les stats
    stats = agent.get_collection_stats()
    print("\n" + "="*80)
    print("STATISTIQUES DE LA COLLECTION:")
    print("="*80)
    for key, value in stats.items():
        print(f"{key}: {value}")
    print("="*80)
    
    # Sélectionner les services
    print("\n" + "="*80)
    print("SÉLECTION DE SERVICES:")
    print("="*80)
    
    services = agent.select_services(intent, top_k=3)
    
    if services:
        print(f"\n✅ {len(services)} service(s) sélectionné(s):\n")
        for i, svc in enumerate(services, 1):
            print(f"{i}. {svc['name']}")
            print(f"   UUID: {svc['id']}")
            print(f"   Score: {svc['score']}")
            print(f"   Description: {svc['description'][:100]}...")
            print()
    else:
        print("\n⚠️  Aucun service trouvé. La collection est peut-être vide.")
        print("   Exécutez d'abord: python scripts/ingest_catalog.py")
    
    print("="*80)
    
    return services


if __name__ == "__main__":
    # Test de l'agent
    test_agent()
