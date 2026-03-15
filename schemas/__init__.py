"""Schémas pour les intentions et ordres de service"""
# Format d'intention agnostique (non TMF921)
from .intent import (
    Intent,
    SubIntent
)

# Format TMF641 pour OpenSlice (conservé)
from .tmf641 import (
    ServiceOrder,
    ServiceOrderItem,
    Service,
    ServiceSpecificationRef,
    ServiceCharacteristic,
    ServiceOrderCreateRequest,
    ServiceOrderStateType,
    ServiceOrderItemActionType,
    RelatedParty
)

__all__ = [
    # Intent agnostique
    "Intent",
    "SubIntent",
    
    # TMF641 (OpenSlice)
    "ServiceOrder",
    "ServiceOrderItem",
    "Service",
    "ServiceSpecificationRef",
    "ServiceCharacteristic",
    "ServiceOrderCreateRequest",
    "ServiceOrderStateType",
    "ServiceOrderItemActionType",
    "RelatedParty",
]
