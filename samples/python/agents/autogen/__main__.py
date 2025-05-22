"""
Main entry point for the A2A Weather Agent server.

This script initializes and starts the A2A server with the weather agent.
"""

from common.server import A2AServer
from common.types import (
    AgentCard, AgentCapabilities, AgentSkill, MissingAPIKeyError
)
from task_manager import WeatherTaskManager
from agent import WeatherAgent
import click
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


@click.command()
@click.option("--host", default="localhost", help="Host to bind the server to")
@click.option("--port", default=10000, type=int, help="Port to run the server on")
def main(host, port):
    """Start the A2A Weather Agent server."""
    try:
        # Check for API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise MissingAPIKeyError("OPENAI_API_KEY environment variable not set.")
        
        # Define capabilities and skills
        capabilities = AgentCapabilities(streaming=True)
        skill = AgentSkill(
            id="weather_information",
            name="Weather Information",
            description="Provides current weather information for locations around the world.",
            tags=["weather", "forecast"],
            examples=[
                "What's the weather like in New York?",
                "Is it raining in London?",
                "Temperature in Tokyo",
                "How's the weather in Paris?",
                "What's the humidity in Sydney?",
            ],
        )
        
        # Create agent card
        agent_card = AgentCard(
            name="Weather Assistant",
            description="An AutoGen-powered weather assistant that can provide current weather information.",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=WeatherAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=WeatherAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )
        
        # Create task manager
        task_manager = WeatherTaskManager(api_key=api_key)
        
        # Create and start the server
        server = A2AServer(
            agent_card=agent_card,
            task_manager=task_manager,
            host=host,
            port=port,
        )
        
        logger.info(f"Starting A2A server for AutoGen Weather Assistant on {host}:{port}")
        server.start()
    
    except MissingAPIKeyError as e:
        logger.error(f"Error: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)


if __name__ == "__main__":
    main()