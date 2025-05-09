# Using the HelloWorld Example Project

For this tutorial, we'll start with the "HelloWorld" example provided within the A2A Python SDK. This example demonstrates the fundamental structure of an A2A agent and server using the SDK components.

## Navigate to the HelloWorld Example

Ensure your virtual environment from the [Setup](./2-setup.md) step is still activated. From the `a2a-python-sdk` directory (where you installed the SDK), navigate to the `examples/helloworld` directory:

```bash
cd examples/helloworld
```

## Project Structure

The HelloWorld example has a simple and focused structure:

```console { .no-copy }
a2a-python-sdk/
└── examples/
    └── helloworld/
        ├── __main__.py         # Main script to define AgentCard and run the A2A server
        ├── agent_executor.py   # Implements the agent's core logic (HelloWorldAgentExecutor)
        └── test_client.py      # A simple client script to test the HelloWorld server
```

- `__main__.py`: This script is the entry point. It defines the `AgentCard` (which describes the agent's capabilities) and uses `A2AServer` from the SDK to start the HTTP server.
- `agent_executor.py`: This file contains the `HelloWorldAgentExecutor` class. This class implements the `a2a.server.AgentExecutor` interface, providing the actual logic for how the agent responds to `message/send` and `message/sendStream` requests.
- `test_client.py`: This script demonstrates how to use `a2a.client.A2AClient` to connect to the running HelloWorld A2A server, send requests, and process responses.

We will explore the contents of these files in detail in the upcoming sections of the tutorial.

## Test Run: Starting the HelloWorld Server

Let's try running the HelloWorld server to make sure everything is set up correctly. From within the `a2a-python-sdk/examples/helloworld` directory, execute the main script:

```bash
python __main__.py
```

If the server starts successfully, you should see output similar to this in your terminal:

```console { .no-copy }
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:9999 (Press CTRL+C to quit)
```

*(The process ID `[XXXXX]` will vary.)*

This output indicates that your A2A server is running and listening for requests on port 9999. You can stop the server for now by pressing `CTRL+C` in the terminal.

In the next sections, we'll dive into the code to understand how this HelloWorld agent is defined, how its server operates, and how to interact with it.
