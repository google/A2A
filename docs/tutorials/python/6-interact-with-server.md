# 6. Interacting with the Server

With the Helloworld A2A server running, let's send some requests to it. The SDK includes a client (`A2AClient`) that simplifies these interactions.

## The Helloworld Test Client

The `examples/helloworld/test_client.py` script demonstrates how to:

1. Fetch the Agent Card from the server.
2. Create an `A2AClient` instance.
3. Send both non-streaming (`message/send`) and streaming (`message/sendStream`) requests.
4. Handle task-related operations like `get_task` and `cancel_task` (though Helloworld doesn't fully support these).

Open a **new terminal window**, activate your virtual environment, and navigate to the `a2a-python-sdk` directory.

Run the test client:

```bash
python examples/helloworld/test_client.py
```

## Understanding the Client Code

Let's look at key parts of `examples/helloworld/test_client.py`:

1. **Fetching the Agent Card & Initializing the Client**:

    ```python
    # examples/helloworld/test_client.py
    async with httpx.AsyncClient() as httpx_client:
        client = await A2AClient.get_client_from_agent_card_url(
            httpx_client, 'http://localhost:9999'
        )
    ```

    The `A2AClient.get_client_from_agent_card_url` class method is a convenience. It first fetches the `AgentCard` from the server's `/.well-known/agent.json` endpoint (based on the provided base URL) and then initializes the client with it.

2. **Sending a Non-Streaming Message (`send_message`)**:

    ```python
    # examples/helloworld/test_client.py
    send_message_payload: dict[str, Any] = {
        'message': {
            'role': 'user',
            'parts': [{'type': 'text', 'text': 'how much is 10 USD in INR?'}], # Content doesn't matter for Helloworld
            'messageId': uuid4().hex,
        },
        # 'id' for the task can also be provided here. If not, the server/handler might generate one.
    }

    response = await client.send_message(payload=send_message_payload)
    print(response.model_dump(mode='json', exclude_none=True))
    ```

    - The `payload` constructs the `params` for the `message/send` RPC call.
    - It includes a `message` object with the `role` set to "user" and the content in `parts`.
    - The Helloworld agent will simply echo "Hello World" back.
    - The `response` will be a `SendMessageResponse` object, which contains either a `SendMessageSuccessResponse` (with the agent's `Message` as the result) or a `JSONRPCErrorResponse`.

3. **Handling Task IDs (Illustrative)**:
    The Helloworld client attempts to demonstrate `get_task` and `cancel_task`.

    ```python
    # examples/helloworld/test_client.py
    # ... (after send_message)
    if isinstance(response.root, SendMessageSuccessResponse) and isinstance(
        response.root.result, Task # If the agent returned a Task object
    ):
        task_id: str = response.root.result.id
        # ... client.get_task(...) and client.cancel_task(...) ...
    else:
        # Helloworld send_message returns a direct Message, not a Task object,
        # so this branch will be taken.
        print(
            'Received an instance of Message, getTask and cancelTask are not applicable for invocation'
        )
    ```

    - **Important Note:** The Helloworld `HelloWorldAgentExecutor.on_message_send` returns a direct `Message` as the result, not a `Task` object. More complex agents that manage long-running operations would typically return a `Task` object, whose `id` could then be used for `get_task` or `cancel_task`. The `langgraph` example demonstrates this.

4. **Sending a Streaming Message (`send_message_streaming`)**:

    ```python
    # examples/helloworld/test_client.py
    stream_response = client.send_message_streaming(
        payload=send_message_payload # Same payload can be used
    )
    async for chunk in stream_response:
        print(chunk.model_dump(mode='json', exclude_none=True))
    ```

    - This method calls the agent's `message/sendStream` endpoint.
    - It returns an `AsyncGenerator`. As the server streams SSE events, the client receives them as `SendMessageStreamingResponse` objects.
    - The Helloworld agent will stream "Hello " and then "World".

## Expected Output

When you run `test_client.py`, you'll see JSON outputs for:

- The non-streaming response (a single "Hello World" message).
- A message indicating that `get_task` and `cancel_task` are not applicable because the non-streaming Helloworld returns a direct message.
- The streaming responses (two chunks: "Hello " and then "World", each wrapped in an A2A message structure).

This confirms your server is correctly handling basic A2A interactions!
