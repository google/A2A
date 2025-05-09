from typing import Any

from starlette.applications import Starlette

from a2a.server.app import A2AApplication
from a2a.server.request_handler import A2ARequestHandler
from a2a.types import AgentCard


class A2AServer:
    """A2A Server that runs a Starlette application."""

    def __init__(
        self, agent_card: AgentCard, request_handler: A2ARequestHandler
    ):
        self.agent_card = agent_card
        self.request_handler = request_handler

    def app(self, **kwargs: Any) -> Starlette:
        return A2AApplication(
            agent_card=self.agent_card, request_handler=self.request_handler
        ).build(**kwargs)

    def start(self, **kwargs: Any):
        import uvicorn

        uvicorn.run(self.app(), **kwargs)
