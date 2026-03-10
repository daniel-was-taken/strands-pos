#!/usr/bin/env python3
"""
# Database Management Strands Agent

A specialized Strands agent that orchestrates database schema and management
tasks through tools at its disposal.
"""

from strands import Agent

from delete_assistant import delete_assistant
from insert_assistant import insert_assistant
from schema_assistant import schema_assistant


# Define a focused system prompt for database management
DATABASE_SYSTEM_PROMPT = """
You are DBControl, a database management orchestrator.

You are responsible for calling the necessary tools to handle database-related requests.
Use these tools:
- schema_assistant for read-only schema and SELECT queries
- insert_assistant for insert requests
- delete_assistant for delete requests

Keep responses clear and actionable.
"""

# Create a file-focused agent with selected tools
database_agent = Agent(
    system_prompt=DATABASE_SYSTEM_PROMPT,
    callback_handler=None,
    tools=[schema_assistant, insert_assistant, delete_assistant],
)


# Example usage
if __name__ == "__main__":
    print("\nDatabase Management Strands Agent\n")
    print("Ask a database question, and I'll route it to the right assistant.")
    print("Type 'exit' to quit.")

    # Interactive loop
    while True:
        try:
            user_input = input("\n> ")
            if user_input.lower() == "exit":
                print("\nGoodbye! 👋")
                break

            response = database_agent(
                user_input, 
            )
            
            # Extract and print only the relevant content from the specialized agent's response
            content = str(response)
            print(content)
            
        except KeyboardInterrupt:
            print("\n\nExecution interrupted. Exiting...")
            break
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            print("Please try asking a different question.")