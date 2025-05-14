import asyncio
import contextlib
import logging

from collections.abc import AsyncGenerator

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import (
    Event,
    EventConsumer,
    EventQueue,
    InMemoryQueueManager,
    NoTaskQueue,
    QueueManager,
    TaskQueueExists,
)
from a2a.server.request_handlers.request_handler import RequestHandler
from a2a.server.tasks import ResultAggregator, TaskManager, TaskStore
from a2a.types import (
    InternalError,
    Message,
    MessageSendParams,
    Task,
    TaskIdParams,
    TaskNotFoundError,
    TaskPushNotificationConfig,
    TaskQueryParams,
    UnsupportedOperationError,
)
from a2a.utils.errors import ServerError


logger = logging.getLogger(__name__)


class DefaultRequestHandler(RequestHandler):
    """Default request handler for all incoming requests."""

    def __init__(
        self,
        agent_executor: AgentExecutor,
        task_store: TaskStore,
        queue_manager: QueueManager | None = None,
    ) -> None:
        self.agent_executor = agent_executor
        self.task_store = task_store
        self._queue_manager = queue_manager or InMemoryQueueManager()

    async def on_get_task(self, params: TaskQueryParams) -> Task | None:
        """Default handler for 'tasks/get'."""
        task: Task | None = await self.task_store.get(params.id)
        if not task:
            raise ServerError(error=TaskNotFoundError())
        return task

    async def on_cancel_task(self, params: TaskIdParams) -> Task | None:
        """Default handler for 'tasks/cancel'."""
        task: Task | None = await self.task_store.get(params.id)
        if not task:
            raise ServerError(error=TaskNotFoundError())

        task_manager = TaskManager(
            task_id=task.id,
            context_id=task.contextId,
            task_store=self.task_store,
            initial_message=None,
        )
        result_aggregator = ResultAggregator(task_manager)

        queue = await self._queue_manager.tap(task.id)
        if not queue:
            queue = EventQueue()

        await self.agent_executor.cancel(
            RequestContext(
                None,
                task_id=task.id,
                context_id=task.contextId,
                task=task,
            ),
            queue,
        )
        consumer = EventConsumer(queue)
        result = await result_aggregator.consume_all(consumer)
        if isinstance(result, Task):
            return result

        raise ServerError(
            error=InternalError(message='Agent did not result valid response')
        )

    async def _run_event_stream(
        self, request: RequestContext, queue: EventQueue
    ) -> None:
        await self.agent_executor.execute(request, queue)
        queue.close()

    async def on_message_send(
        self, params: MessageSendParams
    ) -> Message | Task:
        """Default handler for 'message/send' interface."""
        task_manager = TaskManager(
            task_id=params.message.taskId,
            context_id=params.message.contextId,
            task_store=self.task_store,
            initial_message=params.message,
        )
        task: Task | None = await task_manager.get_task()
        if task:
            task = task_manager.update_with_message(params.message, task)
            queue = await self._queue_manager.create_or_tap(task.id)
        else:
            queue = EventQueue()
        result_aggregator = ResultAggregator(task_manager)
        # TODO to manage the non-blocking flows.
        producer_task = asyncio.create_task(
            self._run_event_stream(
                RequestContext(
                    params,
                    task.id if task else None,
                    task.contextId if task else None,
                    task,
                ),
                queue,
            )
        )

        try:
            consumer = EventConsumer(queue)

            # TODO - register the queue for the task upon the first sign it is a task.
            result = await result_aggregator.consume_all(consumer)
            if not result:
                raise ServerError(error=InternalError())

            return result
        finally:
            await producer_task
            if task:
                with contextlib.suppress(NoTaskQueue):
                    await self._queue_manager.close(task.id)

    async def on_message_send_stream(
        self, params: MessageSendParams
    ) -> AsyncGenerator[Event, None]:
        """Default handler for 'message/stream'."""
        task_manager = TaskManager(
            task_id=params.message.taskId,
            context_id=params.message.contextId,
            task_store=self.task_store,
            initial_message=params.message,
        )
        task: Task | None = await task_manager.get_task()

        if task:
            task = task_manager.update_with_message(params.message, task)
            queue = await self._queue_manager.create_or_tap(task.id)
        else:
            queue = EventQueue()
        result_aggregator = ResultAggregator(task_manager)
        task_id: str | None = task.id if task else None
        producer_task = asyncio.create_task(
            self._run_event_stream(
                RequestContext(
                    params,
                    task.id if task else None,
                    task.contextId if task else None,
                    task,
                ),
                queue,
            )
        )
        try:
            consumer = EventConsumer(queue)
            async for event in result_aggregator.consume_and_emit(consumer):
                # Now we know we have a Task, register the queue
                if isinstance(event, Task):
                    try:
                        await self._queue_manager.add(event.id, queue)
                        task_id = event.id
                    except TaskQueueExists:
                        logging.info(
                            'Multiple Task objects created in event stream.'
                        )
                yield event
        finally:
            await producer_task
            if task_id:
                with contextlib.suppress(NoTaskQueue):
                    await self._queue_manager.close(task_id)

    async def on_set_task_push_notification_config(
        self, params: TaskPushNotificationConfig
    ) -> TaskPushNotificationConfig:
        """Default handler for 'tasks/pushNotificationConfig/set'."""
        raise ServerError(error=UnsupportedOperationError())

    async def on_get_task_push_notification_config(
        self, params: TaskIdParams
    ) -> TaskPushNotificationConfig:
        """Default handler for 'tasks/pushNotificationConfig/get'."""
        raise ServerError(error=UnsupportedOperationError())

    async def on_resubscribe_to_task(
        self, params: TaskIdParams
    ) -> AsyncGenerator[Event, None]:
        """Default handler for 'tasks/resubscribe'."""
        task: Task | None = await self.task_store.get(params.id)
        if not task:
            raise ServerError(error=TaskNotFoundError())

        task_manager = TaskManager(
            task_id=task.id,
            context_id=task.contextId,
            task_store=self.task_store,
            initial_message=None,
        )

        result_aggregator = ResultAggregator(task_manager)

        queue = await self._queue_manager.tap(task.id)
        if not queue:
            raise ServerError(error=TaskNotFoundError())

        consumer = EventConsumer(queue)
        async for event in result_aggregator.consume_and_emit(consumer):
            yield event
