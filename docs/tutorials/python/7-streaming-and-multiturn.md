# 7. Streaming & Multi-Turn Interactions (LangGraph Example)

The Helloworld example demonstrates the basic mechanics of A2A. For more advanced features like robust streaming, task state management, and multi-turn conversations powered by an LLM, we'll turn to the `langgraph` example located in `a2a-python-sdk/examples/langgraph/`.

This example features a "Currency Agent" that uses the Gemini model via LangChain and LangGraph to answer currency conversion questions.

## Setting up the LangGraph Example

1. Create a [Gemini API Key](https://ai.google.dev/gemini-api/docs/api-key), if you don't already have one.

2. **Environment Variable:**

    Create a `.env` file in the `a2a-python-sdk/examples/langgraph/` directory:

    ```bash
    # In a2a-python-sdk/examples/langgraph/
    echo "GOOGLE_API_KEY=YOUR_API_KEY_HERE" > .env
    ```

    Replace `YOUR_API_KEY_HERE` with your actual Gemini API key.

3. **Install Dependencies (if not already covered):**
    The `langgraph` example has its own `pyproject.toml` which includes dependencies like `langchain-google-genai` and `langgraph`. When you installed the SDK, these should have been installed as part of the `langgraph-example` extras. If you encounter import errors, you might need to install them explicitly from within the `a2a-python-sdk/examples/langgraph/` directory:

    ```bash
    # From a2a-python-sdk/examples/langgraph/
    pip install -e .[dev]
    ```

    Typically, the top-level SDK install should cover this.

## Running the LangGraph Server

Navigate to the `a2a-python-sdk/examples/langgraph/` directory in your terminal and ensure your virtual environment (from the SDK root) is activated.

Start the LangGraph agent server:

```bash
# From a2a-python-sdk/examples/langgraph/
python __main__.py
```

This will start the server, usually on `http://localhost:10000`.

## Interacting with the LangGraph Agent

Open a **new terminal window**, activate your virtual environment, and navigate to `a2a-python-sdk/examples/langgraph/`.

Run its test client:

```bash
# From a2a-python-sdk/examples/langgraph/
python test_client.py
```

Now, you can shut down the server by typing Ctrl+C in the terminal window.

## Key Features Demonstrated

The `langgraph` example showcases several important A2A concepts:

1. **LLM Integration**:

    - `examples/langgraph/agent.py` defines `CurrencyAgent`. It uses `ChatGoogleGenerativeAI` and LangGraph's `create_react_agent` to process user queries.
    - This demonstrates how a real LLM can power the agent's logic.

2. **Task State Management**:

    - `examples/langgraph/__main__.py` initializes an `InMemoryTaskStore`.
    - The `CurrencyAgentExecutor` (in `examples/langgraph/agent_executor.py`) uses this `task_store` to save and retrieve `Task` objects.
    - Unlike Helloworld, `on_message_send` in `CurrencyAgentExecutor` returns a full `Task` object. The `id` of this task can be used for subsequent interactions.

3. **Streaming with `TaskStatusUpdateEvent` and `TaskArtifactUpdateEvent`**:

    - The `on_message_stream` method in `CurrencyAgentExecutor` demonstrates a more realistic streaming scenario.
    - As the LangGraph agent processes the request (which might involve calling tools like `get_exchange_rate`), it yields intermediate updates.
    - `examples/langgraph/helpers.py` (`process_streaming_agent_response`) shows how these agent steps are converted into A2A `TaskStatusUpdateEvent` (e.g., "Looking up exchange rates...") and `TaskArtifactUpdateEvent` (when the final answer is ready).
    - The `test_client.py`'s `run_streaming_test` function will print these individual chunks.

4. **Multi-Turn Conversation (`TaskState.INPUT_REQUIRED`)**:

    - The `CurrencyAgent` can ask for clarification if a query is ambiguous (e.g., "USD to what?").
    - When this happens, the `agent_response` in `CurrencyAgentExecutor` will indicate `require_user_input: True`.
    - The `Task` status will be set to `TaskState.input_required`.
    - The `test_client.py` `run_multi_turn_test` function demonstrates this:
        - It sends an initial ambiguous query ("how much is 100 USD?").
        - The agent responds with `TaskState.input_required` and a message asking for the target currency.
        - The client then sends a second message _with the same `sessionId` (derived from `contextId`)_ to provide the missing information ("in GBP").

## Exploring the Code

Take some time to look through these files in `examples/langgraph/`:

- `__main__.py`: Server setup, Agent Card definition (note `capabilities.streaming=True`).
- `agent.py`: The `CurrencyAgent` with LangGraph and tool definitions.
- `agent_executor.py`: The `CurrencyAgentExecutor` implementing A2A methods, managing task state, and handling streaming.
- `helpers.py`: Utility functions for creating and updating task objects and processing agent responses for streaming.
- `test_client.py`: Demonstrates various interaction patterns.

This example provides a much richer illustration of how A2A facilitates complex, stateful, and asynchronous interactions between agents.
