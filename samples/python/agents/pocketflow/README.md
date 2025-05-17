# PocketFlow Agent with A2A Protocol

 I modified [Pocketflow cookbook](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-a2a) to make the the LLM calling from client side available, and be able to communicate between client and server.

TL;DR The LLM flow from client side will decide which agent to consult and send task to execute, then decide whether should it answer to user.

This implementation is based  on the tutorial: [A2A Protocol Simply Explained: Here are 3 key differences to MCP!](https://zacharyhuang.substack.com/p/a2a-protocol-simply-explained-here)


# Run example

## Server
```
uv run --env-file .env python -m a2a_server
```

## Client
```
# With log
uv run --env-file .env --directory examples/user_agent_talking_with_duckduckgo_agent python -m a2a_client.chat

# Without log
POCKETFLOW_LOG_LEVEL=REMOVE uv run --env-file .env --directory examples/user_agent_talking_with_duckduckgo_agent python -m a2a_client.chat
```