"""
Agent 1: L'Interpréteur (Intent Planner)

Rôle: Transformer toute requête en langage naturel en intentions structurées (JSON Agnostique)
Technologie: LLM (GPT-4o/Claude 3.5) + Pydantic
Responsable: Cyrine

Principe: Décomposition adaptative - L'agent analyse la complexité et crée 1, 2, 3+ sous-intentions selon les besoins réels
"""
import os
import json
from typing import Optional
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import ValidationError

from schemas.intent import Intent, SubIntent
from config import settings


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
        Initialise l'agent avec Llama 3.3 70B via Ollama (GRATUIT, LOCAL)
        
        Args:
            llm_model: Nom du modèle Llama (par défaut "llama3.3:70b")
            temperature: Température pour la génération (0 = déterministe)
        """
        self.llm_model = llm_model or settings.llm_model
        self.temperature = temperature
        
        # Initialiser Llama 3.2 via Ollama (gratuit, local)
        self.llm = ChatOllama(
            model=self.llm_model,
            temperature=self.temperature,
            base_url=settings.ollama_base_url
        )
        
        print(f"✅ Llama initialisé: {self.llm_model} @ {settings.ollama_base_url}")
        
        # Créer le prompt système
        self.prompt = self._create_prompt()
        
        # Parser de sortie JSON
        self.json_parser = JsonOutputParser(pydantic_object=Intent)
        
    def _create_prompt(self) -> ChatPromptTemplate:
        """Crée le prompt système pour l'extraction d'intentions"""
        
        system_message = """
Tu es un expert en analyse d'intentions. Ton rôle est d'analyser des requêtes utilisateur en langage naturel 
et de les structurer en intentions avec leurs sous-intentions.

PRINCIPE FONDAMENTAL:
- Analyse la COMPLEXITÉ réelle de la requête
- Décompose en sous-intentions SEULEMENT si c'est pertinent
- Une intention simple = 1 sous-intention
- Une intention complexe = plusieurs sous-intentions (2, 3, 4+)

RÈGLES D'EXTRACTION:

1. **Identifier le type de service global**
   - Déterminer s'il s'agit d'un service composite (multiple aspects) ou simple (un seul aspect)
   - Générer un intent_id unique et descriptif

2. **Décomposer intelligemment en sous-intentions**
   
   POUR CHAQUE ASPECT/DOMAINE DISTINCT de la requête :
   - Si la requête mentionne UN SEUL aspect → créer 1 sous-intention
   - Si la requête mentionne PLUSIEURS aspects → créer autant de sous-intentions que nécessaire
   
   Chaque sous-intention contient:
   - domain: nom du domaine/aspect (ex: "compute", "storage", "network", "database", etc.)
   - requirements: dictionnaire des exigences spécifiques
   
   Exemples de domaines (adaptez selon le contexte):
   - Infrastructure: "compute", "storage", "network", "edge", "cloud"
   - Application: "frontend", "backend", "database", "cache", "api"
   - Réseau: "connectivity", "bandwidth", "ran", "transport", "security"
   - IoT: "sensors", "gateway", "processing", "analytics"
   - IA/ML: "training", "inference", "data_pipeline"
   - Autre: tout domaine pertinent selon la requête

3. **Extraire les contraintes globales**
   - Identifier les contraintes transversales (localisation, latence, disponibilité, etc.)
   - Les placer dans "qos" si elles s'appliquent à l'ensemble du service

DIRECTIVE IMPORTANTE:
- NE PAS inventer des sous-intentions si elles ne sont pas dans la requête
- NE PAS décomposer artificiellement une intention simple
- Rester fidèle à ce que demande l'utilisateur

CONTRAINTES TECHNIQUES STRICTES:
- Retourne UNIQUEMENT un objet JSON valide, RIEN d'autre
- PAS de texte avant ou après le JSON
- PAS d'explication, PAS de commentaire
- JUSTE le JSON brut
- Utilise des types appropriés: integer pour nombres, string pour mesures avec unités
- Sois créatif dans le choix des domaines selon le contexte réel

FORMAT DE SORTIE OBLIGATOIRE:
{{"intent_id": "...", "type": "...", "sub_intents": [...]}}

EXEMPLES:

Exemple 1 - Intention SIMPLE (1 sous-intention):
Requête: "I need a PostgreSQL database with 100GB storage"
{{
  "intent_id": "Database_PostgreSQL_001",
  "type": "simple_service",
  "sub_intents": [
    {{
      "domain": "database",
      "requirements": {{
        "type": "PostgreSQL",
        "storage": "100GB",
        "backup": "daily"
      }}
    }}
  ]
}}

Exemple 2 - Intention MOYENNE (2 sous-intentions):
Requête: "Deploy IoT sensors with analytics dashboard"
{{
  "intent_id": "IoT_SmartCity_001",
  "type": "composite_service",
  "sub_intents": [
    {{
      "domain": "sensors",
      "requirements": {{
        "count": 1000,
        "protocol": "MQTT"
      }}
    }},
    {{
      "domain": "analytics",
      "requirements": {{
        "processing": "real-time",
        "dashboard": true
      }}
    }}
  ]
}}

Exemple 3 - Intention COMPLEXE (3 sous-intentions):
Requête: "XR applications with computing resources, interconnected via high-speed links, and 5G connectivity"
{{
  "intent_id": "XR_Service_Nice_001",
  "type": "composite_service",
  "sub_intents": [
    {{
      "domain": "compute",
      "requirements": {{
        "cpu": 4,
        "ram": "2GB",
        "applications": ["AR_server", "VR_engine"]
      }}
    }},
    {{
      "domain": "network",
      "requirements": {{
        "bandwidth": "5Gbps",
        "topology": "mesh"
      }}
    }},
    {{
      "domain": "connectivity",
      "requirements": {{
        "type": "5G",
        "max_latency": "5ms"
      }}
    }}
  ],
  "qos": {{"max_latency": "5ms"}}
}}

Maintenant, analyse la requête utilisateur suivante et décompose-la selon SA VRAIE COMPLEXITÉ (1, 2, 3+ sous-intentions):"""

        user_message = "{user_query}"
        
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
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Le LLM n'a pas retourné un JSON valide: {e}")
        except ValidationError as e:
            raise ValidationError(f"Le JSON généré ne respecte pas le schéma d'intention: {e}")
    
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
