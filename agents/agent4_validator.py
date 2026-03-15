from typing import Tuple, List
from pydantic import ValidationError
from schemas.tmf641 import ServiceOrder

class ServiceValidatorAgent:
    """
    Agent 4: Responsable de la Qualité (QA). 
    Vérifie la conformité du JSON TMF641 avant soumission.
    """

    def validate(self, service_order: ServiceOrder) -> Tuple[bool, List[str]]:
        """
        Valide l'ordre de service.
        Returns: (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # La validation Pydantic de base est déjà faite lors de l'instanciation
            # On ajoute ici des règles métier spécifiques à OpenSlice
            
            # 1. Vérifier la présence d'au moins un item
            if not service_order.serviceOrderItem or len(service_order.serviceOrderItem) == 0:
                errors.append("L'ordre de service ne contient aucun item (serviceOrderItem).")

            # 2. Vérifier que chaque item a un UUID de spécification valide
            for item in service_order.serviceOrderItem:
                spec_id = item.service.serviceSpecification.id
                if not spec_id or len(spec_id) < 10:
                    errors.append(f"UUID de spécification invalide pour l'item {item.id}")

            if not errors:
                return True, []
            return False, errors

        except Exception as e:
            return False, [str(e)]