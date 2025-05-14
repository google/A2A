import logging

from collections.abc import AsyncGenerator

from a2a.server.events import Event, EventConsumer
from a2a.server.tasks.task_manager import TaskManager
from a2a.types import (
    Message,
    Task,
)


logger = logging.getLogger(__name__)


class ResultAggregator:
    """ResultAggregator is used to process the event streams from an AgentExecutor.

    There are three main ways to use the ResultAggregator:
    1) As part of a processing pipe. consume_and_emit will construct the updated
       task as the events arrive, and re-emit those events for another consumer
    2) As part of a blocking call. consume_all will process the entire stream and
       return the final Task or Message object
    3) As part of a push solution where the latest Task is emitted after processing an event.
       consume_and_emit_task will consume the Event stream, process the events to the current
       Task object and emit that Task object.
    """

    def __init__(self, task_manager: TaskManager):
        self.task_manager = task_manager
        self._message: Message | None = None

    @property
    async def current_result(self) -> Task | Message | None:
        if self._message:
            return self._message
        return await self.task_manager.get_task()

    async def consume_and_emit(
        self, consumer: EventConsumer
    ) -> AsyncGenerator[Event, None]:
        """Processes the event stream and emits the same event stream out."""
        async for event in consumer.consume_all():
            await self.task_manager.process(event)
            yield event

    async def consume_all(
        self, consumer: EventConsumer
    ) -> Task | Message | None:
        """Processes the entire event stream and returns the final result."""
        async for event in consumer.consume_all():
            if isinstance(event, Message):
                self._message = event
                return event
            await self.task_manager.process(event)
        return await self.task_manager.get_task()

    # async def consume_and_emit_task(
    #     self, consumer: EventConsumer
    # ) -> AsyncGenerator[Event, None]:
    #     """Processes the event stream and emits the current state of the task."""
    #     async for event in consumer.consume_all():
    #         if isinstance(event, Message):
    #             self._current_task_or_message = event
    #             break
    #         yield await self.task_manager.process(event)
