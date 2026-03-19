#!/usr/bin/env python3
"""
Database Management Strands Agent — CLI entrypoint.

Run:  python database_agent.py

A specialized Strands agent that orchestrates database schema and management
tasks through sub-agents sharing a single MCP connection.
"""

import logging

from dotenv import load_dotenv

load_dotenv()

from server.orchestrator import DatabaseOrchestrator


def main():
    orchestrator = DatabaseOrchestrator()

    print("\nDatabase Management Strands Agent\n")
    print("Ask a database question, and I'll route it to the right assistant.")
    print("Type 'exit' to quit.")

    while True:
        try:
            user_input = input("\n> ")
            if user_input.lower() == "exit":
                print("\nGoodbye!")
                break

            response = orchestrator.handle_cli_query(user_input)
            print(str(response))

        except KeyboardInterrupt:
            print("\n\nExecution interrupted. Exiting...")
            break
        except Exception:
            logging.exception("Query failed")
            print("Please try asking a different question.")


if __name__ == "__main__":
    main()