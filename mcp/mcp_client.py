"""
Client MCP (Model Context Protocol) pour communiquer avec le serveur MCP

Ce client permet aux agents de :
- Appeler des outils MCP (authenticate, submit_order, validate, etc.)
- Lire des ressources MCP (catalog, inventory, etc.)
- Communiquer via le serveur MCP

Utilisation:
    from mcp.mcp_client import MCPClient
    
    client = MCPClient(mode="local")
    
    # Appeler un outil
    result = client.call_tool("get_service_catalog")
    
    # Lire une ressource
    catalog = client.read_resource("catalog://services")
"""
import json
import logging
from typing import Any, Dict, Optional

from .openslice_mcp_server import OpenSliceMCPServer

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPClient:
    """
    Client MCP pour communiquer avec le serveur MCP
    
    Mode local : Communication directe avec OpenSliceMCPServer (pas de serveur externe)
    """
    
    def __init__(self, mode: str = "local"):
        """
        Initialise le client MCP
        
        Args:
            mode: "local" (direct) - défaut: local
        """
        self.mode = mode
        
        if mode == "local":
            # Mode local : communication directe avec le serveur MCP
            self.mcp_server = OpenSliceMCPServer()
            logger.info("✅ Client MCP initialisé (mode LOCAL - communication directe)")
        else:
            raise NotImplementedError("Mode 'remote' nécessite une implémentation HTTP")
    
    # ========================================================================
    # OUTILS MCP - Interface publique
    # ========================================================================
    
    def authenticate(self) -> Dict[str, Any]:
        """
        Outil MCP: Authentification auprès de Keycloak
        
        Returns:
            Dict avec token JWT et statut
        """
        logger.info("🔐 Appel MCP: authenticate()")
        return self.call_tool("authenticate")
    
    def get_service_catalog(self) -> Dict[str, Any]:
        """
        Outil MCP: Récupère le catalogue complet des services (TMF633)
        
        Utilisé par Agent 2 (Service Selector)
        
        Returns:
            Dict avec la liste des services
        """
        logger.info("📦 Appel MCP: get_service_catalog()")
        return self.call_tool("get_service_catalog")
    
    def submit_service_order(self, service_order_json: str) -> Dict[str, Any]:
        """
        Outil MCP: Soumet un ordre de service à OpenSlice (TMF641)
        
        Utilisé par Orchestrator
        
        Args:
            service_order_json: Ordre de service au format JSON string
            
        Returns:
            Dict avec l'ID de l'ordre créé
        """
        logger.info("📤 Appel MCP: submit_service_order()")
        return self.call_tool("submit_service_order", service_order_json=service_order_json)
    
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Outil MCP: Récupère le statut d'un ordre de service
        
        Utilisé par Orchestrator pour suivre le déploiement
        
        Args:
            order_id: ID de l'ordre (UUID)
            
        Returns:
            Dict avec l'état actuel de l'ordre
        """
        logger.info(f"🔍 Appel MCP: get_order_status({order_id})")
        return self.call_tool("get_order_status", order_id=order_id)
    
    def get_service_inventory(self) -> Dict[str, Any]:
        """
        Outil MCP: Récupère l'inventaire des services déployés (TMF638)
        
        Returns:
            Dict avec la liste des services déployés
        """
        logger.info("📊 Appel MCP: get_service_inventory()")
        return self.call_tool("get_service_inventory")
    
    def validate_service_order(self, service_order_json: str) -> Dict[str, Any]:
        """
        Outil MCP: Valide un ordre de service (validation côté client)
        
        Utilisé par Agent 4 (Validator)
        
        Args:
            service_order_json: Ordre de service au format JSON string
            
        Returns:
            Dict avec is_valid (bool), erreurs, avertissements
        """
        logger.info("✅ Appel MCP: validate_service_order()")
        return self.call_tool("validate_service_order", service_order_json=service_order_json)
    
    # ========================================================================
    # RESSOURCES MCP - Interface publique
    # ========================================================================
    
    def read_catalog(self) -> Dict[str, Any]:
        """
        Ressource MCP: Lit le catalogue des services
        
        Returns:
            Dict avec la liste des services et les métadonnées
        """
        logger.info("📖 Lecture ressource MCP: catalog://services")
        return self.read_resource("catalog://services")
    
    def read_inventory(self) -> Dict[str, Any]:
        """
        Ressource MCP: Lit l'inventaire des services déployés
        
        Returns:
            Dict avec la liste des services déployés
        """
        logger.info("📖 Lecture ressource MCP: inventory://services")
        return self.read_resource("inventory://services")
    
    # ========================================================================
    # INTERFACE GÉNÉRIQUE
    # ========================================================================
    
    def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Appelle un outil MCP par son nom
        
        Args:
            tool_name: Nom de l'outil
            **kwargs: Arguments de l'outil
            
        Returns:
            Résultat de l'outil au format Dict
        """
        try:
            if self.mode == "local":
                result = self.mcp_server.call_tool(tool_name, **kwargs)
                status = result.get("status", "unknown")
                if status == "success":
                    logger.debug(f"   ✅ Outil '{tool_name}' : succès")
                else:
                    logger.warning(f"   ⚠️  Outil '{tool_name}' : {result.get('message', 'erreur inconnue')}")
                return result
        except Exception as e:
            logger.error(f"   ❌ Erreur lors de l'appel de '{tool_name}': {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def read_resource(self, resource_uri: str) -> Dict[str, Any]:
        """
        Lit une ressource MCP
        
        Args:
            resource_uri: URI de la ressource (ex: "catalog://services")
            
        Returns:
            Contenu de la ressource au format Dict
        """
        try:
            if self.mode == "local":
                result = self.mcp_server.get_resource(resource_uri)
                if "error" not in result:
                    logger.debug(f"   ✅ Ressource '{resource_uri}' : succès")
                else:
                    logger.warning(f"   ⚠️  Ressource '{resource_uri}' : {result.get('error', 'erreur inconnue')}")
                return result
        except Exception as e:
            logger.error(f"   ❌ Erreur lors de la lecture de '{resource_uri}': {e}")
            return {
                "error": str(e)
            }
    
    def get_available_tools(self) -> Dict[str, Any]:
        """Retourne la liste des outils MCP disponibles"""
        return self.mcp_server.get_tools_info()
    
    def get_available_resources(self) -> Dict[str, str]:
        """Retourne la liste des ressources MCP disponibles"""
        return self.mcp_server.get_resources_info()
    
    def close(self):
        """Ferme la connexion MCP"""
        if self.mode == "local":
            self.mcp_server.close()
            logger.info("Client MCP fermé")


# ============================================================================
# TEST / DÉMO
# ============================================================================

def main():
    """Test du client MCP"""
    print("\n" + "="*80)
    print("TEST -- Client MCP OpenSlice")
    print("="*80 + "\n")
    
    # Créer le client
    client = MCPClient(mode="local")
    
    # Afficher les outils disponibles
    print("📋 OUTILS MCP DISPONIBLES:")
    tools = client.get_available_tools()
    for tool_name in tools.keys():
        print(f"  • {tool_name}")
    
    # Afficher les ressources disponibles
    print("\n📚 RESSOURCES MCP DISPONIBLES:")
    resources = client.get_available_resources()
    for resource_uri in resources.keys():
        print(f"  • {resource_uri}")
    
    print("\n" + "="*80)
    print("Client MCP prêt à être utilisé par les agents")
    print("="*80 + "\n")
    
    client.close()


if __name__ == "__main__":
    main()
