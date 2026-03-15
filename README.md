# Agentic AI Framework for Intent-Based Network Service Management

## Description
Solution générique de gestion de services à base d'intentions. Décompose toute intention complexe en sous-intentions par domaine/aspect, puis génère des ordres de service TMF641 pour OpenSlice.

## Architecture Multi-Agents

### Agent 1: L'Interpréteur (Intent Planner)
- **Rôle**: Transforme le langage naturel en intentions structurées (JSON agnostique)
- **Technologie**: `langchain-openai` (ChatOpenAI) → API Groq + Pydantic
- **Modèle**: `llama-3.3-70b-versatile` via `https://api.groq.com/openai/v1`
- **Décomposition**: Adaptative selon complexité (1 sous-intention si simple, 2-3+ si complexe)
- **Flexibilité**: Fonctionne pour tout type de service (réseau, web, IoT, IA, etc.)

### Agent 2: Le Sélecteur (Service Broker)
- **Rôle**: Sélection sémantique de services via RAG
- **Technologie**: `ChromaDB` + `sentence-transformers` (all-MiniLM-L6-v2)
- **Entrée**: Intention structurée (sous-intentions avec description)
- **Sortie**: UUID de ServiceSpecification OpenSlice

### Agent 3: Le Traducteur (TMF641 Mapper)
- **Rôle**: Génération d'ordres de service TMF641
- **Technologie**: `langchain-groq` (ChatGroq) — Few-Shot Prompting
- **Modèle**: `llama-3.3-70b-versatile` via API Groq
- **Entrée**: Intention structurée + services sélectionnés (UUID + métadonnées)
- **Sortie**: ServiceOrder TMF641 (JSON)

### Agent 4: Le Validateur (Quality Assurance)
- **Rôle**: Validation de l'ordre de service TMF641 avant soumission
- **Technologie**: `Pydantic` + règles métier OpenSlice
- **Vérifications**: Présence des items, validité des UUIDs de ServiceSpecification

## Installation

```bash
# 1. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env et renseigner votre clé API Groq
```

## 🔑 Configuration LLM — API Groq

Les agents 1 et 3 utilisent **Llama 3.3 70B** via l'API Groq (gratuite).

### Étapes

1. **Créer un compte** sur [console.groq.com](https://console.groq.com)
2. **Générer une clé API** dans la section "API Keys"
3. **Configurer `.env`** :
   ```env
   LLM_PROVIDER=groq
   LLM_API_KEY=gsk_votre_clé_ici
   LLM_MODEL=llama-3.3-70b-versatile
   ```

📖 **Guide détaillé** : Voir [API_SETUP.md](API_SETUP.md)

## Utilisation

```bash
# 1. Ingestion du catalogue OpenSlice dans ChromaDB
python scripts/ingest_catalog.py

# 2. Lancer le pipeline complet avec une requête

# Infrastructure réseau 5G
python main.py --query "I need XR applications with 5G connectivity in Nice"

# Application web
python main.py --query "Deploy an e-commerce platform with React frontend and PostgreSQL database"

# Plateforme IoT
python main.py --query "Smart city IoT platform with 1000 sensors and real-time analytics"

# Mode interactif
python main.py --interactive

# 3. Tester les agents individuellement
python -m agents.agent1_interpreter
python -m agents.agent2_selector
```

## Structure du Projet

```
ai_agent/
├── agents/
│   ├── agent1_interpreter.py  # Agent 1 — LangChain + Groq API
│   ├── agent2_selector.py     # Agent 2 — ChromaDB + sentence-transformers
│   ├── agent3_translator.py   # Agent 3 — LangChain Groq + Few-Shot
│   └── agent4_validator.py    # Agent 4 — Pydantic QA
├── schemas/
│   ├── intent.py              # Schémas Intent (Pydantic)
│   └── tmf641.py              # Schémas ServiceOrder TMF641 (Pydantic)
├── mcp/
│   └── openslice_client.py    # Client HTTP OpenSlice
├── scripts/
│   └── ingest_catalog.py      # Ingestion catalogue → ChromaDB
├── tests/
│   └── test_agent1.py         # Tests Agent 1
├── orchestrator.py            # Orchestration LangGraph
├── config.py                  # Configuration centralisée (pydantic-settings)
├── main.py                    # Point d'entrée
└── requirements.txt
```

## Pipeline

```
Langage Naturel
     │
     ▼
Agent 1 — Intent Planner     (ChatOpenAI → Groq API → llama-3.3-70b)
     │ Intention structurée (JSON)
     ▼
Agent 2 — Service Broker     (ChromaDB + sentence-transformers)
     │ UUID(s) ServiceSpecification
     ▼
Agent 3 — TMF641 Mapper      (ChatGroq → Groq API → llama-3.3-70b)
     │ ServiceOrder TMF641 (JSON)
     ▼
Agent 4 — Quality Assurance  (Pydantic)
     │ Ordre validé
     ▼
OpenSlice
```

## Stack Technique

| Composant | Technologie |
|---|---|
| LLM Agent 1 | `langchain-openai` → API Groq (`llama-3.3-70b-versatile`) |
| LLM Agent 3 | `langchain-groq` → API Groq (`llama-3.3-70b-versatile`) |
| Vector DB | `ChromaDB` |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| Validation | `Pydantic v2` + `pydantic-settings` |
| Orchestration | `LangGraph` |
| Protocole MCP | `fastmcp` |
| Standards | TMF641 (Service Ordering), TMF633 (Service Catalog) |

## Références
- [TMF641 — Service Ordering Management API](https://www.tmforum.org/resources/standard/tmf641-service-ordering-management-api-user-guide-v4-0/)
- [TMF633 — Service Catalog Management API](https://www.tmforum.org/resources/standard/tmf633-service-catalog-management-api-user-guide-v4-0/)
- [Groq Console](https://console.groq.com)
- [OpenSlice](https://openslice.io)
