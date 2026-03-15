import json
import os
import re
from typing import List, Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from schemas.intent import Intent
from schemas.tmf641 import ServiceOrder
from config import settings

class ServiceTranslatorAgent:
    """
    Agent 3: Traduit une intention structurée (Agent 1) et des services 
    sélectionnés (Agent 2) en un ordre de service TMF641 valide.
    """

    def __init__(self):
        # Initialisation du LLM via la configuration centralisée
        self.llm = ChatGroq(
            model_name=settings.llm_model,
            temperature=0,
            groq_api_key=settings.llm_api_key
        )

    def translate(self, intent: Intent, selected_services: List[Dict[str, Any]]) -> ServiceOrder:
        """
        Génère l'ordre de service TMF641 en utilisant le Few-Shot Prompting.
        """
        
        prompt = ChatPromptTemplate.from_template("""
        Tu es un expert en standards TM Forum (TMF641). 
        Ta mission est de générer un 'Service Order' JSON pour l'orchestrateur OpenSlice.

        --- CONTEXTE ---
        INTENTION (ID: {intent_id}): {intent_json}
        SERVICES SÉLECTIONNÉS: {services_json}

        --- RÈGLES DE MAPPING STRICTES ---
        1. Action: Toujours "add".
        2. ExternalId: Utilise l'ID de l'intention ({intent_id}).
        3. ServiceSpecification: Pour chaque service, utilise l'UUID 'id' fourni.
        4. Characteristics: Mappe les 'requirements' de l'intention.
        5. FORMAT DE VALEUR: Chaque caractéristique doit suivre ce format exact :
           {{"name": "Nom", "value": {{"value": "Valeur"}}}}

        --- EXEMPLE DE STRUCTURE ---
        {{
            "externalId": "ID_Exemple",
            "priority": "normal",
            "serviceOrderItem": [
                {{
                    "id": "1",
                    "action": "add",
                    "service": {{
                        "name": "Nom du Service",
                        "serviceSpecification": {{ "id": "uuid-service-1" }},
                        "serviceCharacteristic": [
                            {{ "name": "param", "value": {{ "value": "valeur" }} }}
                        ]
                    }}
                }}
            ]
        }}

        RETOURNE UNIQUEMENT LE JSON PUR. PAS DE TEXTE, PAS D'EXPLICATION.
        """)

        # Exécution de la chaîne
        chain = prompt | self.llm
        response = chain.invoke({
            "intent_id": intent.intent_id or "intent-001",
            "intent_json": intent.model_dump_json(),
            "services_json": json.dumps(selected_services)
        })

        content = response.content.strip()

        # --- SYSTÈME DE NETTOYAGE ROBUSTE ---
        # On cherche le premier '{' et le dernier '}' pour extraire le bloc JSON
        try:
            start_index = content.find("{")
            end_index = content.rfind("}") + 1
            if start_index == -1 or end_index == 0:
                raise ValueError("L'IA n'a pas retourné de bloc JSON valide (accolades manquantes).")
            
            clean_json_str = content[start_index:end_index]
            raw_json = json.loads(clean_json_str)
            
            # Conversion en objet Pydantic (vérifie la structure selon schemas/tmf641.py)
            return ServiceOrder(**raw_json)

        except json.JSONDecodeError as e:
            print(f"❌ Erreur de parsing JSON de l'Agent 3.")
            print(f"Contenu brut reçu de Llama : {content}")
            raise e
        except Exception as e:
            print(f"❌ Erreur imprévue lors de la traduction : {e}")
            raise e

if __name__ == "__main__":
    print("Agent 3 (Translator) chargé. Prêt pour intégration main.py.")