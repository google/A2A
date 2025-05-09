# Advanced Example: Integrating a LangGraph Agent

Now that we've covered the basics with the HelloWorld example and discussed agent capabilities like streaming, let's explore a more sophisticated A2A agent: the LangGraph Currency Conversion agent. This example is located in the `a2a-python-sdk/examples/langgraph/` directory.

This agent demonstrates several advanced concepts:

- **Integration with a popular agent framework**: It uses LangGraph to define the agent's logic and tool usage.
- **Use of external tools**: The agent calls an external currency conversion API (Frankfurter.app) via a LangGraph tool.
- **Management of task state**: It uses a `TaskStore` to maintain the context of conversations, enabling multi-turn interactions.
- **Streaming of intermediate steps and final results**: Clients can receive real-time updates as the agent works.

## LangGraph Currency Agent Overview

The `CurrencyAgent` in this example is designed to:

- Understand user queries about currency exchange rates (e.g., "How much is 10 USD in EUR?").
- Use a LangGraph tool (`get_exchange_rate`) which internally calls the Frankfurter.app API to fetch live exchange rates.
- Respond to the user with the conversion information or an error message if the API call fails.
- Potentially ask clarifying questions if the user's query is ambiguous (handled by the LangGraph ReAct agent logic).

## Setup for the LangGraph Example

1. **Ensure the A2A SDK is Installed:**
    You should have already installed the A2A Python SDK from the `a2a-python-sdk` root directory as per the [Setup section](./2-setup.md) (`pip install .`). This makes the `a2a` package available in your virtual environment.

2. **Navigate to the Example Directory:**
    From the root of the `a2a-python-sdk` directory (ensure your main virtual environment, `.venv`, is activated):

    ```bash
    cd examples/langgraph
    ```

3. **Install LangGraph Example Dependencies:**
    The LangGraph example has its own set of additional dependencies, including `langgraph`, `langchain-google-genai`, `python-dotenv`, and `click`. Install them into your existing virtual environment:

    ```bash
    pip install .
    ```

    This command installs the dependencies listed in `examples/langgraph/pyproject.toml`.

4. **Set Your Google API Key:**
    This agent uses Google's Generative AI models (specifically Gemini Flash by default) via `langchain-google-genai` to power the LangGraph agent. You'll need a Google API key.
    Create a file named `.env` in the `a2a-python-sdk/examples/langgraph` directory with the following content:

    ```
    GOOGLE_API_KEY=YOUR_API_KEY_HERE
    ```

    Replace `YOUR_API_KEY_HERE` with your actual Google API key. You can obtain one from [Google AI Studio](https://aistudio.google.com/app/apikey).

## Code Highlights

Let's briefly look at the key files within `a2a-python-sdk/examples/langgraph/`:

- **`agent.py`**:
  - Defines the `CurrencyAgent` class, which encapsulates the LangGraph agent's logic.
  - It initializes a `ChatGoogleGenerativeAI` model (e.g., `gemini-2.0-flash`).
  - It defines a LangGraph tool named `get_exchange_rate` that makes an HTTP request to `https://api.frankfurter.app/` to fetch currency data.
  - It uses `langgraph.prebuilt.create_react_agent` to construct the agent with the LLM and the tool. This creates a ReAct (Reasoning and Acting) style agent.
  - The agent uses an in-memory `MemorySaver` checkpointer, allowing it to maintain conversation history for a given `sessionId` (which maps to `thread_id` in LangGraph).
  - The `CurrencyAgent` has an `invoke()` method (for non-streaming, though the example focuses on streaming) and an `async stream()` method that yields dictionaries representing the agent's progress and final answer.

    ```python
    # Snippet from examples/langgraph/agent.py
    # ...
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langgraph.prebuilt import create_react_agent
    # ...

    class CurrencyAgent:
        SYSTEM_INSTRUCTION = ( ... ) # Prompt for the agent
        # ...
        def __init__(self):
            self.model = ChatGoogleGenerativeAI(model='gemini-2.0-flash')
            self.tools = [get_exchange_rate] # Tool to fetch exchange rates
            self.graph = create_react_agent( # LangGraph agent
                self.model,
                tools=self.tools,
                checkpointer=memory, # In-memory checkpointer for session history
                # ...
            )
        # ...
        async def stream(
            self, query: str, sessionId: str # sessionId maps to LangGraph's thread_id
        ) -> AsyncIterable[dict[str, Any]]:
            inputs: dict[str, Any] = {'messages': [('user', query)]}
            config: RunnableConfig = {'configurable': {'thread_id': sessionId}}

            for item in self.graph.stream(inputs, config, stream_mode='values'):
                # Process and yield intermediate steps and final response
                # ...
            yield self.get_agent_response(config) # Yield final structured response
    ```

- **`agent_executor.py`**:
  - Defines `CurrencyAgentExecutor`, which implements the `a2a.server.AgentExecutor` interface. This class acts as the bridge between the A2A server infrastructure and the `CurrencyAgent`.
  - It is initialized with a `TaskStore` (an `InMemoryTaskStore` in this example) to save and manage the state of A2A `Task` objects.
  - `on_message_send`: Handles non-streaming requests. It invokes `self.agent.invoke()`, creates or updates a `Task` object in the `TaskStore`, and returns the `Task` in the `SendMessageResponse`.
  - `on_message_stream`: Handles streaming requests. It calls `self.agent.stream()` and, using helper functions from `helpers.py`, processes the dictionaries yielded by the `CurrencyAgent` into A2A-compatible `TaskStatusUpdateEvent` and `TaskArtifactUpdateEvent` objects. These events are then yielded back to the client via SSE. It also manages creating/updating the `Task` in the `TaskStore`.

    ```python
    # Snippet from examples/langgraph/agent_executor.py
    from helpers import create_task_obj, process_streaming_agent_response # ...
    # ...
    class CurrencyAgentExecutor(AgentExecutor):
        def __init__(self, task_store: TaskStore):
            self.agent = CurrencyAgent()
            self.task_store = task_store
        # ...
        async def on_message_stream( # type: ignore
            self, request: SendMessageStreamingRequest, task: Task | None
        ) -> AsyncGenerator[SendMessageStreamingResponse, None]:
            params: MessageSendParams = request.params
            query = self._get_user_query(params)

            if not task: # If no existing task, create a new one
                task = create_task_obj(params)
                await self.task_store.save(task)
            # ...
            # Iterate over responses from the LangGraph agent's stream method
            async for item in self.agent.stream(query, task.contextId):
                task_artifact_update_event, task_status_event = (
                    process_streaming_agent_response(task, item) # Convert to A2A events
                )
                if task_artifact_update_event:
                    yield SendMessageStreamingResponse(
                        root=SendMessageStreamingSuccessResponse(
                            id=request.id, result=task_artifact_update_event
                        )
                    )
                yield SendMessageStreamingResponse(
                    root=SendMessageStreamingSuccessResponse(
                        id=request.id, result=task_status_event
                    )
                )
    ```

- **`__main__.py`**:
  - Defines the `AgentCard` for the Currency Agent, advertising its skills and capabilities (including `streaming=True` and `pushNotifications=True`, though push is not fully implemented in this example's executor).
  - Initializes an `InMemoryTaskStore` to store task states.
  - Creates an instance of `CurrencyAgentExecutor`, passing the `task_store` to it.
  - This executor is then used with `DefaultA2ARequestHandler` (which also receives the `task_store` for direct task operations like `tasks/get`).
  - Finally, it starts the `A2AServer`.

    ```python
    # Snippet from examples/langgraph/__main__.py
    # ...
    from agent_executor import CurrencyAgentExecutor
    from a2a.server import A2AServer, DefaultA2ARequestHandler, InMemoryTaskStore
    # ...
    if __name__ == '__main__':
        # ... (load_dotenv, click options) ...
        task_store = InMemoryTaskStore() # For storing task states
        request_handler = DefaultA2ARequestHandler(
            agent_executor=CurrencyAgentExecutor(task_store=task_store),
            task_store=task_store, # Handler also uses task_store for /tasks/get etc.
        )
        server = A2AServer(
            agent_card=get_agent_card(host, port), # get_agent_card defines the AgentCard
            request_handler=request_handler
        )
        server.start(host=host, port=port) # Starts Uvicorn server
    ```

## Running the LangGraph Agent Server

1. Ensure your `.env` file in `examples/langgraph/` is correctly configured with your `GOOGLE_API_KEY`.
2. From the `a2a-python-sdk/examples/langgraph` directory (with your virtual environment activated):

    ```bash
    python __main__.py
    ```

    The server will start, typically listening on `http://localhost:10000` (this can be configured with `--host` and `--port` options). Check the console output for the exact address.

## Interacting with the LangGraph Agent

The LangGraph example also includes a `test_client.py` script.

1. **Keep the LangGraph agent server running in one terminal.**
2. **Open a new terminal window.**
3. Navigate to the `a2a-python-sdk/examples/langgraph` directory.
4. Activate the same virtual environment:
    - On macOS/Linux: `source ../../.venv/bin/activate`
    - On Windows: `..\..\.venv\Scripts\activate.bat` or `..\..\.venv\Scripts\Activate.ps1`
5. Run the test client:

    ```bash
    python test_client.py
    ```

The `test_client.py` for the LangGraph example demonstrates several scenarios:

- **Single-turn non-streaming request**: (`run_single_turn_test`) Asks for a currency conversion and gets a task object back. It then queries the task status.
- **Single-turn streaming request**: (`run_streaming_test`) Asks for a currency conversion and prints out the stream of events (intermediate steps like "Looking up exchange rates..." and final results).
- **Multi-turn non-streaming request**: (`run_multi_turn_test`) Simulates a conversation where the agent might ask for clarification. For example, if you ask "how much is 100 USD?", the agent (powered by the LLM) might respond with `TaskState.input_required` asking "In which currency?". The client script then sends a follow-up message "in GBP" using the same `contextId` (referred to as `sessionId` in the client payload, which maps to `Task.contextId`) to continue the task.

**Example Interaction Snippet (from `test_client.py` output for a streaming request):**

```
--- Single Turn Streaming Request ---
--- Streaming Chunk ---
{
  "root": {
    "jsonrpc": "2.0",
    "id": "...",
    "result": {
      "type": "status-update",
      "taskId": "...",
      "status": {
        "state": "working",
        "message": {
          "role": "agent",
          "parts": [ { "type": "text", "text": "Looking up the exchange rates..." } ],
          "messageId": "...", "contextId": "..."
        },
        "timestamp": "..."
      },
      "final": false
    }
  }
}
--- Streaming Chunk ---
{
  "root": {
    "jsonrpc": "2.0",
    "id": "...",
    "result": {
      "type": "status-update",
      "taskId": "...",
      "status": {
        "state": "working",
        "message": {
          "role": "agent",
          "parts": [ { "type": "text", "text": "Processing the exchange rates.." } ],
          "messageId": "...", "contextId": "..."
        },
        "timestamp": "..."
      },
      "final": false
    }
  }
}
--- Streaming Chunk ---
{
  "root": { // This might be an artifact update or the final status update with the message
    "jsonrpc": "2.0",
    "id": "...",
    "result": {
      "type": "artifact-update", // Or "status-update" with final message in status
      "taskId": "...",
      "artifact": {
         "artifactId": "...",
         "parts": [{"type":"text", "text":"50 EUR is approximately 7966.5 JPY based on the latest rates."}]
         // ...
      },
      "lastChunk": true // Or final:true in status-update
    }
  }
}
```

*(Actual output structure for the final result might vary slightly depending on how `process_streaming_agent_response` in `helpers.py` structures it as an artifact or a final status message).*

This LangGraph example provides a more complete and realistic illustration of how to build robust, stateful, and interactive A2A agents using the Python SDK and integrate them with powerful AI frameworks.
