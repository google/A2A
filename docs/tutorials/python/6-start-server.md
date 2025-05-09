# Starting the A2A Server

With the Agent Card defined, the next step is to implement the server logic that will handle incoming A2A requests and execute the agent's capabilities. The A2A Python SDK provides classes to help build this server in a structured way.

## Core Server Components in the SDK

1. **`AgentExecutor` (from `a2a.server`)**:
    - This is an abstract base class (ABC) that you must implement.
    - It defines methods corresponding to the core A2A RPC calls related to task and message handling, such as:
        - `on_message_send(request, task)`: For handling non-streaming `message/send` requests.
        - `on_message_stream(request, task)`: For handling streaming `message/sendStream` requests, returning an `AsyncGenerator`.
        - `on_cancel(request, task)`: For handling `tasks/cancel` requests.
        - `on_resubscribe(request, task)`: For handling `tasks/resubscribe` requests for streaming.
    - Your agent's specific logic for how it processes these requests and generates responses goes into your implementation of these methods.

2. **`A2ARequestHandler` (e.g., `DefaultA2ARequestHandler` from `a2a.server`)**:
    - This class takes your `AgentExecutor` implementation.
    - It is responsible for the lower-level details of:
        - Receiving incoming, validated A2A JSON-RPC requests.
        - Routing these requests to the appropriate method on your `AgentExecutor`.
        - Managing task state if a `TaskStore` is provided (for more complex agents that handle persistent tasks).

3. **`A2AServer` (from `a2a.server`)**:
    - This class orchestrates the entire server setup.
    - It takes the `AgentCard` (which describes your agent) and an instance of `A2ARequestHandler`.
    - Under the hood, it uses `Starlette` (a lightweight ASGI framework) and `Uvicorn` (an ASGI server) to create and run the HTTP server. This server listens for A2A requests at the URL specified in your Agent Card and also serves the Agent Card itself (typically at `/.well-known/agent.json`).

## HelloWorld Server Implementation

Let's examine how these components are used in the `a2a-python-sdk/examples/helloworld/` directory:

### 1. `HelloWorldAgentExecutor` (in `agent_executor.py`)

This class provides the concrete implementation for the `AgentExecutor` interface, defining how the HelloWorld agent behaves.

```python
# From examples/helloworld/agent_executor.py
import asyncio
from collections.abc import AsyncGenerator
from typing import Any
from uuid import uuid4

from a2a.server import AgentExecutor # Base class
from a2a.types import (
    CancelTaskRequest, CancelTaskResponse, JSONRPCErrorResponse, Message, Part, Role,
    SendMessageRequest, SendMessageResponse, SendMessageStreamingRequest,
    SendMessageStreamingResponse, SendMessageStreamingSuccessResponse,
    SendMessageSuccessResponse, Task, TaskResubscriptionRequest, TextPart,
    UnsupportedOperationError,
)

class HelloWorldAgent:
    """A simple agent that can return 'Hello World' or stream it."""
    async def invoke(self):
        return 'Hello World'

    async def stream(self) -> AsyncGenerator[dict[str, Any], None]:
        yield {'content': 'Hello ', 'done': False}
        await asyncio.sleep(0.1) # Simulate a small delay for demonstration
        yield {'content': 'World', 'done': True}

class HelloWorldAgentExecutor(AgentExecutor):
    """HelloWorld AgentExecutor Implementation."""
    def __init__(self):
        self.agent = HelloWorldAgent() # The actual "logic" part

    async def on_message_send(
        self, request: SendMessageRequest, task: Task | None # Task is not used in this simple example
    ) -> SendMessageResponse:
        """Handles non-streaming message/send requests."""
        result_text = await self.agent.invoke()
        response_message = Message(
            role=Role.agent,
            parts=[Part(root=TextPart(text=result_text))],
            messageId=str(uuid4()),
        )
        # For a simple agent not managing persistent tasks,
        # we can return the message directly in the success response.
        return SendMessageResponse(
            root=SendMessageSuccessResponse(id=request.id, result=response_message)
        )

    async def on_message_stream(
        self, request: SendMessageStreamingRequest, task: Task | None # Task is not used here
    ) -> AsyncGenerator[SendMessageStreamingResponse, None]:
        """Handles streaming message/sendStream requests."""
        async for chunk in self.agent.stream():
            stream_message = Message(
                role=Role.agent,
                parts=[Part(root=TextPart(text=chunk['content']))],
                messageId=str(uuid4()),
                final=chunk['done'], # Crucial for SSE: signals if this is the last chunk
            )
            yield SendMessageStreamingResponse(
                root=SendMessageStreamingSuccessResponse(id=request.id, result=stream_message)
            )

    # For methods not explicitly supported by this simple agent,
    # we return an UnsupportedOperationError.
    async def on_cancel(
        self, request: CancelTaskRequest, task: Task
    ) -> CancelTaskResponse:
        return CancelTaskResponse(
            root=JSONRPCErrorResponse(id=request.id, error=UnsupportedOperationError())
        )

    async def on_resubscribe(
        self, request: TaskResubscriptionRequest, task: Task
    ) -> AsyncGenerator[SendMessageStreamingResponse, None]:
        yield SendMessageStreamingResponse(
            root=JSONRPCErrorResponse(id=request.id, error=UnsupportedOperationError())
        )
```

**Key Points for `HelloWorldAgentExecutor`:**

- It instantiates a `HelloWorldAgent` which contains the very simple logic.
- `on_message_send`: Handles synchronous requests. It invokes the agent, gets the "Hello World" string, and packages it into an A2A `Message` within a `SendMessageSuccessResponse`.
- `on_message_stream`: Handles streaming requests. It iterates over the chunks produced by `self.agent.stream()` (which is an async generator) and yields each chunk as a `SendMessageStreamingSuccessResponse` containing an A2A `Message`. The `final` attribute on the `Message` is set to `True` for the last chunk.
- Other methods like `on_cancel` and `on_resubscribe` are implemented to return an `UnsupportedOperationError`, as this basic agent doesn't manage complex task lifecycles or resubscriptions.

### 2. Server Setup in `__main__.py`

This script ties all the components together to start the server:

```python
# From examples/helloworld/__main__.py
from agent_executor import HelloWorldAgentExecutor # Our AgentExecutor implementation
from a2a.server import A2AServer, DefaultA2ARequestHandler # SDK components
from a2a.types import (
    AgentAuthentication, AgentCapabilities, AgentCard, AgentSkill, # Types for AgentCard
)

if __name__ == '__main__':
    # Define the skill (as shown in "Agent Skills" section)
    skill = AgentSkill(
        id='hello_world',
        name='Returns hello world',
        description='just returns hello world',
        tags=['hello world'],
        examples=['hi', 'hello world'],
    )

    # Define the AgentCard (as shown in "Add Agent Card" section)
    agent_card = AgentCard(
        name='Hello World Agent',
        description='Just a hello world agent',
        url='http://localhost:9999/',
        version='1.0.0',
        defaultInputModes=['text'],
        defaultOutputModes=['text'],
        capabilities=AgentCapabilities(), # Default capabilities
        skills=[skill],
        authentication=AgentAuthentication(schemes=['public']),
    )

    # Create the request handler with our agent executor
    request_handler = DefaultA2ARequestHandler(
        agent_executor=HelloWorldAgentExecutor()
    )

    # Create and start the A2A server
    server = A2AServer(agent_card=agent_card, request_handler=request_handler)
    server.start(host='0.0.0.0', port=9999)
```

**Sequence of setup:**

1. The `AgentSkill` and `AgentCard` are defined.
2. An instance of our `HelloWorldAgentExecutor` is created.
3. This executor is passed to `DefaultA2ARequestHandler`. For this simple example, we're not explicitly providing a `TaskStore`, so the `DefaultA2ARequestHandler` will use a transient, in-memory one if its task-related features were engaged (they are minimally used by HelloWorld's direct responses).
4. The `agent_card` and the `request_handler` are used to initialize the `A2AServer`.
5. `server.start(host='0.0.0.0', port=9999)` launches the Uvicorn server, making the HelloWorld A2A agent available at `http://localhost:9999/`. The server will also serve its Agent Card at `http://localhost:9999/.well-known/agent.json`.

## Running the Server

As you did in the previous "Create Project" step:

1. Make sure your virtual environment is activated.
2. Navigate to the `a2a-python-sdk/examples/helloworld` directory in your terminal.
3. Run the main script:

    ```bash
    python __main__.py
    ```

The server will start, and you'll see Uvicorn's output indicating it's running and listening on port 9999.

Your A2A server for the HelloWorld agent is now live and ready to receive requests! In the next step, we'll use the provided `test_client.py` to interact with it.
