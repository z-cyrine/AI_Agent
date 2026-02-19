"""
Agent 3: Le Traducteur (TMF641 Mapper)

Rôle: Génération d'ordres de service TMF641 à partir d'intentions structurées
Technologie: Few-Shot Prompting + LLM
Responsable: Sarra

TODO: À implémenter par Sarra
"""
from typing import List, Dict, Any
from schemas.intent import Intent
class ServiceTranslatorAgent:
    """
    Agent 3: Traduit une intention structurée (JSON agnostique) en ordre de service TMF641
    
    Exemple d'utilisation:
    ```python
    agent = ServiceTranslatorAgent()
    intent = Intent(...)
    selected_services = [{"id": "uuid-1", "name": "XR Service", ...}]
    
    service_order = agent.translate(intent, selected_services)
    print(service_order.model_dump_json())
    ```
    """
    
    def __init__(self):
        """
        Initialise l'agent traducteur
        
        TODO Sarra:
        - Initialiser le LLM (GPT-4o ou Claude 3.5)
        - Créer les prompts Few-Shot avec des exemples Intent → TMF641
        - Préparer les templates de mapping
        """
        pass
    
    def translate(
        self,
        intent: Intent,
        selected_services: List[Dict[str, Any]]
    ) -> ServiceOrder:
        """
        Traduit une intention et des services sélectionnés en ordre TMF641
        
        Args:
            intent: Intention structurée (JSON agnostique avec sub_intents par domaine)
            selected_services: Services sélectionnés par l'Agent 2
            
        Returns:
            ServiceOrder: Ordre de service TMF641 complet
            
        TODO Sarra:
        1. Créer le prompt avec:
           - L'intention structurée (en JSON)
           - Les services sélectionnés avec leurs UUIDs
           - Des exemples de ServiceOrder TMF641 valides
        
        2. Invoquer le LLM avec Few-Shot Prompting
        
        3. Parser la réponse JSON
        
        4. Créer les ServiceOrderItem pour chaque service
        
        5. Mapper les caractéristiques de l'intention vers ServiceCharacteristic
        
        6. Retourner un objet ServiceOrder Pydantic
        """
        raise NotImplementedError("Agent 3 à implémenter par Sarra")


# Exemple de structure attendue pour Few-Shot Prompting
EXAMPLE_FEW_SHOT_PROMPT = """
Tu es un expert en standards TMForum. Ton rôle est de transformer une intention structurée
(JSON agnostique avec décomposition par domaine) et des services sélectionnés en un ordre de service TMF641 valide.

EXEMPLE 1:
----------
Intent structuré:
{
  "name": "IoT Platform Deployment",
  "description": "Deploy IoT platform for smart city",
  "intentExpectation": [
    {"expectationType": "delivery", "name": "Platform", "targetValue": "IoT Platform"}
  ]
}

Services sélectionnés:
[
  {"id": "iot-platform-uuid-001", "name": "IoT Platform Service"}
]

Service Order TMF641:
{
  "externalId": "intent-iot-001",
  "description": "IoT Platform deployment based on user intent",
  "priority": "normal",
  "serviceOrderItem": [
    {
      "id": "1",
      "action": "add",
      "service": {
        "name": "IoT Platform Service",
        "serviceSpecification": {
          "id": "iot-platform-uuid-001"
        }
      }
    }
  ]
}

EXEMPLE 2:
----------
[Ajouter d'autres exemples réels découverts lors de l'exploration OpenSlice]

MAINTENANT, traduis cette intention:
Intent structuré: {intent_json}
Services sélectionnés: {services_json}

Retourne UNIQUEMENT le JSON du ServiceOrder TMF641, sans commentaire.
"""


if __name__ == "__main__":
    print("⚠️  Agent 3 - À implémenter par Sarra")
    print("\nFonctionnalités attendues:")
    print("- Mapping Intent structuré (JSON agnostique) → ServiceOrder TMF641")
    print("- Utilisation de Few-Shot Prompting")
    print("- Génération de ServiceOrderItem pour chaque service")
    print("- Mapping des caractéristiques")
