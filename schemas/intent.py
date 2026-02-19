"""
Schémas pour les Intentions (Format JSON Agnostique)

Format simplifié et générique permettant de décomposer toute intention
en sous-intentions par domaine/aspect. Non lié à un standard spécifique.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class SubIntent(BaseModel):
    """
    Sous-intention représentant un domaine/aspect spécifique de l'intention globale
    
    Le domaine peut être n'importe quoi selon le contexte:
    - Infrastructure: "compute", "storage", "network", "edge"
    - Application: "frontend", "backend", "database", "cache"
    - Réseau: "cloud", "transport", "ran", "security"
    - IoT: "sensors", "gateway", "analytics"
    - Etc.
    """
    domain: str = Field(..., description="Nom du domaine/aspect (ex: 'compute', 'network', 'database')")
    requirements: Dict[str, Any] = Field(
        default_factory=dict,
        description="Exigences techniques spécifiques à ce domaine"
    )


class Intent(BaseModel):
    """
    Intention structurée au format JSON agnostique
    
    Exemple:
    {
      "intent_id": "XR_Deployment_Nice_001",
      "type": "composite_service",
      "sub_intents": [
        {
          "domain": "cloud",
          "requirements": { "cpu": 4, "ram": "2GB" }
        },
        {
          "domain": "transport",
          "requirements": { "bandwidth": "5Gbps" }
        },
        {
          "domain": "ran",
          "requirements": { "max_latency": "5ms", "location": "Nice" }
        }
      ]
    }
    """
    intent_id: Optional[str] = Field(None, description="Identifiant unique de l'intention")
    type: str = Field("composite_service", description="Type de service désiré")
    sub_intents: List[SubIntent] = Field(
        default_factory=list,
        description="Liste des sous-intentions par domaine"
    )
    
    # Métadonnées globales
    location: Optional[str] = Field(None, description="Localisation (ex: Nice)")
    qos: Optional[Dict[str, Any]] = Field(
        None,
        description="QoS global: max_latency, min_bandwidth, etc."
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "intent_id": "XR_Deployment_Nice_001",
                "type": "composite_service",
                "sub_intents": [
                    {
                        "domain": "cloud",
                        "requirements": {
                            "cpu": 4,
                            "ram": "2GB",
                            "applications": [
                                "AR_content_server",
                                "MR_collaboration",
                                "VR_simulation"
                            ]
                        }
                    },
                    {
                        "domain": "transport",
                        "requirements": {
                            "bandwidth": "5Gbps",
                            "interconnection": "all_to_all"
                        }
                    },
                    {
                        "domain": "ran",
                        "requirements": {
                            "network_type": "5G",
                            "location": "Nice",
                            "max_latency": "5ms"
                        }
                    }
                ],
                "location": "Nice",
                "qos": {
                    "max_latency": "5ms"
                }
            }
        }


__all__ = ["Intent", "SubIntent"]
