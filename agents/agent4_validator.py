"""
Agent 4: Le Validateur (Quality Assurance)

Rôle: Validation d'ordres de service TMF641
Technologie: jsonschema + Pydantic
Responsable: Sarra

TODO: À implémenter par Sarra
"""
from typing import Dict, Any, List, Tuple
import jsonschema
from schemas.tmf641 import ServiceOrder


class ServiceValidatorAgent:
    """
    Agent 4: Valide les ordres de service TMF641 avant envoi à OpenSlice
    
    Exemple d'utilisation:
    ```python
    agent = ServiceValidatorAgent()
    service_order = ServiceOrder(...)
    
    is_valid, errors = agent.validate(service_order)
    if not is_valid:
        print(f"Erreurs: {errors}")
    ```
    """
    
    def __init__(self):
        """
        Initialise l'agent validateur
        
        TODO Sarra:
        - Charger le schéma JSON TMF641 (si disponible)
        - Configurer les règles de validation personnalisées
        - Préparer les validateurs Pydantic
        """
        pass
    
    def validate(self, service_order: ServiceOrder) -> Tuple[bool, List[str]]:
        """
        Valide un ordre de service TMF641
        
        Args:
            service_order: Ordre de service à valider
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, error_messages)
            
        TODO Sarra:
        1. Validation Pydantic (types, champs obligatoires)
        2. Validation des UUIDs de services
        3. Validation des ServiceOrderItem:
           - Chaque item doit avoir un ID unique
           - L'action doit être valide (add, modify, delete)
           - Le ServiceSpecificationRef doit avoir un ID valide
        4. Validation des ServiceCharacteristic:
           - Les types doivent correspondre (integer, string, etc.)
        5. Validation métier:
           - Au moins un ServiceOrderItem
           - Les dates sont cohérentes
        
        Retourner:
        - (True, []) si tout est valide
        - (False, ["erreur1", "erreur2", ...]) sinon
        """
        raise NotImplementedError("Agent 4 à implémenter par Sarra")
    
    def validate_and_fix(
        self,
        service_order: ServiceOrder,
        max_retries: int = 3
    ) -> Tuple[bool, ServiceOrder, List[str]]:
        """
        Valide et tente de corriger automatiquement les erreurs
        
        Args:
            service_order: Ordre de service à valider
            max_retries: Nombre maximum de tentatives de correction
            
        Returns:
            Tuple[bool, ServiceOrder, List[str]]: (is_valid, corrected_order, errors)
            
        TODO Sarra:
        - Implémenter une boucle de correction
        - Si validation échoue, identifier les corrections possibles:
          * Ajouter des IDs manquants
          * Corriger les types (string → integer, etc.)
          * Formater les dates
        - Utiliser le LLM pour les corrections complexes
        - Réessayer la validation
        """
        raise NotImplementedError("Agent 4 à implémenter par Sarra")


# Exemple de règles de validation
VALIDATION_RULES = {
    "serviceOrderItem": {
        "min_items": 1,
        "required_fields": ["id", "action", "service"],
        "action_values": ["add", "modify", "delete", "noChange"]
    },
    "service": {
        "required_fields": ["serviceSpecification"],
        "serviceSpecification_required": ["id"]
    },
    "dates": {
        "requestedStartDate_before_requestedCompletionDate": True
    }
}


if __name__ == "__main__":
    print("⚠️  Agent 4 - À implémenter par Sarra")
    print("\nFonctionnalités attendues:")
    print("- Validation Pydantic (types, champs obligatoires)")
    print("- Validation jsonschema (structure TMF641)")
    print("- Validation métier (cohérence des données)")
    print("- Boucle de correction automatique avec Agent 3")
    print("- Détection et correction des erreurs de type")
