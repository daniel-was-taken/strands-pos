#!/usr/bin/env python3
"""
Database Management Strands Agent

A specialized Strands agent that orchestrates database schema and management
tasks through sub-agents sharing a single MCP connection.
"""

import traceback

from strands import Agent
from strands.tools.executors import SequentialToolExecutor

from server.neon_mcp import create_neon_mcp_client
from server.tools.delete_assistant import create_delete_tool
from server.tools.insert_assistant import create_insert_tool
from server.tools.schema_assistant import create_schema_tool

DATABASE_SYSTEM_PROMPT = """
You are DBControl, a database management orchestrator.

You are responsible for calling the necessary tools to handle database-related requests.
Use these tools:
- schema_assistant for read-only schema and SELECT queries
- insert_assistant for insert requests
- delete_assistant for delete requests

Keep responses clear and actionable.
"""


def main():
    mcp_client = create_neon_mcp_client()

    with mcp_client:
        mcp_tools = mcp_client.list_tools_sync()
        # for t in mcp_tools:  # Debug: print available tools
        #     print(t.tool_name)
        database_agent = Agent(
            system_prompt=DATABASE_SYSTEM_PROMPT,
            tool_executor=SequentialToolExecutor(),
            tools=[
                create_schema_tool(mcp_tools),
                create_insert_tool(mcp_tools),
                create_delete_tool(mcp_tools),
            ],
        )

        print("\nDatabase Management Strands Agent\n")
        print("Ask a database question, and I'll route it to the right assistant.")
        print("Type 'exit' to quit.")

        while True:
            try:
                user_input = input("\n> ")
                if user_input.lower() == "exit":
                    print("\nGoodbye!")
                    break

                response = database_agent(user_input)
                print(str(response))

            except KeyboardInterrupt:
                print("\n\nExecution interrupted. Exiting...")
                break
            except Exception:
                traceback.print_exc()
                print("Please try asking a different question.")


if __name__ == "__main__":
    main()