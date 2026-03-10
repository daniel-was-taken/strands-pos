# strands-pos

Small command-line database assistant built with Strands and Neon MCP.

## What this project does

- Routes read-only questions to `schema_assistant`
- Routes insert requests to `insert_assistant`
- Routes delete requests to `delete_assistant`
- Uses Neon MCP tools for database access

## Quick startup

### 1) Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Create your env file

```bash
cp .env.example .env
```

Fill in `.env` with your Neon values:

- `NEON_API_KEY`
- `NEON_PROJECT_ID`
- `NEON_DATABASE`
- `NEON_BRANCH`

`DATABASE_URL` is optional for this app.

### 4) Run the app

```bash
python database_agent.py
```

Type your request at the prompt.
Type `exit` to quit.

## Example prompts

- `List all tables`
- `Show schema for employees`
- `Insert a new employee` (It should specify the fields that need to be filled)
- `Delete employee where id = 101` (WIP: add confirmation to delete)

## Files

- `database_agent.py`: Main CLI and request router
- `schema_assistant.py`: Read-only schema and SELECT operations
- `insert_assistant.py`: Insert operations
- `delete_assistant.py`: Delete operations
- `neon_mcp.py`: MCP client setup and Neon config loading
