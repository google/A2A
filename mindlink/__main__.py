import uuid
import os
from mindlink.agents.user_agent import UserAgent
from mindlink.core.a2a_server import A2AServer
from mindlink.core.agent_card_generator import AgentCardGenerator
from mindlink.models import User
from a2a.agent import A2AAgent

def create_user_and_start_server(user_id: int, initial_knowledge: str):
    """Creates a user with a default agent and starts a server for that agent."""

    # Create the user
    user = User(
        id=user_id,
        name=f"User {user_id}",
        tools=[],  # No tools initially
        knowledge=initial_knowledge,
        agent_card_url=""
    )

    # Create the user agent
    user_agent = UserAgent(user_id=user.id, initial_knowledge=user.knowledge)

    # Generate agent card
    agent_card_generator = AgentCardGenerator()
    agent_card = agent_card_generator.generate(
        agent_name=f"UserAgent {user.id}",
        description=f"Agent for User {user.id}",
        capabilities=[]
    )

    # Create A2A agent
    a2a_agent = A2AAgent(agent=user_agent, agent_card=agent_card)

    # Start the server
    server = A2AServer(agents=[a2a_agent])
    server.run()

    # Update agent card url
    agent_card_url = f"{server.base_url}/agent_card/{a2a_agent.agent_id}"
    user.agent_card_url = agent_card_url

    print(f"User ID: {user.id}")
    print(f"Agent Card URL: {user.agent_card_url}")


if __name__ == "__main__":
    initial_knowledge = "I am a psycologist and this is my initial knowledge."
    create_user_and_start_server(user_id=1, initial_knowledge=initial_knowledge)