from agent_executor import HelloWorldAgentExecutor

from a2a.server import A2AServer, DefaultA2ARequestHandler
from a2a.types import (
    AgentAuthentication,
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)


if __name__ == '__main__':
    skill = AgentSkill(
        id='hello_world',
        name='Returns hello world',
        description='just returns hello world',
        tags=['hello world'],
        examples=['hi', 'hello world'],
    )

    agent_card = AgentCard(
        name='Hello World Agent',
        description='Just a hello world agent',
        url='http://localhost:9999/',
        version='1.0.0',
        defaultInputModes=['text'],
        defaultOutputModes=['text'],
        capabilities=AgentCapabilities(),
        skills=[skill],
        authentication=AgentAuthentication(schemes=['public']),
    )

    request_handler = DefaultA2ARequestHandler(
        agent_executor=HelloWorldAgentExecutor()
    )

    server = A2AServer(agent_card=agent_card, request_handler=request_handler)
    server.start(host='0.0.0.0', port=9999)
