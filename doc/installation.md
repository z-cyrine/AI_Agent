# Guide d'installation

## Prerequis

- Python 3.10 ou superieur
- pip
- Une cle API Groq (gratuite sur console.groq.com)
- OpenSlice (optionnel — non requis en mode mock)

---

## 1. Preparer l'environnement Python

```bash
# Se placer dans le repertoire du projet
cd ai_agent

# Creer l'environnement virtuel
python -m venv .venv

# Activer l'environnement virtuel
# Windows PowerShell :
.venv\Scripts\Activate.ps1
# Windows cmd :
.venv\Scripts\activate.bat
# Linux / macOS :
source .venv/bin/activate
```

Installer les dependances :

```bash
pip install -r requirements.txt
```

Les paquets principaux installes :

| Paquet                  | Version minimale | Role                                          |
|-------------------------|------------------|-----------------------------------------------|
| langgraph               | 0.2.0            | Orchestration des agents (graphe d'etat)      |
| langchain               | 0.3.0            | Chaines LLM                                   |
| langchain-openai        | 0.2.0            | Client Llama 3.3 70B via API Groq             |
| langchain-groq          | 0.1.0            | Client Groq natif (Agent 3)                   |
| pydantic                | 2.0.0            | Validation des schemas de donnees             |
| pydantic-settings       | 2.0.0            | Gestion de la configuration                   |
| chromadb                | 0.4.0            | Base vectorielle pour la recherche RAG        |
| sentence-transformers   | 2.2.0            | Modele d'embeddings (all-MiniLM-L6-v2)        |
| httpx                   | 0.24.0            | Client HTTP pour l'API OpenSlice              |
| streamlit               | (derniere)       | Interface web                                 |

---

## 2. Configurer les variables d'environnement

Creer un fichier `.env` a la racine du projet en copiant le modele ci-dessous :

```dotenv
# ============================================================
# LLM 
# ============================================================
LLM_PROVIDER=groq
LLM_API_KEY=
LLM_MODEL=llama-3.3-70b-versatile
LLM_TEMPERATURE=0.0

# ============================================================
# OpenSlice
# ============================================================
OPENSLICE_BASE_URL=http://localhost:13082
OPENSLICE_AUTH_URL=http://localhost:8080
OPENSLICE_USERNAME=admin
OPENSLICE_PASSWORD=admin
OPENSLICE_CLIENT_ID=osapiWebClientId
OPENSLICE_MOCK_MODE=true

# ============================================================
# ChromaDB
# ============================================================
CHROMA_PERSIST_DIR=./data/chroma_db
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

Pour obtenir une cle API Groq :
1. Aller sur console.groq.com
2. Creer un compte et generer une cle API
3. Copier la cle dans `LLM_API_KEY`

---

## 3. Alimenter la base vectorielle ChromaDB

ChromaDB doit etre alimentee avec le catalogue de services **avant** la premiere execution
du pipeline. Sans cette etape, l'Agent 2 ne trouvera aucun service.

### En mode mock

Le script recupere le catalogue depuis OpenSlice en mode mock, ce qui retourne une liste
vide. Il faut donc d'abord importer des services directement dans ChromaDB.

```bash
python scripts/ingest_catalog.py --mock
```

### En mode reel (avec OpenSlice)

```bash
# Etape 1 : creer les services dans OpenSlice (TMF633)
python scripts/populate_openslice.py

# Etape 2 : indexer le catalogue dans ChromaDB
python scripts/ingest_catalog.py
```

Verifier que des services sont bien presents :

```bash
python scripts/list_services.py
```

---

## 4. Lancer l'application

### Interface Streamlit

```bash
streamlit run app.py
```

L'interface s'ouvre automatiquement dans le navigateur (par defaut sur http://localhost:8501).

### En ligne de commande

```bash
python main.py --query "I need a 5G network with XR applications in Nice"
python main.py --query "Deploy a PostgreSQL database with 32GB RAM" --verbose
```