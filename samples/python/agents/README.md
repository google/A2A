## Sample Agents

All the agents in this directory are samples built on different frameworks highlighting different capabilities. Each agent runs as a standalone A2A server. 

Each agent can be run as its own A2A server with the instructions on its README. By default, each will run on a separate port on localhost (you can use command line arguments to override).

To interact with the servers, use an A2AClient in a host app (such as the CLI). See [Host Apps](/samples/python/hosts/README.md) for details.

* [**Google ADK**](/samples/python/agents/google_adk/README.md)  
Sample agent to (mock) fill out expense reports. Showcases multi-turn interactions and returning/replying to webforms through A2A.

* [**AG2 MCP Agent with A2A Protocol**](/samples/python/agents/ag2/README.md)  
Demonstrates an MCP-enabled agent built with [AG2](https://github.com/ag2ai/ag2) that is exposed through the A2A protocol.

* [**LangGraph**](/samples/python/agents/langgraph/README.md)  
Sample agent which can convert currency using tools. Showcases multi-turn interactions, tool usage, and streaming updates. 

* [**CrewAI**](/samples/python/agents/crewai/README.md)  
Sample agent which can generate images. Showcases multi-turn interactions and sending images through A2A.

* [**LlamaIndex**](/samples/python/agents/llama_index_file_chat/README.md)  
Sample agent which can parse a file and then chat with the user using the parsed content as context. Showcases multi-turn interactions, file upload and parsing, and streaming updates. 

* [**Marvin Contact Extractor Agent**](/samples/python/agents/marvin/README.md)  
Demonstrates an agent using the [Marvin](https://github.com/prefecthq/marvin) framework to extract structured contact information from text, integrated with the Agent2Agent (A2A) protocol.

* [**Enterprise Data Agent**](/samples/python/agents/mindsdb/README.md)  
Sample agent which can answer questions from any database, datawarehouse, app. - Powered by Gemini 2.5 flash + MindsDB.

* [**Semantic Kernel Agent**](/samples/python/agents/semantickernel/README.md)  
Demonstrates how to implement a travel agent built on [Semantic Kernel](https://github.com/microsoft/semantic-kernel/) and exposed through the A2A protocol.
