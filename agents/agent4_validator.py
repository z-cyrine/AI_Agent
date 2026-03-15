from typing import Tuple, List
from pydantic import ValidationError
from schemas.tmf641 import ServiceOrder
from mcp.mcp_client import MCPClient
import json


class ServiceValidatorAgent:
    """
    Agent 4: Responsable de la Qualité (QA). 
    Vérifie la conformité du JSON TMF641 avant soumission via le protocole MCP.
    """

    def __init__(self):
        """Initialise l'agent avec le client MCP"""
        self.mcp_client = MCPClient(mode="local")

    def validate(self, service_order: ServiceOrder) -> Tuple[bool, List[str]]:
        """
        Valide l'ordre de service en utilisant l'outil MCP.
        
        Returns: (is_valid, list_of_errors)
        """
        try:
            # Convertir l'ordre en JSON pour l'outil MCP
            order_json = service_order.model_dump_json(exclude_none=True)
            
            # Appeler l'outil MCP de validation
            result = self.mcp_client.validate_service_order(order_json)
            
            # Extraire les résultats
            is_valid = result.get("is_valid", False)
            errors = result.get("errors", [])
            warnings = result.get("warnings", [])
            
            # Logger les avertissements (ne pas bloquer)
            if warnings:
                for warning in warnings:
                    print(f"⚠️  Avertissement: {warning}")
            
            return is_valid, errors

        except Exception as e:
            return False, [str(e)]

    def close(self):
        """Ferme la connexion MCP"""
        self.mcp_client.close()