"""
Schémas Pydantic pour TMF641 - Service Ordering Management API

Référence: https://www.tmforum.org/resources/specification/tmf641-service-ordering-api-rest-specification-r19-0-1/

Ces schémas seront utilisés par les Agents 3 et 4 (Sarra)
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ServiceOrderStateType(str, Enum):
    """États d'un ordre de service"""
    ACKNOWLEDGED = "acknowledged"
    REJECTED = "rejected"
    PENDING = "pending"
    HELD = "held"
    IN_PROGRESS = "inProgress"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
    ASSESSED_customer_approved = "assessedCustomerApproved"


class ServiceOrderItemStateType(str, Enum):
    """États d'un item d'ordre de service"""
    ACKNOWLEDGED = "acknowledged"
    REJECTED = "rejected"
    PENDING = "pending"
    HELD = "held"
    IN_PROGRESS = "inProgress"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"


class ServiceOrderItemActionType(str, Enum):
    """Actions possibles sur un item de service"""
    ADD = "add"
    MODIFY = "modify"
    DELETE = "delete"
    NO_CHANGE = "noChange"


class ServiceSpecificationRef(BaseModel):
    """Référence à une spécification de service (catalogue)"""
    id: str = Field(..., description="UUID de la ServiceSpecification dans OpenSlice")
    href: Optional[str] = None
    name: Optional[str] = None
    version: Optional[str] = None


class ServiceCharacteristic(BaseModel):
    """Caractéristique d'un service"""
    name: str
    value: Any
    valueType: Optional[str] = None


class Service(BaseModel):
    """Service à commander"""
    id: Optional[str] = None
    serviceType: Optional[str] = None
    name: Optional[str] = None
    
    # Référence à la spécification du catalogue
    serviceSpecification: ServiceSpecificationRef
    
    # Caractéristiques du service
    serviceCharacteristic: Optional[List[ServiceCharacteristic]] = Field(default_factory=list)


class ServiceOrderItem(BaseModel):
    """Item d'un ordre de service"""
    id: str = Field(..., description="Identifiant unique de l'item (e.g., '1', '2')")
    action: ServiceOrderItemActionType
    state: Optional[ServiceOrderItemStateType] = Field(default=ServiceOrderItemStateType.ACKNOWLEDGED)
    
    # Service à commander
    service: Service
    
    # Quantité
    quantity: Optional[int] = Field(default=1, ge=1)


class RelatedParty(BaseModel):
    """Partie prenante (utilisateur, organisation)"""
    id: Optional[str] = None
    name: str
    role: Optional[str] = None
    href: Optional[str] = None


class ServiceOrder(BaseModel):
    """
    Ordre de service TMF641 complet
    
    Exemple d'utilisation:
    ```python
    order = ServiceOrder(
        externalId="intent-xr-service-001",
        description="XR Service deployment based on user intent",
        requestedStartDate=datetime.now(),
        relatedParty=[RelatedParty(name="Cyrine", role="requester")],
        serviceOrderItem=[
            ServiceOrderItem(
                id="1",
                action="add",
                service=Service(
                    name="XR Service Bundle",
                    serviceSpecification=ServiceSpecificationRef(
                        id="uuid-from-openslice-catalog"
                    ),
                    serviceCharacteristic=[
                        ServiceCharacteristic(name="vCPU", value=4),
                        ServiceCharacteristic(name="memory", value="2GB")
                    ]
                )
            )
        ]
    )
    ```
    """
    id: Optional[str] = None
    href: Optional[str] = None
    
    # Identifiant externe (lien avec l'intention)
    externalId: Optional[str] = Field(None, description="Référence à l'intention TMF921")
    
    # Description
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    
    # État
    state: Optional[ServiceOrderStateType] = Field(default=ServiceOrderStateType.ACKNOWLEDGED)
    
    # Dates
    orderDate: Optional[datetime] = None
    requestedStartDate: Optional[datetime] = None
    requestedCompletionDate: Optional[datetime] = None
    expectedCompletionDate: Optional[datetime] = None
    completionDate: Optional[datetime] = None
    
    # Items de l'ordre
    serviceOrderItem: List[ServiceOrderItem] = Field(
        ...,
        min_length=1,
        description="Liste des services à commander"
    )
    
    # Parties prenantes
    relatedParty: Optional[List[RelatedParty]] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "externalId": "intent-xr-001",
                "description": "XR Service deployment for Nice area",
                "priority": "high",
                "requestedStartDate": "2026-02-19T10:00:00Z",
                "serviceOrderItem": [
                    {
                        "id": "1",
                        "action": "add",
                        "service": {
                            "name": "XR AR Content Server",
                            "serviceSpecification": {
                                "id": "uuid-ar-service-spec"
                            },
                            "serviceCharacteristic": [
                                {"name": "vCPU", "value": 4, "valueType": "integer"},
                                {"name": "memory", "value": "2GB", "valueType": "string"}
                            ]
                        }
                    }
                ],
                "relatedParty": [
                    {"name": "Cyrine", "role": "requester"}
                ]
            }
        }


class ServiceOrderCreateRequest(BaseModel):
    """Requête simplifiée pour créer un ordre de service"""
    externalId: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    requestedStartDate: Optional[datetime] = None
    serviceOrderItem: List[ServiceOrderItem]
    relatedParty: Optional[List[RelatedParty]] = Field(default_factory=list)
