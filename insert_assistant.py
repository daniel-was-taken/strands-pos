from strands import tool

from neon_mcp import BRANCH, DATABASE, PROJECT_ID, run_neon_agent


INSERT_ASSISTANT_SYSTEM_PROMPT = f"""
You are InsertAssistant, responsible for insert operations on the database.

You may inspect schema details before inserting data.
Use the available MCP tools for these tasks:
- get_database_tables: List all tables
- describe_table_schema: Get table schema details
- run_sql: Execute INSERT statements and follow-up SELECT checks when needed

Only perform insert operations or read-only checks needed to support an insert.
Do not update, delete, alter, create, or drop database objects.

Always query the actual database. Never fabricate schema information.
"""


INSERT_TOOL_FILTERS = {
    "allowed": [
        "get_database_tables",
        "describe_table_schema",
        "run_sql",
    ]
}


@tool
def insert_assistant(query: str) -> str:
    """Process and respond to insert requests."""
    formatted_query = f"""Handle this database insert request using the available MCP tools:

    {query}

    Required connection details:
    - Project ID: {PROJECT_ID}
    - Database: {DATABASE}
    - Branch: {BRANCH}

    If needed, inspect the target table first.
    Only execute INSERT statements and read-only verification queries."""

    try:
        print("Routed to Insert Assistant")

        text_response = run_neon_agent(
            system_prompt=INSERT_ASSISTANT_SYSTEM_PROMPT,
            query=formatted_query,
            tool_filters=INSERT_TOOL_FILTERS,
        )

        if len(text_response) > 0:
            return text_response

        return "Unable to process your insert request. Please provide the target table and the data to insert."
    except Exception as e:
        return f"Error processing your insert request: {str(e)}"