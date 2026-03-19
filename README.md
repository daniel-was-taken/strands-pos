# strands-pos

Command-line database assistant built with Strands and Neon MCP.

## What this project does

- Routes schema and read-only questions to `schema_assistant`
- Routes insert requests to `insert_assistant`
- Routes delete requests to `delete_assistant`
- Runs a safety review + human approval step for destructive requests
- Uses managed Neon MCP integration via `Agent(tools=[mcp_client])`
- Executes routed tools sequentially through `SequentialToolExecutor`

## Architecture

The CLI creates one shared Neon `MCPClient` and the sub-agents use managed MCP lifecycle per invocation.

Flow:

1. User enters a request in `database_agent.py`
2. If the request is destructive (for example contains delete/drop keywords), `safety_reviewer` evaluates it and a human must approve or reject
3. The top-level `DBControl` agent routes to a specialized tool (`schema_assistant`, `insert_assistant`, or `delete_assistant`)
4. The selected tool creates a fresh specialist `Agent` and runs with `tools=[mcp_client]`
5. MCP tools (`get_database_tables`, `describe_table_schema`, `run_sql`) execute against Neon and return results

- `database_agent.py` creates the top-level router agent
- `server/neon_mcp.py` builds the shared Neon MCP client
- `server/tools/safety_reviewer.py` creates the safety reviewer and handles human approval prompts
- `server/tools/schema_assistant.py` creates the read-only schema tool
- `server/tools/insert_assistant.py` creates the insert tool
- `server/tools/delete_assistant.py` creates the delete tool

This is still a multi-agent architecture: one orchestrator agent, three specialist database agents, and one safety reviewer agent.

## Deployment to GCP

This project deploys to Google Cloud via Terraform and Cloud Run.

### 1. Prerequisites
- GCP CLI (`gcloud`) installed and authenticated.
- Terraform >= 1.5 installed.
- A GCP project with billing enabled.

### 2. Scaffold Infrastructure

Run the deploy script to create the Artifact Registry, Cloud Build action, and Cloud Run service stub:
```bash
./deploy.sh <your-gcp-project-id> us-central1 <github_owner> <github_repo> <github_branch>
```

### 3. Bootstrap Secrets
We use GCP Secret Manager explicitly to avoid storing plaintext in Terraform state.
Before you can run the app, upload the secret versions via the GCP Console or CLI:
```bash
echo -n "..." | gcloud secrets versions add production-strands-pos-DATABASE_URL --data-file=-
echo -n "..." | gcloud secrets versions add production-strands-pos-NEON_API_KEY --data-file=-
echo -n "..." | gcloud secrets versions add production-strands-pos-NEON_PROJECT_ID --data-file=-
echo -n "..." | gcloud secrets versions add production-strands-pos-NEON_DATABASE --data-file=-
echo -n "..." | gcloud secrets versions add production-strands-pos-NEON_BRANCH_ID --data-file=-
```

### 4. Deploy
With the CI/CD pipeline set up, a simple push to the target GitHub branch will trigger a deployment.
Alternatively, follow the CLI output hints from `./deploy.sh` to trigger a manual container build & deploy locally.

### 5. Tear Down
To free the sandbox resources later, use the destroy script with the same argument pattern:

```bash
./destroy.sh <your-gcp-project-id> us-central1 <github_owner> <github_repo> <github_branch>
```

### 6. Troubleshooting
For the full deployment runbook, including the errors encountered during setup, recovery steps, and redeploy instructions, see [docs/gcp-deployment-troubleshooting.md](docs/gcp-deployment-troubleshooting.md).

## Setup

### 1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
# Production only
pip install -r requirements.txt

# Development (includes pytest)
pip install -r requirements-dev.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Set these values in `.env`:

- `DATABASE_URL`
- `NEON_API_KEY`
- `NEON_PROJECT_ID`
- `NEON_DATABASE`
- `NEON_BRANCH_ID`

For the Gemini model, set one of:

- `GOOGLE_API_KEY` — for Google AI Studio (simplest for local dev)
- `GOOGLE_CLOUD_PROJECT` + `GOOGLE_CLOUD_LOCATION` — for Vertex AI (requires `gcloud auth application-default login`)

Optional:

- `NEON_MCP_URL` if you need a non-default MCP endpoint
- `GEMINI_MODEL_ID` to override the default model (`gemini-2.5-flash`)

## Run

### CLI

```bash
python database_agent.py
```

At the prompt, enter a database request. Type `exit` to quit.

### Web UI

```bash
uvicorn server.api:app --reload
```

Then open `http://localhost:8000` in your browser.

Interactive API docs are available at `http://localhost:8000/docs` (Swagger UI).

## Tests

```bash
# Run all tests
pytest tests/ -v

# Run only smoke / lifecycle / e2e tests
pytest tests/test_smoke.py -v
pytest tests/test_query_lifecycle.py -v
pytest tests/test_approval_lifecycle.py -v
pytest tests/test_e2e.py -v
```

All tests use mocked agents and an in-memory repository — no real database or LLM calls.

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

## Example prompts

```
Show me all tables in the database
Describe the schema of the employees table
Insert a new employee named John Doe with email john@example.com
Delete the employee with id 5
```

## Notes

- The top-level agent uses `SequentialToolExecutor` for deterministic routing.
- Each assistant creates a fresh specialist `Agent` per call and uses `tools=[mcp_client]`.
- Safety review and human approval happen before destructive requests are executed.
- This project is currently focused on schema inspection, inserts, and deletes.

## Project structure

```
strands-pos/
├── database_agent.py          # CLI entrypoint — python database_agent.py
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # Dev dependencies (includes pytest)
├── Dockerfile                 # Container image for Cloud Run
├── deploy.sh / destroy.sh     # GCP infrastructure lifecycle scripts
├── server/
│   ├── api.py                 # FastAPI app — uvicorn server.api:app --reload
│   ├── schemas.py             # Pydantic request/response models
│   ├── log_stream.py          # SSE log streaming to the web UI
│   ├── static/index.html      # Web UI
│   ├── core/                  # Business logic
│   │   ├── model.py           # Shared Gemini model configuration
│   │   └── orchestrator.py    # Request routing, safety review, approval workflow
│   ├── db/                    # Data access layer
│   │   ├── repository.py      # PostgreSQL persistence (requests + audit trail)
│   │   └── neon_mcp.py        # Neon MCP client factory
│   └── tools/                 # Agent tools
│       ├── assistant_factory.py   # Shared factory for specialist database tools
│       ├── safety_reviewer.py     # Safety reviewer agent + human approval
│       ├── schema_assistant.py    # Read-only schema/SELECT tool
│       ├── insert_assistant.py    # INSERT tool
│       └── delete_assistant.py    # DELETE tool
├── tests/                     # pytest tests/ -v (all mocked, no real DB/LLM)
│   ├── conftest.py            # Shared fixtures
│   ├── test_smoke.py          # Health + HTML serving
│   ├── test_query_lifecycle.py    # Non-destructive query flow
│   ├── test_approval_lifecycle.py # Destructive query + approval flow
│   └── test_e2e.py            # Full end-to-end lifecycle
├── infra/                     # Terraform IaC for GCP
│   ├── main.tf / variables.tf / outputs.tf / providers.tf
│   └── modules/               # artifact-registry, cloudrun-runtime, cloudbuild-pipeline
└── docs/
    └── gcp-deployment-troubleshooting.md
```
