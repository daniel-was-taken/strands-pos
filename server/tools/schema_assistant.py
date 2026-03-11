from strands import Agent, tool
from server.neon_mcp import BRANCH, DATABASE, PROJECT_ID


SCHEMA_SYSTEM_PROMPT = """
You are SchemaAssistant, responsible for running read-only queries on the database.

Use the available MCP tools to execute read-only SELECT queries and retrieve schema information:
- get_database_tables: List all tables
- describe_table_schema: Get table schema details
- run_sql: Execute SELECT queries only

Always query the actual database. Never fabricate schema information.
"""


def create_schema_tool(mcp_tools):
    agent = Agent(system_prompt=SCHEMA_SYSTEM_PROMPT, tools=mcp_tools)

    @tool
    def schema_assistant(query: str) -> str:
        """Process and respond to read-only schema and data inspection queries.

        Args:
            query: A request for schema inspection or read-only data access

        Returns:
            Query results or schema details from the database
        """
        formatted_query = f"""Query the database using the available MCP tools to answer this request:

        {query}

        Required connection details:
        - Project ID: {PROJECT_ID}
        - Database: {DATABASE}
        - Branch: {BRANCH}

        Use only read-only queries. For SQL, execute SELECT statements only."""

        print("Routed to Schema Assistant")
        return str(agent(formatted_query))

    return schema_assistant