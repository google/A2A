# 7. Streaming & Multi-Turn Interactions (LangGraph Example)

The Helloworld example demonstrates the basic mechanics of A2A. For more advanced features like robust streaming, task state management, and multi-turn conversations powered by an LLM, we'll turn to the `langgraph` example located in `a2a-python/examples/langgraph/`.

This example features a "Currency Agent" that uses the Gemini model via LangChain and LangGraph to answer currency conversion questions.

## Setting up the LangGraph Example

1. Create a [Gemini API Key](https://ai.google.dev/gemini-api/docs/api-key), if you don't already have one.

2. **Environment Variable:**

    Create a `.env` file in the `a2a-python/examples/langgraph/` directory:

    ```bash
    # In a2a-python/examples/langgraph/
    echo "GOOGLE_API_KEY=YOUR_API_KEY_HERE" > .env
    ```

    Replace `YOUR_API_KEY_HERE` with your actual Gemini API key.

3. **Install Dependencies (if not already covered):**
    The `langgraph` example has its own `pyproject.toml` which includes dependencies like `langchain-google-genai` and `langgraph`. When you installed the SDK from the `a2a-python` root using `pip install -e .[dev]`, this should have also installed the dependencies for the workspace examples, including `langgraph-example`. If you encounter import errors, ensure your primary SDK installation from the root directory was successful.

## Running the LangGraph Server

Navigate to the `a2a-python/examples/langgraph/` directory in your terminal and ensure your virtual environment (from the SDK root) is activated.

Start the LangGraph agent server:

```bash
# From a2a-python/examples/langgraph/
python __main__.py
```

This will start the server, usually on `http://localhost:10000`.

## Interacting with the LangGraph Agent

Open a **new terminal window**, activate your virtual environment, and navigate to `a2a-python/examples/langgraph/`.

Run its test client:

```bash
# From a2a-python/examples/langgraph/
python test_client.py
```

Now, you can shut down the server by typing Ctrl+C in the terminal window where `__main__.py` is running.

## Key Features Demonstrated

The `langgraph` example showcases several important A2A concepts:

1. **LLM Integration**:

    - `examples/langgraph/agent.py` defines `CurrencyAgent`. It uses `ChatGoogleGenerativeAI` and LangGraph's `create_react_agent` to process user queries.
    - This demonstrates how a real LLM can power the agent's logic.

2. **Task State Management**:

    - `examples/langgraph/__main__.py` initializes a `DefaultRequestHandler` with an `InMemoryTaskStore`.
        ```python { .no-copy }
        # examples/langgraph/__main__.py
        request_handler = DefaultRequestHandler(
            agent_executor=CurrencyAgentExecutor(),
            task_store=InMemoryTaskStore(),
        )
        ```
    - The `CurrencyAgentExecutor` (in `examples/langgraph/agent_executor.py`), when its `execute` method is called by the `DefaultRequestHandler`, interacts with the `RequestContext` which contains the current task (if any).
    - For `message/send`, the `DefaultRequestHandler` uses the `TaskStore` to persist and retrieve task state across interactions. The response to `message/send` will be a full `Task` object if the agent's execution flow involves multiple steps or results in a persistent task.
    - The `test_client.py`'s `run_single_turn_test` demonstrates getting a `Task` object back and then querying it using `get_task`.

3. **Streaming with `TaskStatusUpdateEvent` and `TaskArtifactUpdateEvent`**:

    - The `execute` method in `CurrencyAgentExecutor` is responsible for handling both non-streaming and streaming requests, orchestrated by the `DefaultRequestHandler`.
    - As the LangGraph agent processes the request (which might involve calling tools like `get_exchange_rate`), the `CurrencyAgentExecutor` enqueues different types of events onto the `EventQueue`:
        - `TaskStatusUpdateEvent`: For intermediate updates (e.g., "Looking up exchange rates...", "Processing the exchange rates.."). The `final` flag on these events is `False`.
        - `TaskArtifactUpdateEvent`: When the final answer is ready, it's enqueued as an artifact. The `lastChunk` flag is `True`.
        - A final `TaskStatusUpdateEvent` with `state=TaskState.completed` and `final=True` is sent to signify the end of the task for streaming.
    - The `test_client.py`'s `run_streaming_test` function will print these individual event chunks as they are received from the server.

4. **Multi-Turn Conversation (`TaskState.input_required`)**:

    - The `CurrencyAgent` can ask for clarification if a query is ambiguous (e.g., user asks "how much is 100 USD?").
    - When this happens, the `CurrencyAgentExecutor` will enqueue a `TaskStatusUpdateEvent` where `status.state` is `TaskState.input_required` and `status.message` contains the agent's question (e.g., "To which currency would you like to convert?"). This event will have `final=True` for the current interaction stream.
    - The `test_client.py`'s `run_multi_turn_test` function demonstrates this:
        - It sends an initial ambiguous query.
        - The agent responds (via the `DefaultRequestHandler` processing the enqueued events) with a `Task` whose status is `input_required`.
        - The client then sends a second message, including the `taskId` and `contextId` from the first turn's `Task` response, to provide the missing information ("in GBP"). This continues the same task.

## Exploring the Code

Take some time to look through these files in `examples/langgraph/`:

- `__main__.py`: Server setup using `A2AStarletteApplication` and `DefaultRequestHandler`. Note the `AgentCard` definition includes `capabilities.streaming=True`.
- `agent.py`: The `CurrencyAgent` with LangGraph, LLM model, and tool definitions.
- `agent_executor.py`: The `CurrencyAgentExecutor` implementing the `execute` (and `cancel`) method. It uses the `RequestContext` to understand the ongoing task and the `EventQueue` to send back various events (`TaskStatusUpdateEvent`, `TaskArtifactUpdateEvent`, new `Task` object implicitly via the first event if no task exists).
- `test_client.py`: Demonstrates various interaction patterns, including retrieving task IDs and using them for multi-turn conversations.

This example provides a much richer illustration of how A2A facilitates complex, stateful, and asynchronous interactions between agents.
