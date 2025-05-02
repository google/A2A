# Using a Local Ollama Model

Now we get to the exciting part. We're going to add AI to our A2A server.

In this tutorial, we'll be setting up a local Ollama model and integrating it with our A2A server. However there are many other options such as using Google's Agent Development Kit (ADK). You can check out the [sample projects](https://github.com/google/A2A/tree/main/samples/python/agents) on GitHub.

## Requirements <!-- {docsify-ignore} -->

We'll be installing `ollama`, `langchain` as well as downloading an ollama model that supports MCP tools (for a future tutorial).

1. Download [ollama](https://ollama.com/download)
2. Run an ollama server

```bash
# Note: if ollama is already running, you may get an error such as
# Error: listen tcp 127.0.0.1:11434: bind: address already in use
# On linux you can run systemctl stop ollama to stop ollama
ollama serve
```

3. Download a model from [this list](https://ollama.com/search). We'll be using `qwq` as it supports `tools` (as shown by its tags) and runs on a 24GB graphics card

```bash
ollama pull qwq
```

4. Install `langchain`

```bash
uv add langchain langchain-ollama langgraph
```

Now with ollama setup, we can start integrating it into our A2A server

## Integrating Ollama into our A2A server <!-- {docsify-ignore} -->

First open up `src/my_project/__init__.py`

```python
# ...

@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=10002)
@click.option("--ollama-host", default="http://127.0.0.1:11434")
@click.option("--ollama-model", default=None)
def main(host, port, ollama_host, ollama_model):
  # ...
  capabilities = AgentCapabilities(
    streaming=False # We'll leave streaming capabilities as an exercise for the reader
  )
  # ...
  task_manager = MyAgentTaskManager(
    ollama_host=ollama_host,
    ollama_model=ollama_mode,
  )
  # ..
```

Now let's add AI functionality in `src/my_project/agent.py`

```python
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from langgraph.graph.graph import CompiledGraph

def create_ollama_agent(ollama_base_url: str, ollama_model: str):
  ollama_chat_llm = ChatOllama(
    base_url=ollama_base_url,
    model=ollama_model,
    temperature=0.2
  )
  agent = create_react_agent(ollama_chat_llm, tools=[])
  return agent

async def run_ollama(ollama_agent: CompiledGraph, prompt: str):
  agent_response = await ollama_agent.ainvoke(
    {"messages": prompt }
  )
  message = agent_response["messages"][-1].content
  return str(message)
```

Finally let's call our ollama agent from `src/my_project/task_manager.py`

```python
# ...
from my_project.agent import create_ollama_agent, run_ollama

class MyAgentTaskManager(InMemoryTaskManager):
  def __init__(
    self,
    ollama_host: str,
    ollama_model: typing.Union[None, str]
  ):
    super().__init__()
    if ollama_model is not None:
      self.ollama_agent = create_ollama_agent(
        ollama_base_url=ollama_host,
        ollama_model=ollama_model
      )
    else:
      self.ollama_agent = None

  async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
    # ...
    received_text = request.params.message.parts[0].text
    response_text = f"on_send_task received: {received_text}"
    if self.ollama_agent is not None:
      response_text = await run_ollama(ollama_agent=self.ollama_agent, prompt=received_text)

    task = await self._update_task(
      task_id=task_id,
      task_state=TaskState.COMPLETED,
      response_text=response_text
    )

    # Send the response
    return SendTaskResponse(id=request.id, result=task)

  # ...
```

Lets test it out!

First rerun our A2A server replacing `qwq` with the ollama model you downloaded

```bash
uv run my-project --ollama-host http://127.0.0.1:11434 --ollama-model qwq
```

And then rerun the cli

```bash
uv run google-a2a-cli --agent http://localhost:10002
```

Note, if you're using a large model, it may take a while to load. The cli may timeout. In which case rerun the cli once the ollama server has finished loading the model.

You should see something like the following

```bash
=========  starting a new task ========

What do you want to send to the agent? (:q or quit to exit): hey

"message":{"role":"agent","parts":[{"type":"text","text":"<think>\nOkay, the user said \"hey\". That's pretty casual. I should respond in a friendly way. Maybe ask how I can help them today. Keep it open-ended so they feel comfortable sharing what they need. Let me make sure my tone is positive and approachable. Alright, something like, \"Hey there! How can I assist you today?\" Yeah, that sounds good.\n</think>\n\nHey there! How can I assist you today? 😊"}]}
```

Congratulations! You now have an A2A server generating responses using an AI model!

<div class="bottom-buttons" style="flex flex-row">
  <a href="#/tutorials/python/8_agent_capabilities.md" class="back-button">Back</a>
  <a href="#/tutorials/python/10_next_steps.md?id=next-steps" class="next-button">Next</a>
</div>
