import os
from typing import List, Dict
from pydantic import BaseModel, Field
from pydantic_ai import AICallable
from mindlink.models import Tool, AgentCard
from a2a.agent import A2AAgent

class UserAgent(BaseModel):
    """
    Represents a personalized AI agent for a psychologist.
    """
    name: str = Field(..., description="The name of the user agent")
    description: str = Field(..., description="A description of the user agent")
    initial_knowledge: str = Field(..., description="Initial knowledge base for the agent")
    tools: List[Tool] = Field(default_factory=list, description="List of tools available to the agent")
    api_key: str = Field(default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", ""), description="API key for Claude 3")
    agent_card: AgentCard = Field(default=None, description="The agent card for this agent.")

    def __init__(self, **data):
        super().__init__(**data)
        self.agent_card = self.generate_agent_card()

    def generate_agent_card(self) -> AgentCard:
        """
        Generates the AgentCard for this user agent.
        """
        capabilities = [tool.name for tool in self.tools]
        agent_card = AgentCard(
            name=self.name,
            description=self.description,
            capabilities=capabilities,
        )
        return agent_card

    @AICallable(api_key_field="api_key", system_prompt_template="""
        You are a helpful AI assistant specialized in psychology. 
        You have access to the following initial knowledge: {initial_knowledge}.
        You also have access to the following tools: {tools}.
        Use the tools when the prompt requires it.
    """)
    def process_prompt(self, prompt: str) -> str:
        """
        Processes a prompt and returns a response, potentially using tools.

        Args:
            prompt: The user's prompt.

        Returns:
            A response to the prompt.
        """
        ...