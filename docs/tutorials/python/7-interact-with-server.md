# Interacting With Your A2A Server

First we'll use Google-A2A's command-line tool to send requests to our A2A server. After trying it out, we'll write our own basic client to see how this works under the hood

## Using Google-A2A's command-line tool <!-- {docsify-ignore} -->

With your A2A server already running from the previous run

```bash
# This should already be running in your terminal
$ uv run my-project
INFO:     Started server process [20538]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:10002 (Press CTRL+C to quit)
```

Open up a new terminal in the same directory

```bash
source .venv/bin/activate
uv run google-a2a-cli --agent http://localhost:10002
```

Note: This will only work if you've installed google-a2a from this [pull request](https://github.com/google/A2A/pull/169) as the cli was not exposed previously.

Otherwise you'll have to checkout the [Google/A2A repository](https://github.com/google/A2A/) directly, navigate to the `samples/python` repository and run the cli directly

You can then send messages to your server and pressing Enter

```bash
=========  starting a new task ========

What do you want to send to the agent? (:q or quit to exit): Hello!
```

If everything is working correctly you'll see this in the response

```bash
"message":{"role":"agent","parts":[{"type":"text","text":"on_send_task received: Hello!"}]}
```

To exit type `:q` and press Enter

<div class="bottom-buttons" style="flex flex-row">
  <a href="#/tutorials/python/6_start_server.md" class="back-button">Back</a>
  <a href="#/tutorials/python/8_agent_capabilities.md?id=adding-agent-capabilities" class="next-button">Next</a>
</div>
