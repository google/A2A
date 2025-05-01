# Adding Agent Capabilities

Now that we have a basic A2A server running, let's add some more functionality. We'll explore how A2A can work asynchronously and stream responses.

## Streaming <!-- {docsify-ignore} -->

This allows clients to subscribe to the server and receive multiple updates instead of a single response. This can be useful for long running agent tasks, or where multiple Artifacts may streamed back to the client. See the [Streaming Documentation](/documentation.md?id=streaming-support)

First we'll declare our agent as ready for streaming. Open up `src/my_project/__init__.py` and update AgentCapabilities

```python
# ...
def main(host, port):
  # ...
  capabilities = AgentCapabilities(
    streaming=True
  )
  # ...
```

Now in `src/my_project/task_manager.py` we'll have to implement `on_send_task_subscribe`

```python
import asyncio
# ...
class MyAgentTaskManager(InMemoryTaskManager):
  # ...
  async def _stream_3_messages(self, request: SendTaskStreamingRequest):
    task_id = request.params.id
    received_text = request.params.message.parts[0].text

    text_messages = ["one", "two", "three"]
    for text in text_messages:
      parts = [
        {
          "type": "text",
          "text": f"{received_text}: {text}",
        }
      ]
      message = Message(role="agent", parts=parts)
      is_last = text == text_messages[-1]
      task_state = TaskState.COMPLETED if is_last else TaskState.WORKING
      task_status = TaskStatus(
        state=task_state,
        message=message
      )
      task_update_event = TaskStatusUpdateEvent(
        id=request.params.id,
        status=task_status,
        final=is_last,
      )
      await self.enqueue_events_for_sse(
        request.params.id,
        task_update_event
      )

  async def on_send_task_subscribe(
    self,
    request: SendTaskStreamingRequest
  ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
    # Upsert a task stored by InMemoryTaskManager
    await self.upsert_task(request.params)

    task_id = request.params.id
    # Create a queue of work to be done for this task
    sse_event_queue = await self.setup_sse_consumer(task_id=task_id)

    # Start the asynchronous work for this task
    asyncio.create_task(self._stream_3_messages(request))

    # Tell the client to expect future streaming responses
    return self.dequeue_events_for_sse(
      request_id=request.id,
      task_id=task_id,
      sse_event_queue=sse_event_queue,
    )
```

Restart your A2A server to pickup the new changes and then rerun the cli

```bash
$ uv run google-a2a-cli --agent http://localhost:10002
=========  starting a new task ========

What do you want to send to the agent? (:q or quit to exit): Streaming?

"status":{"state":"working","message":{"role":"agent","parts":[{"type":"text","text":"Streaming?: one"}]}
"status":{"state":"working","message":{"role":"agent","parts":[{"type":"text","text":"Streaming?: two"}]}
"status":{"state":"completed","message":{"role":"agent","parts":[{"type":"text","text":"Streaming?: three"}]}

```

Sometimes the agent might need additional input. For example, maybe the agent will ask the client if they'd like to keep repeating the 3 messages. In this case, the agent will respond with `TaskState.INPUT_REQUIRED` to which the client will then resend `send_task_streaming` with the same `task_id` and `session_id` but with an updated message providing the input required by the agent. On the server-side we'll update `on_send_task_subscribe` to handle this case.

```python
# ...

class MyAgentTaskManager(InMemoryTaskManager):
  # ...
  async def _stream_3_messages(self, request: SendTaskStreamingRequest):
    # ...
    async for message in messages:
      # ...
      # is_last = message == messages[-1] # Delete this line
      task_state = TaskState.WORKING
      # ...
      task_update_event = TaskStatusUpdateEvent(
        id=request.params.id,
        status=task_status,
        final=False,
      )
      # ...

    ask_message = Message(
      role="agent",
      parts=[
        {
          "type": "text",
          "text": "Would you like more messages? (Y/N)"
        }
      ]
    )
    task_update_event = TaskStatusUpdateEvent(
      id=request.params.id,
      status=TaskStatus(
        state=TaskState.INPUT_REQUIRED,
        message=ask_message
      ),
      final=True,
    )
    await self.enqueue_events_for_sse(
      request.params.id,
      task_update_event
    )
  # ...
  async def on_send_task_subscribe(
    self,
    request: SendTaskStreamingRequest
  ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
    task_id = request.params.id
    is_new_task = task_id in self.tasks
    # Upsert a task stored by InMemoryTaskManager
    await self.upsert_task(request.params)

    received_text = request.params.message.parts[0].text
    sse_event_queue = await self.setup_sse_consumer(task_id=task_id)
    if not is_new_task and received_text == "N":
      task_update_event = TaskStatusUpdateEvent(
        id=request.params.id,
        status=TaskStatus(
          state=TaskState.COMPLETED,
          message=Message(
            role="agent",
            parts=[
              {
                "type": "text",
                "text": "All done!"
              }
            ]
          )
        ),
        final=True,
      )
      await self.enqueue_events_for_sse(
        request.params.id,
        task_update_event,
      )
    else:
      asyncio.create_task(self._stream_3_messages(request))

    return self.dequeue_events_for_sse(
      request_id=request.id,
      task_id=task_id,
      sse_event_queue=sse_event_queue,
    )
```

Now after restarting the server and running the cli, we can see the task will keep running until we tell the agent `N`

```bash
$ uv run google-a2a-cli --agent http://localhost:10002
=========  starting a new task ========

What do you want to send to the agent? (:q or quit to exit): Streaming?

"status":{"state":"working","message":{"role":"agent","parts":[{"type":"text","text":"Streaming?: one"}]}
"status":{"state":"working","message":{"role":"agent","parts":[{"type":"text","text":"Streaming?: two"}]}
"status":{"state":"working","message":{"role":"agent","parts":[{"type":"text","text":"Streaming?: three"}]}
"status":{"state":"input-required","message":{"role":"agent","parts":[{"type":"text","text":"Would you like more messages? (Y/N)"}]}

What do you want to send to the agent? (:q or quit to exit): N

"status":{"state":"completed","message":{"role":"agent","parts":[{"type":"text","text":"All done!"}]}

```

Congradulations! You now have an agent that is able to asynchronously perform work and ask users for input when needed.

## Other Capabilities <!-- {docsify-ignore} -->

If you're interested, check out the [documentation](/documentation.md?id=sample-methods-and-json-responses) for other capabilities for your A2A agent. For now we'll jump into adding AI into A2A using a local LLM.

<div class="bottom-buttons" style="flex flex-row">
  <a href="#/tutorials/python/7_interact_with_server.md" class="back-button">Back</a>
  <a href="#/tutorials/python/9_ollama_agent.md?id=using-a-local-ollama-model" class="next-button">Next</a>
</div>
