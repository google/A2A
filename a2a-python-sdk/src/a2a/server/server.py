import logging

from typing import Any

from starlette.applications import Starlette

from a2a.server.app import A2AApplication
from a2a.server.request_handlers.request_handler import A2ARequestHandler
from a2a.types import AgentCard


logger = logging.getLogger(__name__)


class A2AServer:
    """A2A Server that runs a Starlette application."""

    def __init__(
        self, agent_card: AgentCard, request_handler: A2ARequestHandler
    ):
        """Initializes the A2AServer."""
        self.agent_card = agent_card
        self.request_handler = request_handler

    def app(self, **kwargs: Any) -> Starlette:
        """Builds and returns the Starlette application instance."""
        logger.info('Building A2A Application instance')
        return A2AApplication(
            agent_card=self.agent_card, request_handler=self.request_handler
        ).build(**kwargs)

    def start(self, **kwargs: Any):
        """Starts the server using Uvicorn."""
        logger.info('Starting A2A Server')
        import uvicorn

        uvicorn.run(self.app(), **kwargs)
