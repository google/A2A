# type: ignore
from abc import ABC, abstractmethod
from typing import List

from pydantic import BaseModel, Field

from a2a_mcp.common.types import AgentResponse


class BaseAgent(BaseModel, ABC):
    model_config = {
        "arbitrary_types_allowed": True,
        "extra": "allow",
    }

    agent_name: str = Field(
        description="The name of the agent.",
    )

    description: str = Field(
        description="A brief description of the agent's purpose.",
    )

    content_types: List[str] = Field(description="Supported content types.")

    @abstractmethod
    async def invoke(self, query, session_id) -> str:
        pass

    @abstractmethod
    async def get_agent_response() -> AgentResponse:
        pass
