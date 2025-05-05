from abc import ABC, abstractmethod
from .task_manager import InMemoryTaskManager
from typing import AsyncIterable
from common.types import (
    SendTaskRequest, SendTaskResponse, SendTaskStreamingRequest, SendTaskStreamingResponse, JSONRPCResponse, TaskSendParams, TaskStatus, Artifact, Task
)

class BaseAgentTaskManager(InMemoryTaskManager, ABC):
    def __init__(self, agent, notification_sender_auth=None):
        super().__init__()
        self.agent = agent
        self.notification_sender_auth = notification_sender_auth

    @abstractmethod
    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        pass

    @abstractmethod
    async def on_send_task_subscribe(self, request: SendTaskStreamingRequest) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        pass

    def _validate_request(self, request):
        # Default output type validation logic, override if needed
        return None

    def _get_user_query(self, task_send_params: TaskSendParams) -> str:
        # Default implementation for text-based query extraction
        part = task_send_params.message.parts[0]
        if hasattr(part, 'text'):
            return part.text
        raise ValueError("Only text parts are supported")

    async def _update_store(self, task_id: str, status: TaskStatus, artifacts: list[Artifact]) -> Task:
        # Default task store update implementation
        async with self.lock:
            try:
                task = self.tasks[task_id]
            except KeyError as exc:
                raise ValueError(f"Task {task_id} not found") from exc
            task.status = status
            if status.message is not None:
                self.task_messages[task_id].append(status.message)
            if artifacts is not None:
                if task.artifacts is None:
                    task.artifacts = []
                task.artifacts.extend(artifacts)
            return task 