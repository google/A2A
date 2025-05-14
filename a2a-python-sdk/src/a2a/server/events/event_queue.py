import asyncio
import logging

from pydantic import RootModel

from a2a.types import (
    A2AError,
    JSONRPCError,
    Message,
    Task,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
)


logger = logging.getLogger(__name__)


Event = (
    Message
    | Task
    | TaskStatusUpdateEvent
    | TaskArtifactUpdateEvent
    | A2AError
    | JSONRPCError
)


class Event1(
    RootModel[
        Message
        | Task
        | TaskStatusUpdateEvent
        | TaskArtifactUpdateEvent
        | A2AError
        | JSONRPCError
    ]
):
    """Type used for dispatching A2A events to consumers."""

    root: (
        Message
        | Task
        | TaskStatusUpdateEvent
        | TaskArtifactUpdateEvent
        | A2AError
        | JSONRPCError
    )


class EventQueue:
    """Event queue for A2A responses from agent."""

    def __init__(self) -> None:
        self.queue: asyncio.Queue[Event] = asyncio.Queue()
        logger.debug('EventQueue initialized.')

    def enqueue_event(self, event: Event):
        logger.debug(f'Enqueuing event of type: {type(event)}')
        self.queue.put_nowait(event)

    async def dequeue_event(self, no_wait: bool = False) -> Event:
        if no_wait:
            logger.debug('Attempting to dequeue event (no_wait=True).')
            event = self.queue.get_nowait()
            logger.debug(
                f'Dequeued event (no_wait=True) of type: {type(event)}'
            )
            return event

        logger.debug('Attempting to dequeue event (waiting).')
        event = await self.queue.get()
        logger.debug(f'Dequeued event (waited) of type: {type(event)}')
        return event

    def task_done(self) -> None:
        logger.debug('Marking task as done in EventQueue.')
        self.queue.task_done()
