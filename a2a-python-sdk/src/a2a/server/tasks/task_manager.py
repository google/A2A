import logging

from a2a.server.events.event_queue import Event
from a2a.server.tasks.task_store import TaskStore
from a2a.types import (
    InvalidParamsError,
    Message,
    Task,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from a2a.utils import append_artifact_to_task
from a2a.utils.errors import ServerError


logger = logging.getLogger(__name__)


class TaskManager:
    """Helps manage a task's lifecycle during execution of a request."""

    def __init__(
        self,
        task_id: str | None,
        context_id: str | None,
        task_store: TaskStore,
        initial_message: Message | None,
    ):
        self.task_id = task_id
        self.context_id = context_id
        self.task_store = task_store
        self._initial_message = initial_message
        self._current_task: Task | None = None
        logger.debug(
            'TaskManager initialized with task_id: %s, context_id: %s',
            task_id,
            context_id,
        )

    async def get_task(self) -> Task | None:
        if not self.task_id:
            logger.debug('task_id is not set, cannot get task.')
            return None

        if self._current_task:
            return self._current_task

        logger.debug(
            'Attempting to get task from store with id: %s', self.task_id
        )
        self._current_task = await self.task_store.get(self.task_id)
        if self._current_task:
            logger.debug('Task %s retrieved successfully.', self.task_id)
        else:
            logger.debug('Task %s not found.', self.task_id)
        return self._current_task

    async def save_task_event(
        self, event: Task | TaskStatusUpdateEvent | TaskArtifactUpdateEvent
    ) -> Task | None:
        task_id_from_event = (
            event.id if isinstance(event, Task) else event.taskId
        )
        # If task id is known, make sure it is matched
        if self.task_id and self.task_id != task_id_from_event:
            raise ServerError(
                error=InvalidParamsError(
                    message=f"Task in event doesn't match TaskManager {self.task_id} : {task_id_from_event}"
                )
            )
        if not self.task_id:
            self.task_id = task_id_from_event
        if not self.context_id and self.context_id != event.contextId:
            self.context_id = event.contextId

        logger.debug(
            'Processing save of task event of type %s for task_id: %s',
            type(event).__name__,
            task_id_from_event,
        )
        if isinstance(event, Task):
            await self._save_task(event)
            return event

        task: Task = await self.ensure_task(event)

        if isinstance(event, TaskStatusUpdateEvent):
            logger.debug(
                'Updating task %s status to: %s', task.id, event.status.state
            )
            if task.status.message:
                if not task.history:
                    task.history = [task.status.message]
                else:
                    task.history.append(task.status.message)

            task.status = event.status
        else:
            logger.debug('Appending artifact to task %s', task.id)
            append_artifact_to_task(task, event)

        await self._save_task(task)
        return task

    async def ensure_task(
        self, event: TaskStatusUpdateEvent | TaskArtifactUpdateEvent
    ) -> Task:
        task: Task | None = self._current_task
        if not task and self.task_id:
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

        return task

    async def process(self, event: Event) -> Event:
        """Processes an event, store the task state and return the task or message.

        The returned Task or Message represent the current status of the result.
        """
        if isinstance(
            event, Task | TaskStatusUpdateEvent | TaskArtifactUpdateEvent
        ):
            await self.save_task_event(event)

        return event

    def _init_task_obj(self, task_id: str, context_id: str) -> Task:
        """Initializes a new task object."""
        logger.debug(
            'Initializing new Task object with task_id: %s, context_id: %s',
            task_id,
            context_id,
        )
        history = [self._initial_message] if self._initial_message else []
        return Task(
            id=task_id,
            contextId=context_id,
            status=TaskStatus(state=TaskState.submitted),
            history=history,
        )

    async def _save_task(self, task: Task) -> None:
        logger.debug('Saving task with id: %s', task.id)
        await self.task_store.save(task)
        self._current_task = task
        if not self.task_id:
            logger.info('New task created with id: %s', task.id)
            self.task_id = task.id
            self.context_id = task.contextId

    def update_with_message(self, message: Message, task: Task) -> Task:
        """Update the prior status to history, and add the incoming message to history.

        This updates the object in memory, and the _current_task, but does not
        persist it. This is the job of the processor after this step.
        """
        if task.status.message:
            if task.history:
                task.history.append(task.status.message)
            else:
                task.history = [task.status.message]
            task.status.message = None
        if task.history:
            task.history.append(message)
        else:
            task.history = [message]
        self._current_task = task
        return task
