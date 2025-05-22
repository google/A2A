import logging

from collections.abc import AsyncIterable

import httpx

from a2a_mcp.common.base_agent import BaseAgent
from a2a_mcp.common.utils import (
    config_logger,
    get_mcp_server_config,
    init_api_key,
)
from a2a_mcp.common.workflow import WorkflowGraph, WorkflowNode


logger = logging.getLogger(__name__)
config_logger(logger=logger)


class OrchestratorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name='Orchestrator Agent',
            description='Facilitate inter agent communication',
            content_types=['text', 'text/plain'],
        )
        self.graph = None

    async def stream(self, query, context_id) -> AsyncIterable[dict[str, any]]:
        logger.info(
            f'Running {self.agent_name} stream for session {context_id} - {query}'
        )

        if not query:
            raise ValueError('Query cannot be empty')
        start_node_id = None
        async with httpx.AsyncClient() as httpx_client:
            if not self.graph:
                self.graph = WorkflowGraph()
                planner_node = WorkflowNode(
                    task=query, node_key='planner', node_label='Planner'
                )
                # planner_node.client = planner_node.get_planner_resource(
                #    httpx_client=httpx_client
                # )
                self.graph.add_node(planner_node)
                start_node_id = planner_node.id
            elif self.graph.state == 'PAUSED':
                start_node_id = self.graph.paused_node_id

            async for chunk in self.graph.execute(
                httpx_client=httpx_client, start_node_id=start_node_id
            ):
                yield chunk
