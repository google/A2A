"""This file serves as the main entry point for the application.

It initializes the A2A server, defines the agent's capabilities,
and starts the server to handle incoming requests.
"""

from agent import ImageGenerationAgent
import click
from common.server import A2AServer
from common.types import AgentCapabilities, AgentCard, AgentSkill, MissingAPIKeyError
import logging
import os
from task_manager import AgentTaskManager
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=10001)
def main(host, port):
  """Entry point for the A2A + CrewAI Image generation sample."""
  try:
    if not os.getenv("GOOGLE_API_KEY"):
        raise MissingAPIKeyError("GOOGLE_API_KEY environment variable not set.")

    capabilities = AgentCapabilities(streaming=False)
    skill = AgentSkill(
        id="image_generator",
        name="Image Generator",
        description=(
            "Generate stunning, high-quality images on demand and leverage"
            " powerful editing capabilities to modify, enhance, or completely"
            " transform visuals."
        ),
        tags=["generate image", "edit image"],
        examples=["Generate a photorealistic image of raspberry lemonade"],
    )

    agent_card = AgentCard(
        name="Image Generator Agent",
        description=(
            "Generate stunning, high-quality images on demand and leverage"
            " powerful editing capabilities to modify, enhance, or completely"
            " transform visuals."
        ),
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=ImageGenerationAgent.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=ImageGenerationAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[skill],
    )

    server = A2AServer(
        agent_card=agent_card,
        task_manager=AgentTaskManager(agent=ImageGenerationAgent()),
        host=host,
        port=port,
    )
    logger.info(f"Starting server on {host}:{port}")
    server.start()
  except MissingAPIKeyError as e:
    logger.error(f"Error: {e}")
    exit(1)
  except Exception as e:
    logger.error(f"An error occurred during server startup: {e}")
    exit(1)


if __name__ == "__main__":
  main()
