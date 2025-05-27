import json
import logging
import uuid

from collections.abc import AsyncIterable
from enum import Enum
from uuid import uuid4

import httpx
import networkx as nx

from a2a.client import A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendStreamingMessageRequest,
    SendStreamingMessageSuccessResponse,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatusUpdateEvent,
)
from a2a_mcp.common.utils import get_mcp_server_config
from a2a_mcp.mcp import client


logger = logging.getLogger(__name__)


class Status(Enum):
    """Represents the status of a workflow and its associated node."""

    READY = 'READY'
    RUNNING = 'RUNNING'
    COMPLETED = 'COMPLETED'
    PAUSED = 'PAUSED'
    INITIALIZED = 'INITIALIZED'


class WorkflowNode:
    """Represents a single node in a workflow graph.

    Each node encapsulates a specific task to be executed, such as finding an
    agent or invoking an agent's capabilities. It manages its own state
    (e.g., READY, RUNNING, COMPLETED, PAUSED) and can execute its assigned task.

    """

    def __init__(
        self,
        task: str,
        node_key: str | None = None,
        node_label: str | None = None,
    ):
        self.id = str(uuid.uuid4())
        self.node_key = node_key
        self.node_label = node_label
        self.task = task
        self.results = None
        self.state = Status.READY

    async def get_planner_resource(self) -> AgentCard | None:
        logger.info(f'Getting resource for node {self.id}')
        config = get_mcp_server_config()
        async with client.init_session(
            config.host, config.port, config.transport
        ) as session:
            response = await client.find_resource(
                session, 'resource://agent_cards/planner_agent'
            )
            data = json.loads(response.contents[0].text)
            return AgentCard(**data['agent_card'][0])

    async def find_agent_for_task(self) -> AgentCard | None:
        logger.info(f'Find agent for task - {self.task}')
        config = get_mcp_server_config()
        async with client.init_session(
            config.host, config.port, config.transport
        ) as session:
            result = await client.find_agent(session, self.task)
            agent_card_json = json.loads(result.content[0].text)
            logger.debug(f'Found agent {agent_card_json} for task {self.task}')
            return AgentCard(**agent_card_json)

    async def run_node(
        self,
        query: str,
        task_id: str,
        context_id: str,
    ) -> AsyncIterable[dict[str, any]]:
        logger.info(f'Executing node {self.id}')
        agent_card = None
        if self.node_key == 'planner':
            agent_card = await self.get_planner_resource()
        else:
            agent_card = await self.find_agent_for_task()
        async with httpx.AsyncClient() as httpx_client:
            client = A2AClient(httpx_client, agent_card)

            payload: dict[str, any] = {
                'message': {
                    'role': 'user',
                    'parts': [{'kind': 'text', 'text': query}],
                    'messageId': uuid4().hex,
                    'taskId': task_id,
                    'contextId': context_id,
                },
            }
            request = SendStreamingMessageRequest(
                params=MessageSendParams(**payload)
            )
            response_stream = client.send_message_streaming(request)
            async for chunk in response_stream:
                # Save the artifact as a result of the node
                if isinstance(
                    chunk.root, SendStreamingMessageSuccessResponse
                ) and (isinstance(chunk.root.result, TaskArtifactUpdateEvent)):
                    artifact = chunk.root.result.artifact
                    self.results = artifact
                yield chunk


class WorkflowGraph:
    """Represents a graph of workflow nodes."""

    def __init__(self):
        self.graph = nx.DiGraph()
        self.nodes = {}
        self.latest_node = None
        self.node_type = None
        self.state = Status.INITIALIZED
        self.paused_node_id = None

    def add_node(self, node) -> None:
        logger.info(f'Adding node {node.id}')
        self.graph.add_node(node.id, query=node.task)
        self.nodes[node.id] = node
        self.latest_node = node.id

    def add_edge(self, from_node_id: str, to_node_id: str) -> None:
        if from_node_id not in self.nodes or to_node_id not in self.nodes:
            raise ValueError('Invalid node IDs')

        self.graph.add_edge(from_node_id, to_node_id)

    async def run_workflow(
        self, start_node_id: str = None
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
        logger.info(f'Sub graph {sub_graph} size {len(sub_graph)}')
        self.state = Status.RUNNING
        # Alternative is to loop over all nodes, but we only need the connected nodes.
        for node_id in sub_graph:
            node = self.nodes[node_id]
            node.state = Status.RUNNING
            query = self.graph.nodes[node_id].get('query')
            task_id = self.graph.nodes[node_id].get('task_id')
            context_id = self.graph.nodes[node_id].get('context_id')
            async for chunk in node.run_node(query, task_id, context_id):
                # When the workflow node is paused, do not yeild any chunks
                # but, let the loop complete.
                if node.state != Status.PAUSED:
                    if isinstance(
                        chunk.root, SendStreamingMessageSuccessResponse
                    ) and (
                        isinstance(chunk.root.result, TaskStatusUpdateEvent)
                    ):
                        task_status_event = chunk.root.result
                        context_id = task_status_event.contextId
                        if (
                            task_status_event.status.state
                            == TaskState.input_required
                            and context_id
                        ):
                            node.state = Status.PAUSED
                            self.state = Status.PAUSED
                            self.paused_node_id = node.id
                    yield chunk
            if self.state == Status.PAUSED:
                break
            if node.state == Status.RUNNING:
                node.state = Status.COMPLETED
        if self.state == Status.RUNNING:
            self.state = Status.COMPLETED

    def set_node_attribute(self, node_id, attribute, value):
        nx.set_node_attributes(self.graph, {node_id: value}, attribute)

    def set_node_attributes(self, node_id, attr_val):
        nx.set_node_attributes(self.graph, {node_id: attr_val})

    def is_empty(self) -> bool:
        return self.graph.number_of_nodes() == 0
