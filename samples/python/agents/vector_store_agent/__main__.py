#!/usr/bin/env python3
"""
Vector Store Knowledge Agent - Main Entry Point

This file serves as the main entry point for the Vector Store Agent.
It initializes the A2A server with the vector store agent capabilities
and handles command-line configuration.
"""

import os
import click
import logging
from pathlib import Path
import sys

# This allows the module to be run directly with 'python -m' or 'uv run .'
# and properly find the A2A common modules
parent_dir = Path(__file__).parent.parent.parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from samples.python.agents.vector_store_agent.agent import VectorStoreAgent, run_server
from samples.python.agents.vector_store_agent.config import DEFAULT_HOST, DEFAULT_PORT, VECTOR_STORE_ID, DEFAULT_MODEL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host", default=DEFAULT_HOST, help="Host to run the server on")
@click.option("--port", default=DEFAULT_PORT, help="Port to run the server on")
def main(host, port):
    """Entry point for the Vector Store Knowledge Agent."""
    # Display startup information
    print("Starting Vector Store Agent server...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Vector Store ID: {VECTOR_STORE_ID or 'Not set (using mock mode)'}")
    print(f"Model: {DEFAULT_MODEL}")
    print("\nUse Ctrl+C to stop the server")
    print("\nYou can query this agent using an A2A compatible client, e.g.:")
    print(f"cd samples/python/hosts/cli && uv run . --agent http://localhost:{port}")
    
    # Start the server with configured host and port
    run_server(host=host, port=port)

if __name__ == "__main__":
    main()
