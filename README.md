# IT Asset DB API

Built by Dean Wilshaw.

IT Asset DB API is a robust Python backend for tracking hardware assets across an organisation. Upgraded from a simple CLI script, this project now provides a full REST API built with **FastAPI** and is fully containerized using **Docker** for reliable deployments. It uses SQLite for lightweight, persistent data storage.

## The Business Problem

IT teams need reliable visibility of hardware assets: which devices exist, where they are assigned, and which department owns them. In many smaller environments, this data lives in spreadsheets, ticket notes, or technician memory. That makes audits slower, onboarding messier, and troubleshooting harder.

Common problems this project addresses:
- Hardware records scattered across spreadsheets or informal notes.
- Difficulty querying assets by department during audits or refresh projects.
- Increased risk of duplicate IP or MAC records.
- Weak handover evidence when devices move between departments.

For MSPs and internal IT teams, a clean asset database with a standardized API is the foundation for endpoint management, lifecycle planning, and automated infrastructure support.

## The Solution & Architecture

This project demonstrates a modern, "Next-Level" backend architecture:

1. **FastAPI (Python):** Provides a high-performance REST API with built-in data validation (Pydantic) and auto-generated Swagger documentation.
2. **SQLite:** A lightweight local database backend. The database file is mapped to a Docker volume to ensure data persists across container restarts.
3. **Docker & Docker Compose:** The entire application is containerized, meaning it can be run on any machine (Windows, Mac, Linux) with a single command, eliminating "it works on my machine" issues.

### Core Endpoints

- `GET /health` - Checks if the API is running and the database is accessible.
- `GET /assets` - Returns all assets.
- `GET /assets?department=Finance` - Returns assets filtered by department.
- `POST /assets` - Adds a new asset to the database.

## Local Execution Setup (Docker)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

### Run the API
To start the API, open your terminal in the project folder and run:

```bash
docker-compose up --build
```

The API will start on port `8000`. When it starts, it automatically provisions the SQLite database and seeds it with demo assets (Finance, IT Support, Operations).

## Usage & Examples

### 1. Interactive Swagger UI (Recommended)
Because this project uses FastAPI, it automatically generates a beautiful interactive documentation page. 
Open your browser and navigate to:
**http://localhost:8000/docs**

From there, you can test all the endpoints directly in your browser without writing any code!

### 2. cURL Examples

**Check API Health:**
```bash
curl http://localhost:8000/health
```

**Get All Assets:**
```bash
curl http://localhost:8000/assets
```

**Get Finance Department Assets:**
```bash
curl "http://localhost:8000/assets?department=Finance"
```

**Add a New Asset:**
```bash
curl -X 'POST' \
  'http://localhost:8000/assets' \
  -H 'Content-Type: application/json' \
  -d '{
  "AssetID": "AST-2099",
  "Hostname": "HR-LAP-99",
  "MAC_Address": "00:1A:2B:3C:99:99",
  "IP_Address": "10.20.50.15",
  "Department": "HR"
}'
```

## Project Files

```text
main.py            # FastAPI REST application routes
asset_db.py        # Python SQLite database layer
Dockerfile         # Container blueprint
docker-compose.yml # Orchestration for easy local running
requirements.txt   # Python dependencies
it_assets.db       # Generated SQLite database (persisted via Docker volume)
README.md          # Project documentation
```

## Future Enhancements
- Switch the SQLite backend to PostgreSQL using Supabase for production scalability.
- Add JWT Authentication before exposing asset data beyond local networks.
- Build a React frontend dashboard that consumes this API.

## ✅ CI Pipeline & Verification

This repository integrates a GitHub Actions CI workflow to ensure code health on every commit:
- **Syntax Verification:** Automatically compiles all Python source files (`main.py`, `asset_db.py`) to confirm no structural syntax errors exist.
- **Dependency Integrity:** Verifies that requirements install cleanly in the target environment.
