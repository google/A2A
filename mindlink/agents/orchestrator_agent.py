from mindlink.models import AgentCard, Tool
from typing import List, Dict
import re


class OrchestratorAgent:
    """
    An agent responsible for directing user requests to the appropriate destination:
    user notes, the user's personal agent, or external A2A agents.
    """

    def __init__(self, user_agent_card: AgentCard, notes_tool: Tool, external_agent_cards: List[AgentCard] = None):
        """
        Initializes the OrchestratorAgent.

        Args:
            user_agent_card: The AgentCard of the user's personal agent.
            notes_tool: a Tool to acces to the user notes.
            external_agent_cards: A list of AgentCards for external A2A agents.
        """
        self.user_agent_card = user_agent_card
        self.notes_tool = notes_tool
        self.external_agent_cards = external_agent_cards or []

    def route_request(self, user_request: str) -> Dict:
        """
        Routes a user request to the appropriate destination based on the request content.

        Args:
            user_request: The user's request as a string.

        Returns:
            A dictionary containing information about where the request should be routed, with keys:
            - "destination": One of "user_agent", "notes", or "external_agent".
            - "agent_card" (optional): The AgentCard of the external agent if the destination is "external_agent".
            - "notes_tool": (optional): The tool to access the user notes.
            - "prompt": The user request (or a modified version) to be passed to the destination.
        """
        if self._is_notes_related(user_request):
            return {
                "destination": "notes",
                "notes_tool": self.notes_tool,
                "prompt": user_request
            }

        if self._is_user_agent_related(user_request):
            return {
                "destination": "user_agent",
                "prompt": user_request
            }

        external_agent = self._find_matching_external_agent(user_request)
        if external_agent:
            return {
                "destination": "external_agent",
                "agent_card": external_agent,
                "prompt": user_request
            }

        return {
            "destination": "user_agent",
            "prompt": user_request
        }

    def _is_notes_related(self, user_request: str) -> bool:
        """
        Checks if the user request is related to the user's notes.

        Args:
            user_request: The user's request as a string.

        Returns:
            True if the request is related to notes, False otherwise.
        """
        keywords = ["notes", "remember", "record", "client notes"]
        return any(keyword in user_request.lower() for keyword in keywords)

    def _is_user_agent_related(self, user_request: str) -> bool:
        """
        Checks if the user request is intended for the user's personal agent.
        """
        keywords = ["i", "my", "me", "myself"]
        return any(keyword in user_request.lower() for keyword in keywords)

    def _find_matching_external_agent(self, user_request: str) -> AgentCard:
        """
        Finds an external agent that is a good match for the user request.

        Args:
            user_request: The user's request as a string.

        Returns:
            The AgentCard of the best-matching external agent, or None if no good match is found.
        """
        for agent_card in self.external_agent_cards:
            if re.search(agent_card.description, user_request, re.IGNORECASE):
                return agent_card
        return None