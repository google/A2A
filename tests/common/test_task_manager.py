import unittest

from collections.abc import AsyncIterable

from common.server.task_manager import InMemoryTaskManager
from common.types import (
    Artifact,
    CancelTaskRequest,
    CancelTaskResponse,
    GetTaskPushNotificationRequest,
    GetTaskPushNotificationResponse,
    GetTaskRequest,
    GetTaskResponse,
    JSONRPCError,
    JSONRPCResponse,
    Message,
    PushNotificationConfig,
    SendTaskRequest,
    SendTaskResponse,
    SendTaskStreamingRequest,
    SendTaskStreamingResponse,
    SetTaskPushNotificationRequest,
    SetTaskPushNotificationResponse,
    Task,
    TaskIdParams,
    TaskNotCancelableError,
    TaskNotFoundError,
    TaskPushNotificationConfig,
    TaskQueryParams,
    TaskResubscriptionRequest,
    TaskSendParams,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
    UnsupportedOperationError,
)


class TestTaskManager(InMemoryTaskManager):
    __test__ = False

    def __init__(self):
        super().__init__()

    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        pass

    async def on_send_task_subscribe(
        self, request: SendTaskStreamingRequest
    ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        pass


class TestInMemoryTaskManager(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.task_manager = TestTaskManager()

    def get_test_message(self, role='agent', text='Test Message'):
        return Message(role=role, parts=[TextPart(text=text)])

    async def test_on_get_task_success(self):
        task_id = 'test_task'
        task = Task(
            id=task_id,
            messages=[self.get_test_message()],
            status=TaskStatus(state=TaskState.SUBMITTED),
        )
        self.task_manager.tasks[task_id] = task
        request = GetTaskRequest(id='1', params=TaskQueryParams(id=task_id))
        response = await self.task_manager.on_get_task(request)
        self.assertIsInstance(response, GetTaskResponse)
        self.assertEqual(response.result.id, task_id)

    async def test_on_get_task_not_found(self):
        request = GetTaskRequest(
            id='1', params=TaskQueryParams(id='nonexistent_task')
        )
        response = await self.task_manager.on_get_task(request)
        self.assertIsInstance(response, GetTaskResponse)
        self.assertIsInstance(response.error, TaskNotFoundError)

    async def test_on_cancel_task_success(self):
        task_id = 'test_task'
        task = Task(
            id=task_id,
            messages=[self.get_test_message()],
            status=TaskStatus(state=TaskState.SUBMITTED),
        )
        self.task_manager.tasks[task_id] = task
        request = CancelTaskRequest(id='1', params=TaskIdParams(id=task_id))
        response = await self.task_manager.on_cancel_task(request)
        self.assertIsInstance(response, CancelTaskResponse)
        self.assertIsInstance(response.error, TaskNotCancelableError)

    async def test_on_cancel_task_not_found(self):
        request = CancelTaskRequest(
            id='1', params=TaskIdParams(id='nonexistent_task')
        )
        response = await self.task_manager.on_cancel_task(request)
        self.assertIsInstance(response, CancelTaskResponse)
        self.assertIsInstance(response.error, TaskNotFoundError)

    async def test_on_send_task(self):
        request = SendTaskRequest(
            id='1',
            params=TaskSendParams(
                id='test_task', message=self.get_test_message(role='user')
            ),
        )
        with self.assertRaises(TypeError):
            # invoking abstract class should raise exception
            task_manager = InMemoryTaskManager()
            await task_manager.on_send_task(request)

    async def test_on_send_task_subscribe(self):
        request = SendTaskStreamingRequest(
            id='1',
            params=TaskSendParams(
                id='test_task', message=self.get_test_message(role='user')
            ),
        )
        with self.assertRaises(TypeError):
            task_manager = InMemoryTaskManager()
            await task_manager.on_send_task_subscribe(request)

    async def test_on_set_task_push_notification(self):
        task_send_params = TaskSendParams(
            id='test_task', message=self.get_test_message(role='user')
        )
        await self.task_manager.upsert_task(task_send_params)

        request = SetTaskPushNotificationRequest(
            id='1',
            params=TaskPushNotificationConfig(
                id='test_task',
                pushNotificationConfig=PushNotificationConfig(
                    url='http://test.com', token='token'
                ),
            ),
        )
        response = await self.task_manager.on_set_task_push_notification(
            request
        )
        self.assertIsInstance(response, SetTaskPushNotificationResponse)
        self.assertIsInstance(response.result, TaskPushNotificationConfig)

    async def test_on_get_task_push_notification(self):
        task_send_params = TaskSendParams(
            id='test_task', message=self.get_test_message(role='user')
        )
        await self.task_manager.upsert_task(task_send_params)

        request = GetTaskPushNotificationRequest(
            id='1', params=TaskIdParams(id='test_task')
        )
        response = await self.task_manager.on_get_task_push_notification(
            request
        )
        self.assertIsInstance(response, GetTaskPushNotificationResponse)
        assert response.result is None

    async def test_upsert_task_new(self):
        task_send_params = TaskSendParams(
            id='new_task', message=self.get_test_message(role='user')
        )
        task = await self.task_manager.upsert_task(task_send_params)
        self.assertEqual(task.id, 'new_task')
        self.assertEqual(len(self.task_manager.tasks), 1)
        self.assertEqual(task.status.state, TaskState.SUBMITTED)

    async def test_upsert_task_existing(self):
        task_send_params = TaskSendParams(
            id='existing_task', message=self.get_test_message(role='user')
        )
        await self.task_manager.upsert_task(task_send_params)
        task_send_params2 = TaskSendParams(
            id='existing_task',
            message=self.get_test_message(role='agent', text='agent message'),
        )
        task = await self.task_manager.upsert_task(task_send_params2)
        self.assertEqual(task.id, 'existing_task')
        self.assertEqual(len(self.task_manager.tasks), 1)
        self.assertEqual(len(task.history), 2)

    async def test_on_resubscribe_to_task(self):
        request = TaskResubscriptionRequest(
            id='1', params=TaskIdParams(id='test_task')
        )
        response = await self.task_manager.on_resubscribe_to_task(request)
        self.assertIsInstance(response, JSONRPCResponse)
        self.assertIsInstance(response.error, UnsupportedOperationError)

    async def test_update_store_success(self):
        task_id = 'test_task'
        task = Task(
            id=task_id,
            messages=[self.get_test_message()],
            status=TaskStatus(state=TaskState.SUBMITTED),
            history=[self.get_test_message()],
        )
        self.task_manager.tasks[task_id] = task
        new_status = TaskStatus(
            state=TaskState.COMPLETED,
            message=self.get_test_message(role='agent', text='completed'),
        )
        artifacts = [Artifact(parts=[TextPart(text='artifact')])]
        updated_task = await self.task_manager.update_store(
            task_id, new_status, artifacts
        )
        self.assertEqual(updated_task.status.state, TaskState.COMPLETED)
        self.assertEqual(len(updated_task.history), 2)
        self.assertEqual(len(updated_task.artifacts), 1)

    async def test_update_store_task_not_found(self):
        with self.assertRaises(ValueError):
            await self.task_manager.update_store(
                'nonexistent_task', TaskStatus(state=TaskState.COMPLETED), []
            )

    async def test_append_task_history_with_length(self):
        task = Task(
            id='test_task',
            messages=[self.get_test_message()],
            status=TaskStatus(state=TaskState.SUBMITTED),
            history=[
                self.get_test_message(role='agent', text=f'Message {i}')
                for i in range(5)
            ],
        )
        new_task = self.task_manager.append_task_history(task, 3)
        self.assertEqual(len(new_task.history), 3)
        self.assertEqual(new_task.history[0].parts[0].text, 'Message 2')

    async def test_append_task_history_no_length(self):
        task = Task(
            id='test_task',
            messages=[self.get_test_message()],
            status=TaskStatus(state=TaskState.SUBMITTED),
            history=[
                self.get_test_message(role='agent', text=f'Message {i}')
                for i in range(5)
            ],
        )
        new_task = self.task_manager.append_task_history(task, None)
        self.assertEqual(len(new_task.history), 0)

    async def test_setup_sse_consumer_new_task(self):
        task_id = 'new_task'
        sse_queue = await self.task_manager.setup_sse_consumer(task_id)
        self.assertIsNotNone(sse_queue)
        self.assertIn(task_id, self.task_manager.task_sse_subscribers)
        self.assertEqual(
            len(self.task_manager.task_sse_subscribers[task_id]), 1
        )

    async def test_setup_sse_consumer_existing_task(self):
        task_id = 'existing_task'
        await self.task_manager.setup_sse_consumer(task_id)
        sse_queue = await self.task_manager.setup_sse_consumer(task_id)
        self.assertIsNotNone(sse_queue)
        self.assertEqual(
            len(self.task_manager.task_sse_subscribers[task_id]), 2
        )

    async def test_setup_sse_consumer_resubscribe_not_found(self):
        task_id = 'nonexistent_task'
        with self.assertRaises(ValueError):
            await self.task_manager.setup_sse_consumer(
                task_id, is_resubscribe=True
            )

    async def test_enqueue_events_for_sse_no_task(self):
        task_id = 'new_task'
        task_update_event = TaskStatusUpdateEvent(
            id=task_id, final=False, status=TaskStatus(state=TaskState.WORKING)
        )
        await self.task_manager.enqueue_events_for_sse(
            task_id, task_update_event
        )
        self.assertNotIn(task_id, self.task_manager.task_sse_subscribers)

    async def test_enqueue_events_for_sse_existing_task(self):
        task_id = 'existing_task'
        sse_queue = await self.task_manager.setup_sse_consumer(task_id)
        task_update_event = TaskStatusUpdateEvent(
            id=task_id, final=False, status=TaskStatus(state=TaskState.WORKING)
        )
        await self.task_manager.enqueue_events_for_sse(
            task_id, task_update_event
        )
        retrieved_event = await sse_queue.get()
        self.assertEqual(retrieved_event, task_update_event)

    async def test_dequeue_events_for_sse_success(self):
        task_id = 'test_task'
        request_id = '1'
        sse_queue = await self.task_manager.setup_sse_consumer(task_id)
        task_update_event = TaskStatusUpdateEvent(
            id=task_id, final=True, status=TaskStatus(state=TaskState.COMPLETED)
        )
        await self.task_manager.enqueue_events_for_sse(
            task_id, task_update_event
        )
        async for response in self.task_manager.dequeue_events_for_sse(
            request_id, task_id, sse_queue
        ):
            self.assertIsInstance(response, SendTaskStreamingResponse)
            self.assertEqual(response.result, task_update_event)
            break

    async def test_dequeue_events_for_sse_error(self):
        task_id = 'test_task'
        request_id = '1'
        sse_queue = await self.task_manager.setup_sse_consumer(task_id)
        error_event = JSONRPCError(code=1, message='Test Error')
        await self.task_manager.enqueue_events_for_sse(task_id, error_event)
        async for response in self.task_manager.dequeue_events_for_sse(
            request_id, task_id, sse_queue
        ):
            self.assertIsInstance(response, SendTaskStreamingResponse)
            self.assertIsInstance(response.error, JSONRPCError)
            break

    async def test_dequeue_events_for_sse_cleanup(self):
        task_id = 'test_task'
        request_id = '1'
        sse_queue = await self.task_manager.setup_sse_consumer(task_id)
        task_update_event = TaskStatusUpdateEvent(
            id=task_id, final=True, status=TaskStatus(state=TaskState.COMPLETED)
        )
        await self.task_manager.enqueue_events_for_sse(
            task_id, task_update_event
        )
        async for _ in self.task_manager.dequeue_events_for_sse(
            request_id, task_id, sse_queue
        ):
            pass
        self.assertEqual(
            len(self.task_manager.task_sse_subscribers[task_id]), 0
        )
