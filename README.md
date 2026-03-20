# strands-pos

> Database assistant that routes natural-language requests to specialist agents
> backed by a Neon PostgreSQL database via MCP.

## What It Does

strands-pos accepts natural-language database requests via a REST API and routes them to the appropriate specialist agent. Destructive operations (DELETE, DROP, TRUNCATE) are intercepted by a safety reviewer and require explicit human approval before execution.

## Architecture

```
User Input (API/Web UI)
      │
      ▼
 Orchestrator ──► Safety Reviewer (destructive ops only)
      │                   │
      ├──► Schema Agent    │ Rejected → abort
      ├──► Insert Agent    │ Approved ↓
      └──► Delete Agent ◄──┘
             │
             ▼
       Neon MCP Client
             │
             ▼
     Neon PostgreSQL
```

## Prerequisites

- Python >= 3.11
- Docker >= 24 (for containerized deployment)
- GCP project with Cloud Run and Secret Manager APIs enabled (for production deployment)
- Neon account + API key

## Quick Start (Local)

```bash
git clone https://github.com/your-org/strands-pos
cd strands-pos
python3 -m venv .venv
source .venv/bin/activate
cp .env.example .env           # Edit with your credentials
pip install -e ".[dev]"
uvicorn server.api:app --reload
```

Open http://localhost:8000 for the web UI, or http://localhost:8000/docs for API docs.

## Environment Variables

| Variable               | Required | Default     | Description                          |
|------------------------|----------|-------------|--------------------------------------|
| `DATABASE_URL`         | Yes      | —           | PostgreSQL URL for request state     |
| `NEON_API_KEY`         | Yes      | —           | Neon API key for MCP                 |
| `NEON_PROJECT_ID`      | Yes      | —           | Neon project ID                      |
| `NEON_DATABASE`        | Yes      | —           | Neon database name                   |
| `NEON_BRANCH_ID`       | Yes      | —           | Neon branch ID                       |
| `GOOGLE_API_KEY`       | No*      | —           | Gemini API key (local dev)           |
| `GOOGLE_CLOUD_PROJECT` | No*      | —           | GCP project for Vertex AI            |
| `GEMINI_MODEL_ID`      | No       | gemini-2.5-flash | Model ID                        |
| `LOG_LEVEL`            | No       | INFO        | Logging verbosity                    |

*Either `GOOGLE_API_KEY` or `GOOGLE_CLOUD_PROJECT` is needed for the LLM.

## Commands

| Command                        | Description                           |
|--------------------------------|---------------------------------------|
| `uvicorn server.api:app --reload` | Start the API server (dev)         |
| `python database_agent.py`     | Start the CLI assistant               |
| `pytest tests/ -v`             | Run all tests                         |
| `ruff check server/`           | Lint                                  |
| `mypy server/`                 | Type check                            |
| `docker build -t strands-pos .`| Build container image                 |
| `cd infra && terraform apply`  | Deploy infrastructure to GCP          |

## Agents

| Agent             | Responsibility                                    |
|-------------------|---------------------------------------------------|
| Orchestrator      | Routes requests to the correct specialist         |
| Schema Assistant  | Read-only queries, schema introspection           |
| Insert Assistant  | INSERT operations                                 |
| Delete Assistant  | DELETE / DROP (always routed via Safety Reviewer) |
| Safety Reviewer   | Flags destructive ops, requires human approval    |


### Quick Deploy

```bash
# 1. Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. Enable APIs
gcloud services enable run.googleapis.com secretmanager.googleapis.com

# 3. Apply Terraform
cd infra
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init
terraform apply

# 4. Populate secrets
echo -n "postgresql://..." | gcloud secrets versions add production-strands-pos-DATABASE_URL --data-file=-
# ... repeat for other secrets

# 5. Build and push image
docker build -t gcr.io/YOUR_PROJECT/strands-pos:latest .
docker push gcr.io/YOUR_PROJECT/strands-pos:latest
```

## Documentation

- [GCP Troubleshooting](docs/gcp-deployment-troubleshooting.md) — Deployment issues

## Testing

```bash
# Run all tests
pytest tests/ -v

# Tests use mocked agents — no real DB or LLM calls
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Web UI |
| `GET` | `/health` | Liveness check |
| `GET` | `/ready` | Readiness check (verifies database) |
| `POST` | `/query` | Submit a database query |
| `GET` | `/query/{request_id}` | Poll query status / result |
| `POST` | `/approval/{approval_id}` | Approve or reject a destructive query |
| `GET` | `/logs/stream` | SSE stream of server logs |

## Project Structure

```
strands-pos/
├── server/
│   ├── api.py                 # FastAPI application
│   ├── config/                # Centralized configuration
│   ├── core/                  # Business logic (orchestrator, model)
│   ├── db/                    # Data access (repository, MCP client)
│   └── tools/                 # Specialist agents
├── tests/                     # Pytest tests (all mocked)
├── infra/                     # Terraform for GCP
├── docs/                      # Documentation
└── .github/workflows/         # CI/CD pipelines
```
