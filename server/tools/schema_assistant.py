from strands import Agent, tool

from server.model import create_model
from server.neon_mcp import BRANCH, DATABASE, PROJECT_ID


SCHEMA_SYSTEM_PROMPT = """
You are SchemaAssistant, responsible for running read-only queries on the database.

Use the available MCP tools to execute read-only SELECT queries and retrieve schema information:
- get_database_tables: List all tables
- describe_table_schema: Get table schema details
- run_sql: Execute SELECT queries only

Always query the actual database. Never fabricate schema information.
"""


def create_schema_tool(mcp_client):
    @tool
    def schema_assistant(query: str) -> str:
        """Process and respond to read-only schema and data inspection queries.

        Args:
            query: A request for schema inspection or read-only data access

        Returns:
            Query results or schema details from the database
        """
        formatted_query = (
            "Please answer this database schema request, "
            "showing all steps and explaining clearly: "
            f"{query}\n\n"
            f"Required connection details:\n"
            f"- Project ID: {PROJECT_ID}\n"
            f"- Database: {DATABASE}\n"
            f"- Branch: {BRANCH}\n\n"
            "Use only read-only queries. For SQL, execute SELECT statements only."
        )

        print("Routed to Schema Assistant")
        agent = Agent(
            model=create_model(),
            system_prompt=SCHEMA_SYSTEM_PROMPT,
            tools=[mcp_client],
        )
        return str(agent(formatted_query))

    return schema_assistant
