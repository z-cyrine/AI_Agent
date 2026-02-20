# Agentic AI Framework for Intent-Based Network Service Management

## Description
Solution générique de gestion de services à base d'intentions. Décompose toute intention complexe en sous-intentions par domaine/aspect, puis génère des ordres de service TMF641 pour OpenSlice.

## Architecture Multi-Agents

### Agent 1: L'Interpréteur (Intent Planner)
- **Rôle**: Transforme le langage naturel en intentions structurées (JSON agnostique)
- **Technologie**: Llama 3.3 70B (via API Groq) + Pydantic
- **Décomposition**: Adaptative selon complexité (1 sous-intention si simple, 2-3+ si complexe)
- **Flexibilité**: Fonctionne pour tout type de service (réseau, web, IoT, IA, etc.)

### Agent 2: Le Sélecteur (Service Broker)
- **Rôle**: Sélection sémantique de services via RAG
- **Technologie**: ChromaDB + sentence-transformers
- **Entrée**: Intention structurée
- **Sortie**: UUID de ServiceSpecification OpenSlice

### Agent 3: Le Traducteur (TMF641 Mapper)
- **Rôle**: Génération d'ordres de service TMF641
- **Technologie**: Few-Shot Prompting
- **Entrée**: UUID + Contraintes
- **Sortie**: ServiceOrder TMF641 (JSON)

### Agent 4: Le Validateur (Quality Assurance)
- **Rôle**: Validation JSON TMF641
- **Technologie**: jsonschema + Pydantic

## Installation

```bash
# 1. Créer un environnement virtuel
python -m venv venv
venv\Scripts\activate  # Windows

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer l'API
cp .env.example .env
# Éditer .env et ajouter votre clé API Groq
```

## 🤖 Configuration LLM

**Llama 3.3 70B via API (Groq recommandé)**

1. **Créer un compte gratuit**: [console.groq.com](https://console.groq.com)
2. **Générer une clé API** dans "API Keys"
3. **Configurer `.env`**:
   ```env
   LLM_PROVIDER=groq
   LLM_API_KEY=gsk_votre_clé_ici
   LLM_MODEL=llama-3.3-70b-versatile
   ```

📖 **Guide complet**: Voir [API_SETUP.md](API_SETUP.md) pour plus de détails

## Utilisation

```bash
# 1. Ingestion du catalogue OpenSlice
python scripts/ingest_catalog.py

# 2. Exemples d'exécution avec différents types de requêtes

# Infrastructure réseau
python main.py --query "I need XR applications with 5G connectivity in Nice"

# Application web
python main.py --query "Deploy an e-commerce platform with React frontend and PostgreSQL database"

# Plateforme IoT
python main.py --query "Smart city IoT platform with 1000 sensors and real-time analytics"

# Mode interactif (pour tester vos propres requêtes)
python main.py --interactive

# 3. Test rapide Agent 1 (mode interactif)
python test_quick.py

# 4. Test Agent 2 seul
python -m agents.agent2_selector
```

## Structure du Projet

```
ai_agent/
├── agents/
│   ├── agent1_interpreter.py  # Agent 1
│   ├── agent2_selector.py     # Agent 2
│   ├── agent3_translator.py   # Agent 3
│   └── agent4_validator.py    # Agent 4
├── schemas/
│   ├── intent.py              # Schémas Intent (JSON Agnostique)
│   └── tmf641.py              # Schémas Service Order TMF641
├── mcp/
│   └── openslice_server.py    # Serveur MCP
├── scripts/
│   └── ingest_catalog.py      # Ingestion catalogue
├── orchestrator.py            # LangGraph orchestration
├── config.py                  # Configuration
└── main.py                    # Point d'entrée
```

## Pipeline

```
Langage Naturel → Agent 1 (Structuration adaptative) → Agent 2 (UUID) → Agent 3 (TMF641) → Agent 4 (Validation) → OpenSlice
```

## Références
- TMF641: Service Ordering Management API
- TMF633: Service Catalog Management API
- Format d'intention: JSON agnostique avec décomposition par domaine/aspect
