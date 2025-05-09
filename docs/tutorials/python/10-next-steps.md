# Next Steps

Congratulations! You now have mastered the basics of running an A2A server with an AI model as the agent. Here's some ideas of where to go next.

- Connect our AI model with [MCP tools]
  - Hint: first [create a MCP Server](https://modelcontextprotocol.io/quickstart/server)
  - Then: [Integrate MCP Tools](https://github.com/langchain-ai/langchain-mcp-adapters?tab=readme-ov-file#client) into our existing call to `create_react_agent(ollama_chat_llm, tools=[])`
- Develop your own agent using Google's Agent Development Kit or other framework. Check out the [A2A samples](https://github.com/google/A2A/tree/main/samples/python/agents)
- 📚 Read the A2A [technical documentation](https://google.github.io/A2A/) to understand the capabilities
- 📝 Review the A2A [specification](../../specification.md) of the protocol structures
- 📑 Review key topics to understand protocol details
  - [A2A and MCP](../../topics/a2a-and-mcp.md)
  - [Enterprise Ready](../../topics/enterprise-ready.md)
  - [Streaming & Asynchronous Operations](../../topics/streaming-and-async.md)
  - [Agent Discovery](../../topics/agent-discovery.md)

[Prev](./9-ollama-agent.md)
