import asyncio

from a2a.server.events.event_queue import EventQueue
from a2a.server.events.queue_manager import (
    NoTaskQueue,
    QueueManager,
    TaskQueueExists,
)


class InMemoryQueueManager(QueueManager):
    """InMemoryQueueManager is used for a single binary management.

    This implements the QueueManager but requires all incoming interactions
    to hit the same binary that manages the queues.

    This works for single binary solution. Needs a distributed approach for
    true scalable deployment.
    """

    def __init__(self):
        self._task_queue: dict[str, EventQueue] = {}
        self._lock = asyncio.Lock()

    async def add(self, task_id: str, queue: EventQueue):
        async with self._lock:
            if task_id in self._task_queue:
                raise TaskQueueExists()
            self._task_queue[task_id] = queue

    async def get(self, task_id: str) -> EventQueue | None:
        async with self._lock:
            if task_id not in self._task_queue:
                return None
            return self._task_queue[task_id]

    async def tap(self, task_id: str) -> EventQueue | None:
        async with self._lock:
            if task_id not in self._task_queue:
                return None
            return self._task_queue[task_id].tap()

    async def close(self, task_id: str):
        async with self._lock:
            if task_id not in self._task_queue:
                raise NoTaskQueue()
            del self._task_queue[task_id]

    async def create_or_tap(self, task_id: str) -> EventQueue:
        async with self._lock:
            if task_id not in self._task_queue:
                queue = EventQueue()
                self._task_queue[task_id] = queue
                return queue
            return self._task_queue[task_id].tap()
