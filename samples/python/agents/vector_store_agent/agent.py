#!/usr/bin/env python3
"""
Vector Store Knowledge Agent

A general-purpose A2A agent that provides information from an OpenAI vector store.
This agent uses OpenAI's Responses API to query any vector store and return relevant
information based on the user's query.
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional, List, Generator, AsyncGenerator

try:
    from openai import OpenAI
except ImportError:
    print("Error: OpenAI package not installed. Install with 'pip install openai'")
    exit(1)

from common.types import (
    Message,
    TextPart,
    TaskState, 
    TaskStatus,
    Task,
    SendTaskRequest,
    SendTaskResponse,
    SendTaskStreamingRequest,
    SendTaskStreamingResponse,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
    Artifact,
    AgentCard,
    AgentProvider,
    AgentCapabilities,
    AgentSkill,
)

from common.server import A2AServer, InMemoryTaskManager
from .config import (
    OPENAI_API_KEY,
    DEFAULT_MODEL,
    VECTOR_STORE_ID,
    USE_MOCK,
    DEFAULT_HOST,
    DEFAULT_PORT,
    AGENT_NAME,
    AGENT_DESCRIPTION,
    AGENT_ORGANIZATION,
    DEFAULT_MAX_RESULTS,
    DEFAULT_MODEL_PROMPT,
    MOCK_RESPONSE_TEMPLATE,
    ENABLE_STREAMING,
    STREAMING_CHUNK_SIZE,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class VectorStoreAgent:
    def __init__(self, openai_client=None, vector_store_id=None):
        """
        Initialize the Vector Store Agent with the necessary configurations.

        Args:
            openai_client: OpenAI client, if None a new one will be created
            vector_store_id: ID of the vector store to query
        """
        self.openai_client = openai_client or OpenAI(api_key=OPENAI_API_KEY)
        self.vector_store_id = vector_store_id or VECTOR_STORE_ID
        self.use_mock = (
            not self.vector_store_id or self.vector_store_id == "mock-store-id"
        )

        if self.use_mock:
            logger.warning("No vector store ID provided. Using mock responses.")
        else:
            logger.info(f"Using vector store ID: {self.vector_store_id}")

        self.model = DEFAULT_MODEL
        self.max_results = DEFAULT_MAX_RESULTS
        self.prompt_template = DEFAULT_MODEL_PROMPT

    async def process_query(self, query: str) -> str:
        """
        Process a user query by searching the vector store and returning relevant information.

        Args:
            query: The user's query string

        Returns:
            A formatted string response containing information from the vector store
        """
        if self.use_mock:
            return MOCK_RESPONSE_TEMPLATE.format(query=query)

        try:
            logger.info(
                f"Querying vector store for: '{query}' using Vector Store: {self.vector_store_id}"
            )
            logger.info(f"Using model: {self.model}")

            response = self.openai_client.responses.create(
                input=self.prompt_template.format(query=query),
                model=self.model,
                tools=[
                    {"type": "file_search", "vector_store_ids": [self.vector_store_id]}
                ],
                tool_choice={"type": "file_search"},
            )

            assistant_response = "Error: Could not extract response from API output."
            if response.output:
                for output_item in response.output:
                    if (
                        hasattr(output_item, "role")
                        and output_item.role == "assistant"
                        and hasattr(output_item, "content")
                        and output_item.content
                    ):
                        if hasattr(output_item.content[0], "text"):
                            assistant_response = output_item.content[0].text
                            break

            model_info = f"\n\n_Response generated using {self.model}_"
            return assistant_response + model_info

        except Exception as e:
            logger.error(f"Error querying vector store: {e}")
            return f"Error: Unable to query the vector store. {str(e)}"

    async def stream_query(self, query: str) -> AsyncGenerator[str, None]:
        """
        Stream a response from the vector store for a given query.

        Args:
            query: The user's query string

        Yields:
            Chunks of the response as they become available
        """
        if self.use_mock:
            yield MOCK_RESPONSE_TEMPLATE.format(query=query)
            return

        try:
            logger.info(
                f"Streaming response for query: '{query}' using Vector Store: {self.vector_store_id}"
            )
            logger.info(f"Using model: {self.model}")
            
            stream = self.openai_client.responses.create(
                input=self.prompt_template.format(query=query),
                model=self.model,
                tools=[
                    {"type": "file_search", "vector_store_ids": [self.vector_store_id]}
                ],
                tool_choice={"type": "file_search"},
                stream=True,
            )
            
            assistant_response = ""
            model_info_added = False
            
            for chunk in stream:
                logger.debug(f"Received chunk type: {type(chunk).__name__}")
                
                text_chunk = None
                
                if hasattr(chunk, "choices") and chunk.choices:
                    choice = chunk.choices[0]
                    if hasattr(choice, "delta") and hasattr(choice.delta, "content"):
                        text_chunk = choice.delta.content
                elif hasattr(chunk, "delta"):
                    text_chunk = chunk.delta
                elif hasattr(chunk, "content"):
                    text_chunk = chunk.content
                
                if text_chunk:
                    assistant_response += text_chunk
                    yield text_chunk
            
            if not model_info_added:
                model_info = f"\n\n_Response generated using {self.model}_"
                assistant_response += model_info
                yield model_info
                    
        except Exception as e:
            logger.error(f"Error streaming from vector store: {e}")
            yield f"Error: Unable to stream from the vector store. {str(e)}"


class VectorStoreTaskManager(InMemoryTaskManager):
    def __init__(self, agent: VectorStoreAgent):
        """
        Initialize the task manager with the Vector Store Agent.

        Args:
            agent: The VectorStoreAgent instance to use for processing queries
        """
        super().__init__()
        self.agent = agent

    def _extract_query(self, params: Any) -> str:
        """Helper to extract text query from task parameters."""
        message_text = ""
        if params and hasattr(params, "message") and hasattr(params.message, "parts"):
            for part in params.message.parts:
                if hasattr(part, "text"):
                    message_text += part.text
        if not message_text:
            logger.warning("Could not extract text query from message parts.")
            raise ValueError("No text query found in the message.")
        logger.info(f"Extracted message text: '{message_text}'")
        return message_text

    async def _invoke_agent(self, query: str, task_id: str, session_id: str) -> Task:
        """Handles the synchronous agent invocation and task update."""
        try:
            result = await self.agent.process_query(query)
            status = TaskStatus(
                state=TaskState.COMPLETED,
                message=Message(
                    role="agent", parts=[TextPart(type="text", text=result)]
                ),
            )
            task = await self.update_store(
                task_id,
                status,
                [
                    Artifact(parts=[TextPart(type="text", text=result)])
                ],
            )
            return task
        except Exception as e:
            logger.error(f"Error invoking agent for task {task_id}: {e}", exc_info=True)
            status = TaskStatus(
                state=TaskState.FAILED,
                message=Message(
                    role="agent", parts=[TextPart(type="text", text=f"Error: {str(e)}")]
                ),
            )
            task = await self.update_store(task_id, status, None)
            return task

    async def _run_streaming_agent(
        self, query: str, task_id: str, session_id: str
    ) -> AsyncGenerator[Task, None]:
        """Handles the streaming agent invocation and yields task updates."""
        initial_status = TaskStatus(
            state=TaskState.WORKING,
            message=Message(
                role="agent",
                parts=[TextPart(type="text", text="Starting vector store query...")],
            ),
        )
        task = await self.update_store(task_id, initial_status, None)
        yield task

        try:
            if not ENABLE_STREAMING:
                result = await self.agent.process_query(query)
                final_status = TaskStatus(
                    state=TaskState.COMPLETED,
                    message=Message(
                        role="agent", parts=[TextPart(type="text", text=result)]
                    ),
                )
                task = await self.update_store(
                    task_id,
                    final_status,
                    [
                        Artifact(parts=[TextPart(type="text", text=result)])
                    ],
                )
                yield task
                return

            full_response = ""
            current_chunk = ""
            chunk_size = STREAMING_CHUNK_SIZE
            
            async for chunk in self.agent.stream_query(query):
                full_response += chunk
                current_chunk += chunk
                
                if len(current_chunk) >= chunk_size:
                    chunk_status = TaskStatus(
                        state=TaskState.WORKING,
                        message=Message(
                            role="agent",
                            parts=[TextPart(type="text", text=current_chunk)],
                        ),
                    )
                    task = await self.update_store(task_id, chunk_status, None)
                    yield task
                    
                    current_chunk = ""
            
            if current_chunk:
                chunk_status = TaskStatus(
                    state=TaskState.WORKING,
                    message=Message(
                        role="agent",
                        parts=[TextPart(type="text", text=current_chunk)],
                    ),
                )
                task = await self.update_store(task_id, chunk_status, None)
                yield task

            final_status = TaskStatus(
                state=TaskState.COMPLETED,
                message=Message(
                    role="agent", parts=[TextPart(type="text", text=full_response)]
                ),
            )
            task = await self.update_store(
                task_id,
                final_status,
                [
                    Artifact(parts=[TextPart(type="text", text=full_response)])
                ],
            )
            yield task
        except Exception as e:
            logger.error(
                f"Error during agent streaming for task {task_id}: {e}", exc_info=True
            )
            final_status = TaskStatus(
                state=TaskState.FAILED,
                message=Message(
                    role="agent", parts=[TextPart(type="text", text=f"Error: {str(e)}")]
                ),
            )
            task = await self.update_store(task_id, final_status, None)
            yield task

    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """
        Handle a send task request synchronously.

        Args:
            request: The task request parameters

        Returns:
            Response containing the task results
        """
        params = request.params
        logger.info(f"Received task request: {params}")

        if not params or not params.message or not params.message.parts:
            logger.error("Invalid task request parameters.")
            raise ValueError("Invalid task parameters")

        await self.upsert_task(params)
        await self.update_store(params.id, TaskStatus(state=TaskState.WORKING), None)

        try:
            query = self._extract_query(params)
            task_result = await self._invoke_agent(query, params.id, params.sessionId)
            return SendTaskResponse(id=request.id, result=task_result)

        except Exception as e:
            logger.error(f"Error processing task {params.id}: {e}", exc_info=True)
            status = TaskStatus(
                state=TaskState.FAILED,
                message=Message(
                    role="agent",
                    parts=[TextPart(text=f"Internal Server Error: {str(e)}")],
                ),
            )
            try:
                failed_task = await self.update_store(params.id, status, None)
                return SendTaskResponse(id=request.id, result=failed_task)
            except Exception as update_err:
                logger.error(
                    f"Failed to update task {params.id} to FAILED state: {update_err}"
                )
                raise

    async def on_send_task_subscribe(
        self, request: SendTaskStreamingRequest
    ) -> AsyncGenerator[SendTaskStreamingResponse, None]:
        """
        Handle a streaming task request.

        Args:
            request: The task request parameters

        Yields:
            Task updates wrapped in SendTaskStreamingResponse
        """
        params = request.params
        logger.info(f"Received streaming task request: {params.id}")

        if not params or not params.message or not params.message.parts:
            logger.error("Invalid streaming task request parameters.")
            raise ValueError("Invalid task parameters")

        await self.upsert_task(params)
        await self.update_store(params.id, TaskStatus(state=TaskState.WORKING), None)

        sse_event_queue = await self.setup_sse_consumer(params.id, is_resubscribe=False)

        try:
            query = self._extract_query(params)

            async def event_producer():
                try:
                    async for task_update in self._run_streaming_agent(
                        query, params.id, params.sessionId
                    ):
                        event = TaskStatusUpdateEvent(
                            id=task_update.id,
                            status=task_update.status,
                            final=(
                                task_update.status.state
                                in [
                                    TaskState.COMPLETED,
                                    TaskState.FAILED,
                                    TaskState.CANCELED,
                                ]
                            ),
                        )
                        await self.enqueue_events_for_sse(params.id, event)

                        if (
                            task_update.status.state == TaskState.COMPLETED
                            and task_update.artifacts
                        ):
                            for artifact in task_update.artifacts:
                                artifact_event = TaskArtifactUpdateEvent(
                                    id=task_update.id, artifact=artifact
                                )
                                await self.enqueue_events_for_sse(
                                    params.id, artifact_event
                                )

                except Exception as e:
                    logger.error(
                        f"Error in event producer for task {params.id}: {e}",
                        exc_info=True,
                    )
                    error_status = TaskStatus(
                        state=TaskState.FAILED,
                        message=Message(
                            role="agent",
                            parts=[TextPart(text=f"Streaming Error: {str(e)}")],
                        ),
                    )
                    error_event = TaskStatusUpdateEvent(
                        id=params.id, status=error_status, final=True
                    )
                    await self.enqueue_events_for_sse(params.id, error_event)
                finally:
                    logger.info(f"Event producer finished for task {params.id}")

            asyncio.create_task(event_producer())

            return self.dequeue_events_for_sse(request.id, params.id, sse_event_queue)  # type: ignore

        except Exception as e:
            logger.error(
                f"Error setting up streaming for task {params.id}: {e}", exc_info=True
            )
            raise


def run_server(host="0.0.0.0", port=10050):
    """Initialize and run the A2A server with the Vector Store agent"""

    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        logger.warning(
            "OPENAI_API_KEY environment variable not set. Some features may not work."
        )

    vector_store_id = os.environ.get("VECTOR_STORE_ID")
    if not vector_store_id:
        logger.warning("VECTOR_STORE_ID environment variable not set. Using mock mode.")
        vector_store_id = "mock-store-id"

    logger.info(f"Using Vector Store ID: {vector_store_id}")

    logger.info("Initializing Vector Store Agent...")
    openai_client = OpenAI(api_key=openai_api_key)
    vector_store_agent = VectorStoreAgent(openai_client, vector_store_id)

    logger.info("Initializing Task Manager...")
    task_manager = VectorStoreTaskManager(vector_store_agent)

    logger.info("Configuring A2A Server...")
    agent_card = AgentCard(
        name=AGENT_NAME,
        description=AGENT_DESCRIPTION,
        url=f"http://{host}:{port}/",
        provider=AgentProvider(organization=AGENT_ORGANIZATION),
        version="1.0.0",
        capabilities=AgentCapabilities(
            streaming=True, pushNotifications=False, stateTransitionHistory=False
        ),
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        skills=[
            AgentSkill(
                id="vector_store_knowledge_retrieval",
                name="vector_store_knowledge_retrieval",
                description="Retrieve information from a vector store based on natural language queries",
            )
        ],
    )

    server = A2AServer(
        host=host,
        port=port,
        endpoint="/",
        agent_card=agent_card,
        task_manager=task_manager,
    )

    server.start()


if __name__ == "__main__":
    run_server()
