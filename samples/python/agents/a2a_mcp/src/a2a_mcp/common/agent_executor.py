import json
import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import Event, EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    DataPart,
    InvalidParamsError,
    Part,
    SendStreamingMessageSuccessResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatusUpdateEvent,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import new_agent_text_message, new_task
from a2a.utils.errors import ServerError
from a2a_mcp.common.base_agent import BaseAgent
from typing_extensions import override


logger = logging.getLogger(__name__)


class GenericAgentExecutor(AgentExecutor):
    def __init__(self, agent: BaseAgent):
        self.agent = agent

    @override
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        logger.info(f'Executing agent {self.agent.agent_name}')
        error = self._validate_request(context)
        if error:
            raise ServerError(error=InvalidParamsError())

        query = context.get_user_input()

        task = context.current_task

        if not task:
            task = new_task(context.message)
            event_queue.enqueue_event(task)

        updater = TaskUpdater(event_queue, task.id, task.contextId)

        async for item in self.agent.stream(query, task.contextId):
            # Agent to Agent call will return events,
            # Update the relevant ids to proxy back.
            if hasattr(item, 'root') and isinstance(
                item.root, SendStreamingMessageSuccessResponse
            ):
                event = item.root.result
                if isinstance(event, TaskStatusUpdateEvent):
                    event.taskId = task.id
                    event.contextId = task.contextId
                    event.status.message.taskId = task.id
                    event.status.message.contextId = task.contextId
                    event_queue.enqueue_event(event)
                elif isinstance(event, TaskArtifactUpdateEvent):
                    event.taskId = task.id
                    event.contextId = task.contextId
                    event_queue.enqueue_event(event)
                continue

            is_task_complete = item['is_task_complete']
            require_user_input = item['require_user_input']

            if is_task_complete:
                if item['response_type'] == 'data':
                    part = DataPart(data=item['content'])
                else:
                    part = TextPart(text=item['content'])

                updater.add_artifact(
                    [part],
                    name=f'{self.agent.agent_name}-result',
                )
                updater.complete()
                break
            elif require_user_input:
                updater.update_status(
                    TaskState.input_required,
                    new_agent_text_message(
                        item['content'],
                        task.contextId,
                        task.id,
                    ),
                    final=True,
                )
                break
            else:
                updater.update_status(
                    TaskState.working,
                    new_agent_text_message(
                        item['content'],
                        task.contextId,
                        task.id,
                    ),
                )

    def _validate_request(self, context: RequestContext) -> bool:
        return False

    @override
    async def cancel(
        self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        raise ServerError(error=UnsupportedOperationError())
