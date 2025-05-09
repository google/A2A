# Interacting With Your A2A Server

Now that your HelloWorld A2A server is running, let's send some requests to it. The `a2a-python-sdk/examples/helloworld/` directory includes a `test_client.py` script that demonstrates how to use the `A2AClient` from the SDK to communicate with an A2A server.

## The `a2a.client.A2AClient`

The `A2AClient` class is the primary tool for client-side A2A interactions. It provides asynchronous methods to:

- **Discover an agent**: Fetch and parse its Agent Card using `A2AClient.get_client_from_agent_card_url()`.
- **Send non-streaming messages**: Use `client.send_message()` for `message/send` RPC calls.
- **Send streaming messages**: Use `client.send_message_streaming()` for `message/sendStream` RPC calls, which returns an async generator for SSE.
- **Manage tasks**: Methods like `client.get_task()`, `client.cancel_task()`, etc., are available for agents that implement full task management (our HelloWorld agent has minimal task management, but the client shows how these would be called).

## Using `test_client.py` for HelloWorld

1. **Ensure your HelloWorld server is running:**
    If you stopped it in the previous step, go back to the `a2a-python-sdk/examples/helloworld` directory in one terminal window and start it:

    ```bash
    # (In terminal 1, inside examples/helloworld)
    # Ensure your virtual environment (.venv) is activated
    python __main__.py
    ```

    You should see the Uvicorn server running and listening on `http://0.0.0.0:9999`.

2. **Run `test_client.py`:**
    Open a **new terminal window**.
    Navigate to the `a2a-python-sdk/examples/helloworld` directory.
    Activate the same virtual environment you used for the server:
    - On macOS and Linux:

        ```bash
        source ../../.venv/bin/activate
        ```

    - On Windows (Command Prompt):

        ```bash
        ..\..\.venv\Scripts\activate.bat
        ```

    - On Windows (PowerShell):

        ```bash
        ..\..\.venv\Scripts\Activate.ps1
        ```

    Now, execute the test client script:

    ```bash
    python test_client.py
    ```

## Understanding `test_client.py` Code

Let's look at the key parts of `a2a-python-sdk/examples/helloworld/test_client.py`:

```python
# From examples/helloworld/test_client.py
from a2a.client import A2AClient # The SDK's client class
from typing import Any
import httpx # For making async HTTP requests
from uuid import uuid4
from a2a.types import SendMessageSuccessResponse, Task # Relevant A2A types

async def main() -> None:
    async with httpx.AsyncClient() as httpx_client:
        # 1. Discover the agent and get an A2AClient instance
        #    This fetches the Agent Card from http://localhost:9999/.well-known/agent.json
        client = await A2AClient.get_client_from_agent_card_url(
            httpx_client, 'http://localhost:9999'
        )

        # 2. Prepare a payload for sending a message
        send_message_payload: dict[str, Any] = {
            'message': {
                'role': 'user', # Message is from the user's perspective
                'parts': [
                    {'type': 'text', 'text': 'Hello from A2A client!'}
                ],
                'messageId': uuid4().hex, # Unique ID for the message
            },
            # For agents managing tasks, you might also include 'id' (task ID)
            # and 'sessionId' here if continuing an existing task/session.
        }

        # 3. Send a non-streaming message
        print("--- Sending non-streaming message ---")
        response = await client.send_message(payload=send_message_payload)
        # Print the JSON representation of the response
        print(response.model_dump_json(exclude_none=True, indent=2))

        # The original test_client.py includes logic for get_task and cancel_task.
        # These are more relevant when the agent returns a Task object that progresses
        # through states. Our HelloWorld agent's on_message_send directly returns a Message.
        # If it returned a Task, the following would be applicable:
        # if isinstance(response.root, SendMessageSuccessResponse) and isinstance(
        #     response.root.result, Task
        # ):
        #     task_id: str = response.root.result.id
        #     # ... (code to get_task, cancel_task) ...
        # else:
        #     print(
        #         'Received an instance of Message, getTask and cancelTask are not applicable for invocation'
        #     )


        # 4. Send a streaming message
        print("\n--- Sending streaming message ---")
        # send_message_streaming returns an async generator
        stream_response_generator = client.send_message_streaming(
            payload=send_message_payload # Reusing the same payload for simplicity
        )
        async for chunk in stream_response_generator:
            # Each chunk is a SendMessageStreamingResponse
            print(chunk.model_dump_json(exclude_none=True, indent=2))

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
```

**Key Client Actions:**

1. **Client Initialization**: `A2AClient.get_client_from_agent_card_url()` is a convenience method. It constructs the well-known Agent Card URL (`http://localhost:9999/.well-known/agent.json`), fetches the card, parses it, and initializes an `A2AClient` instance configured to talk to the agent's `url` specified in the card.
2. **Payload Preparation**: A dictionary `send_message_payload` is created. This structure corresponds to the `MessageSendParams` type in A2A, containing the `message` to be sent.
3. **Non-Streaming `send_message`**:
    - `client.send_message()` makes a `POST` request to the agent's URL with a JSON-RPC request for the `message/send` method.
    - It `await`s a single `SendMessageResponse`. For HelloWorld, this response directly contains the agent's reply message.
4. **Streaming `send_message_streaming`**:
    - `client.send_message_streaming()` makes a `POST` request for the `message/sendStream` method.
    - This method returns an `AsyncGenerator`. The `async for chunk in stream_response_generator:` loop iterates over the Server-Sent Events (SSE) received from the server. Each `chunk` is a `SendMessageStreamingResponse` object.

## Expected Output from `test_client.py`

When you run `test_client.py` while the HelloWorld server is active, you should see output similar to this (exact UUIDs will differ):

```
--- Sending non-streaming message ---
{
  "root": {
    "jsonrpc": "2.0",
    "id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "result": {
      "role": "agent",
      "parts": [
        {
          "type": "text",
          "text": "Hello World"
        }
      ],
      "messageId": "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy"
    }
  }
}

--- Sending streaming message ---
{
  "root": {
    "jsonrpc": "2.0",
    "id": "zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz",
    "result": {
      "role": "agent",
      "parts": [
        {
          "type": "text",
          "text": "Hello "
        }
      ],
      "messageId": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
      "final": false
    }
  }
}
{
  "root": {
    "jsonrpc": "2.0",
    "id": "zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz",
    "result": {
      "role": "agent",
      "parts": [
        {
          "type": "text",
          "text": "World"
        }
      ],
      "messageId": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
      "final": true
    }
  }
}
```

This output confirms:

- The non-streaming request received a single "Hello World" response.
- The streaming request received "Hello " as the first chunk (`final: false`) and "World" as the second, final chunk (`final: true`).

You have now successfully set up an A2A server for the HelloWorld agent and interacted with it using the SDK's A2A client, demonstrating both non-streaming and streaming communication!

Next, we'll recap agent capabilities like streaming and prepare to look at a more advanced agent example.
