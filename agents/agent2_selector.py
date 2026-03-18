"""
Agent 2: Le Sélecteur (Service Broker)

Rôle: Sélection sémantique de services via RAG (Retrieval Augmented Generation)
Technologie: ChromaDB + sentence-transformers
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions

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
        
        # Initialiser le modèle d'embeddings (une seule fois, via ChromaDB)
        print(f"Chargement du modèle d'embeddings: {self.embedding_model_name}")
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
            print(f" Collection '{self.collection_name}' chargée ({self.collection.count()} services)")
        except Exception:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "OpenSlice Service Catalog"}
            )
            print(f" Collection '{self.collection_name}' créée (vide)")
    
    def _query_chromadb(self, query: str, top_k: int, min_score: float) -> List[Dict[str, Any]]:
        """Exécute une recherche dans ChromaDB et retourne les résultats formatés."""
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["metadatas", "documents", "distances"]
        )
        services = []
        if results and results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                distance = results['distances'][0][i]
                score = 1 / (1 + distance)
                if score < min_score:
                    continue
                service = {
                    "id": results['ids'][0][i],
                    "score": round(score, 3),
                    "description": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {}
                }
                if results['metadatas'] and results['metadatas'][0][i]:
                    service["name"] = results['metadatas'][0][i].get('name', 'Unknown Service')
                services.append(service)
        return services

    def _sub_intent_to_query(self, sub_intent, intent: Intent) -> str:
        """
        Convertit une sous-intention en requête textuelle ciblée.

        Priorité:
        1. sub_intent.description (fournie par Agent 1 / LLM) — riche sémantiquement
        2. Fallback: construction à partir du domain + requirements (si pas de description)
        """
        # Cas idéal : Agent 1 a fourni une description en langage naturel
        if sub_intent.description:
            query = sub_intent.description
            # Enrichir avec QoS global si pertinent
            if intent.qos:
                for key, value in intent.qos.items():
                    if "latency" in key.lower():
                        query += f" low latency {value}"
            return query

        # Fallback : construction manuelle à partir du domain
        # (utilisé seulement si Agent 1 ne fournit pas de description)
        parts = [f"{sub_intent.domain} service"]
        for key, value in sub_intent.requirements.items():
            if isinstance(value, list):
                parts.append(" ".join(str(v).replace("_", " ") for v in value))
            elif "type" in key.lower() or "network" in key.lower():
                parts.append(str(value))
            elif "latency" in key.lower():
                parts.append(f"low latency {value}")
        if intent.qos:
            for key, value in intent.qos.items():
                if "latency" in key.lower():
                    parts.append(f"low latency {value}")
        return " ".join(parts)

    def select_services(
        self,
        intent: Intent,
        top_k: int = 3,
        min_score: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Sélectionne le meilleur service pour chaque sous-intention.

        Logique :
        - Récupère top_k candidats par sous-intention (pour avoir des alternatives)
        - Retourne 1 service par sous-intention (le meilleur non-doublon)
        - Inclut les candidats alternatifs dans 'alternatives' pour Agent 4 (validateur)

        Args:
            intent: Intention structurée avec sous-intentions
            top_k: Taille du pool de candidats par sous-intention (défaut: 3)
                   → 3 est optimal : fallback en cas de doublon, sans surcharger
            min_score: Score de similarité minimum (0-1)

        Returns:
            List[Dict]: Un service par sous-intention
        [
            {
                "id": "uuid",
                "name": "XR Service Bundle",
                "domain": "cloud",
                "score": 0.87,
                "description": "...",
                "metadata": {...},
                "alternatives": [  # ← candidats de remplacement pour Agent 4
                    {"id": "...", "name": "...", "score": 0.71, ...},
                    ...
                ]
            },
            ...
        ]
        """
        if self.collection.count() == 0:
            print("    La collection est vide. Exécutez d'abord le script d'ingestion.")
            return []

        services = []
        seen_ids = set()  # éviter les doublons entre sous-intentions

        for sub_intent in intent.sub_intents:
            query = self._sub_intent_to_query(sub_intent, intent)
            print(f"    [{sub_intent.domain}] Requête: {query[:120]}...")

            candidates = self._query_chromadb(query, top_k=top_k, min_score=min_score)

            # Sélectionner le meilleur candidat non déjà assigné à une autre sous-intention
            selected = None
            alternatives = []
            for candidate in candidates:
                if candidate["id"] not in seen_ids:
                    if selected is None:
                        selected = candidate
                        seen_ids.add(candidate["id"])
                    else:
                        alternatives.append(candidate)  # garder pour Agent 4

            if selected:
                selected["domain"] = sub_intent.domain
                selected["constraints"] = sub_intent.requirements  # pour Agent 3 (Traducteur TMF641)
                selected["alternatives"] = alternatives
                services.append(selected)
                alt_info = f" (+{len(alternatives)} alternative(s))" if alternatives else ""
                print(f"    Sélectionné: {selected['name']} (score: {selected['score']}){alt_info}")
            else:
                print(f"    Aucun service trouvé pour le domaine '{sub_intent.domain}'")

        print(f"\n    {len(services)} service(s) sélectionné(s) au total ({len(intent.sub_intents)} sous-intentions)")
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
                description="cloud hosting for augmented reality AR and virtual reality VR applications with extended reality XR capabilities",
                requirements={
                    "cpu": 4,
                    "ram": "2GB",
                    "applications": ["AR_server", "VR_engine"]
                }
            ),
            SubIntent(
                domain="ran",
                description="5G radio access network with mobile broadband low latency connectivity",
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
        print(f"\n {len(services)} service(s) sélectionné(s):\n")
        for i, svc in enumerate(services, 1):
            print(f"{i}. [{svc.get('domain', '?').upper()}] {svc['name']}")
            print(f"   UUID: {svc['id']}")
            print(f"   Score: {svc['score']}")
            print(f"   Description: {svc['description'][:100]}...")
            print()
    else:
        print("\n  Aucun service trouvé. La collection est peut-être vide.")
        print("   Exécutez d'abord: python scripts/ingest_catalog.py")
    
    print("="*80)
    
    return services


if __name__ == "__main__":
    # Test de l'agent
    test_agent()
