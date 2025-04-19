# Go Samples

This directory contains sample implementations of A2A agents in Go.

## Agents

- [LangGraph](/samples/go/agents/langgraph/README.md)  
  Sample agent which can perform currency conversion and chat. Shows how to implement a simple agent with tools.

- [CrewAI](/samples/go/agents/crewai/README.md)  
  Sample agent which can generate images based on text prompts. Shows how to handle binary data and streaming responses.

- [Semantic Kernel](/samples/go/agents/semantickernel/README.md)  
  Sample travel planning agent that demonstrates multi-turn conversations and task completion.

## Prerequisites

- Go 1.21 or higher

## Running the Samples

Run one (or more) agent servers:

```bash
cd samples/go/agents/langgraph
go run .
```

Then in another terminal, run a client:

```bash
cd samples/go/hosts/cli
go run . --agent http://localhost:10000
```

---

**NOTE:**
This is sample code and not production-quality libraries.

---
