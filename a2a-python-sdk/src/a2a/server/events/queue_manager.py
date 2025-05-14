from abc import ABC, abstractmethod

from a2a.server.events.event_queue import EventQueue


class QueueManager(ABC):
    """Interface for managing the event queue lifecycles."""

    @abstractmethod
    async def add(self, task_id: str, queue: EventQueue):
        pass

    @abstractmethod
    async def get(self, task_id: str) -> EventQueue | None:
        pass

    @abstractmethod
    async def tap(self, task_id: str) -> EventQueue | None:
        pass

    @abstractmethod
    async def close(self, task_id: str):
        pass

    @abstractmethod
    async def create_or_tap(self, task_id: str) -> EventQueue:
        pass


class TaskQueueExists(Exception):
    pass


class NoTaskQueue(Exception):
    pass
