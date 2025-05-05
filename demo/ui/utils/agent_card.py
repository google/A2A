import requests

from common.types import AgentCard


def get_agent_card(remote_agent_address: str) -> AgentCard:
    """Get the agent card."""
    agent_card = requests.get(
        f'http://{remote_agent_address}/.well-known/agent.json'
    )
    return AgentCard(**agent_card.json())
