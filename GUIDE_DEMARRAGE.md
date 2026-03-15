# Guide de Démarrage - IBN Agentic AI Framework

## 📁 Structure du Projet

```
ai_agent/
├── agents/
│   ├── agent1_interpreter.py  ✅ Agent 1 - Interpréteur
│   ├── agent2_selector.py     ✅ Agent 2 - Sélecteur RAG
│   ├── agent3_translator.py   📝 Agent 3 - Traducteur TMF641
│   └── agent4_validator.py    📝 Agent 4 - Validateur
├── schemas/
│   ├── intent.py              ✅ Schémas Intent (JSON Agnostique)
│   └── tmf641.py              ✅ Schémas Service Ordering
├── mcp/
│   └── openslice_client.py    📝 Client HTTP OpenSlice
├── scripts/
│   └── ingest_catalog.py      ✅ Ingestion catalogue OpenSlice
├── tests/
│   └── test_agents.py         ✅ Tests unitaires
├── config.py                  ✅ Configuration centralisée
├── orchestrator.py            📝 Orchestration LangGraph 
├── main.py                    ✅ Pipeline Agents 1 & 2
├── requirements.txt           ✅ Dépendances Python
├── .env.example               ✅ Template configuration
├── README.md                  ✅ Documentation projet
└── QUICKSTART.txt             ✅ Guide de démarrage rapide
```

## 🚀 Installation

### Étape 1: Environnement virtuel

```powershell
# Créer l'environnement
python -m venv venv

# Activer (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Ou (Windows CMD)
venv\Scripts\activate.bat
```

### Étape 2: Installer les dépendances

```powershell
pip install -r requirements.txt
```

**Note**: L'installation peut prendre quelques minutes (notamment pour les modèles d'embeddings).

### Étape 3: Configuration

```powershell
# Copier le template
copy .env.example .env
```

Éditer le fichier `.env`:

**Groq**:
```env
LLM_PROVIDER=groq
LLM_API_KEY=gsk_votre_clé_ici  # Créer sur console.groq.com
LLM_MODEL=llama-3.3-70b-versatile
```

📖 **Plus de détails**: Voir [API_SETUP.md](API_SETUP.md)

## 🧪 Tests et Validation

### Test 1: Ingestion du catalogue (Agent 2)

**Option A - Mode Test (sans OpenSlice)**
```powershell
python scripts/ingest_catalog.py --mock
```

Cela crée 5 services de test dans ChromaDB:
- XR Application Bundle
- 4K Video Streaming Service
- IoT Platform Service
- Edge Computing Service
- 5G Network Slice - eMBB

**Option B - Avec OpenSlice**
```powershell
python scripts/ingest_catalog.py
```

### Test 2: Agent 1 seul (Interpréteur)

```powershell
python test_quick.py
```

✅ **Résultat attendu**: Mode interactif pour tester vos propres requêtes. Conversion en intention structurée (JSON Agnostique) avec décomposition adaptative.

### Test 3: Agent 2 seul (Sélecteur)

```powershell
python -m agents.agent2_selector
```

✅ **Résultat attendu**: Recherche sémantique de services dans ChromaDB

### Test 4: Pipeline complet (Agents 1 + 2)

```powershell
# Exemple prédéfini
python main.py --example

# Requête personnalisée
python main.py --query "I need a low-latency 5G service for IoT"

# Mode interactif
python main.py --interactive
```

### Test 5: Suite de tests complète

```powershell
python tests/test_agents.py
```

## 📋 Exemples de Requêtes

### 1. XR Application (du contexte)
```
I need a network composed of three XR applications: an augmented reality content server,
a mixed reality collaboration platform, and a virtual reality simulation engine. Each application
requires 4 vCPUs and 2 gigabytes (GB) of memory. All XR applications are interconnected
using 5 GB/s links. The clients are connected through a 5G network located in the Nice area
and tolerate a maximum latency of 5 ms.
```

### 2. IoT Platform
```
I need an IoT platform for smart city with low power devices and edge computing capabilities
```

### 3. Video Streaming
```
Deploy a 4K video streaming service with CDN and adaptive bitrate for residential customers
```

### 4. Edge Computing
```
I need edge computing resources with low latency near Nice for real-time processing of sensor data
```

### 5. 5G Network Slice
```
Create a 5G network slice with high throughput and low latency for mobile augmented reality applications
```

## 🔍 Fonctionnement des Agents

### Agent 1: Interpréteur
**Entrée**: Langage naturel (tout type de requête)  
**Sortie**: Intention structurée (JSON Agnostique)

**Principe**: L'agent analyse la complexité de chaque requête et décompose intelligemment:
- **Intention simple** → 1 sous-intention
- **Intention complexe** → 2, 3, ou plus selon les besoins réels

**Processus**:
1. Analyse de la requête avec LLM (Llama 3.3 70B via API Groq)
2. Évaluation de la complexité réelle
3. Identification automatique des domaines/aspects distincts
4. Décomposition adaptative (1 à N sous-intentions selon la complexité)
5. Extraction des contraintes/QoS globaux
6. Validation Pydantic du JSON généré
7. Retour de l'objet Intent

**Flexibilité**: L'agent fonctionne pour **tout type de service**:
- Infrastructure réseau (cloud, transport, ran)
- Applications web (frontend, backend, database)
- Plateformes IoT (sensors, gateway, analytics)
- Services cloud (compute, storage, security)
- Etc.

**Exemples de décomposition**:

**Cas 1 - Intention SIMPLE (1 sous-intention)**:
Requête: "I need a PostgreSQL database with 100GB storage"
```json
{
  "intent_id": "Database_PostgreSQL_001",
  "type": "simple_service",
  "sub_intents": [
    {
      "domain": "database",
      "requirements": {
        "type": "PostgreSQL",
        "storage": "100GB",
        "backup": "daily"
      }
    }
  ]
}
```

**Cas 2 - Infrastructure réseau XR (3 sous-intentions)**:
```json
{
  "intent_id": "XR_Deployment_Nice_001",
  "type": "composite_service",
  "sub_intents": [
    {
      "domain": "cloud",
      "requirements": {
        "cpu": 4,
        "ram": "2GB",
        "applications": ["AR_server", "MR_platform", "VR_engine"]
      }
    },
    {
      "domain": "transport",
      "requirements": {
        "bandwidth": "5Gbps",
        "interconnection": "all_to_all"
      }
    },
    {
      "domain": "ran",
      "requirements": {
        "network_type": "5G",
        "location": "Nice",
        "max_latency": "5ms"
      }
    }
  ],
  "location": "Nice",
  "qos": {
    "max_latency": "5ms"
  }
}
```

**Cas 3 - IoT Platform (2 sous-intentions)**:
```json
{
  "intent_id": "IoT_SmartCity_001",
  "type": "composite_service",
  "sub_intents": [
    {
      "domain": "sensors",
      "requirements": {
        "count": 1000,
        "protocol": "MQTT",
        "data_frequency": "1min"
      }
    },
    {
      "domain": "analytics",
      "requirements": {
        "processing": "real-time",
        "alerts": true,
        "dashboard": true
      }
    }
  ],
  "location": "Paris"
}
```

**Cas 4 - Application Web E-commerce (3 sous-intentions)**:
```json
{
  "intent_id": "WebApp_Shop_001",
  "type": "composite_service",
  "sub_intents": [
    {
      "domain": "frontend",
      "requirements": {
        "framework": "React",
        "cdn_enabled": true,
        "responsive": true
      }
    },
    {
      "domain": "backend",
      "requirements": {
        "api_type": "REST",
        "instances": 3,
        "load_balancing": true
      }
    },
    {
      "domain": "database",
      "requirements": {
        "type": "PostgreSQL",
        "storage": "100GB",
        "backup_frequency": "daily"
      }
    }
  ],
  "qos": {"availability": "99.9%"}
}
```

### Agent 2: Sélecteur RAG
**Entrée**: Intention structurée (JSON Agnostique)  
**Sortie**: Liste de services sélectionnés (avec UUIDs et scores)

**Processus**:
1. Conversion de l'intention en requête textuelle
2. Génération d'embeddings avec sentence-transformers
3. Recherche de similarité dans ChromaDB
4. Ranking des services par score de pertinence
5. Retour des top-k services avec leurs UUIDs

**Exemple de sortie**:
```python
[
  {
    "id": "mock-xr-service-001",
    "name": "XR Application Bundle",
    "score": 0.87,
    "description": "Extended Reality service bundle...",
    "metadata": {
      "category": "XR",
      "type": "5G Edge Service"
    }
  }
]
```

## 🛠️ Dépannage

### Problème: `ModuleNotFoundError`
**Solution**:
```powershell
# Vérifier que venv est activé
pip install -r requirements.txt
```

### Problème: "Collection vide" (Agent 2)
**Solution**:
```powershell
python scripts/ingest_catalog.py --mock
```

### Problème: "API key not found"
**Solution**: Vérifier le fichier `.env` et les clés API

### Problème: Erreur d'encodage sur Windows
**Solution**:
```powershell
$env:PYTHONIOENCODING="utf-8"
```

### Problème: ChromaDB ne démarre pas
**Solution**: Supprimer et recréer
```powershell
Remove-Item -Recurse -Force data\chroma_db
python scripts/ingest_catalog.py --mock
```

## 📊 Données de Test

Le mode `--mock` crée ces services:

1. **XR Application Bundle** (Catégorie: XR)
   - Extended Reality avec 5G et edge computing
   
2. **4K Video Streaming Service** (Catégorie: Video)
   - Streaming HD avec CDN
   
3. **IoT Platform Service** (Catégorie: IoT)
   - Plateforme IoT industrielle
   
4. **Edge Computing Service** (Catégorie: Edge)
   - Infrastructure edge à faible latence
   
5. **5G Network Slice - eMBB** (Catégorie: 5G)
   - Slice 5G haut débit mobile

## 🔗 Intégration Future

### Agents 3 & 4 (Sarra)
- **Agent 3**: Traduction UUID + Contraintes → ServiceOrder TMF641
- **Agent 4**: Validation et correction du ServiceOrder

### Serveur MCP (Ilef)
- Interface avec OpenSlice via MCP
- Tools: `get_catalog()`, `submit_order()`, `get_service_status()`

### Orchestrateur LangGraph (Ilef)
- Coordination des 4 agents
- Gestion des boucles de correction
- Soumission finale à OpenSlice

## 📚 Standards TMForum

- **TMF641**: Service Ordering Management API
  - Spécification: https://www.tmforum.org/resources/specification/tmf641
  
- **TMF633**: Service Catalog Management API
  - Spécification: https://www.tmforum.org/resources/specification/tmf633

**Note**: On n'utilise pas TMF921. Les intentions sont représentées par un format JSON agnostique décomposé par domaine (cloud, transport, ran).

## 🎯 Prochaines Étapes pour Cyrine

1. ✅ Tester l'installation complète
2. ✅ Exécuter les tests des Agents 1 & 2
3. ✅ Valider avec plusieurs requêtes différentes
4. 📝 Documenter les cas limites rencontrés
5. 📝 Préparer l'intégration avec les Agents 3 & 4 (Sarra)
6. 📝 Coordonner avec Ilef pour MCP et LangGraph

## 💡 Conseils

- **Utilisez le mode `--mock`** pour développer sans OpenSlice
- **Mode interactif** (`python main.py --interactive`) pour tester rapidement
- **Variez les requêtes** pour tester la robustesse de l'extraction
- **Vérifiez les logs** pour comprendre le comportement des agents
- **ChromaDB persiste** les données dans `data/chroma_db/`

## 📞 Support

Pour toute question:
- Vérifiez d'abord [QUICKSTART.py](QUICKSTART.py)
- Consultez [README.md](README.md)
- Examinez les exemples dans les fichiers de tests

Bon développement ! 🚀
