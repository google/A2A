import asyncio
import logging

from collections.abc import AsyncGenerator

from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks.task_manager import TaskManager
from a2a.types import (
    A2AError,
    InternalError,
    JSONRPCError,
    Message,
    Task,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
)


logger = logging.getLogger(__name__)


class EventConsumer:
    """Consumer to read events from the agent event queue."""

    def __init__(self, queue: EventQueue, task_manager: TaskManager):
        self.queue = queue
        self.task_manager = task_manager
        logger.debug('EventConsumer initialized')

    async def consume_one(
        self,
    ) -> Task | Message | A2AError | JSONRPCError:
        """Consume one event from the agent event queue."""
        logger.debug('Attempting to consume one event.')
        try:
            event = await self.queue.dequeue_event(no_wait=True)
            logger.debug(
                f'Dequeued event of type: {type(event)} in consume_one.'
            )
        except asyncio.QueueEmpty:
            logger.warning('Event queue was empty in consume_one.')
            return A2AError(
                InternalError(message='Agent did not return any response')
            )

        if isinstance(event, Task):
            logger.debug(f'Saving task from event: {event.id} to TaskStore')
            await self.task_manager.save_task_event(event)

        self.queue.task_done()

        if isinstance(event, Message | Task | A2AError | JSONRPCError):
            logger.debug(
                f'Returning event of type: {type(event)} from consume_one.'
            )
            return event

        logger.error(
            f'Consumer received an unexpected message type: {type(event)}.'
        )
        return A2AError(
            InternalError(
                message=f'The agent did not return valid response_type: {type(event)}'
            )
        )

    async def consume_all(
        self,
    ) -> AsyncGenerator[
        Message
        | Task
        | TaskStatusUpdateEvent
        | TaskArtifactUpdateEvent
        | A2AError
        | JSONRPCError
    ]:
        """Consume all the generated streaming events from the agent."""
        logger.debug('Starting to consume all events from the queue.')
        while True:
            event = await self.queue.dequeue_event()

            logger.debug(
                f'Dequeued event of type: {type(event)} in consume_all.'
            )

            if isinstance(
                event, Task | TaskStatusUpdateEvent | TaskArtifactUpdateEvent
            ):
                # persist task related updates to TaskStore
                logger.debug(
                    f'Saving task event of type {type(event)} to TaskStore'
                )
                await self.task_manager.save_task_event(event)

            yield event
            self.queue.task_done()
            logger.debug('Marked task as done in event queue in consume_all')

            is_error = isinstance(event, A2AError | JSONRPCError)
            is_final_event = (
                isinstance(event, TaskStatusUpdateEvent | Message)
                and event.final
            )

            if is_error or is_final_event:
                logger.debug(
                    f'Stopping event consumption in consume_all. is_error={is_error}, is_final_event={is_final_event} '
                )
                break
