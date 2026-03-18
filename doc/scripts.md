# Scripts utilitaires

Le repertoire `scripts/` contient des scripts destines a :
- l'administration du catalogue de services
- le test du pipeline et de la couche MCP
- la consultation et la maintenance des ordres OpenSlice

Tous les scripts doivent etre executes depuis la racine du projet avec l'environnement
virtuel active.

---

## ingest_catalog.py

**Role** : Indexer le catalogue de services OpenSlice (TMF633) dans ChromaDB.

C'est l'etape preparatoire indispensable avant la premiere utilisation du pipeline.
L'Agent 2 ne peut selectionner des services que si ChromaDB est alimentee.

**Fonctionnement** :
1. Authentification Keycloak et recuperation des `ServiceSpecification` via l'API TMF633
2. Construction d'un document textuel pour chaque service (nom, description, caracteristiques)
3. Calcul des embeddings via `sentence-transformers/all-MiniLM-L6-v2`
4. Stockage dans la collection ChromaDB `openslice_services`

```bash
# Indexer le catalogue
python scripts/ingest_catalog.py

# Effacer la collection existante avant l'indexation
python scripts/ingest_catalog.py --clear
```

---

## populate_openslice.py

**Role** : Creer un jeu de services de demonstration dans le catalogue OpenSlice reel
(API TMF633).

Services crees par le script :

| Nom                         | Categorie | Description                                        |
|-----------------------------|-----------|----------------------------------------------------|
| Edge_AR_Content_Provider    | XR        | Serveur de contenu AR optimise pour le Edge        |
| Mixed_Reality_Collab_Hub    | XR        | Plateforme de collaboration pour realite mixte     |
| VR_Simulation_Core          | XR        | Moteur de simulation realite virtuelle             |
| 5G_Slice_Paris_Region       | Network   | Connectivite 5G Ile-de-France, latence < 5ms       |
| HD_Video_Streaming_Standard | Entertainment | Diffusion video standard                       |
| Legacy_4G_LTE_Access        | Network   | Acces reseau mobile 4G LTE                         |

Chaque service est cree avec des caracteristiques par defaut : `vCPU`, `RAM_GB`, `Location`.

```bash
python scripts/populate_openslice.py
```

---

## list_services.py

**Role** : Consulter le catalogue de services disponibles dans OpenSlice.

```bash
# Afficher un resume (nom, ID, version)
python scripts/list_services.py

# Afficher les details complets de chaque service
python scripts/list_services.py --detail

# Afficher en format JSON brut
python scripts/list_services.py --json

# Rechercher un service par mot cle
python scripts/list_services.py --search 5G
```

---

## check_orders.py

**Role** : Consulter les ordres de service soumis a OpenSlice (TMF641).

```bash
# Afficher tous les ordres (resume + statistiques par statut)
python scripts/check_orders.py

# Afficher les details complets d'un ordre specifique
python scripts/check_orders.py --id <uuid-de-l-ordre>
```

Le resume indique pour chaque ordre : ID, statut, identifiant externe (externalId).
Les statuts possibles sont : `acknowledged`, `inProgress`, `completed`, `failed`,
`cancelled`.

---

## cleanup_svr_order.py

**Role** : Supprimer tous les ordres de service existants dans OpenSlice.

Utile pour remettre l'environnement a zero entre deux sessions de test.

```bash
python scripts/cleanup_svr_order.py
```

Le script :
1. Liste tous les ordres via `GET /tmf-api/serviceOrdering/v4/serviceOrder`
2. Supprime chaque ordre via `DELETE /tmf-api/serviceOrdering/v4/serviceOrder/{id}`

---

## test_mcp.py

**Role** : Tester la couche MCP de maniere isolee (sans executer le pipeline complet).

Le script teste sequentiellement :
1. Authentification Keycloak
2. Recuperation du catalogue TMF633
3. Validation d'un ordre de service (format TMF641)
4. Soumission d'un ordre de service TMF641
5. Recuperation du statut d'un ordre
6. Recuperation de l'inventaire TMF638

```bash
python scripts/test_mcp.py
python scripts/test_mcp.py --verbose
```

---

## test_pipeline_mcp.py

**Role** : Tester le pipeline complet de bout en bout (Agents 1 a 4 + soumission MCP).

```bash
python scripts/test_pipeline_mcp.py
python scripts/test_pipeline_mcp.py --verbose
```

Ce script utilise une requete de test codee en dur, execute le graphe LangGraph complet
et affiche le resultat de chaque etape. Il necessite une cle API Groq valide et une
collection ChromaDB alimentee.

---

## Ordre d'utilisation recommande

Pour une premiere mise en route :

```bash
# 1. Creer des services dans OpenSlice
python scripts/populate_openslice.py

# 2. Alimenter ChromaDB
python scripts/ingest_catalog.py

# 3. Verifier que des services sont bien presents
python scripts/list_services.py

# 4. Tester la couche MCP seule
python scripts/test_mcp.py

# 5. Tester le pipeline complet
python scripts/test_pipeline_mcp.py

# 6. Lancer l'interface
streamlit run app.py
```
