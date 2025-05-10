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
