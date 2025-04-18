# Sample Code

This code is used to demonstrate A2A capabilities as the spec progresses.\ Samples are divided into 3 sub directories:

* [**Common**](/samples/python/src/google_a2a/common)
Common code that all sample agents and apps use to speak A2A over HTTP.

* [**Agents**](/samples/python/src/google_a2a/agents/README.md)
Sample agents written in multiple frameworks that perform example tasks with tools. These all use the common A2AServer.

* [**Hosts**](/samples/python/src/google_a2a/hosts/README.md)
Host applications that use the A2AClient. Includes a CLI which shows simple task completion with a single agent, a mesop web application that can speak to multiple agents, and an orchestrator agent that delegates tasks to one of multiple remote A2A agents.

## Prerequisites

- Python 3.13 or higher
- [UV](https://docs.astral.sh/uv/)

## Running the Samples

Run one (or more) [agent](/samples/python/src/google_a2a/agents/README.md) A2A server and one of the [host applications](/samples/python/src/google_a2a/hosts/README.md).

The following example will run the langgraph agent with the python CLI host:

1. Navigate to the agent directory:
    ```bash
    cd samples/python/src/google_a2a/agents/langgraph
    ```
2. Run an agent:
    ```bash
    uv run .
    ```
3. In another terminal, navigate to the CLI directory:
    ```bash
    cd samples/python/src/google_a2a/hosts/cli
    ```
4. Run the example client
    ```
    uv run .
    ```
---
**NOTE:**
This is sample code and not production-quality libraries.
---
