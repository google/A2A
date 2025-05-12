import logging

from a2a.server.tasks.task_store import TaskStore
from a2a.types import (
    Task,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from a2a.utils import append_artifact_to_task


logger = logging.getLogger(__name__)


class TaskManager:
    """Helps manage a task's lifecycle during execution of a request."""

    def __init__(
        self, task_id: str | None, context_id: str | None, task_store: TaskStore
    ):
        self.task_id = task_id
        self.context_id = context_id
        self.task_store = task_store
        logger.debug(
            'TaskManager initialized with task_id: %s, context_id: %s',
            task_id,
            context_id,
        )

    async def get_task(self) -> Task | None:
        if not self.task_id:
            logger.debug('task_id is not set, cannot get task.')
            return None

        logger.debug('Attempting to get task with id: %s', self.task_id)
        task = await self.task_store.get(self.task_id)
        if task:
            logger.debug('Task %s retrieved successfully.', self.task_id)
        else:
            logger.debug('Task %s not found.', self.task_id)
        return task

    async def save_task_event(
        self, event: Task | TaskStatusUpdateEvent | TaskArtifactUpdateEvent
    ) -> None:
        event_type = type(event).__name__
        task_id_from_event = (
            event.id if isinstance(event, Task) else event.taskId
        )
        logger.debug(
            'Processing save of task event of type %s for task_id: %s',
            event_type,
            task_id_from_event,
        )
        if isinstance(event, Task):
            await self._save_task(event)
            return

        task: Task = await self.ensure_task(event)

        if isinstance(event, TaskStatusUpdateEvent):
            logger.debug(
                'Updating task %s status to: %s', task.id, event.status.state
            )
            task.status = event.status
        else:
            logger.debug('Appending artifact to task %s', task.id)
            append_artifact_to_task(task, event)

        await self._save_task(task)

    async def ensure_task(
        self, event: TaskStatusUpdateEvent | TaskArtifactUpdateEvent
    ) -> Task:
        task: Task | None = None
        if self.task_id:
            logger.debug(
                'Attempting to retrieve existing task with id: %s', self.task_id
            )
            task = await self.task_store.get(self.task_id)

        if not task:
            logger.info(
                'Task not found or task_id not set. Creating new task for event (task_id: %s, context_id: %s).',
                event.taskId,
                event.contextId,
            )
            # streaming agent did not previously stream task object.
            # Create a task object with the available information and persist the event
            task = self._init_task_obj(event.taskId, event.contextId)
            await self._save_task(task)
        else:
            logger.debug('Existing task %s found in TaskStore.', task.id)

        return task

    def _init_task_obj(self, task_id: str, context_id: str) -> Task:
        """Initializes a new task object."""
        logger.debug(
            'Initializing new Task object with task_id: %s, context_id: %s',
            task_id,
            context_id,
        )
        return Task(
            id=task_id,
            contextId=context_id,
            status=TaskStatus(state=TaskState.submitted),
            history=[],
        )

    async def _save_task(self, task: Task) -> None:
        logger.debug('Saving task with id: %s', task.id)
        await self.task_store.save(task)
        if not self.task_id:
            logger.info('New task created with id: %s', task.id)
            self.task_id = task.id
            self.context_id = task.contextId
