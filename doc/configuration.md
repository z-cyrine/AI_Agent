# Reference de configuration

La configuration est geree par la classe `Settings` dans `config.py`, implementee avec
`pydantic-settings`. Les valeurs sont lues depuis le fichier `.env` a la racine du projet.

---

## Variables de configuration

### LLM — Modele de langage

| Variable          | Type   | Defaut                      | Description                                           |
|-------------------|--------|-----------------------------|-------------------------------------------------------|
| `LLM_PROVIDER`    | str    | `groq`                      | Fournisseur LLM     |
| `LLM_API_KEY`     | str    | *obligatoire*               | Cle API Groq                                          |
| `LLM_BASE_URL`    | str    | auto-detecte selon provider | URL de base de l'API  |
| `LLM_MODEL`       | str    | `llama-3.3-70b-versatile`   | Nom du modele Groq                                    |
| `LLM_TEMPERATURE` | float  | `0.0`                       | Temperature de generation (0 = deterministe)          |

Le LLM est utilise par :
- Agent 1 (`langchain-openai`) pour l'interpretation de l'intention
- Agent 3 (`langchain-groq`) pour la generation de l'ordre TMF641

### OpenSlice — API reseau cible

| Variable                  | Type   | Defaut                    | Description                                              |
|---------------------------|--------|---------------------------|----------------------------------------------------------|
| `OPENSLICE_BASE_URL`      | str    | `http://localhost:13082`  | URL de l'API OpenSlice (port OSSCAPI)                    |
| `OPENSLICE_AUTH_URL`      | str    | `http://localhost:8080`   | URL de Keycloak (authentification OAuth2)                |
| `OPENSLICE_USERNAME`      | str    | `admin`                   | Nom d'utilisateur Keycloak                               |
| `OPENSLICE_PASSWORD`      | str    | `admin`                   | Mot de passe Keycloak                                    |
| `OPENSLICE_CLIENT_ID`     | str    | `osapiWebClientId`        | Client ID OAuth2 Keycloak                                |
| `OPENSLICE_MOCK_MODE`     | bool   | `false`                   | Si `true`, simule OpenSlice localement sans connexion    |

### ChromaDB — Base vectorielle

| Variable            | Type   | Defaut                              | Description                                     |
|---------------------|--------|-------------------------------------|-------------------------------------------------|
| `CHROMA_PERSIST_DIR`| str    | `./data/chroma_db`                  | Repertoire de persistance de ChromaDB           |
| `EMBEDDING_MODEL`   | str    | `sentence-transformers/all-MiniLM-L6-v2` | Modele d'embeddings utilise par Agent 2    |

Le modele d'embeddings est telecharge automatiquement depuis Hugging Face lors de la
premiere execution.

### Application

| Variable      | Type   | Defaut  | Description                                       |
|---------------|--------|---------|---------------------------------------------------|
| `LOG_LEVEL`   | str    | `INFO`  | Niveau de journalisation Python                   |
| `MAX_RETRIES` | int    | `3`     | Nombre maximal de retries de validation (Agent 4) |

---

## Fichier .env complet (modele)

```dotenv
# LLM
LLM_PROVIDER=groq
LLM_API_KEY=
LLM_MODEL=llama-3.3-70b-versatile
LLM_TEMPERATURE=0.0

# OpenSlice
OPENSLICE_BASE_URL=http://localhost:13082
OPENSLICE_AUTH_URL=http://localhost:8080
OPENSLICE_USERNAME=admin
OPENSLICE_PASSWORD=admin
OPENSLICE_CLIENT_ID=osapiWebClientId
OPENSLICE_MOCK_MODE=true

# ChromaDB
CHROMA_PERSIST_DIR=./data/chroma_db
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Application
LOG_LEVEL=INFO
MAX_RETRIES=3
```

---

## Classe Settings (config.py)

```python
class Settings(BaseSettings):
    # LLM
    llm_provider: str = "groq"
    llm_api_key: str                          # obligatoire
    llm_base_url: Optional[str] = None
    llm_model: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.0

    # OpenSlice
    openslice_base_url: str = "http://localhost:13082"
    openslice_auth_url: str = "http://localhost:8080"
    openslice_username: str = "admin"
    openslice_password: str = "admin"
    openslice_client_id: str = "osapiWebClientId"
    openslice_mock_mode: bool = False

    # ChromaDB
    chroma_persist_dir: str = "./data/chroma_db"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Application
    log_level: str = "INFO"
    max_retries: int = 3

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

L'instance globale `settings` est importee partout dans le projet :
