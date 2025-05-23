import json
from typing import List, Dict

class AgentCardGenerator:
    def generate(self, agent_name: str, description: str, capabilities: List[Dict]) -> str:
        agent_card = {
            "agent_id": agent_name,
            "description": description,
            "methods": capabilities,
            "endpoint": f"http://localhost:8080/agents/{agent_name}",  # Default endpoint for now
        }
        return json.dumps(agent_card, indent=4)