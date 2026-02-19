"""
Agent 1: L'Interpréteur (Intent Planner)

Rôle: Transformer toute requête en langage naturel en intentions structurées (JSON Agnostique)
Technologie: LLM (Llama 3.3 70B via API) + Pydantic
Responsable: Cyrine

Principe: Décomposition adaptative - L'agent analyse la complexité et crée 1, 2, 3+ sous-intentions selon les besoins réels
"""
import os
import json
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import ValidationError

from schemas.intent import Intent, SubIntent
from config import settings

from langchain_core.exceptions import OutputParserException


class IntentInterpreterAgent:
    """
    Agent 1: Interprète toute requête en langage naturel et la structure intelligemment
    
    Format de sortie: JSON agnostique avec décomposition adaptative (1 à N sous-intentions)
    
    L'agent identifie automatiquement les domaines selon le contexte et la complexité réelle:
    - Infrastructure réseau: cloud, transport, ran
    - Application web: frontend, backend, database
    - IoT: sensors, gateway, analytics
    - Etc.
    
    Exemple d'utilisation:
    ```python
    agent = IntentInterpreterAgent()
    
    # Exemple 1: Infrastructure réseau
    intent = agent.interpret("I need XR applications with 5G connectivity...")
    
    # Exemple 2: Application web
    intent = agent.interpret("Deploy an e-commerce platform with PostgreSQL...")
    
    # Exemple 3: IoT
    intent = agent.interpret("Smart city IoT platform with 1000 sensors...")
    
    print(intent.model_dump_json(indent=2))
    ```
    """
    
    def __init__(self, llm_model: Optional[str] = None, temperature: float = 0.0):
        """
        Initialise l'agent avec Llama 3.3 70B via API externe (Groq/Together/etc.)
        
        Args:
            llm_model: Nom du modèle Llama (par défaut depuis settings)
            temperature: Température pour la génération (0 = déterministe)
        """
        self.llm_model = llm_model or settings.llm_model
        self.temperature = temperature
        
        # Auto-détection de la base_url selon le provider
        provider_urls = {
            "groq": "https://api.groq.com/openai/v1",
            "together": "https://api.together.xyz/v1",
            "fireworks": "https://api.fireworks.ai/inference/v1",
            "replicate": "https://openai-proxy.replicate.com/v1"
        }
        
        base_url = settings.llm_base_url or provider_urls.get(settings.llm_provider.lower())
        
        if not base_url:
            raise ValueError(f"Provider '{settings.llm_provider}' non supporté. Options: {list(provider_urls.keys())}")
        
        # Initialiser Llama 3.3 70B via API
        self.llm = ChatOpenAI(
            base_url=base_url,
            api_key=settings.llm_api_key,
            model=self.llm_model,
            temperature=self.temperature
        )
        
        print(f"✅ Llama 3.3 70B initialisé via {settings.llm_provider.upper()}: {self.llm_model}")
        
        # Créer le prompt système
        self.prompt = self._create_prompt()
        
        # Parser de sortie JSON
        self.json_parser = JsonOutputParser(pydantic_object=Intent)
        
    def _create_prompt(self) -> ChatPromptTemplate:
        """Crée le prompt système pour l'extraction d'intentions"""
        
        system_message = """
You are a JSON generator. Output ONLY valid JSON, no explanations.

ABSOLUTE PROHIBITIONS (DO NOT VIOLATE):
- NEVER invent numeric values (latency in ms, storage in GB, CPU count, etc.) if user didn't specify numbers
- NEVER invent framework/technology names (React, FastAPI, MongoDB, etc.) if user didn't name them
- NEVER deduce impossible values like "0ms" latency or "infinite" bandwidth
- IGNORE non-technical context (bakery, croissants, morning traffic = IRRELEVANT, skip them)

CRITICAL RULES:
1. Extract ONLY information explicitly mentioned in the query
2. Vague terms like "fast", "scalable", "highly available" → use booleans (high_performance: true)
3. Location/city → use "location" field at Intent level (NOT a sub_intent)
4. QoS constraints ONLY if numeric values stated → use "qos" field at Intent level
5. Create 1 sub-intent for simple requests, multiple for complex ones

SUB-INTENT DOMAINS (Physical or logical components):
- Infrastructure: compute, storage, network, database, cache
- Application: frontend, backend, api, microservice
- Connectivity: 5G, fiber, vpn, cdn
- IoT: sensors, gateway, analytics
- AI/ML: training, inference, pipeline

COMPONENT ATTRIBUTES (Place these INSIDE the specific domain they apply to):
- Quality attributes: performance, scalability, availability (use booleans)

OUTPUT FORMAT:
{{"intent_id": "...", "type": "simple_service|composite_service", "sub_intents": [...], "location": "city|null", "qos": {{}}|null}}

❌ WRONG EXAMPLES:
"Let me analyze... {{json}}"
Query: "fast backend" → {{"framework": "FastAPI"}} ❌ (invented framework)
Query: "zero downtime" → {{"max_latency": "0ms"}} ❌ (impossible value)

✅ CORRECT EXAMPLES:
Query: "fast backend" → {{"high_performance": true}} ✅ (boolean for vague term)
Query: "zero downtime" → {{"high_availability": true}} ✅ (boolean)
Query: "backend with FastAPI" → {{"framework": "FastAPI"}} ✅ (explicitly stated)

EXAMPLES:

Example 1 - SIMPLE (1 sub-intent, no location):
Query: "I need a database"
{{
  "intent_id": "Database_001",
  "type": "simple_service",
  "sub_intents": [
    {{
      "domain": "database",
      "requirements": {{
        "type": "relational"
      }}
    }}
  ],
  "location": null,
  "qos": null
}}

Example 2 - COMPLEX with LOCATION and QoS (3 sub-intents):
Query: "XR applications with 5G connectivity in Nice"
{{
  "intent_id": "XR_Service_Nice_001",
  "type": "composite_service",
  "sub_intents": [
    {{
      "domain": "applications",
      "requirements": {{
        "type": "XR"
      }}
    }},
    {{
      "domain": "connectivity",
      "requirements": {{
        "type": "5G"
      }}
    }}
  ],
  "location": "Nice",
  "qos": null
}}

Example 3 - WITH specific values from query:
Query: "Deploy web app with PostgreSQL 32GB RAM, React frontend, FastAPI backend with 8 cores"
{{
  "intent_id": "WebApp_Deployment_001",
  "type": "composite_service",
  "sub_intents": [
    {{
      "domain": "database",
      "requirements": {{
        "type": "PostgreSQL",
        "ram": "32GB"
      }}
    }},
    {{
      "domain": "frontend",
      "requirements": {{
        "framework": "React"
      }}
    }},
    {{
      "domain": "backend",
      "requirements": {{
        "framework": "FastAPI",
        "cores": 8
      }}
    }}
  ],
  "location": null,
  "qos": null
}}

Example 4 - VAGUE terms (use booleans, NOT invented values):
Query: "Backend setup, super fast, highly scalable, zero downtime"
{{
  "intent_id": "Backend_Setup_001",
  "type": "simple_service",
  "sub_intents": [
    {{
      "domain": "backend",
      "requirements": {{
        "high_performance": true,
        "auto_scaling": true,
        "high_availability": true
      }}
    }}
  ],
  "location": null,
  "qos": null
}}

YOUR RESPONSE MUST:
- Start directly with {{
- End directly with }}
- Contain ZERO text outside the JSON object
- Extract ONLY values explicitly stated in query
- Use "location" field for cities/places (NOT as sub_intent domain)
- Use booleans for vague quality terms (fast → high_performance: true)

QUERY:"""

        user_message = "{user_query}\n\nJSON:"
        
        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", user_message)
        ])
    
    def interpret(self, user_query: str) -> Intent:
        """
        Interprète une requête utilisateur et retourne une intention structurée
        
        Args:
            user_query: Requête en langage naturel
            
        Returns:
            Intent: Intention structurée avec sous-intentions par domaine
            
        Raises:
            ValidationError: Si le JSON généré ne respecte pas le schéma
            ValueError: Si le LLM ne retourne pas un JSON valide
        """
        # Créer la chaîne LangChain
        chain = self.prompt | self.llm | self.json_parser
        
        # Invoquer le LLM
        try:
            result = chain.invoke({"user_query": user_query})
            
            # Valider avec Pydantic
            intent = Intent(**result)
            
            print(f"✅ Intention structurée créée: {intent.intent_id or intent.type}")
            print(f"   - {len(intent.sub_intents)} sous-intention(s) par domaine")
            for sub in intent.sub_intents:
                print(f"     • {sub.domain}: {len(sub.requirements)} exigence(s)")
            
            return intent
            
        except OutputParserException as e:
            # Attrape les erreurs de formatage JSON de LangChain
            raise ValueError(f"Le LLM n'a pas retourné un JSON valide: {e}")
        except ValidationError as e:
            # Attrape les erreurs de schéma de Pydantic
            raise ValidationError(f"Le JSON généré ne respecte pas le schéma d'intention: {e}")
        except Exception as e:
            # Sécurité globale
            raise RuntimeError(f"Une erreur inattendue s'est produite: {e}")
    
    def interpret_to_dict(self, user_query: str) -> dict:
        """Version qui retourne un dictionnaire au lieu d'un objet Pydantic"""
        intent = self.interpret(user_query)
        return intent.model_dump(exclude_none=True)
    
    def interpret_to_json(self, user_query: str) -> str:
        """Version qui retourne une chaîne JSON"""
        intent = self.interpret(user_query)
        return intent.model_dump_json(indent=2, exclude_none=True)


# Fonction utilitaire pour tests
def test_agent():
    """Teste l'agent avec l'exemple XR du contexte"""
    
    query = """I need a network composed of three XR applications: an augmented reality content server,
    a mixed reality collaboration platform, and a virtual reality simulation engine. Each application
    requires 4 vCPUs and 2 gigabytes (GB) of memory. All XR applications are interconnected
    using 5 GB/s links. The clients are connected through a 5G network located in the Nice area
    and tolerate a maximum latency of 5 ms."""
    
    try:
        agent = IntentInterpreterAgent()
        intent = agent.interpret(query)
        
        print("\n" + "="*80)
        print("INTENTION STRUCTURÉE GÉNÉRÉE (JSON Agnostique)")
        print("="*80)
        print(intent.model_dump_json(indent=2, exclude_none=True))
        print("="*80)
        
        return intent
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        raise


if __name__ == "__main__":
    # Test de l'agent
    test_agent()
