import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Union, AsyncIterable, List, Dict

from A2A.samples.python.common.server.utils import new_not_implemented_error
from A2A.samples.python.common.types import (
    JSONRPCResponse,
    TaskIdParams,
    TaskQueryParams,
    GetTaskRequest,
    TaskNotFoundError,
    SendTaskRequest,
    CancelTaskRequest,
    TaskNotCancelableError,
    SetTaskPushNotificationRequest,
    GetTaskPushNotificationRequest,
    GetTaskResponse,
    CancelTaskResponse,
    SendTaskResponse,
    SetTaskPushNotificationResponse,
    GetTaskPushNotificationResponse,
    PushNotificationNotSupportedError,
    TaskSendParams,
    TaskStatus,
    TaskState,
    TaskResubscriptionRequest,
    SendTaskStreamingRequest,
    SendTaskStreamingResponse,
    Artifact,
    PushNotificationConfig,
    TaskStatusUpdateEvent,
    JSONRPCError,
    TaskPushNotificationConfig,
    InternalError,
    # New Knowledge Types
    KnowledgeQueryRequest,
    KnowledgeQueryResponse,
    KnowledgeUpdateRequest,
    KnowledgeUpdateResponse,
    KnowledgeSubscribeRequest,
    KnowledgeSubscriptionEvent,
    UnsupportedOperationError, TaskArtifactUpdateEvent,
)
from A2A.samples.python.common.types import Task

logger = logging.getLogger(__name__)


# Interface definition for Task Management and potentially Knowledge Management
class TaskManager(ABC):

    # --- Task Methods ---
    @abstractmethod
    async def on_get_task(self, request: GetTaskRequest) -> GetTaskResponse:
        """Handles requests to retrieve task status and details."""
        pass

    @abstractmethod
    async def on_cancel_task(self, request: CancelTaskRequest) -> CancelTaskResponse:
        """Handles requests to cancel an ongoing task."""
        pass

    @abstractmethod
    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """Handles requests to submit a new task (non-streaming)."""
        pass

    @abstractmethod
    async def on_send_task_subscribe(
            self, request: SendTaskStreamingRequest
    ) -> Union[AsyncIterable[SendTaskStreamingResponse], JSONRPCResponse]:
        """Handles requests to submit a new task and subscribe to updates (streaming)."""
        pass

    @abstractmethod
    async def on_set_task_push_notification(
            self, request: SetTaskPushNotificationRequest
    ) -> SetTaskPushNotificationResponse:
        """Handles requests to set up push notifications for a task."""
        pass

    @abstractmethod
    async def on_get_task_push_notification(
            self, request: GetTaskPushNotificationRequest
    ) -> GetTaskPushNotificationResponse:
        """Handles requests to retrieve push notification settings for a task."""
        pass

    @abstractmethod
    async def on_resubscribe_to_task(
            self, request: TaskResubscriptionRequest
    ) -> Union[AsyncIterable[SendTaskStreamingResponse], JSONRPCResponse]:
        """Handles requests to resubscribe to an existing task's updates."""
        pass

    # --- Knowledge Methods (Interface) ---
    # These methods are added here for simplicity. In a larger system,
    # they might belong to a separate KnowledgeManager ABC.

    @abstractmethod
    async def on_knowledge_query(self, request: KnowledgeQueryRequest) -> KnowledgeQueryResponse:
        """Handles requests to query the agent's knowledge graph."""
        pass

    @abstractmethod
    async def on_knowledge_update(self, request: KnowledgeUpdateRequest) -> KnowledgeUpdateResponse:
        """Handles requests to update the agent's knowledge graph."""
        pass

    @abstractmethod
    async def on_knowledge_subscribe(
            self, request: KnowledgeSubscribeRequest
    ) -> Union[AsyncIterable[KnowledgeSubscriptionEvent], JSONRPCResponse]:
        """Handles requests to subscribe to changes in the agent's knowledge graph."""
        pass


# Example implementation keeping tasks in memory
class InMemoryTaskManager(TaskManager):
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.push_notification_infos: Dict[str, PushNotificationConfig] = {}
        self.lock = asyncio.Lock()
        # SSE Subscribers for Tasks
        self.task_sse_subscribers: Dict[str, List[asyncio.Queue[SendTaskStreamingResponse]]] = {}
        self.subscriber_lock = asyncio.Lock()
        # SSE Subscribers for Knowledge Graph (Placeholder - structure might change)
        # Key could be subscription ID, topic, etc.
        self.knowledge_sse_subscribers: Dict[str, List[asyncio.Queue[KnowledgeSubscriptionEvent]]] = {}
        self.knowledge_subscriber_lock = asyncio.Lock()

        # Placeholder for Knowledge Graph data and GraphQL engine
        # self.knowledge_graph = ... # E.g., RDFLib graph, Neo4j connection
        # self.graphql_engine = ... # E.g., Ariadne schema/executable

    # --- Task Method Implementations ---

    async def on_get_task(self, request: GetTaskRequest) -> GetTaskResponse:
        logger.info(f"Getting task {request.params.id}")
        task_query_params: TaskQueryParams = request.params

        async with self.lock:
            task = self.tasks.get(task_query_params.id)
            if task is None:
                return GetTaskResponse(id=request.id, error=TaskNotFoundError())

            task_result = self.append_task_history(
                task, task_query_params.historyLength
            )

        return GetTaskResponse(id=request.id, result=task_result)

    async def on_cancel_task(self, request: CancelTaskRequest) -> CancelTaskResponse:
        logger.info(f"Cancelling task {request.params.id}")
        task_id_params: TaskIdParams = request.params

        async with self.lock:
            task = self.tasks.get(task_id_params.id)
            if task is None:
                return CancelTaskResponse(id=request.id, error=TaskNotFoundError())

            # Simple implementation: Mark as canceled if not already completed/failed
            if task.status.state not in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELED]:
                logger.info(f"Task {task.id} cancellation requested. Marking as canceled.")
                # In a real scenario, you'd signal the running task to stop.
                task.status.state = TaskState.CANCELED
                task.status.timestamp = datetime.now()
                task.status.message = None  # Or add a cancellation message
                # Optionally notify subscribers
                status_update = TaskStatusUpdateEvent(
                    id=task.id, status=task.status, final=True
                )
                # Using a non-blocking approach to avoid deadlock if queue is full (though unlikely with size=0)
                asyncio.create_task(self.enqueue_events_for_sse(task.id, status_update))

                return CancelTaskResponse(id=request.id, result=self.append_task_history(task, None))  # Return cancelled task
            elif task.status.state == TaskState.CANCELED:
                logger.info(f"Task {task.id} is already canceled.")
                return CancelTaskResponse(id=request.id, result=self.append_task_history(task, None))
            else:
                logger.warning(f"Task {task.id} cannot be canceled in state {task.status.state}.")
                return CancelTaskResponse(id=request.id, error=TaskNotCancelableError(data={"currentState": task.status.state}))

    @abstractmethod  # Keep abstract as per original - needs specific agent logic
    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """Requires concrete implementation based on agent's purpose."""
        # Example placeholder (should be replaced in a subclass):
        logger.warning("on_send_task is not implemented in InMemoryTaskManager base.")
        return new_not_implemented_error(request.id)
        pass

    @abstractmethod  # Keep abstract as per original - needs specific agent logic
    async def on_send_task_subscribe(
            self, request: SendTaskStreamingRequest
    ) -> Union[AsyncIterable[SendTaskStreamingResponse], JSONRPCResponse]:
        """Requires concrete implementation based on agent's purpose."""
        # Example placeholder (should be replaced in a subclass):
        logger.warning("on_send_task_subscribe is not implemented in InMemoryTaskManager base.")
        return new_not_implemented_error(request.id)
        pass

    async def set_push_notification_info(self, task_id: str, notification_config: PushNotificationConfig):
        async with self.lock:
            if task_id not in self.tasks:
                # Check if task exists before setting notification info
                logger.error(f"Task {task_id} not found when trying to set push notification info.")
                raise ValueError(f"Task not found for {task_id}")

            self.push_notification_infos[task_id] = notification_config
            logger.info(f"Set push notification info for task {task_id}")

    async def get_push_notification_info(self, task_id: str) -> PushNotificationConfig:
        async with self.lock:
            if task_id not in self.tasks:
                logger.error(f"Task {task_id} not found when trying to get push notification info.")
                raise ValueError(f"Task not found for {task_id}")

            notification_config = self.push_notification_infos.get(task_id)
            if notification_config is None:
                logger.warning(f"Push notification info not set for task {task_id}.")
                raise ValueError(f"Push notification info not set for {task_id}")  # Or return specific error/None
            return notification_config

    async def has_push_notification_info(self, task_id: str) -> bool:
        async with self.lock:
            # Check task exists first? Optional, depends on desired semantics.
            # if task_id not in self.tasks: return False
            return task_id in self.push_notification_infos

    async def on_set_task_push_notification(
            self, request: SetTaskPushNotificationRequest
    ) -> SetTaskPushNotificationResponse:
        logger.info(f"Setting task push notification for task {request.params.id}")
        task_notification_params: TaskPushNotificationConfig = request.params

        try:
            await self.set_push_notification_info(
                task_notification_params.id,
                task_notification_params.pushNotificationConfig
            )
            return SetTaskPushNotificationResponse(id=request.id, result=task_notification_params)
        except ValueError as e:  # Catch Task not found specifically
            logger.error(f"Error setting push notification: {e}")
            return SetTaskPushNotificationResponse(id=request.id, error=TaskNotFoundError(data={"id": task_notification_params.id, "reason": str(e)}))
        except Exception as e:
            logger.error(f"Unexpected error while setting push notification info: {e}", exc_info=True)
            return SetTaskPushNotificationResponse(
                id=request.id,
                error=InternalError(
                    message="An error occurred while setting push notification info",
                    data=str(e)
                ),
            )

    async def on_get_task_push_notification(
            self, request: GetTaskPushNotificationRequest
    ) -> GetTaskPushNotificationResponse:
        logger.info(f"Getting task push notification for task {request.params.id}")
        task_params: TaskIdParams = request.params

        try:
            # First check if the task itself exists
            async with self.lock:
                if task_params.id not in self.tasks:
                    logger.error(f"Task {task_params.id} not found when trying to get push notification info.")
                    raise ValueError(f"Task not found for {task_params.id}")

            # Now get the notification info
            notification_info = await self.get_push_notification_info(task_params.id)
            result_data = TaskPushNotificationConfig(
                id=task_params.id,
                pushNotificationConfig=notification_info
            )
            return GetTaskPushNotificationResponse(id=request.id, result=result_data)

        except ValueError as e:  # Catches both task not found and push info not set
            logger.error(f"Error getting push notification info: {e}")
            # Distinguish between task not found and config not set
            if "Task not found" in str(e):
                error: JSONRPCError = TaskNotFoundError(data={"id": task_params.id, "reason": str(e)})
            else:  # Assume config not set
                error = PushNotificationNotSupportedError(  # Or a custom error?
                    message=f"Push notification config not set for task {task_params.id}",
                    data={"id": task_params.id, "reason": str(e)}
                )
            return GetTaskPushNotificationResponse(id=request.id, error=error)
        except Exception as e:
            logger.error(f"Unexpected error while getting push notification info: {e}", exc_info=True)
            return GetTaskPushNotificationResponse(
                id=request.id,
                error=InternalError(
                    message="An error occurred while getting push notification info",
                    data=str(e)
                ),
            )

    async def upsert_task(self, task_send_params: TaskSendParams) -> Task:
        logger.info(f"Upserting task {task_send_params.id}")
        async with self.lock:
            task = self.tasks.get(task_send_params.id)
            timestamp = datetime.now()
            if task is None:
                logger.info(f"Creating new task {task_send_params.id}")
                task = Task(
                    id=task_send_params.id,
                    sessionId=task_send_params.sessionId,
                    messages=[task_send_params.message],  # Initial message starts conversation
                    status=TaskStatus(state=TaskState.SUBMITTED, timestamp=timestamp),
                    history=[task_send_params.message],  # History also starts with initial message
                    metadata=task_send_params.metadata.copy() if task_send_params.metadata else None,
                    artifacts=[]  # Initialize artifacts list
                )
                self.tasks[task_send_params.id] = task
            else:
                logger.info(f"Appending message to existing task {task_send_params.id}")
                # Append user message to history
                if task.history is None: task.history = []
                task.history.append(task_send_params.message)
                # If task was completed/failed, maybe transition back to working? Depends on logic.
                # For simplicity, let's assume sending a new message restarts or continues.
                task.status.state = TaskState.WORKING  # Or re-submitted? Let's say WORKING
                task.status.timestamp = timestamp
                task.status.message = None  # Clear previous agent message from status
                # Update metadata if provided
                if task_send_params.metadata:
                    if task.metadata is None: task.metadata = {}
                    task.metadata.update(task_send_params.metadata)

            return task.model_copy(deep=True)  # Return a copy

    async def on_resubscribe_to_task(
            self, request: TaskResubscriptionRequest
    ) -> Union[AsyncIterable[SendTaskStreamingResponse], JSONRPCResponse]:
        logger.info(f"Resubscribe requested for task {request.params.id}")
        task_id = request.params.id
        request_id = request.id

        async with self.lock:
            task = self.tasks.get(task_id)
            if task is None:
                return JSONRPCResponse(id=request_id, error=TaskNotFoundError())

            # Check if task is in a final state already
            if task.status.state in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELED]:
                logger.info(f"Task {task_id} is already final ({task.status.state}). Sending final status.")
                # Send just the final status update event
                final_event = TaskStatusUpdateEvent(
                    id=task.id, status=task.status, final=True
                )

                async def final_event_generator():
                    yield SendTaskStreamingResponse(id=request_id, result=final_event)

                return final_event_generator()  # Return as async iterable

        # Task exists and is potentially ongoing, set up SSE consumer
        try:
            logger.info(f"Setting up SSE consumer for task {task_id} resubscription.")
            sse_event_queue = await self.setup_sse_consumer(task_id, is_resubscribe=True)
            # Start dequeuing and yielding events
            return self.dequeue_events_for_sse(request_id, task_id, sse_event_queue)
        except ValueError as e:  # Catch "Task not found for resubscription" from setup_sse_consumer
            logger.error(f"Error during resubscription setup for task {task_id}: {e}")
            # This case indicates an internal inconsistency if the task existed moments ago
            return JSONRPCResponse(id=request_id, error=InternalError(message=str(e)))
        except Exception as e:
            logger.error(f"Unexpected error during resubscription setup for task {task_id}: {e}", exc_info=True)
            return JSONRPCResponse(id=request_id, error=InternalError(message="Failed to set up resubscription stream"))

    async def update_store(
            self, task_id: str, status: TaskStatus, artifacts: List[Artifact] | None = None
    ) -> Task:
        """
        Updates the task in the store with new status and artifacts.
        Also notifies SSE subscribers.
        """
        async with self.lock:
            try:
                task = self.tasks[task_id]
            except KeyError:
                logger.error(f"Task {task_id} not found for updating the task")
                raise ValueError(f"Task {task_id} not found")  # Let caller handle

            is_final_state = status.state in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELED]

            # Update task fields
            task.status = status
            if status.message is not None:
                if task.history is None: task.history = []
                task.history.append(status.message)  # Add agent response to history

            if artifacts:
                if task.artifacts is None:
                    task.artifacts = []
                task.artifacts.extend(artifacts)

            # Create event for SSE
            task_update_event = TaskStatusUpdateEvent(
                id=task_id,
                status=status,
                final=is_final_state,
                # metadata could be added here if needed
            )

            logger.debug(f"Task {task_id} updated to state {status.state}. Final: {is_final_state}")

            # Enqueue for SSE subscribers (non-blocking)
            asyncio.create_task(self.enqueue_events_for_sse(task_id, task_update_event))

            # If artifacts were added, also send artifact events
            if artifacts:
                for artifact in artifacts:
                    artifact_event = TaskArtifactUpdateEvent(id=task_id, artifact=artifact)
                    asyncio.create_task(self.enqueue_events_for_sse(task_id, artifact_event))

            # If the state is final, remove the task from SSE subscribers after a short delay?
            # Or let dequeue handle it when the final event is sent. Let dequeue handle it.

            return task.model_copy(deep=True)  # Return a copy

    def append_task_history(self, task: Task, historyLength: int | None) -> Task:
        """Creates a copy of the task with history potentially truncated."""
        new_task = task.model_copy(deep=True)
        if new_task.history is None:
            new_task.history = []

        if historyLength is None:
            # Default behavior: maybe return full history or none? Let's return none if None specified.
            new_task.history = []
            logger.debug(f"Task {task.id}: History omitted as historyLength is None.")
        elif historyLength == 0:
            new_task.history = []
            logger.debug(f"Task {task.id}: History omitted as historyLength is 0.")
        elif historyLength > 0 and len(new_task.history) > historyLength:
            original_len = len(new_task.history)
            new_task.history = new_task.history[-historyLength:]
            logger.debug(f"Task {task.id}: History truncated from {original_len} to {len(new_task.history)} messages (historyLength={historyLength}).")
        # else: history is already shorter than or equal to historyLength, do nothing

        return new_task

    # --- SSE Helper Methods for Tasks ---

    async def setup_sse_consumer(self, task_id: str, is_resubscribe: bool = False) -> asyncio.Queue[SendTaskStreamingResponse]:
        """Sets up a queue for a new SSE subscriber for a given task."""
        async with self.subscriber_lock:
            if task_id not in self.task_sse_subscribers:
                if is_resubscribe:
                    # This check ensures we don't create subscriber lists for tasks that don't exist on resubscribe
                    logger.error(f"Task {task_id} not found for resubscription setup.")
                    raise ValueError("Task not found for resubscription")
                else:
                    logger.info(f"Initializing SSE subscriber list for new task {task_id}.")
                    self.task_sse_subscribers[task_id] = []

            # Unlimited queue size allows the producer (update_store) not to block,
            # but consumers must keep up or memory could grow.
            sse_event_queue: asyncio.Queue[SendTaskStreamingResponse] = asyncio.Queue(maxsize=0)
            self.task_sse_subscribers[task_id].append(sse_event_queue)
            logger.info(f"Added SSE subscriber queue for task {task_id}. Total subscribers: {len(self.task_sse_subscribers[task_id])}")
            return sse_event_queue

    async def enqueue_events_for_sse(self, task_id: str, event: Union[TaskStatusUpdateEvent, TaskArtifactUpdateEvent, JSONRPCError]):
        """Puts an event into the queues of all subscribers for a task."""
        async with self.subscriber_lock:
            if task_id not in self.task_sse_subscribers:
                logger.debug(f"No SSE subscribers found for task {task_id} to enqueue event.")
                return  # No subscribers to notify

            subscribers = self.task_sse_subscribers[task_id]
            if not subscribers:
                logger.debug(f"Subscriber list empty for task {task_id}.")
                return

            logger.debug(f"Enqueuing event {type(event)} for {len(subscribers)} subscribers of task {task_id}.")
            response_event = SendTaskStreamingResponse(result=event) if not isinstance(event, JSONRPCError) else SendTaskStreamingResponse(error=event)

            # Use asyncio.gather to put into all queues concurrently (though put is usually fast)
            put_tasks = [queue.put(response_event) for queue in subscribers]
            await asyncio.gather(*put_tasks)

            # If it's a final event, the dequeue logic will handle cleanup.

    async def dequeue_events_for_sse(
            self, request_id: str | int | None, task_id: str, sse_event_queue: asyncio.Queue[SendTaskStreamingResponse]
    ) -> AsyncIterable[SendTaskStreamingResponse]:
        """Dequeues events from a specific subscriber's queue and yields them."""
        is_final = False
        try:
            while True:
                event_response = await sse_event_queue.get()
                # Assign the correct request_id to the response before yielding
                event_response.id = request_id
                yield event_response
                sse_event_queue.task_done()  # Mark task as done

                # Check if the event indicates the end of the stream
                if event_response.error:
                    logger.info(f"Error event dequeued for task {task_id}, request {request_id}. Stopping stream.")
                    is_final = True
                    break
                if isinstance(event_response.result, TaskStatusUpdateEvent) and event_response.result.final:
                    logger.info(f"Final event dequeued for task {task_id}, request {request_id}. Stopping stream.")
                    is_final = True
                    break
        except asyncio.CancelledError:
            logger.info(f"SSE dequeue task cancelled for task {task_id}, request {request_id}.")
            # Propagate cancellation if needed, or just clean up
            raise
        finally:
            # Clean up the queue from the subscriber list
            async with self.subscriber_lock:
                if task_id in self.task_sse_subscribers:
                    try:
                        self.task_sse_subscribers[task_id].remove(sse_event_queue)
                        logger.info(
                            f"Removed SSE subscriber queue for task {task_id}, request {request_id}. Remaining: {len(self.task_sse_subscribers[task_id])}")
                        # If no subscribers left and task is final, clean up the entry? Optional.
                        if not self.task_sse_subscribers[task_id] and is_final:
                            logger.info(f"Last subscriber for final task {task_id} removed. Cleaning up task subscriber entry.")
                            del self.task_sse_subscribers[task_id]
                    except ValueError:
                        # Queue already removed, maybe due to concurrent cleanup? Log warning.
                        logger.warning(f"SSE queue for task {task_id}, request {request_id} was already removed.")
                else:
                    logger.warning(f"Task ID {task_id} not found in subscriber list during cleanup for request {request_id}.")

    # --- Knowledge Method Implementations (Placeholders) ---

    async def on_knowledge_query(self, request: KnowledgeQueryRequest) -> KnowledgeQueryResponse:
        """
        Handles knowledge/query requests.
        Placeholder implementation: Returns UnsupportedOperationError.
        A real implementation requires a KG backend and GraphQL engine.
        """
        logger.warning(f"Received knowledge/query request for task {request.params.taskId}, but it is not implemented.")
        # In a real implementation:
        # 1. Validate query syntax (e.g., GraphQL parsing)
        # 2. Check permissions/alignment based on request.params.metadata
        # 3. Execute query against the knowledge graph using a GraphQL engine
        # 4. Filter results based on certainty, age etc.
        # 5. Format the result according to KnowledgeQueryResponseResult
        # 6. Handle potential errors (syntax, execution, not found, permission)
        return KnowledgeQueryResponse(
            id=request.id,
            error=UnsupportedOperationError(message="knowledge/query not implemented")
        )

    async def on_knowledge_update(self, request: KnowledgeUpdateRequest) -> KnowledgeUpdateResponse:
        """
        Handles knowledge/update requests.
        Placeholder implementation: Returns UnsupportedOperationError.
        A real implementation requires KG write access and verification logic.
        """
        logger.warning(f"Received knowledge/update request for task {request.params.taskId}, but it is not implemented.")
        # In a real implementation:
        # 1. Check permissions/alignment for update based on metadata, sourceAgentId
        # 2. Validate proposed patches (KnowledgeGraphPatch list)
        # 3. Potentially stage changes for verification/approval
        # 4. Apply changes to the knowledge graph (add/remove statements)
        # 5. Record provenance and justification
        # 6. Return success status and details
        # 7. Handle potential errors (conflict, constraint violation, permission)
        return KnowledgeUpdateResponse(
            id=request.id,
            error=UnsupportedOperationError(message="knowledge/update not implemented")
        )

    async def on_knowledge_subscribe(
            self, request: KnowledgeSubscribeRequest
    ) -> Union[AsyncIterable[KnowledgeSubscriptionEvent], JSONRPCResponse]:
        """
        Handles knowledge/subscribe requests.
        Placeholder implementation: Returns UnsupportedOperationError.
        A real implementation requires a subscription manager and event bus tied to KG changes.
        """
        logger.warning(f"Received knowledge/subscribe request for task {request.params.taskId}, but it is not implemented.")
        # In a real implementation:
        # 1. Validate subscription query syntax (e.g., GraphQL subscription parsing)
        # 2. Check permissions/alignment for subscription
        # 3. Generate a unique subscription ID
        # 4. Register the subscription query with a knowledge event bus/manager
        # 5. Set up an SSE queue similar to task subscriptions
        # 6. When the event bus detects relevant KG changes:
        #    a. Format the change as KnowledgeGraphChangeEvent
        #    b. Create KnowledgeSubscriptionEvent response
        #    c. Enqueue the response to the subscriber's queue
        # 7. Return the async iterable that dequeues from the queue
        # 8. Handle errors (invalid query, permission denied, subscription lifecycle)
        return JSONRPCResponse(
            id=request.id,
            error=UnsupportedOperationError(message="knowledge/subscribe not implemented")
        )
