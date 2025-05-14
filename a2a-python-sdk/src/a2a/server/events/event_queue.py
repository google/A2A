import asyncio
import logging

from typing import Any

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


class EventQueue:
    """Event queue for A2A responses from agent."""

    def __init__(self) -> None:
        self.queue: asyncio.Queue[Event] = asyncio.Queue()
        self._children: list[EventQueue] = []
        logger.debug('EventQueue initialized.')

    def enqueue_event(self, event: Event):
        logger.debug(f'Enqueuing event of type: {type(event)}')
        self.queue.put_nowait(event)
        for child in self._children:
            child.enqueue_event(event)

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

    def tap(self) -> Any:
        """Taps the event queue to branch the future events."""
        queue = EventQueue()
        self._children.append(queue)
        return queue

    def close(self):
        """Closes the queue for future push events."""
        self.queue.shutdown()
        for child in self._children:
            child.close()
