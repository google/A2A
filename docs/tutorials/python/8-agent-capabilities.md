# Agent Capabilities: Streaming and Asynchronicity

The Agent2Agent (A2A) protocol is designed to handle more than just simple, immediate request-response interactions. Real-world agent collaborations often involve:

- **Streaming**: Receiving partial results or continuous updates as an agent processes a task. This is useful for providing immediate feedback or handling large amounts of data incrementally.
- **Long-Running Tasks**: Operations that might take considerable time to complete, where the client shouldn't block waiting for a single response.
- **Multi-Turn Conversations**: Interactions where the agent might need to ask clarifying questions or provide intermediate feedback before reaching a final result.

A2A supports these through Server-Sent Events (SSE) for streaming and by defining task lifecycle states that allow for asynchronous operations and further client input.

## Streaming with Server-Sent Events (SSE)

As demonstrated by our HelloWorld agent and its `test_client.py`, A2A supports streaming responses using SSE.

**Recap of Server-Side Streaming (`HelloWorldAgentExecutor`):**
The `on_message_stream` method in your `AgentExecutor` implementation is key for SSE.

```python
# From examples/helloworld/agent_executor.py
# ...
class HelloWorldAgentExecutor(AgentExecutor):
    # ...
    async def on_message_stream(
        self, request: SendMessageStreamingRequest, task: Task | None
    ) -> AsyncGenerator[SendMessageStreamingResponse, None]:
        async for chunk in self.agent.stream(): # self.agent.stream() is an async generator
            message = Message(
                role=Role.agent,
                parts=[Part(root=TextPart(text=chunk['content']))],
                messageId=str(uuid4()),
                final=chunk['done'], # Key for SSE: signals if this is the last chunk
            )
            yield SendMessageStreamingResponse(
                root=SendMessageStreamingSuccessResponse(id=request.id, result=message)
            )
```

When an `AgentExecutor`'s `on_message_stream` method is an `async def` that `yields` `SendMessageStreamingResponse` objects, the `A2AServer` (via `DefaultA2ARequestHandler` and `Starlette`) automatically handles:

1. Establishing an SSE connection with the client.
2. Sending each `yielded` response as an individual server-sent event.
The `message.final` attribute in the yielded `Message` object is crucial: when `True`, it indicates to the client that this is the last piece of the current streamed response for that particular request.

**Recap of Client-Side SSE Handling (`test_client.py`):**

```python
# From examples/helloworld/test_client.py
# ...
        stream_response_generator = client.send_message_streaming(
            payload=send_message_payload
        )
        async for chunk in stream_response_generator: # Iterates over SSE events
            # Each 'chunk' is a SendMessageStreamingResponse
            print(chunk.model_dump_json(exclude_none=True, indent=2))
```

The `A2AClient.send_message_streaming()` method returns an `AsyncGenerator`. The client code can then use `async for` to iterate over this generator, processing each `SendMessageStreamingResponse` (each SSE event) as it arrives from the server.

**Advertising Streaming Capability in `AgentCard`:**
To formally let clients know that an agent supports streaming, its `AgentCard` should set the `streaming` capability to `true`.

```python
# In __main__.py for an agent that supports streaming
# (e.g., if we were to update HelloWorld's AgentCard explicitly)
    agent_card = AgentCard(
        # ... other fields ...
        capabilities=AgentCapabilities(streaming=True), # Explicitly enable streaming
        # ...
    )
```

While our `HelloWorldAgentExecutor` *does* implement `on_message_stream`, its `AgentCard` in `__main__.py` currently initializes `AgentCapabilities()` with no arguments, meaning `streaming` defaults to `None` (which is effectively `False` if a client strictly checks this capability before attempting a streaming call). For production agents, accurately reflecting capabilities in the Agent Card is important.

## Handling Task State and Multi-Turn Interactions

Beyond simple request-response or one-way streams, A2A is designed for complex, stateful tasks that might involve multiple back-and-forth exchanges.

- **The `Task` Object**: As defined in `a2a.types.Task` and the [A2A Specification](../specification.md#61-task-object), the `Task` object is central to managing the state of an interaction. It includes:
  - `id`: A unique identifier for the task.
  - `contextId` (previously `sessionId` in older drafts): For grouping related messages or tasks within a broader conversational context.
  - `status`: A `TaskStatus` object indicating the current `TaskState` (e.g., `submitted`, `working`, `input_required`, `completed`, `failed`), an optional `Message` providing context for that status, and a `timestamp`.
  - `history`: An optional list of `Message` objects exchanged so far.
  - `artifacts`: A list of outputs generated by the agent.

- **`TaskStore`**: The `a2a.server.TaskStore` (with `InMemoryTaskStore` as a basic implementation) allows the server-side `A2ARequestHandler` to persist and retrieve `Task` state. This is crucial for multi-turn interactions where the task's context needs to be maintained across multiple client requests.

- **`TaskState.input_required`**: A key state for multi-turn dialogues. If an agent needs more information from the client to proceed with a task, its `AgentExecutor` can:
    1. Update the `Task` object's status to `TaskState.input_required`.
    2. Include a `Message` in `Task.status.message` that prompts the user for the necessary input.
    3. Save the updated `Task` to the `TaskStore`.
    The client, upon receiving this status (either as a direct response or via a stream update), would then gather the required input and send a new `message/send` or `message/sendStream` request. This new request **must use the same `Task.id`** (and typically the same `Task.contextId`) to allow the server to retrieve the existing task context and continue processing.

The HelloWorld example, being very simple, doesn't deeply utilize `TaskStore` or the `input_required` state for complex dialogues because its interactions are typically one-shot. However, the infrastructure within the SDK's `DefaultA2ARequestHandler` is prepared to use a `TaskStore` if the `AgentExecutor`'s responses involve `Task` objects that evolve over time.

The `LangGraph` example, which we will explore in the next section, provides a more comprehensive demonstration of these advanced capabilities, including:

- Creating and persisting `Task` objects.
- Using a `TaskStore` (specifically `InMemoryTaskStore`).
- Streaming intermediate "thinking" steps or progress updates.
- Potentially transitioning a task to `TaskState.input_required` if the LangGraph agent needs clarification.
- Updating the task with final results or artifacts upon completion.

These features are essential for building A2A agents that can engage in meaningful, stateful, and potentially lengthy collaborations.

In the next section, we'll dive into the `LangGraph` example to see these more advanced concepts in action.
