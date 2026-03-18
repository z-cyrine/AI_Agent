# Agentic AI Framework — Gestion de Services Réseau Basée sur les Intentions (IBN)

Framework multi-agents pour la gestion automatisée de services réseau selon le paradigme
Intent-Based Networking (IBN). L'utilisateur exprime un besoin en langage naturel et le
système orchestre un pipeline de 4 agents spécialisés pour produire et soumettre un ordre
de service conforme au standard TM Forum TMF641.

---

## Apercu general

Le pipeline transforme une requete en langage naturel en un ordre de service soumis a
OpenSlice en passant par quatre etapes sequentielles :

```
Requete utilisateur
      |
   Agent 1 — Interpretation : langage naturel -> intention JSON structuree
      |
   Agent 2 — Selection RAG  : intention -> services correspondants (ChromaDB)
      |
   Agent 3 — Traduction     : services + intention -> ordre TMF641
      |
   Agent 4 — Validation     : verification conformite ordre TMF641
      |
   Confirmation utilisateur
      |
   Soumission MCP -> OpenSlice
```

**Technologies principales**

| Composant         | Technologie                                      |
|-------------------|--------------------------------------------------|
| Orchestration     | LangGraph (StateGraph)                           |
| LLM               | Llama 3.3 70B via API Groq                       |
| Base vectorielle  | ChromaDB + sentence-transformers (MiniLM-L6-v2)  |
| Protocole reseau  | MCP (Model Context Protocol)     |
| API reseau cible  | OpenSlice TMF633 / TMF641 / TMF638               |
| Interface web     | Streamlit                                        |
| Validation schema | Pydantic v2                                      |

---

## Architecture

Voir [doc/architecture.md](doc/architecture.md) pour une description detaillee.

Le graphe LangGraph gere les cas suivants :
- Retry automatique de l'Agent 3 si la validation echoue (maximum 3 fois).
- Confirmation interactive de l'utilisateur avant soumission.
- Possibilite pour l'utilisateur de reformuler sa requete (maximum 3 fois).

---

## Installation

Voir [doc/installation.md](doc/installation.md) pour le guide complet.

Etapes resumees :

```bash
# 1. Cloner / ouvrir le repertoire
cd ai_agent

# 2. Creer et activer l'environnement virtuel
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS

# 3. Installer les dependances
pip install -r requirements.txt

# 4. Creer le fichier de configuration
copy .env.example .env          # Windows
# cp .env.example .env          # Linux / macOS
# Editer .env avec votre cle API Groq
```

---

## Configuration

Voir [doc/configuration.md](doc/configuration.md) pour la reference complete.

---

## Demarrage rapide

### Interface graphique (Streamlit)

```bash
streamlit run app.py
```

Ouvre l'interface dans le navigateur. Saisir une intention en langage naturel et cliquer
sur "Lancer".

### En ligne de commande

```bash
python main.py --query "I need a 5G network with XR applications in Nice"
```

Option disponible : `--verbose` pour afficher les details de chaque etape.

### Avant la premiere utilisation : alimenter ChromaDB

Le catalogue de services doit etre indexe dans ChromaDB avant de lancer le pipeline.
Deux approches sont possibles :

**Mode mock (sans OpenSlice)** — utiliser un catalogue local pre-defini :

```bash
python scripts/ingest_catalog.py --mock
```

**Mode reel (avec OpenSlice)** — recuperer le catalogue depuis l'API TMF633 :

```bash
python scripts/populate_openslice.py   # cree les services dans OpenSlice
python scripts/ingest_catalog.py       # indexe dans ChromaDB
```

---

## Utilisation

### Exemple de requete

```
I need a network composed of three XR applications: an augmented reality content server,
a mixed reality collaboration platform, and a virtual reality simulation engine.
Each application requires 4 vCPUs and 2 GB of memory.
The clients are connected through a 5G network located in the Nice area
and tolerate a maximum latency of 5 ms.
```

### Interface Streamlit — onglets

| Onglet           | Contenu                                                |
|------------------|--------------------------------------------------------|
| Pipeline         | Progression en temps reel de chaque agent              |
| Sorties JSON     | JSON brut produit par chaque agent                     |
| Ordres OpenSlice | Liste des ordres soumis (via l'API TMF641)             |

---

## Structure du projet

```
ai_agent/
|
|-- app.py                  Interface Streamlit (pipeline interactif)
|-- main.py                 Point d'entree CLI
|-- orchestrator.py         Graphe LangGraph (orchestration des 4 agents)
|-- config.py               Configuration centralisee
|-- requirements.txt        Dependances Python
|
|-- agents/
|   |-- agent1_interpreter.py   Agent 1 : interpretation NLP -> JSON
|   |-- agent2_selector.py      Agent 2 : recherche semantique RAG
|   |-- agent3_translator.py    Agent 3 : generation ordre TMF641
|   |-- agent4_validator.py     Agent 4 : validation Pydantic + MCP
|
|-- mcp/
|   |-- mcp_client.py           Client MCP (interface vers le serveur)
|   |-- openslice_mcp_server.py Serveur MCP (outils et ressources exposees)
|   |-- openslice_client.py     Client HTTP OpenSlice (TMF633/641/638)
|
|-- schemas/
|   |-- intent.py               Schema Pydantic de l'intention (Intent, SubIntent)
|   |-- tmf641.py               Schemas Pydantic TMF641 (ServiceOrder, etc.)
|
|-- scripts/
|   |-- ingest_catalog.py       Ingestion du catalogue dans ChromaDB
|   |-- populate_openslice.py   Creation de services dans OpenSlice
|   |-- list_services.py        Consultation du catalogue OpenSlice
|   |-- check_orders.py         Consultation des ordres soumis
|   |-- cleanup_svr_order.py    Suppression d'ordres de test
|   |-- test_mcp.py             Test unitaire du serveur MCP
|   |-- test_pipeline_mcp.py    Test end-to-end du pipeline
|
|-- data/
|   |-- chroma_db/              Base vectorielle ChromaDB (persistee)
|
|-- doc/                    Documentation complementaire
```

---

## Documentation complementaire

| Fichier                          | Contenu                                       |
|----------------------------------|-----------------------------------------------|
| [doc/architecture.md](doc/architecture.md)       | Graphe LangGraph, flux de donnees, etats      |
| [doc/installation.md](doc/installation.md)       | Guide d'installation detaille                 |
| [doc/configuration.md](doc/configuration.md)     | Reference de toutes les variables de config   |
| [doc/agents.md](doc/agents.md)                   | Description detaillee de chaque agent         |
| [doc/mcp.md](doc/mcp.md)                         | Couche MCP : outils, ressources, protocole    |
| [doc/scripts.md](doc/scripts.md)                 | Reference des scripts utilitaires             |
