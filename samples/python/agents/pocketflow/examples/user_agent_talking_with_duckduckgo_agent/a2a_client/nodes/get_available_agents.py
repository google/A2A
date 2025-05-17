import asyncio

from loguru import logger
from pocketflow import AsyncNode
from pocketflow_a2a.a2a_common.client import A2AClient
from pocketflow_a2a.a2a_common.types import (
    A2AClientHTTPError,
    A2AClientJSONError,
    AgentCard,
)

from a2a_client.prompt_templates import available_agents_template


class GetAvailableAgentsNode(AsyncNode):
    async def prep_async(self, shared):
        logger.info('📞 Enter GetAvailableAgentsNode')
        a2a_clients = shared['a2a_clients']
        return a2a_clients

    async def exec_async(self, a2a_clients: list[A2AClient]):
        return await asyncio.gather(
            *[a2a_client.get_agent_card() for a2a_client in a2a_clients]
        )

    async def exec_fallback_async(self, prep_res, exc):
        raise exc

    async def post_async(
        self,
        shared,
        prep_res,
        exec_res: list[AgentCard | A2AClientJSONError | A2AClientHTTPError],
    ) -> str:
        agents_list = [res for res in exec_res if isinstance(res, AgentCard)]
        if not agents_list:
            logger.info('🤷‍♂️ No agents found')
            shared['agents_list'] = []
            shared['available_agents_prompt'] = None
        else:
            logger.info(f'💬 Found {len(agents_list)} agents')
            shared['agents_list'] = agents_list
            shared['available_agents_prompt'] = (
                available_agents_template.render(
                    agents=[agent.model_dump() for agent in agents_list]
                )
            )
        return 'agent_selector'


if __name__ == '__main__':
    import asyncio

    get_available_agents_node = GetAvailableAgentsNode()
    shared = {
        'a2a_clients': [A2AClient(url='http://localhost:10003')],
    }
    print(asyncio.run(get_available_agents_node.run_async(shared)))
