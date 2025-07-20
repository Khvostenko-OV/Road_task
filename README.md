# Road Tasks

## Run Application

```bash
git clone https://github.com/Khvostenko-OV/Road_task.git
cd Road_task
docker-compose pull
docker-compose up -d
```

- After startup, the Flask application will be running on port **5000**
- To test it on your local machine, call http://localhost:5000/

## API specification

### 1. Authorisation

| Endpoint    | Method | Params              | Format              | Description       |
| ----------- | ------ |---------------------| ------------------- | ----------------- |
| `/add_user` | POST   | `login`, `password` | multipart/form-data | Create a new user |
| `/login`    | POST   | `login`, `password` | multipart/form-data | User login        |
| `/logout`   | POST   | —                   | —                   | User logout       |

### 2. Create and Update Networks

### Add New Network

**POST** `/add_network`  
**Body (multipart/form-data)**  
- `name` (str): network name  
- `public` (str, optional): `"true"` or `"false"` (default: `"false"`)  
- `file` (file): GeoJSON FeatureCollection  

**Description**  
Creates a road network with geodata and properties.  
Requires authentication; the user becomes the owner.  
If `public=true`, the network can be retrieved without authentication.

**Response**  
Returns network data (see *Getting Network Data* section).

---

### Update Existing Network

**POST** `/update_network`  
**Body (multipart/form-data)**  
- `id` (int): network ID (preferred)  
- `name` (str): network name  
- `file` (file): GeoJSON FeatureCollection  

**Description**  
Adds a new version of a map to an existing network.  
User must be authenticated and must be the owner.

**Response**  
Returns network data (see *Getting Network Data* section).

---

## 3. Getting Data ️

### Get Network Data

**GET** `/network/`  
**Query parameters:**
- `id` (int): network ID (preferred)
- `name` (str): network name

**Description**  
Returns properties of the network. Search by ID or by name (ID has priority).

**Access rules:**
- **Public networks**: accessible by anyone  
- **Private networks**: accessible only by the owner (authenticated user)

**Response example:**
```json
{
  "network_id": 123,
  "name": "My Road Network",
  "owner_id": 42,
  "owner_name": "oleg",
  "public": false,
  "latest_version": 3,
  "versions": { "1":  1, "2": 5, "3": 251},
  "created_at": "Sun, 20 Jul 2025 07:59:28 GMT"
}
```

---

### Get Network Edges

**GET** `/network/edges/`

**Query parameters:**
- `id` (int): network ID (preferred)
- `name` (str): network name
- `version` (int, optional; default = latest): version number

**Description**  
Returns certain version of the edges of a network. Search by ID or by name (ID has priority).

**Access rules:**
- Public networks: accessible by anyone  
- Private networks: accessible only by the owner (authenticated user)

**Response example:**
```json
{
  "network_id": 123,
  "name": "My Road Network",
  "version": 3,
  "map_id": 987,
  "created_at": "Sun, 20 Jul 2025 07:59:28 GMT",
  "edges": [ ]
}
```

## Quickstart

## 1. Start the services:
```bash
docker-compose up -d
```

## 2. Register a user

```bash
curl -X POST \
  -F "username=admin" \
  -F "password=secret" \
  http://localhost:5000/add_user
```

## 3. Log in

```bash
curl -c cookies.txt -X POST \
  -F "username=admin" \
  -F "password=secret" \
  http://localhost:5000/login
```

## 4. Create a network

```bash
curl -b cookies.txt -X POST \
  -F "name=MyRoads" \
  -F "public=true" \
  -F "file=@roads.geojson;type=application/json" \
  http://localhost:5000/add_network
```

## 5. Retrieve edges

```bash
curl http://localhost:5000/network/edges/?name=MyRoads
```

---

## Notes

- All endpoints return **JSON** responses.  
- Authentication is managed via **cookies** and **Flask‑Login** (Flask uses cookies to store session/user ID).  
- GeoJSON parsing supports **FeatureCollection** inputs (standard GeoJSON format).
- Network **versions** increment with each update request.  
- When retrieving edges, the API returns data for the **specified version**, or the **latest version** if not specified.
