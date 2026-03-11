# strands-pos

Command-line database assistant built with Strands and Neon MCP.

## What this project does

- Routes schema and read-only questions to `schema_assistant`
- Routes insert requests to `insert_assistant`
- Routes delete requests to `delete_assistant`
- Uses Neon MCP tools through a single shared MCP client session
- Executes routed tools sequentially to avoid MCP session conflicts

## Architecture

The CLI opens one Neon MCP client for the full application session and reuses the discovered MCP tools across all sub-agents.

- `database_agent.py` creates the top-level router agent
- `server/neon_mcp.py` builds the shared Neon MCP client
- `server/tools/schema_assistant.py` creates the read-only schema tool
- `server/tools/insert_assistant.py` creates the insert tool
- `server/tools/delete_assistant.py` creates the delete tool

This structure keeps the code simple and makes it easier to add more workflow-specific agents later without duplicating MCP connection setup.

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

```bash
python database_agent.py
```

At the prompt, enter a database request. Type `exit` to quit.

## Example prompts

- Look at `sample_prompt.txt` for more details


## Notes

- The top-level agent uses `SequentialToolExecutor` so routed tools do not compete for the same MCP session.
- Each assistant reuses the shared MCP tool list instead of creating its own client.
- This project is currently focused on schema inspection, inserts, and deletes.

## File overview

- `database_agent.py`: CLI entrypoint and top-level request router
- `server/neon_mcp.py`: Neon MCP client factory and environment loading
- `server/tools/schema_assistant.py`: factory for the schema/read-only tool
- `server/tools/insert_assistant.py`: factory for the insert tool
- `server/tools/delete_assistant.py`: factory for the delete tool
- `sample_prompt.txt`: sample multi-intent prompts for manual testing
