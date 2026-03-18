# Couche MCP — Model Context Protocol

## Vue d'ensemble

La couche MCP (Model Context Protocol) est une abstraction locale qui standardise la
communication entre les agents et les services externes (OpenSlice). Elle est implementee
en mode local sans serveur HTTP externe — le client et le serveur s'appelent directement
en Python.

```
Agent / Orchestrateur
        |
   MCPClient (mcp/mcp_client.py)
        |  appel par nom d'outil (string)
        v
   OpenSliceMCPServer (mcp/openslice_mcp_server.py)
        |  dispatch vers handler
        v
   OpenSliceClient (mcp/openslice_client.py)
        |  appels HTTP REST
        v
   OpenSlice API (TMF633 / TMF641 / TMF638)
```

---

## MCPClient (mcp/mcp_client.py)

Point d'entree unique pour les agents. Les agents n'accedent jamais directement a
`OpenSliceMCPServer` — ils passent toujours par `MCPClient`.

### Initialisation

```python
from mcp.mcp_client import MCPClient

client = MCPClient(mode="local")
# mode="local" est le seul mode supporte (communication directe en Python)
```

### Methodes disponibles

#### Outils MCP

| Methode                              | Description                                   |
|--------------------------------------|-----------------------------------------------|
| `authenticate()`                     | Obtenir un token JWT depuis Keycloak          |
| `get_service_catalog()`              | Catalogue TMF633 (ServiceSpecifications)      |
| `submit_service_order(order_json)`   | Soumettre un ordre TMF641                     |
| `get_order_status(order_id)`         | Statut d'un ordre par son ID                  |
| `get_service_inventory()`            | Inventaire des services actifs (TMF638)       |
| `validate_service_order(order_json)` | Valider un ordre TMF641 cote client           |

#### Ressources MCP

| Methode            | URI MCP               | Description                         |
|--------------------|-----------------------|-------------------------------------|
| `read_catalog()`   | `catalog://services`  | Lecture du catalogue des services   |
| `read_inventory()` | `inventory://services`| Lecture de l'inventaire des services|

#### Interface generique

```python
# Appel par nom d'outil
result = client.call_tool("submit_service_order", service_order_json=json_str)

# Lecture d'une ressource
catalog = client.read_resource("catalog://services")
```

### Format de retour standard

Tous les outils retournent un dictionnaire avec au minimum :

```python
{
    "status": "success" | "error",
    "message": "...",       # present si status="error"
    "timestamp": "...",     # ISO 8601
    # + champs specifiques a l'outil
}
```

---

## OpenSliceMCPServer (mcp/openslice_mcp_server.py)

Serveur MCP local qui enregistre et expose les outils et ressources. Instancie
`OpenSliceClient` a l'initialisation.

### Outils enregistres

#### authenticate

```
Description : Authentification Keycloak — obtention d'un token JWT
Arguments   : aucun
Retour      : { status, message, token_preview, timestamp }
```

#### get_service_catalog

```
Description : Recuperation du catalogue TMF633 (ServiceSpecifications)
Arguments   : aucun
Retour      : { status, services: List, count: int, timestamp }
```

#### submit_service_order

```
Description : Soumission d'un ordre de service TMF641
Arguments   : service_order_json (str) — ordre au format JSON
Retour      : { status, order_id, order_state, details, timestamp }
```

#### get_order_status

```
Description : Statut d'un ordre de service
Arguments   : order_id (str) — UUID de l'ordre
Retour      : { status, order_id, order_state, details, timestamp }
```

#### get_service_inventory

```
Description : Inventaire des services deployes (TMF638)
Arguments   : aucun
Retour      : { status, services: List, count: int, timestamp }
```

#### validate_service_order

```
Description : Validation cote client d'un ordre TMF641
Arguments   : service_order_json (str) — ordre au format JSON
Retour      : { status, is_valid: bool, errors: List, warnings: List, timestamp }
```

**Regles de validation implementees** :

- `serviceOrderItem` doit etre present et non vide
- Chaque item doit avoir : `id`, `action`, `service`
- Chaque service doit avoir : `serviceSpecification.id` (UUID non vide)
- Avertissement (non bloquant) si `externalId` absent

### Ressources enregistrees

| URI MCP               | Handler              | Description                      |
|-----------------------|----------------------|----------------------------------|
| `catalog://services`  | `_resource_catalog`  | Liste des services disponibles   |
| `inventory://services`| `_resource_inventory`| Services deployes                |

---

## OpenSliceClient (mcp/openslice_client.py)

Client HTTP bas niveau qui encapsule les appels REST vers OpenSlice et Keycloak.
Utilise `httpx` avec un timeout de 60 secondes.

### Initialisation

```python
from mcp.openslice_client import OpenSliceClient

client = OpenSliceClient(
    base_url="http://localhost:13082",  # optionnel — defaut depuis settings
    auth_url="http://localhost:8080",   # optionnel
    username="admin",                   # optionnel
    password="admin",                   # optionnel
    mock_mode=True                      # optionnel — override settings
)
```

### Methodes

| Methode                      | Endpoint TMF                                               | Description                     |
|------------------------------|------------------------------------------------------------|---------------------------------|
| `authenticate()`             | POST `/auth/realms/openslice/protocol/openid-connect/token` | Token JWT Keycloak             |
| `get_catalog()`              | GET `/tmf-api/serviceCatalogManagement/v4/serviceSpecification` | Liste du catalogue          |
| `submit_order(order_dict)`   | POST `/tmf-api/serviceOrdering/v4/serviceOrder`            | Creer un ordre de service       |
| `get_service_status(order_id)` | GET `/tmf-api/serviceOrdering/v4/serviceOrder/{id}`      | Statut d'un ordre               |
| `get_service_inventory()`    | GET `/tmf-api/serviceInventoryManagement/v4/service`       | Inventaire des services actifs  |

### Comportement en mode mock

Quand `mock_mode=True` :

- `authenticate()` : retourne `"mock-jwt-token-for-testing-purposes-only"`
- `get_catalog()` : retourne une liste vide
- `submit_order()` : cree un enregistrement dans le dictionnaire interne `_mock_orders`
  et retourne un ordre avec un `id` genere (`mock-{uuid}`) et l'etat `acknowledged`
- Aucun appel HTTP n'est effectue — `httpx.Client` n'est pas instancie

---

## Utilisation directe (exemple)

```python
from mcp.mcp_client import MCPClient

client = MCPClient(mode="local")

# Valider un ordre
order_json = '{"externalId": "test", "serviceOrderItem": [...]}'
result = client.validate_service_order(order_json)
print(result["is_valid"])    # True / False
print(result["errors"])      # []

# Soumettre un ordre
response = client.submit_service_order(order_json)
print(response["order_id"])  # UUID de l'ordre cree

# Verifier le statut
status = client.get_order_status(response["order_id"])
print(status["order_state"]) # "acknowledged", "inProgress", "completed", ...
```
