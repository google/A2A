# 5. Starting the Server

Now that we have an Agent Card and an Agent Executor, we can set up and start the A2A server.

The A2A Python SDK provides an `A2AStarletteApplication` class that simplifies running an A2A-compliant HTTP server. It uses [Starlette](https://www.starlette.io/) for the web framework and is typically run with an ASGI server like [Uvicorn](https://www.uvicorn.org/).

## Server Setup in Helloworld

Let's look at `__main__.py` again to see how the server is initialized and started.

```python { .no-copy }
--8<-- "https://raw.githubusercontent.com/google-a2a/a2a-samples/refs/heads/main/samples/python/agents/helloworld/__main__.py"
```

Let's break this down:

1. **`DefaultRequestHandler`**:

    - The SDK provides `DefaultRequestHandler`. This handler takes your `AgentExecutor` implementation (here, `HelloWorldAgentExecutor`) and a `TaskStore` (here, `InMemoryTaskStore`).
    - It routes incoming A2A RPC calls to the appropriate methods on your executor (like `execute` or `cancel`).
    - The `TaskStore` is used by the `DefaultRequestHandler` to manage the lifecycle of tasks, especially for stateful interactions, streaming, and resubscription. Even if your agent executor is simple, the handler needs a task store.

2. **`A2AStarletteApplication`**:

    - The `A2AStarletteApplication` class is instantiated with the `agent_card` and the `request_handler` (referred to as `http_handler` in its constructor).
    - The `agent_card` is crucial because the server will expose it at the `/.well-known/agent.json` endpoint (by default).
    - The `request_handler` is responsible for processing all incoming A2A method calls by interacting with your `AgentExecutor`.

3. **`uvicorn.run(server_app_builder.build(), ...)`**:
    - The `A2AStarletteApplication` has a `build()` method that constructs the actual Starlette application.
    - This application is then run using `uvicorn.run()`, making your agent accessible over HTTP.
    - `host='0.0.0.0'` makes the server accessible on all network interfaces on your machine.
    - `port=9999` specifies the port to listen on. This matches the `url` in the `AgentCard`.

## Running the Helloworld Server

Navigate to the `a2a-samples` directory in your terminal (if you're not already there) and ensure your virtual environment is activated.

To run the Helloworld server:

```bash
# from the a2a-samples directory
python samples/python/agents/helloworld/__main__.py
```

You should see output similar to this, indicating the server is running:

```console { .no-copy }
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:9999 (Press CTRL+C to quit)
```

Your A2A Helloworld agent is now live and listening for requests! In the next step, we'll interact with it.
