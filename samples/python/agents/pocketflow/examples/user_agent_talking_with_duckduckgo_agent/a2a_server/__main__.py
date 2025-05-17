import logging

import click

# Import from the common code you copied
from pocketflow_a2a.a2a_common.server import A2AServer
from pocketflow_a2a.a2a_common.types import (AgentCapabilities, AgentCard,
                                             AgentSkill, MissingAPIKeyError)

# Import your custom TaskManager (which now imports from your original files)
from .task_manager import PocketFlowTaskManager

# --- Configure logging ---
# Set level to INFO to see server start, requests, responses
# Set level to DEBUG to see raw response bodies from client
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
# Optionally silence overly verbose libraries
# logging.getLogger("httpx").setLevel(logging.WARNING)
# logging.getLogger("httpcore").setLevel(logging.WARNING)
# logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=10003)  # Use a different port from other agents
def main(host, port):
    """Starts the PocketFlow A2A Agent server."""
    try:
        # --- Define the Agent Card ---
        capabilities = AgentCapabilities(
            streaming=False,  # This simple implementation is synchronous
            pushNotifications=False,
            stateTransitionHistory=False,  # PocketFlow state isn't exposed via A2A history  # noqa: E501
        )
        skill = AgentSkill(
            id="web_research_qa",
            name="Web Research and Answering",
            description="Answers questions using web search results when necessary.",
            tags=["research", "qa", "web search"],
            examples=[
                "Who won the Nobel Prize in Physics 2024?",
                "What is quantum computing?",
                "Summarize the latest news about AI.",
            ],
            # Input/Output modes defined in the TaskManager
            inputModes=PocketFlowTaskManager.SUPPORTED_CONTENT_TYPES,
            outputModes=PocketFlowTaskManager.SUPPORTED_CONTENT_TYPES,
        )
        agent_card = AgentCard(
            name="PocketFlow Research Agent (A2A Wrapped)",
            description="A simple research agent based on PocketFlow, made accessible via A2A.",  # noqa: E501
            url=f"http://{host}:{port}/",  # The endpoint A2A clients will use
            version="0.1.0-a2a",
            capabilities=capabilities,
            skills=[skill],
            # Assuming no specific provider or auth for this example
            provider=None,
            authentication=None,
            defaultInputModes=PocketFlowTaskManager.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=PocketFlowTaskManager.SUPPORTED_CONTENT_TYPES,
        )

        # --- Initialize and Start Server ---
        task_manager = PocketFlowTaskManager()  # Instantiate your custom manager
        server = A2AServer(
            agent_card=agent_card,
            task_manager=task_manager,
            host=host,
            port=port,
        )

        logger.info(f"Starting PocketFlow A2A server on http://{host}:{port}")
        server.start()

    except MissingAPIKeyError as e:
        logger.error(f"Configuration Error: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}", exc_info=True)
        exit(1)


if __name__ == "__main__":
    main()
