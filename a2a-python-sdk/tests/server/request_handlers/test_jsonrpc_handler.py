import unittest
import unittest.async_case

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from a2a.server.agent_execution import AgentExecutor
from a2a.server.events import (
    QueueManager,
)
from a2a.server.events.event_queue import EventQueue
from a2a.server.request_handlers import (
    DefaultRequestHandler,
    JSONRPCHandler,
)
from a2a.server.tasks import TaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    Artifact,
    CancelTaskRequest,
    CancelTaskSuccessResponse,
    GetTaskRequest,
    GetTaskResponse,
    GetTaskSuccessResponse,
    JSONRPCErrorResponse,
    Message,
    MessageSendParams,
    Part,
    SendMessageRequest,
    SendMessageSuccessResponse,
    SendStreamingMessageRequest,
    SendStreamingMessageSuccessResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskIdParams,
    TaskNotFoundError,
    TaskQueryParams,
    TaskResubscriptionRequest,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils.errors import ServerError


MINIMAL_TASK: dict[str, Any] = {
    'id': 'task_123',
    'contextId': 'session-xyz',
    'status': {'state': 'submitted'},
    'type': 'task',
}
MESSAGE_PAYLOAD: dict[str, Any] = {
    'role': 'agent',
    'parts': [{'text': 'test message'}],
    'messageId': '111',
}


class TestJSONRPCtHandler(unittest.async_case.IsolatedAsyncioTestCase):
    @pytest.fixture(autouse=True)
    def init_fixtures(self) -> None:
        self.mock_agent_card = MagicMock(
            spec=AgentCard, url='http://agent.example.com/api'
        )

    async def test_on_get_task_success(self) -> None:
        mock_agent_executor = AsyncMock(spec=AgentExecutor)
        mock_task_store = AsyncMock(spec=TaskStore)
        request_handler = DefaultRequestHandler(
            mock_agent_executor, mock_task_store
        )
        handler = JSONRPCHandler(self.mock_agent_card, request_handler)
        task_id = 'test_task_id'
        mock_task = Task(**MINIMAL_TASK)
        mock_task_store.get.return_value = mock_task
        request = GetTaskRequest(id='1', params=TaskQueryParams(id=task_id))
        response: GetTaskResponse = await handler.on_get_task(request)
        self.assertIsInstance(response.root, GetTaskSuccessResponse)
        assert response.root.result == mock_task  # type: ignore
        mock_task_store.get.assert_called_once_with(task_id)

    async def test_on_get_task_not_found(self) -> None:
        mock_agent_executor = AsyncMock(spec=AgentExecutor)
        mock_task_store = AsyncMock(spec=TaskStore)
        request_handler = DefaultRequestHandler(
            mock_agent_executor, mock_task_store
        )
        handler = JSONRPCHandler(self.mock_agent_card, request_handler)
        mock_task_store.get.return_value = None
        request = GetTaskRequest(
            id='1',
            method='tasks/get',
            params=TaskQueryParams(id='nonexistent_id'),
        )
        response: GetTaskResponse = await handler.on_get_task(request)
        self.assertIsInstance(response.root, JSONRPCErrorResponse)
        assert response.root.error == TaskNotFoundError()  # type: ignore

    async def test_on_cancel_task_success(self) -> None:
        mock_agent_executor = AsyncMock(spec=AgentExecutor)
        mock_task_store = AsyncMock(spec=TaskStore)
        request_handler = DefaultRequestHandler(
            mock_agent_executor, mock_task_store
        )
        handler = JSONRPCHandler(self.mock_agent_card, request_handler)
        task_id = 'test_task_id'
        mock_task = Task(**MINIMAL_TASK)
        mock_task_store.get.return_value = mock_task
        mock_agent_executor.cancel.return_value = None

        async def streaming_coro():
            yield mock_task

        with patch(
            'a2a.server.request_handlers.default_request_handler.EventConsumer.consume_all',
            return_value=streaming_coro(),
        ):
            request = CancelTaskRequest(id='1', params=TaskIdParams(id=task_id))
            response = await handler.on_cancel_task(request)
            assert mock_agent_executor.cancel.call_count == 1
            self.assertIsInstance(response.root, CancelTaskSuccessResponse)
            assert response.root.result == mock_task  # type: ignore
            mock_agent_executor.cancel.assert_called_once()

    async def test_on_cancel_task_not_supported(self) -> None:
        mock_agent_executor = AsyncMock(spec=AgentExecutor)
        mock_task_store = AsyncMock(spec=TaskStore)
        request_handler = DefaultRequestHandler(
            mock_agent_executor, mock_task_store
        )
        handler = JSONRPCHandler(self.mock_agent_card, request_handler)
        task_id = 'test_task_id'
        mock_task = Task(**MINIMAL_TASK)
        mock_task_store.get.return_value = mock_task
        mock_agent_executor.cancel.return_value = None

        async def streaming_coro():
            raise ServerError(UnsupportedOperationError())
            yield

        with patch(
            'a2a.server.request_handlers.default_request_handler.EventConsumer.consume_all',
            return_value=streaming_coro(),
        ):
            request = CancelTaskRequest(id='1', params=TaskIdParams(id=task_id))
            response = await handler.on_cancel_task(request)
            assert mock_agent_executor.cancel.call_count == 1
            self.assertIsInstance(response.root, JSONRPCErrorResponse)
            assert response.root.error == UnsupportedOperationError()  # type: ignore
            mock_agent_executor.cancel.assert_called_once()

    async def test_on_cancel_task_not_found(self) -> None:
        mock_agent_executor = AsyncMock(spec=AgentExecutor)
        mock_task_store = AsyncMock(spec=TaskStore)
        request_handler = DefaultRequestHandler(
            mock_agent_executor, mock_task_store
        )
        handler = JSONRPCHandler(self.mock_agent_card, request_handler)
        mock_task_store.get.return_value = None
        request = CancelTaskRequest(
            id='1',
            method='tasks/cancel',
            params=TaskIdParams(id='nonexistent_id'),
        )
        response = await handler.on_cancel_task(request)
        self.assertIsInstance(response.root, JSONRPCErrorResponse)
        assert response.root.error == TaskNotFoundError()  # type: ignore
        mock_task_store.get.assert_called_once_with('nonexistent_id')
        mock_agent_executor.cancel.assert_not_called()

    async def test_on_message_new_message_success(self) -> None:
        mock_agent_executor = AsyncMock(spec=AgentExecutor)
        mock_task_store = AsyncMock(spec=TaskStore)
        request_handler = DefaultRequestHandler(
            mock_agent_executor, mock_task_store
        )
        handler = JSONRPCHandler(self.mock_agent_card, request_handler)
        mock_task = Task(**MINIMAL_TASK)
        mock_task_store.get.return_value = mock_task
        mock_agent_executor.execute.return_value = None

        async def streaming_coro():
            yield mock_task

        with patch(
            'a2a.server.request_handlers.default_request_handler.EventConsumer.consume_all',
            return_value=streaming_coro(),
        ):
            request = SendMessageRequest(
                id='1',
                params=MessageSendParams(message=Message(**MESSAGE_PAYLOAD)),
            )
            response = await handler.on_message_send(request)
            assert mock_agent_executor.execute.call_count == 1
            self.assertIsInstance(response.root, SendMessageSuccessResponse)
            assert response.root.result == mock_task  # type: ignore
            mock_agent_executor.execute.assert_called_once()

    async def test_on_message_new_message_with_existing_task_success(
        self,
    ) -> None:
        mock_agent_executor = AsyncMock(spec=AgentExecutor)
        mock_task_store = AsyncMock(spec=TaskStore)
        request_handler = DefaultRequestHandler(
            mock_agent_executor, mock_task_store
        )
        handler = JSONRPCHandler(self.mock_agent_card, request_handler)
        mock_task = Task(**MINIMAL_TASK)
        mock_task_store.get.return_value = mock_task
        mock_agent_executor.execute.return_value = None

        async def streaming_coro():
            yield mock_task

        with patch(
            'a2a.server.request_handlers.default_request_handler.EventConsumer.consume_all',
            return_value=streaming_coro(),
        ):
            request = SendMessageRequest(
                id='1',
                params=MessageSendParams(
                    message=Message(
                        **MESSAGE_PAYLOAD,
                        taskId=mock_task.id,
                        contextId=mock_task.contextId,
                    )
                ),
            )
            response = await handler.on_message_send(request)
            assert mock_agent_executor.execute.call_count == 1
            self.assertIsInstance(response.root, SendMessageSuccessResponse)
            assert response.root.result == mock_task  # type: ignore
            mock_agent_executor.execute.assert_called_once()

    async def test_on_message_error(self) -> None:
        mock_agent_executor = AsyncMock(spec=AgentExecutor)
        mock_task_store = AsyncMock(spec=TaskStore)
        request_handler = DefaultRequestHandler(
            mock_agent_executor, mock_task_store
        )
        handler = JSONRPCHandler(self.mock_agent_card, request_handler)
        mock_task_store.get.return_value = None
        mock_agent_executor.execute.return_value = None

        async def streaming_coro():
            raise ServerError(error=UnsupportedOperationError())
            yield

        with patch(
            'a2a.server.request_handlers.default_request_handler.EventConsumer.consume_all',
            return_value=streaming_coro(),
        ):
            request = SendMessageRequest(
                id='1',
                params=MessageSendParams(
                    message=Message(
                        **MESSAGE_PAYLOAD,
                    )
                ),
            )
            response = await handler.on_message_send(request)

            self.assertIsInstance(response.root, JSONRPCErrorResponse)
            assert response.root.error == UnsupportedOperationError()  # type: ignore
            mock_agent_executor.execute.assert_called_once()

    async def test_on_message_stream_new_message_success(self) -> None:
        mock_agent_executor = AsyncMock(spec=AgentExecutor)
        mock_task_store = AsyncMock(spec=TaskStore)
        request_handler = DefaultRequestHandler(
            mock_agent_executor, mock_task_store
        )
        self.mock_agent_card.capabilities = AgentCapabilities(streaming=True)

        handler = JSONRPCHandler(self.mock_agent_card, request_handler)
        events: list[Any] = [
            Task(**MINIMAL_TASK),
            TaskArtifactUpdateEvent(
                taskId='task_123',
                contextId='session-xyz',
                artifact=Artifact(
                    artifactId='11', parts=[Part(TextPart(text='text'))]
                ),
            ),
            TaskStatusUpdateEvent(
                taskId='task_123',
                contextId='session-xyz',
                status=TaskStatus(state=TaskState.completed),
                final=True,
            ),
        ]

        async def streaming_coro():
            for event in events:
                yield event

        with patch(
            'a2a.server.request_handlers.default_request_handler.EventConsumer.consume_all',
            return_value=streaming_coro(),
        ):
            mock_task_store.get.return_value = None
            mock_agent_executor.execute.return_value = None
            request = SendStreamingMessageRequest(
                id='1',
                params=MessageSendParams(message=Message(**MESSAGE_PAYLOAD)),
            )
            response = handler.on_message_send_stream(request)
            assert isinstance(response, AsyncGenerator)
            collected_events: list[Any] = []
            async for event in response:
                collected_events.append(event)
            assert len(collected_events) == len(events)
            for i, event in enumerate(collected_events):
                assert isinstance(
                    event.root, SendStreamingMessageSuccessResponse
                )
                assert event.root.result == events[i]
            mock_agent_executor.execute.assert_called_once()

    async def test_on_message_stream_new_message_existing_task_success(
        self,
    ) -> None:
        mock_agent_executor = AsyncMock(spec=AgentExecutor)
        mock_task_store = AsyncMock(spec=TaskStore)
        request_handler = DefaultRequestHandler(
            mock_agent_executor, mock_task_store
        )

        self.mock_agent_card.capabilities = AgentCapabilities(streaming=True)

        handler = JSONRPCHandler(self.mock_agent_card, request_handler)
        mock_task = Task(**MINIMAL_TASK, history=[])
        events: list[Any] = [
            mock_task,
            TaskArtifactUpdateEvent(
                taskId='task_123',
                contextId='session-xyz',
                artifact=Artifact(
                    artifactId='11', parts=[Part(TextPart(text='text'))]
                ),
            ),
            TaskStatusUpdateEvent(
                taskId='task_123',
                contextId='session-xyz',
                status=TaskStatus(state=TaskState.working),
                final=True,
            ),
        ]

        async def streaming_coro():
            for event in events:
                yield event

        with patch(
            'a2a.server.request_handlers.default_request_handler.EventConsumer.consume_all',
            return_value=streaming_coro(),
        ):
            mock_task_store.get.return_value = mock_task
            mock_agent_executor.execute.return_value = None
            request = SendStreamingMessageRequest(
                id='1',
                params=MessageSendParams(
                    message=Message(
                        **MESSAGE_PAYLOAD,
                        taskId=mock_task.id,
                        contextId=mock_task.contextId,
                    )
                ),
            )
            response = handler.on_message_send_stream(request)
            assert isinstance(response, AsyncGenerator)
            collected_events: list[Any] = []
            async for event in response:
                collected_events.append(event)
            assert len(collected_events) == len(events)
            mock_agent_executor.execute.assert_called_once()
            assert mock_task.history is not None and len(mock_task.history) == 1

    async def test_on_resubscribe_existing_task_success(
        self,
    ) -> None:
        mock_agent_executor = AsyncMock(spec=AgentExecutor)
        mock_task_store = AsyncMock(spec=TaskStore)
        mock_queue_manager = AsyncMock(spec=QueueManager)
        request_handler = DefaultRequestHandler(
            mock_agent_executor, mock_task_store, mock_queue_manager
        )
        mock_agent_card = MagicMock(spec=AgentCard)
        handler = JSONRPCHandler(self.mock_agent_card, request_handler)
        mock_task = Task(**MINIMAL_TASK, history=[])
        events: list[Any] = [
            TaskArtifactUpdateEvent(
                taskId='task_123',
                contextId='session-xyz',
                artifact=Artifact(
                    artifactId='11', parts=[Part(TextPart(text='text'))]
                ),
            ),
            TaskStatusUpdateEvent(
                taskId='task_123',
                contextId='session-xyz',
                status=TaskStatus(state=TaskState.completed),
                final=True,
            ),
        ]

        async def streaming_coro():
            for event in events:
                yield event

        with patch(
            'a2a.server.request_handlers.default_request_handler.EventConsumer.consume_all',
            return_value=streaming_coro(),
        ):
            mock_task_store.get.return_value = mock_task
            mock_queue_manager.tap.return_value = EventQueue()
            request = TaskResubscriptionRequest(
                id='1', params=TaskIdParams(id=mock_task.id)
            )
            response = handler.on_resubscribe_to_task(request)
            assert isinstance(response, AsyncGenerator)
            collected_events: list[Any] = []
            async for event in response:
                collected_events.append(event)
            assert len(collected_events) == len(events)
            assert mock_task.history is not None and len(mock_task.history) == 0

    async def test_on_resubscribe_no_existing_task_error(self) -> None:
        mock_agent_executor = AsyncMock(spec=AgentExecutor)
        mock_task_store = AsyncMock(spec=TaskStore)
        request_handler = DefaultRequestHandler(
            mock_agent_executor, mock_task_store
        )
        handler = JSONRPCHandler(self.mock_agent_card, request_handler)
        mock_task_store.get.return_value = None
        request = TaskResubscriptionRequest(
            id='1', params=TaskIdParams(id='nonexistent_id')
        )
        response = handler.on_resubscribe_to_task(request)
        assert isinstance(response, AsyncGenerator)
        collected_events: list[Any] = []
        async for event in response:
            collected_events.append(event)
        assert len(collected_events) == 1
        self.assertIsInstance(collected_events[0].root, JSONRPCErrorResponse)
        assert collected_events[0].root.error == TaskNotFoundError()
