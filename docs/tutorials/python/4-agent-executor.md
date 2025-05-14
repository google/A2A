# 4. The Agent Executor

The core logic of how an A2A agent processes requests and generates responses/events is handled by an **Agent Executor**. The A2A Python SDK provides an abstract base class `a2a.server.agent_execution.AgentExecutor` that you implement.

## `AgentExecutor` Interface

The `AgentExecutor` class defines two primary methods:

- `async def execute(self, context: RequestContext, event_queue: EventQueue)`: Handles incoming requests that expect a response or a stream of events. It processes the user's input (available via `context`) and uses the `event_queue` to send back `Message`, `Task`, `TaskStatusUpdateEvent`, or `TaskArtifactUpdateEvent` objects.
- `async def cancel(self, context: RequestContext, event_queue: EventQueue)`: Handles requests to cancel an ongoing task.

The `RequestContext` provides information about the incoming request, such as the user's message and any existing task details. The `EventQueue` is used by the executor to send events back to the client.

## Helloworld Agent Executor

Let's look at `examples/helloworld/agent_executor.py`. It defines `HelloWorldAgentExecutor`.

1. **The Agent (`HelloWorldAgent`)**:
    This is a simple helper class that encapsulates the actual "business logic".

    ```python { .no-copy }
    # examples/helloworld/agent_executor.py
    class HelloWorldAgent:
        """Hello World Agent."""

        async def invoke(self) -> str:
            return 'Hello World'
    ```

    It has a simple `invoke` method that returns the string "Hello World".

2. **The Executor (`HelloWorldAgentExecutor`)**:
    This class implements the `AgentExecutor` interface.

    - **`__init__`**:

        ```python { .no-copy }
        # examples/helloworld/agent_executor.py
        from typing_extensions import override

        from a2a.server.agent_execution import AgentExecutor, RequestContext
        from a2a.server.events import EventQueue
        from a2a.utils import new_agent_text_message


        class HelloWorldAgentExecutor(AgentExecutor):
            """Test AgentProxy Implementation."""

            def __init__(self):
                self.agent = HelloWorldAgent()
        ```

        It instantiates the `HelloWorldAgent`.

    - **`execute`**:

        ```python { .no-copy }
        # examples/helloworld/agent_executor.py
            @override
            async def execute(
                self,
                context: RequestContext,
                event_queue: EventQueue,
            ) -> None:
                result = await self.agent.invoke()
                event_queue.enqueue_event(new_agent_text_message(result))
        ```

        When a `message/send` or `message/stream` request comes in (both are handled by `execute` in this simplified executor):

        1. It calls `self.agent.invoke()` to get the "Hello World" string.
        2. It creates an A2A `Message` object using the `new_agent_text_message` utility function.
        3. It enqueues this message onto the `event_queue`. The underlying `DefaultRequestHandler` will then process this queue to send the response(s) to the client. For a single message like this, it will result in a single response for `message/send` or a single event for `message/stream` before the stream closes.

    - **`cancel`**:
        The Helloworld example's `cancel` method simply raises an exception, indicating that cancellation is not supported for this basic agent.

        ```python { .no-copy }
        # examples/helloworld/agent_executor.py
            @override
            async def cancel(
                self, context: RequestContext, event_queue: EventQueue
            ) -> None:
                raise Exception('cancel not supported')
        ```

The `AgentExecutor` acts as the bridge between the A2A protocol (managed by the request handler and server application) and your agent's specific logic. It receives context about the request and uses an event queue to communicate results or updates back.
