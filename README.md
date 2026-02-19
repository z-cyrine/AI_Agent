# Agentic AI Framework for Intent-Based Network Service Management

## Description
Solution générique de gestion de services à base d'intentions. Décompose toute intention complexe en sous-intentions par domaine/aspect, puis génère des ordres de service TMF641 pour OpenSlice.

## Architecture Multi-Agents

### Agent 1: L'Interpréteur (Intent Planner)
- **Rôle**: Transforme le langage naturel en intentions structurées (JSON agnostique)
- **Technologie**: Llama 3.3 8B (via Ollama) + Pydantic
- **Décomposition**: Adaptative selon complexité (1 sous-intention si simple, 2-3+ si complexe)
- **Flexibilité**: Fonctionne pour tout type de service (réseau, web, IoT, IA, etc.)
- **LLM**: Llama 3.3 8B - **GRATUIT, LOCAL, OFFLINE** (8 GB RAM)
- **Responsable**: Cyrine

### Agent 2: Le Sélecteur (Service Broker)
- **Rôle**: Sélection sémantique de services via RAG
- **Technologie**: ChromaDB + sentence-transformers
- **Entrée**: Intention structurée
- **Sortie**: UUID de ServiceSpecification OpenSlice
- **Responsable**: Cyrine

### Agent 3: Le Traducteur (TMF641 Mapper)
- **Rôle**: Génération d'ordres de service TMF641
- **Technologie**: Few-Shot Prompting
- **Entrée**: UUID + Contraintes
- **Sortie**: ServiceOrder TMF641 (JSON)
- **Responsable**: Sarra

### Agent 4: Le Validateur (Quality Assurance)
- **Rôle**: Validation JSON TMF641
- **Technologie**: jsonschema + Pydantic
- **Responsable**: Sarra

## Installation

```bash
# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Installer Ollama et télécharger Llama 3.3 8B
# Voir INSTALLATION_LLAMA.md pour les instructions détaillées
ollama pull llama3.3:8b

# Configurer les variables d'environnement
cp .env.example .env
# .env contient déjà: LLM_MODEL=llama3.3:8b (suffisant pour extraction d'intention)
```

## 🤖 LLM: Llama 3.3 8B

**Pourquoi Llama 3.3 8B (et PAS Code Llama) ?**

✅ **Llama 3.3 8B** - **MEILLEUR CHOIX** pour extraction d'intention:
- Excellent pour compréhension NL + structured output
- **Gratuit, local, offline** (aucun coût API)
- Privacy: données restent sur votre machine
- **Léger**: Seulement 8 GB RAM requis
- Qualité largement suffisante pour structured output

❌ **Code Llama** - PAS adapté:
- Spécialisé pour **générer** du code (autocomplétion, debugging)
- Moins bon pour **comprendre** du texte NL et extraire des intentions

📝 **Note**: Si vous avez 48+ GB RAM, vous pouvez utiliser `llama3.3:70b` pour une qualité légèrement supérieure.

📖 **Guide complet**: Voir [INSTALLATION_LLAMA.md](INSTALLATION_LLAMA.md)

**Guide détaillé**: Voir [LLAMA_GUIDE.md](LLAMA_GUIDE.md)

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

# 3. Test des agents individuels
python -m agents.agent1_interpreter
python -m agents.agent2_selector
```

## Structure du Projet

```
ai_agent/
├── agents/
│   ├── agent1_interpreter.py  # Agent 1 (Cyrine)
│   ├── agent2_selector.py     # Agent 2 (Cyrine)
│   ├── agent3_translator.py   # Agent 3 (Sarra)
│   └── agent4_validator.py    # Agent 4 (Sarra)
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
