import asyncio
import json
import logging
import traceback
import uuid

from collections.abc import AsyncIterable
from uuid import uuid4

import httpx
import networkx as nx

from a2a.client import A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendStreamingMessageRequest,
    SendStreamingMessageSuccessResponse,
    Task,
    TaskState,
    TaskStatusUpdateEvent,
)
from a2a_mcp.common.utils import (
    config_logger,
    get_mcp_server_config,
    init_api_key,
)
from a2a_mcp.mcp import client


logger = logging.getLogger(__name__)
config_logger(logger)


class WorkflowNode:
    def __init__(
        self,
        task: str,
        node_key: str | None = None,
        node_label: str | None = None,
    ):
        self.id = str(uuid.uuid4())
        self.node_key = node_key
        self.node_label = node_label
        self.client = None
        self.task = task
        self.results = None
        self.state = 'READY'

    async def get_planner_resource(
        self, httpx_client: httpx.AsyncClient
    ) -> A2AClient | None:
        logger.info(f'Getting resource for node {self.id}')
        config = get_mcp_server_config()
        async with client.init_session(
            config.host, config.port, config.transport
        ) as session:
            response = await client.find_resource(
                session, 'resource://agent_cards/planner_agent'
            )
            data = json.loads(response.contents[0].text)
            agent_card = AgentCard(**data['agent_card'][0])
            a2a_client = A2AClient(httpx_client, agent_card)
            logger.info(f'Agent Card {a2a_client.url}')
            return a2a_client

    async def find_agent_for_task(
        self, httpx_client: httpx.AsyncClient
    ) -> A2AClient | None:
        logger.info(f'Find agent for task - {self.task}')
        config = get_mcp_server_config()
        async with client.init_session(
            config.host, config.port, config.transport
        ) as session:
            result = await client.find_agent(session, self.task)
            agent_card_json = json.loads(result.content[0].text)
            logger.debug(f'Found agent {agent_card_json} for task {self.task}')
            agent_card = AgentCard(**agent_card_json)
            a2a_client = A2AClient(httpx_client, agent_card)
            logger.info(f'Agent Card {a2a_client.url}')
            return a2a_client

    async def execute(
        self, httpx_client: httpx.AsyncClient
    ) -> AsyncIterable[dict[str, any]]:
        logger.info(f'Executing node {self.id}')
        if self.node_key == 'planner':
            self.client = await self.get_planner_resource(httpx_client)
        else:
            self.client = await self.find_agent_for_task(httpx_client)
        payload: dict[str, any] = {
            'message': {
                'role': 'user',
                'parts': [{'kind': 'text', 'text': self.task}],
                'messageId': uuid4().hex,
            },
        }
        request = SendStreamingMessageRequest(
            params=MessageSendParams(**payload)
        )
        response_stream = self.client.send_message_streaming(request)
        async for chunk in response_stream:
            yield chunk


class WorkflowGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.nodes = {}
        self.latest_node = None
        self.node_type = None
        self.state = 'INITIALIZED'
        self.paused_node_id = None

    def add_node(self, node) -> None:
        logger.info(f'Adding node {node.id}')
        self.graph.add_node(node.id)
        self.nodes[node.id] = node
        self.latest_node = node.id

    def add_edge(self, from_node_id: str, to_node_id: str) -> None:
        if from_node_id not in self.nodes or to_node_id not in self.nodes:
            raise ValueError('Invalid node IDs')

        self.graph.add_edge(from_node_id, to_node_id)

    def add_after_end(self, node) -> None:
        self.graph.add_node(node.id)
        self.nodes[node.id] = node
        self.add_edge(self.latest_node.id, node.id)
        self.latest_node = node.id

    async def execute(
        self, httpx_client: httpx.AsyncClient, start_node_id: str = None
    ) -> AsyncIterable[dict[str, any]]:
        logger.info('Executing workflow graph')
        if not start_node_id or start_node_id not in self.nodes:
            start_nodes = [n for n, d in self.graph.in_degree() if d == 0]
        else:
            start_nodes = [self.nodes[start_node_id].id]

        applicable_graph = set()

        for node_id in start_nodes:
            applicable_graph.add(node_id)
            applicable_graph.update(nx.descendants(self.graph, node_id))

        complete_graph = list(nx.topological_sort(self.graph))
        sub_graph = [n for n in complete_graph if n in applicable_graph]

        self.state = 'RUNNING'
        for node_id in sub_graph:
            node = self.nodes[node_id]
            node.state = 'RUNNING'
            async for chunk in node.execute(httpx_client):
                if (
                    node.state != 'PAUSED'
                    and isinstance(
                        chunk.root, SendStreamingMessageSuccessResponse
                    )
                    and isinstance(chunk.root.result, TaskStatusUpdateEvent)
                ):
                    task_status_event = chunk.root.result
                    context_id = task_status_event.contextId
                    if (
                        task_status_event.status.state
                        == TaskState.input_required
                        and context_id
                    ):
                        node.state = 'PAUSED'
                        self.state = 'PAUSED'
                        self.paused_node_id = node.id
                    yield chunk
            if self.state == 'PAUSED':
                break
            if node.state == 'RUNNING':
                node.state = 'COMPLETED'
        if self.state == 'RUNNING':
            self.state = 'COMPLETED'


async def main():
    node_1 = WorkflowNode(task='How is the Jane today')
    node_2 = WorkflowNode(task='Book return tickets to London')
    graph = WorkflowGraph()
    graph.add_node(node_1)
    graph.add_node(node_2)
    graph.add_edge(node_1.id, node_2.id)
    async with httpx.AsyncClient() as httpx_client:
        async for result in graph.execute(httpx_client):
            print(result)
    print(graph.state)


if __name__ == '__main__':
    asyncio.run(main())
