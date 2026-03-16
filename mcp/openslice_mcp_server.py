"""
Serveur MCP (Model Context Protocol) pour OpenSlice

Rôle: Fournir une interface MCP standardisée pour l'accès à OpenSlice.
      - Ressources MCP: Catalog, Orders, Inventory
      - Outils MCP: authenticate, submit_order, get_status, etc.

Le protocole MCP assure une communication standardisée entre les agents et les outils externes.

Utilisation:
    from mcp.openslice_mcp_server import OpenSliceMCPServer
    
    server = OpenSliceMCPServer()
    server.authenticate()
    services = server.get_service_catalog()
"""
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from .openslice_client import OpenSliceClient
from config import settings

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenSliceMCPServer:
    """
    Serveur MCP pour OpenSlice exposant :
    - Ressources (catalog, orders, inventory)
    - Outils (authenticate, submit_order, get_status, etc.)
    
    Architecture:
        Agents → OpenSliceMCPServer → OpenSliceClient → OpenSlice API
    """
    
    def __init__(self):
        """Initialise le serveur MCP et le client OpenSlice"""
        self.client = OpenSliceClient()
        self._tools = {}
        self._resources = {}
        self._register_tools()
        self._register_resources()
        logger.info("Serveur MCP OpenSlice initialisé")
    
    # ========================================================================
    # ENREGISTREMENT DES OUTILS ET RESSOURCES
    # ========================================================================
    
    def _register_tools(self):
        """Enregistre tous les outils MCP disponibles"""
        self._tools = {
            "authenticate": {
                "description": "Obtenir un token JWT auprès de Keycloak",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                },
                "handler": self._tool_authenticate
            },
            "get_service_catalog": {
                "description": "Récupère le catalogue complet des services (TMF633)",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                },
                "handler": self._tool_get_service_catalog
            },
            "submit_service_order": {
                "description": "Soumet un ordre de service à OpenSlice (TMF641)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "service_order_json": {"type": "string", "description": "Ordre au format JSON"}
                    },
                    "required": ["service_order_json"]
                },
                "handler": self._tool_submit_service_order
            },
            "get_order_status": {
                "description": "Récupère le statut d'un ordre de service",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string", "description": "ID de l'ordre (UUID)"}
                    },
                    "required": ["order_id"]
                },
                "handler": self._tool_get_order_status
            },
            "get_service_inventory": {
                "description": "Récupère l'inventaire des services déployés (TMF638)",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                },
                "handler": self._tool_get_service_inventory
            },
            "validate_service_order": {
                "description": "Valide un ordre de service (validation côté client)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "service_order_json": {"type": "string", "description": "Ordre au format JSON"}
                    },
                    "required": ["service_order_json"]
                },
                "handler": self._tool_validate_service_order
            }
        }
        logger.info(f"✅ {len(self._tools)} outils MCP enregistrés")
    
    def _register_resources(self):
        """Enregistre toutes les ressources MCP disponibles"""
        self._resources = {
            "catalog://services": {
                "description": "Liste des services disponibles",
                "handler": self._resource_catalog
            },
            "inventory://services": {
                "description": "Services déployés dans l'inventaire",
                "handler": self._resource_inventory
            }
        }
        logger.info(f"✅ {len(self._resources)} ressources MCP enregistrées")
    
    # ========================================================================
    # IMPLÉMENTATION DES OUTILS MCP
    # ========================================================================
    
    def _tool_authenticate(self, **kwargs) -> Dict[str, Any]:
        """Outil MCP: Authentification auprès de Keycloak"""
        try:
            token = self.client.authenticate()
            logger.info("✅ Authentification réussie")
            return {
                "status": "success",
                "message": "Token JWT obtenu auprès de Keycloak",
                "token_preview": token[:50] + "...",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f" Erreur d'authentification: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _tool_get_service_catalog(self, **kwargs) -> Dict[str, Any]:
        """Outil MCP: Récupère le catalogue complet des services (TMF633)"""
        try:
            services = self.client.get_catalog()
            logger.info(f" Catalogue récupéré: {len(services)} service(s)")
            return {
                "status": "success",
                "services": services,
                "count": len(services),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f" Erreur: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _tool_submit_service_order(self, service_order_json: str, **kwargs) -> Dict[str, Any]:
        """Outil MCP: Soumet un ordre de service à OpenSlice (TMF641)"""
        try:
            # Parser le JSON
            service_order = json.loads(service_order_json)
            
            # Soumettre à OpenSlice
            result = self.client.submit_order(service_order)
            
            order_id = result.get("id", "inconnu")
            logger.info(f" Ordre soumis: {order_id}")
            
            return {
                "status": "success",
                "order_id": order_id,
                "order_state": result.get("state", "unknown"),
                "details": result,
                "timestamp": datetime.now().isoformat()
            }
        except json.JSONDecodeError as e:
            logger.error(f" JSON invalide: {e}")
            return {
                "status": "error",
                "message": f"JSON invalide: {str(e)}"
            }
        except Exception as e:
            logger.error(f" Erreur lors de la soumission: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _tool_get_order_status(self, order_id: str, **kwargs) -> Dict[str, Any]:
        """Outil MCP: Récupère le statut d'un ordre de service"""
        try:
            status = self.client.get_service_status(order_id)
            logger.info(f" Statut de l'ordre {order_id}: {status['state']}")
            
            return {
                "status": "success",
                "order_id": order_id,
                "order_state": status.get("state", "unknown"),
                "details": status,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f" Erreur: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _tool_get_service_inventory(self, **kwargs) -> Dict[str, Any]:
        """Outil MCP: Récupère l'inventaire des services déployés (TMF638)"""
        try:
            inventory = self.client.get_service_inventory()
            logger.info(f" Inventaire récupéré: {len(inventory)} service(s) actif(s)")
            
            return {
                "status": "success",
                "services": inventory,
                "count": len(inventory),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f" Erreur: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _tool_validate_service_order(self, service_order_json: str, **kwargs) -> Dict[str, Any]:
        """Outil MCP: Valide un ordre de service (validation côté client)"""
        try:
            # Parser le JSON
            order = json.loads(service_order_json)
            
            errors = []
            warnings = []
            
            # Vérifications obligatoires
            if not order.get("serviceOrderItem"):
                errors.append("serviceOrderItem est manquant ou vide")
            elif not isinstance(order["serviceOrderItem"], list):
                errors.append("serviceOrderItem doit être une liste")
            else:
                # Valider chaque item
                for i, item in enumerate(order["serviceOrderItem"]):
                    if not item.get("id"):
                        errors.append(f"Item {i}: id manquant")
                    if not item.get("action"):
                        errors.append(f"Item {i}: action manquante")
                    if not item.get("service"):
                        errors.append(f"Item {i}: service manquant")
                    elif not item["service"].get("serviceSpecification"):
                        errors.append(f"Item {i}: serviceSpecification manquante")
                    elif not item["service"]["serviceSpecification"].get("id"):
                        errors.append(f"Item {i}: serviceSpecification.id manquant")
            
            # Avertissements
            if not order.get("externalId"):
                warnings.append("externalId recommandé pour traçabilité")
            
            is_valid = len(errors) == 0
            logger.info(f"{'✅' if is_valid else '❌'} Validation: {len(errors)} erreur(s), {len(warnings)} avertissement(s)")
            
            return {
                "status": "success",
                "is_valid": is_valid,
                "errors": errors,
                "warnings": warnings,
                "timestamp": datetime.now().isoformat()
            }
        except json.JSONDecodeError as e:
            logger.error(f" JSON invalide: {e}")
            return {
                "status": "error",
                "message": f"JSON invalide: {str(e)}",
                "is_valid": False
            }
        except Exception as e:
            logger.error(f" Erreur: {e}")
            return {
                "status": "error",
                "message": str(e),
                "is_valid": False
            }
    
    # ========================================================================
    # IMPLÉMENTATION DES RESSOURCES MCP
    # ========================================================================
    
    def _resource_catalog(self) -> Dict[str, Any]:
        """Ressource MCP: Catalogue des services"""
        try:
            services = self.client.get_catalog()
            return {
                "services": services,
                "count": len(services),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du catalogue: {e}")
            return {"error": str(e)}
    
    def _resource_inventory(self) -> Dict[str, Any]:
        """Ressource MCP: Inventaire des services"""
        try:
            inventory = self.client.get_service_inventory()
            return {
                "services": inventory,
                "count": len(inventory),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'inventaire: {e}")
            return {"error": str(e)}
    
    # ========================================================================
    # API PUBLIQUE DU SERVEUR MCP
    # ========================================================================
    
    def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Appelle un outil MCP par son nom
        
        Args:
            tool_name: Nom de l'outil
            **kwargs: Arguments de l'outil
            
        Returns:
            Résultat de l'outil au format JSON
        """
        if tool_name not in self._tools:
            return {
                "status": "error",
                "message": f"Outil MCP '{tool_name}' non trouvé. Outils disponibles: {list(self._tools.keys())}"
            }
        
        tool = self._tools[tool_name]
        try:
            result = tool["handler"](**kwargs)
            return result
        except Exception as e:
            logger.error(f"Erreur lors de l'appel de l'outil '{tool_name}': {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_resource(self, resource_uri: str) -> Dict[str, Any]:
        """
        Récupère une ressource MCP
        
        Args:
            resource_uri: URI de la ressource (ex: "catalog://services")
            
        Returns:
            Contenu de la ressource
        """
        if resource_uri not in self._resources:
            return {
                "error": f"Ressource '{resource_uri}' non trouvée. Ressources disponibles: {list(self._resources.keys())}"
            }
        
        resource = self._resources[resource_uri]
        try:
            result = resource["handler"]()
            return result
        except Exception as e:
            logger.error(f"Erreur lors de l'accès à la ressource '{resource_uri}': {e}")
            return {"error": str(e)}
    
    def get_tools_info(self) -> Dict[str, Any]:
        """Retourne la liste et description des outils MCP"""
        return {
            tool_name: {
                "description": tool["description"],
                "input_schema": tool["input_schema"]
            }
            for tool_name, tool in self._tools.items()
        }
    
    def get_resources_info(self) -> Dict[str, str]:
        """Retourne la liste et description des ressources MCP"""
        return {
            resource_uri: resource["description"]
            for resource_uri, resource in self._resources.items()
        }
    
    # ========================================================================
    # MÉTHODES DE COMPATIBILITÉ (pour l'ancienne API)
    # ========================================================================
    
    def authenticate(self) -> str:
        """Compatibilité: Authentification (retourne le token)"""
        return self.client.authenticate()
    
    def get_service_catalog(self) -> List[Dict[str, Any]]:
        """Compatibilité: Récupère le catalogue"""
        return self.client.get_catalog()
    
    def submit_service_order(self, service_order: Dict[str, Any]) -> Dict[str, Any]:
        """Compatibilité: Soumet un ordre"""
        return self.client.submit_order(service_order)
    
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Compatibilité: Récupère le statut d'un ordre"""
        return self.client.get_service_status(order_id)
    
    def get_service_inventory(self) -> List[Dict[str, Any]]:
        """Compatibilité: Récupère l'inventaire"""
        return self.client.get_service_inventory()
    
    def close(self):
        """Ferme les connexions"""
        self.client.close()
        logger.info("Serveur MCP fermé")


# ============================================================================
# TEST / DEMO
# ============================================================================

def main():
    """Test du serveur MCP"""
    print("\n" + "="*80)
    print("TEST -- Serveur MCP OpenSlice")
    print("="*80 + "\n")
    
    server = OpenSliceMCPServer()
    
    # Afficher les outils disponibles
    print(" OUTILS MCP DISPONIBLES:")
    print("-" * 80)
    tools_info = server.get_tools_info()
    for tool_name, tool_info in tools_info.items():
        print(f"  • {tool_name}")
        print(f"    Description: {tool_info['description']}")
    
    # Afficher les ressources disponibles
    print("\n RESSOURCES MCP DISPONIBLES:")
    print("-" * 80)
    resources_info = server.get_resources_info()
    for resource_uri, description in resources_info.items():
        print(f"  • {resource_uri}")
        print(f"    Description: {description}")
    
    print("\n" + "="*80)
    print("Le serveur MCP est prêt à être utilisé par les agents")
    print("="*80 + "\n")
    
    server.close()


if __name__ == "__main__":
    main()
