from strands import Agent, tool

from server.model import create_model
from server.neon_mcp import BRANCH, DATABASE, PROJECT_ID


DELETE_SYSTEM_PROMPT = """
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


def create_delete_tool(mcp_client):
    @tool
    def delete_assistant(query: str) -> str:
        """Process and respond to delete requests."""
        formatted_query = (
            "Handle this database delete request, "
            "inspecting the target table first if needed: "
            f"{query}\n\n"
            f"Required connection details:\n"
            f"- Project ID: {PROJECT_ID}\n"
            f"- Database: {DATABASE}\n"
            f"- Branch: {BRANCH}\n\n"
            "Only execute DELETE statements and read-only verification queries."
        )

        print("Routed to Delete Assistant")
        agent = Agent(
            model=create_model(),
            system_prompt=DELETE_SYSTEM_PROMPT,
            tools=[mcp_client],
        )
        return str(agent(formatted_query))

    return delete_assistant
