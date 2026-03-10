from strands import tool
from neon_mcp import BRANCH, DATABASE, PROJECT_ID, run_neon_agent


SCHEMA_ASSISTANT_SYSTEM_PROMPT = f"""
You are SchemaAssistant, responsible for running read-only queries on the database.

Use the available MCP tools to execute read-only SELECT queries and retrieve schema information:
- get_database_tables: List all tables
- describe_table_schema: Get table schema details
- run_sql: Execute SELECT queries only

Always query the actual database. Never fabricate schema information.
"""


SCHEMA_TOOL_FILTERS = {
    "allowed": [
        "get_database_tables",
        "describe_table_schema",
        "run_sql",
    ]
}


@tool
def schema_assistant(query: str) -> str:
    """
    Process and respond to read-only schema and data inspection queries.
    
    Args:
        query: A request for schema inspection or read-only data access
        
    Returns:
        Query results or schema details from the database
    """
    # Format the query to emphasize using MCP tools
    formatted_query = f"""Query the database using the available MCP tools to answer this request:

    {query}

    Required connection details:
    - Project ID: {PROJECT_ID}
    - Database: {DATABASE}
    - Branch: {BRANCH}

    Use only read-only queries. For SQL, execute SELECT statements only.
    Use the appropriate MCP tools (get_database_tables, describe_table_schema, or run_sql) to retrieve actual data from the database."""
    
    try:
        print("Routed to Schema Assistant")

        text_response = run_neon_agent(
            system_prompt=SCHEMA_ASSISTANT_SYSTEM_PROMPT,
            query=formatted_query,
            tool_filters=SCHEMA_TOOL_FILTERS,
            read_only=True,
        )

        if len(text_response) > 0:
            return text_response

        return "Unable to process your read-only schema query. Please provide a table name or a SELECT-style request."
    except Exception as e:
        return f"Error processing your schema query: {str(e)}"