from mcp import StdioServerParameters, stdio_client
from strands import Agent, tool
from strands.tools.mcp import MCPClient
import os
from dotenv import load_dotenv

load_dotenv()

project_id = os.environ["NEON_PROJECT_ID"]
database = os.environ["NEON_DATABASE"]
branch = os.environ["NEON_BRANCH"]
api_key = os.environ["NEON_API_KEY"]


SCHEMA_ASSISTANT_SYSTEM_PROMPT = f"""
You are SchemaAssistant, responsible for running read-only queries on the database.

Use the available MCP tools to execute read-only SELECT queries and retrieve schema information:
- mcp_neon_get_database_tables: List all tables
- mcp_neon_describe_table_schema: Get table schema details
- mcp_neon_run_sql: Execute SELECT queries only

Always query the actual database. Never fabricate schema information.
"""


@tool
def schema_assistant(query: str) -> str:
    """
    Process and respond to schema design and management queries.
    
    Args:
        query: A request for schema design, modification, or management assistance
        
    Returns:
        Schema guidance and technical recommendations with explanations
    """
    # Format the query to emphasize using MCP tools
    formatted_query = f"""Query the database using the available MCP tools to answer this request:

    {query}

    Required connection details:
    - Project ID: {project_id}
    - Database: {database}
    - Branch: {branch}

    Use the appropriate MCP tools (mcp_neon_get_database_tables, mcp_neon_describe_table_schema, or mcp_neon_run_sql) to retrieve actual data from the database."""
    
    try:
        print("Routed to Schema Assistant")

        mcp_client = MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                command="npx",
                args=[
                    "-y",
                    "mcp-remote@latest",
                    "https://mcp.neon.tech/mcp",
                    "--header",
                    f"Authorization: Bearer {api_key}"
                ]
            )
        )
    )
        schema_agent = Agent(
            system_prompt=SCHEMA_ASSISTANT_SYSTEM_PROMPT,
            tools=[mcp_client],
        )
        agent_response = schema_agent(formatted_query)
        text_response = str(agent_response)

        if len(text_response) > 0:
            return text_response

        return "Unable to process your schema query. Please provide details about the schema change, design, or management task you need help with."
    except Exception as e:
        # Return specific error message for schema processing
        return f"Error processing your schema query: {str(e)}"