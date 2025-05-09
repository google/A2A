import asyncio

from abc import ABC, abstractmethod

from a2a.types import Task


class TaskStore(ABC):
    """Agent Task Store interface."""

    @abstractmethod
    async def save(self, task: Task):
        pass

    @abstractmethod
    async def get(self, task_id: str) -> Task | None:
        pass

    @abstractmethod
    async def delete(self, task_id: str):
        pass


class InMemoryTaskStore(TaskStore):
    """In-memory implementation of TaskStore."""

    def __init__(self) -> None:
        self.tasks: dict[str, Task] = {}
        self.lock = asyncio.Lock()

    async def save(self, task: Task) -> None:
        async with self.lock:
            self.tasks[task.id] = task

    async def get(self, task_id: str) -> Task | None:
        async with self.lock:
            return self.tasks.get(task_id)

    async def delete(self, task_id: str) -> None:
        async with self.lock:
            del self.tasks[task_id]
