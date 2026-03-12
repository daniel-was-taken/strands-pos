from strands import Agent, tool
from server.neon_mcp import BRANCH, DATABASE, PROJECT_ID


INSERT_SYSTEM_PROMPT = """
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


def create_insert_tool(mcp_client):
    @tool
    def insert_assistant(query: str) -> str:
        """Process and respond to insert requests."""
        formatted_query = (
            "Handle this database insert request, "
            "inspecting the target table first if needed: "
            f"{query}\n\n"
            f"Required connection details:\n"
            f"- Project ID: {PROJECT_ID}\n"
            f"- Database: {DATABASE}\n"
            f"- Branch: {BRANCH}\n\n"
            "Only execute INSERT statements and read-only verification queries."
        )

        print("Routed to Insert Assistant")
        agent = Agent(
            system_prompt=INSERT_SYSTEM_PROMPT,
            tools=[mcp_client],
        )
        return str(agent(formatted_query))

    return insert_assistant