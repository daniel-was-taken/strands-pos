from strands import tool

from neon_mcp import BRANCH, DATABASE, PROJECT_ID, run_neon_agent


DELETE_ASSISTANT_SYSTEM_PROMPT = f"""
You are DeleteAssistant, responsible for delete operations on the database.

You may inspect schema details before deleting data.
Use the available MCP tools for these tasks:
- get_database_tables: List all tables
- describe_table_schema: Get table schema details
- run_sql: Execute DELETE statements and follow-up SELECT checks when needed

Only perform delete operations or read-only checks needed to support a delete.
Do not insert, update, alter, create, or drop database objects.

Always query the actual database. Never fabricate schema information.
"""


DELETE_TOOL_FILTERS = {
    "allowed": [
        "get_database_tables",
        "describe_table_schema",
        "run_sql",
    ]
}


@tool
def delete_assistant(query: str) -> str:
    """Process and respond to delete requests."""
    formatted_query = f"""Handle this database delete request using the available MCP tools:

    {query}

    Required connection details:
    - Project ID: {PROJECT_ID}
    - Database: {DATABASE}
    - Branch: {BRANCH}

    If needed, inspect the target table first.
    Only execute DELETE statements and read-only verification queries."""

    try:
        print("Routed to Delete Assistant")

        text_response = run_neon_agent(
            system_prompt=DELETE_ASSISTANT_SYSTEM_PROMPT,
            query=formatted_query,
            tool_filters=DELETE_TOOL_FILTERS,
        )

        if len(text_response) > 0:
            return text_response

        return "Unable to process your delete request. Please provide the target table and the delete condition."
    except Exception as e:
        return f"Error processing your delete request: {str(e)}"