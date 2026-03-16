"""
Client HTTP pour OpenSlice

Role : Encapsule les appels HTTP vers l'API REST OpenSlice (TMF633, TMF641, TMF638)
       et l'authentification Keycloak.
       
Mode Mock : Si OPENSLICE_MOCK_MODE=true dans .env, simule les réponses sans connexion réelle.
"""
import os
import uuid
from typing import Optional, Dict, Any
from datetime import datetime
import httpx
from config import settings


class OpenSliceClient:

    def __init__(
        self,
        base_url: Optional[str] = None,
        auth_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        client_id: Optional[str] = None,
        timeout: float = 60.0,
        mock_mode: Optional[bool] = None
    ):
        # Mode mock : priorité à l'argument, sinon settings, sinon False
        self.mock_mode = mock_mode if mock_mode is not None else settings.openslice_mock_mode
        
        if self.mock_mode:
            print("🔶 [MOCK MODE] Client OpenSlice en mode simulation (pas de connexion réelle)")
        
        self.base_url = base_url or settings.openslice_base_url
        self.auth_url = auth_url or settings.openslice_auth_url 
        self.username = username or settings.openslice_username
        self.password = password or settings.openslice_password
        self.client_id = client_id or settings.openslice_client_id
        self.token: Optional[str] = None
        
        # Stockage des ordres simulés (mock mode)
        self._mock_orders: Dict[str, Dict[str, Any]] = {}

        self.client = httpx.Client(timeout=timeout) if not self.mock_mode else None

    def authenticate(self) -> str:
        """
        Obtient un token JWT aupres de Keycloak (port 8080).
        En mode mock, retourne un token simulé.
        """
        if self.mock_mode:
            self.token = "mock-jwt-token-for-testing-purposes-only"
            print("🔶 [MOCK] Authentification simulée -- Token JWT fictif généré")
            return self.token
            
        token_url = f"{self.auth_url}/auth/realms/openslice/protocol/openid-connect/token"

        payload = {
            "username": self.username,
            "password": self.password,
            "grant_type": "password",
            "client_id": self.client_id
        }

        print(f"Authentification sur: {token_url} (client: {self.client_id})")

        try:
            response = self.client.post(token_url, data=payload)
            response.raise_for_status()

            self.token = response.json()["access_token"]
            print("Authentification reussie -- Token JWT obtenu")
            return self.token

        except httpx.HTTPStatusError as e:
            print(f"Erreur HTTP {e.response.status_code}: {e.response.text}")
            raise
        except httpx.ConnectError:
            print(f"Impossible de joindre Keycloak sur {self.auth_url}")
            print("  -> Verifiez que le container 'keycloak' est demarre")
            raise
        except KeyError:
            print(f"Reponse inattendue: {response.json()}")
            raise

    def _get_headers(self) -> Dict[str, str]:
        """Headers HTTP avec token JWT. Authentifie automatiquement si besoin."""
        if not self.token:
            self.authenticate()
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def get_catalog(self) -> list:
        """
        Recupere toutes les ServiceSpecifications du catalogue OpenSlice (TMF633).
        En mode mock, retourne une liste vide (utiliser ChromaDB avec --mock).
        """
        if self.mock_mode:
            print("🔶 [MOCK] Catalogue simulé (utilisez ChromaDB avec --mock pour les services)")
            # Retourner les services mock similaires à ceux dans ingest_catalog.py
            return [
                {"id": "mock-xr-service-001", "name": "XR Application Bundle", "description": "Extended Reality service bundle"},
                {"id": "mock-video-streaming-002", "name": "4K Video Streaming Service", "description": "High-definition video streaming"},
                {"id": "mock-iot-platform-003", "name": "IoT Platform Service", "description": "Industrial IoT platform"},
                {"id": "mock-edge-compute-004", "name": "Edge Computing Service", "description": "Low-latency edge computing"},
                {"id": "mock-5g-slice-005", "name": "5G Network Slice - eMBB", "description": "Enhanced Mobile Broadband 5G"},
            ]
        
        url = f"{self.base_url}/tmf-api/serviceCatalogManagement/v4/serviceSpecification"

        print(f"Recuperation du catalogue sur: {url}")

        try:
            response = self.client.get(url, headers=self._get_headers())
            response.raise_for_status()

            services = response.json()

            # Parfois OpenSlice encapsule la liste dans un dict
            if isinstance(services, dict) and "serviceSpecification" in services:
                services = services["serviceSpecification"]

            print(f"{len(services)} service(s) trouve(s) dans le catalogue")
            return services

        except httpx.HTTPStatusError as e:
            print(f"Erreur HTTP {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            print(f"Erreur lors de la recuperation du catalogue: {e}")
            raise


    def submit_order(self, service_order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Soumet un ordre de service a OpenSlice (TMF641).

        Note: L'URL correcte est /tmf-api/serviceOrdering/v4/serviceOrder
        (sans 'Management' dans le path, contrairement au catalogue).

        Appelle : POST http://localhost:13082/tmf-api/serviceOrdering/v4/serviceOrder
        Retourne : la reponse OpenSlice avec l'ID et le statut de l'ordre cree
        """
        url = f"{self.base_url}/tmf-api/serviceOrdering/v4/serviceOrder"

        print(f"Soumission de l'ordre sur: {url}")
        print(f"⏳ En attente de la réponse OpenSlice (timeout: 300 secondes)...")

        # ✅ NE PAS ajouter de dates - laisser OpenSlice les générer
        # Les dates sont optionnelles et OpenSlice peut les créer automatiquement

        try:
            print(f"Envoi de {len(str(service_order))} caractères...")
            
            # ✅ Timeout très long (300s = 5 min) car OpenSlice peut être lent
            response = self.client.post(url, headers=self._get_headers(), json=service_order, timeout=300.0)
            response.raise_for_status()

            result = response.json()
            order_id = result.get("id", "inconnu")
            state = result.get("state", "inconnu")

            print(f"✅ Ordre créé avec succès -- ID: {order_id} | Statut: {state}")
            return result

        except httpx.TimeoutException as e:
            print(f"⏱️  TIMEOUT: OpenSlice a mis trop de temps à répondre ({e})")
            print(f"   L'ordre peut quand même être en cours de création côté OpenSlice")
            raise
        except httpx.HTTPStatusError as e:
            print(f"❌ Erreur HTTP {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            print(f"❌ Erreur lors de la soumission de l'ordre: {e}")
            raise

    def get_service_status(self, order_id: str) -> Dict[str, Any]:
        """
        Recupere le statut d'un ordre de service (TMF641).

        Les statuts possibles dans OpenSlice :
          - ACKNOWLEDGED  : ordre recu, en attente de traitement
          - INPROGRESS    : en cours de deploiement
          - COMPLETED     : deploiement termine avec succes
          - FAILED        : echec du deploiement
          - PARTIAL       : deploiement partiel

        Appelle : GET /tmf-api/serviceOrdering/v4/serviceOrder/{order_id}
        Retourne : dict avec 'id', 'state', et les details complets de l'ordre
        """
        url = f"{self.base_url}/tmf-api/serviceOrdering/v4/serviceOrder/{order_id}"

        print(f"Recuperation du statut pour l'ordre: {order_id}")

        try:
            response = self.client.get(url, headers=self._get_headers())
            response.raise_for_status()

            result = response.json()
            state = result.get("state", "inconnu")

            print(f"Statut de l'ordre {order_id}: {state}")
            return {
                "id": order_id,
                "state": state,
                "details": result
            }

        except httpx.HTTPStatusError as e:
            print(f"Erreur HTTP {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            print(f"Erreur lors de la recuperation du statut: {e}")
            raise

    def get_service_inventory(self) -> list:
        """
        Recupere la liste des services deployes (TMF638 - Service Inventory).

        Difference avec get_catalog() :
          - get_catalog()         -> services DISPONIBLES (ce qu'on peut commander)
          - get_service_inventory() -> services DEPLOYES  (ce qui tourne actuellement)

        Appelle : GET /tmf-api/serviceInventory/v4/service
        Retourne : liste des services actifs dans l'inventaire
        """
        url = f"{self.base_url}/tmf-api/serviceInventory/v4/service"

        print(f"Recuperation de l'inventaire sur: {url}")

        try:
            response = self.client.get(url, headers=self._get_headers())
            response.raise_for_status()

            services = response.json()

            if isinstance(services, dict) and "service" in services:
                services = services["service"]

            print(f"{len(services)} service(s) actif(s) dans l'inventaire")
            return services

        except httpx.HTTPStatusError as e:
            print(f"Erreur HTTP {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            print(f"Erreur lors de la recuperation de l'inventaire: {e}")
            raise
    def close(self):
        """Ferme le client HTTP proprement."""
        self.client.close()


# TEST DIRECT
if __name__ == "__main__":
    print("=" * 60)
    print("TEST -- Toutes les fonctions OpenSlice MCP")
    print("=" * 60)

    server = OpenSliceClient()

    try:
        # Test 1 : Auth
        token = server.authenticate()
        print(f"Token (50 premiers caracteres): {token[:50]}...\n")

        # Test 2 : Catalogue
        services = server.get_catalog()
        print(f"\n{len(services)} service(s) dans le catalogue:")
        for svc in services:
            print(f"  - [{svc.get('id', '?')}] {svc.get('name', 'Sans nom')}")

        # Test 3 : Soumission d'un ordre
        if services:
            first_service_id = services[0]["id"]
            first_service_name = services[0].get("name", "Test Service")

            test_order = {
                "externalId": "test-order-002",
                "priority": "normal",
                "serviceOrderItem": [
                    {
                        "id": "1",
                        "action": "add",
                        "service": {
                            "name": first_service_name,
                            "serviceSpecification": {
                                "id": first_service_id
                            }
                        }
                    }
                ]
            }

            print(f"\nSoumission d'un ordre de test pour: {first_service_name}")
            result = server.submit_order(test_order)
            order_id = result.get("id")
            print(f"Ordre cree -- ID: {order_id}")

            # Test 4 : Statut de l'ordre
            print(f"\nVerification du statut de l'ordre: {order_id}")
            status = server.get_service_status(order_id)
            print(f"Statut: {status['state']}")

        # Test 5 : Inventaire
        print("\nRecuperation de l'inventaire des services deployes:")
        inventory = server.get_service_inventory()
        if inventory:
            for svc in inventory[:3]:
                print(f"  - [{svc.get('id', '?')}] {svc.get('name', 'Sans nom')} | state: {svc.get('state', '?')}")
        else:
            print("  Aucun service deploye pour l'instant (inventaire vide)")

    except Exception as e:
        print(f"\nEchec: {e}")
    finally:
        server.close()