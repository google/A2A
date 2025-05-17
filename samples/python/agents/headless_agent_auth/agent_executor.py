from agent import HRAgent
from typing_extensions import override

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import (
    Task,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from a2a.utils import new_agent_text_message, new_task, new_text_artifact


class HRAgentExecutor(AgentExecutor):
    """HR AgentExecutor Example."""

    def __init__(self):
        self.agent = HRAgent()

    @override
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        query = context.get_user_input()
        task = context.current_task

        if not task:
            task = new_task(context.message)
            event_queue.enqueue_event(task)
        # invoke the underlying agent, using streaming results
        async for event in self.agent.stream(query, task.contextId):
            task_state = TaskState(event['task_state'])
            if event['is_task_complete']:
                event_queue.enqueue_event(
                    TaskArtifactUpdateEvent(
                        append=False,
                        contextId=task.contextId,
                        taskId=task.id,
                        lastChunk=True,
                        artifact=new_text_artifact(
                            name='current_result',
                            description='Result of request to agent.',
                            text=event['content'],
                        ),
                    )
                )
                event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        status=TaskStatus(state=task_state),
                        final=True,
                        contextId=task.contextId,
                        taskId=task.id,
                    )
                )
            else:
                event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        status=TaskStatus(
                            state=task_state,
                            message=new_agent_text_message(
                                event['content'],
                                task.contextId,
                                task.id,
                            ),
                        ),
                        final=task_state in {
                            TaskState.input_required,
                            TaskState.failed,
                            TaskState.unknown,
                        },
                        contextId=task.contextId,
                        taskId=task.id,
                    )
                )

    @override
    async def cancel(
        self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        raise Exception('cancel not supported')
