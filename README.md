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

## Setup

### 1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Set these values in `.env`:

- `NEON_API_KEY`
- `NEON_PROJECT_ID`
- `NEON_DATABASE`
- `NEON_BRANCH`

Optional:

- `NEON_MCP_URL` if you need a non-default MCP endpoint

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

## Example prompts

- Look at `sample_prompt.txt` for more details


## Notes

- The top-level agent uses `SequentialToolExecutor` for deterministic routing.
- Each assistant creates a fresh specialist `Agent` per call and uses `tools=[mcp_client]`.
- Safety review and human approval happen before destructive requests are executed.
- This project is currently focused on schema inspection, inserts, and deletes.

## File overview

- `database_agent.py`: CLI entrypoint and top-level request router
- `server/neon_mcp.py`: Neon MCP client factory and environment loading
- `server/tools/safety_reviewer.py`: safety reviewer agent and human approval helper
- `server/tools/schema_assistant.py`: factory for the schema/read-only tool
- `server/tools/insert_assistant.py`: factory for the insert tool
- `server/tools/delete_assistant.py`: factory for the delete tool
- `sample_prompt.txt`: sample multi-intent prompts for manual testing
