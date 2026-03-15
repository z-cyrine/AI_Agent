"""
MCP (Model Context Protocol) - Communication Agents ↔ Outils Externes

Ce module encapsule toutes les ressources et outils MCP disponibles pour les agents :
- Ressources : Catalogue de services (TMF633), Ordres (TMF641), Inventaire (TMF638)
- Outils : Authentification, Soumission d'ordres, Vérification de statut, Validation

Le protocole MCP assure une communication standardisée entre les agents et les services externes.
"""

from .openslice_client import OpenSliceClient
from .openslice_mcp_server import OpenSliceMCPServer

__all__ = ["OpenSliceClient", "OpenSliceMCPServer"]
