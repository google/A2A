# A2A Server

We're almost ready to start our server! We'll be using the `A2AServer` class from `Google-A2A` which under the hood starts a [uvicorn](https://www.uvicorn.org/) server. However in the future this may change as `Google-A2A` is still in development.

## Task Manager <!-- {docsify-ignore} -->

Before we create our server, we need a task manager to handle incoming requests.

We'll be implementing the InMemoryTaskManager interface which requires us to implement two methods

```python
async def on_send_task(
  self,
  request: SendTaskRequest
) -> SendTaskResponse:
  """
  This method queries or creates a task for the agent.
  The caller will receive exactly one response.
  """
  pass

async def on_send_task_subscribe(
  self,
  request: SendTaskStreamingRequest
) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
  """
  This method subscribes the caller to future updates regarding a task.
  The caller will receive a response and additionally receive subscription
  updates over a session established between the client and the server
  """
  pass

```

Open up `src/my_project/task_manager.py` and add the following code. We will simply returns a direct echo response and immediately mark the task complete without any sessions or subscriptions

```python
from typing import AsyncIterable

import google_a2a
from google_a2a.common.server.task_manager import InMemoryTaskManager
from google_a2a.common.types import (
  Artifact,
  JSONRPCResponse,
  Message,
  SendTaskRequest,
  SendTaskResponse,
  SendTaskStreamingRequest,
  SendTaskStreamingResponse,
  Task,
  TaskState,
  TaskStatus,
  TaskStatusUpdateEvent,
)

class MyAgentTaskManager(InMemoryTaskManager):
  def __init__(self):
    super().__init__()

  async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
    # Upsert a task stored by InMemoryTaskManager
    await self.upsert_task(request.params)

    task_id = request.params.id
    # Our custom logic that simply marks the task as complete
    # and returns the echo text
    received_text = request.params.message.parts[0].text
    task = await self._update_task(
      task_id=task_id,
      task_state=TaskState.COMPLETED,
      response_text=f"on_send_task received: {received_text}"
    )

    # Send the response
    return SendTaskResponse(id=request.id, result=task)

  async def on_send_task_subscribe(
    self,
    request: SendTaskStreamingRequest
  ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
    pass

  async def _update_task(
    self,
    task_id: str,
    task_state: TaskState,
    response_text: str,
  ) -> Task:
    task = self.tasks[task_id]
    agent_response_parts = [
      {
        "type": "text",
        "text": response_text,
      }
    ]
    task.status = TaskStatus(
      state=task_state,
      message=Message(
        role="agent",
        parts=agent_response_parts,
      )
    )
    task.artifacts = [
      Artifact(
        parts=agent_response_parts,
      )
    ]
    return task

```

## A2A Server <!-- {docsify-ignore} -->

With a task manager complete, we can now create our server

Open up `src/my_project/__init__.py` and add the following code.

```python
# ...
from google_a2a.common.server import A2AServer
from my_project.task_manager import MyAgentTaskManager
# ...
def main(host, port):
  # ...

  task_manager = MyAgentTaskManager()
  server = A2AServer(
    agent_card=agent_card,
    task_manager=task_manager,
    host=host,
    port=port,
  )
  server.start()

```

## Test Run <!-- {docsify-ignore} -->

Let's give this a run.

```bash
uv run my-project
```

The output should look something like this.

```bash
INFO:     Started server process [20506]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:10002 (Press CTRL+C to quit)
```

Congratulations! Your A2A server is now running!

<div class="bottom-buttons" style="flex flex-row">
  <a href="#/tutorials/python/5_add_agent_card.md" class="back-button">Back</a>
  <a href="#/tutorials/python/7_interact_with_server.md?id=interacting-with-your-a2a-server" class="next-button">Next</a>
</div>
