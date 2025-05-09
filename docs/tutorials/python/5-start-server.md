# 5. Starting the Server

Now that we have an Agent Card and an Agent Executor, we can set up and start the A2A server.

The `a2a-python-sdk` provides an `A2AServer` class that simplifies running an A2A-compliant HTTP server. It uses Starlette and Uvicorn under the hood.

## Server Setup in Helloworld

Let's look at `examples/helloworld/__main__.py` again to see how the server is initialized and started.

```python
# examples/helloworld/__main__.py
from agent_executor import HelloWorldAgentExecutor

from a2a.server import A2AServer, DefaultA2ARequestHandler
from a2a.types import (
    # ... other imports ...
    AgentCard,
    # ...
)

if __name__ == '__main__':
    # ... AgentSkill and AgentCard definition from previous steps ...
    skill = AgentSkill(...) 
    agent_card = AgentCard(...)

    # 1. Request Handler
    request_handler = DefaultA2ARequestHandler(
        agent_executor=HelloWorldAgentExecutor()
    )

    # 2. A2A Server
    server = A2AServer(agent_card=agent_card, request_handler=request_handler)
    
    # 3. Start Server
    server.start(host='0.0.0.0', port=9999)
```

Let's break this down:

1. **`DefaultA2ARequestHandler`**:
    - The SDK provides `DefaultA2ARequestHandler`. This handler takes your `AgentExecutor` implementation (here, `HelloWorldAgentExecutor`) and routes incoming A2A RPC calls to the appropriate methods (`on_message_send`, `on_message_stream`, etc.) on your executor.
    - It also manages task persistence if a `TaskStore` is provided (which Helloworld doesn't use explicitly, so an in-memory one is used by default within the handler for streaming contexts).

2. **`A2AServer`**:
    - The `A2AServer` class is instantiated with the `agent_card` and the `request_handler`.
    - The `agent_card` is crucial because the server will expose it at the `/.well-known/agent.json` endpoint.
    - The `request_handler` is responsible for processing all incoming A2A method calls.

3. **`server.start()`**:
    - This method starts the Uvicorn server, making your agent accessible over HTTP.
    - `host='0.0.0.0'` makes the server accessible on all network interfaces on your machine.
    - `port=9999` specifies the port to listen on. This matches the `url` in the `AgentCard`.

## Running the Helloworld Server

Navigate to the `a2a-python-sdk` directory in your terminal (if you're not already there) and ensure your virtual environment is activated.

To run the Helloworld server:

```bash
python examples/helloworld/__main__.py
```

You should see output similar to this, indicating the server is running:

```console
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:9999 (Press CTRL+C to quit)
```

Your A2A Helloworld agent is now live and listening for requests! In the next step, we'll interact with it.
