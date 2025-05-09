"""
A2A-MCP Connector Agent - Main entry point

This agent serves as a bridge between A2A (Agent-to-Agent) protocol and MCP (Model Context Protocol),
providing an intuitive interface for connecting to and using MCP tools through A2A.
"""

import os
import sys
import click
import logging
from dotenv import load_dotenv

# Add the parent directory to the Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill, MissingAPIKeyError
from agent import A2AMCPConnectorAgent
from task_manager import AgentTaskManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=10004)
def main(host, port):
    try:
        # Check for API key only if Vertex AI is not configured
        if not os.getenv("GOOGLE_GENAI_USE_VERTEXAI") == "TRUE":
            if not os.getenv("GOOGLE_API_KEY"):
                raise MissingAPIKeyError(
                    "GOOGLE_API_KEY environment variable not set and GOOGLE_GENAI_USE_VERTEXAI is not TRUE."
                )
        
        # Define agent capabilities
        capabilities = AgentCapabilities(streaming=True, pushNotifications=False)
        
        # Define agent skills
        register_skill = AgentSkill(
            id="register_mcp_tool",
            name="Register MCP Tool",
            description="Register a new MCP tool with the connector",
            tags=["mcp", "registration", "setup"],
            examples=["Register a new MCP tool at http://localhost:8000/my-tool", "Add a YouTube transcription tool"],
            inputModes=["text"],
            outputModes=["text"],
        )
        
        list_skill = AgentSkill(
            id="list_mcp_tools",
            name="List MCP Tools",
            description="List all registered MCP tools",
            tags=["mcp", "tools", "list"],
            examples=["Show all available MCP tools", "What tools are registered?"],
            inputModes=["text"],
            outputModes=["text"],
        )
        
        call_skill = AgentSkill(
            id="call_mcp_tool",
            name="Call MCP Tool",
            description="Call a registered MCP tool with input data",
            tags=["mcp", "tools", "execution"],
            examples=["Use the weather tool to check the forecast", "Run YouTube transcription on this video"],
            inputModes=["text", "application/json"],
            outputModes=["text", "application/json"],
        )
        
        # Create the agent card
        agent_card = AgentCard(
            name="A2A-MCP Connector",
            description=(
                "A connector agent that bridges A2A and MCP protocols, "
                "allowing easy registration and interaction with MCP tools."
            ),
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=A2AMCPConnectorAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=A2AMCPConnectorAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[register_skill, list_skill, call_skill],
        )
        
        # Create the agent instance
        agent = A2AMCPConnectorAgent()
        
        # Create and start the A2A server
        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(agent=agent),
            host=host,
            port=port,
        )
        
        logger.info(f"Starting A2A-MCP Connector Agent on http://{host}:{port}/")
        server.start()
        
    except MissingAPIKeyError as e:
        logger.error(f"Error: {e}")
        logger.info("Please set the GOOGLE_API_KEY environment variable or configure GOOGLE_GENAI_USE_VERTEXAI")
        exit(1)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)
    
    
if __name__ == "__main__":
    main()