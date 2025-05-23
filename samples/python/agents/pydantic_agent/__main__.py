from a2a.server import A2AServer
from a2a.agent import A2AAgent
from samples.python.agents.pydantic_agent.agent import SummarizerAgent

if __name__ == "__main__":
    agent = SummarizerAgent()
    a2a_agent = A2AAgent(agent=agent)
    server = A2AServer(agents=[a2a_agent])
    server.run()