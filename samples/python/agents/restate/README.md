## Resilient Agents with Restate

This sample uses [Restate](https://ai.restate.dev/) and the Agent Development Kit (ADK) to create a resilient "Expense Reimbursement" agent that is hosted as an A2A server.

Restate lets you build resilient applications easily. It provides a distributed durable version of your everyday building blocks.

In this example, Restate acts as a scalable, resilient task orchestrator that speaks the A2A protocol and gives you:
- 🔁 **Automatic retries** - Handles LLM API downtime, timeouts, and infrastructure failures
- 🔄 **Smart recovery** - Preserves progress across failures without duplicating work
- ⏱️ **Persistent task handles** - Tracks progress across failures, time, and processes
- 🎮 **Task control** - Cancel tasks, query status, re-subscribe to ongoing tasks
- 🧠 **Idempotent submission** - Automatic deduplication based on task ID
- 🤖 **Agentic workflows** - Build resilient agents with human-in-the-loop and parallel tool execution
- 💾 **Durable state** - Maintain consistent agent state across infrastructure events
- 👀 **Full observability** - Line-by-line execution tracking with built-in audit trail
- ☁️️ **Easy to self-host** - or connect to Restate Cloud

<img src="https://raw.githubusercontent.com/restatedev/img/refs/heads/main/a2a/a2a.png" width="600px"/>

This agent takes text requests from the client and, if any details are missing, returns a webform for the client (or its user) to fill out. 
After the client fills out the form, the agent will complete the task.

## Prerequisites

- Python 3.12 or higher
- [UV](https://docs.astral.sh/uv/)
- Access to an LLM and API Key


## Running the Sample

1. Navigate to the samples directory:
    ```bash
    cd samples/python/agents/restate
    ```
2. Create an environment file with your API key:

   ```bash
   echo "GOOGLE_API_KEY=your_api_key_here" > .env
   ```

4. Run the A2A server and agent:
    ```bash
    uv run .
    ```
   
6. Start the Restate Server with Docker ([for other options check the docs](https://docs.restate.dev/develop/local_dev#running-restate-server--cli-locally)).
   
   ```shell
   docker run -p 8080:8080 -p 9070:9070  \
     --add-host=host.docker.internal:host-gateway \
     -e 'RESTATE_WORKER__INVOKER__INACTIVITY_TIMEOUT=5min' \
     -e 'RESTATE_WORKER__INVOKER__ABORT_TIMEOUT=5min'  \
     docker.restate.dev/restatedev/restate:latest
   ```
   
   Let Restate know where the A2A server is running:
   ```shell
   docker run -it --network=host docker.restate.dev/restatedev/restate-cli:latest \
     deployments register http://host.docker.internal:9080/restate/v1
   ```

5. In a separate terminal, run the A2A client:
    ```
    # Connect to the agent (specify the agent URL with correct port)
    cd samples/python/hosts/cli
    uv run . --agent http://localhost:9080

    # If you changed the port when starting the agent, use that port instead
    # uv run . --agent http://localhost:YOUR_PORT
    ```

6. Send requests with the A2A client like: `Reimburse my flight of 700 USD`

Open the Restate UI ([http://localhost:9070](http://localhost:9070)) to see the task execution log and the task state.

<img src="https://raw.githubusercontent.com/restatedev/img/refs/heads/main/a2a/journal.png" width="900px" alt="Example of Restate journal view"/>
<img src="https://raw.githubusercontent.com/restatedev/img/refs/heads/main/a2a/state.png" width="900px" alt="Example of Restate state view"/>

# Learn more
- [Restate Website](https://restate.dev/)
- [Restate Documentation](https://docs.restate.dev/)
- [Restate GitHub repo](https://github.com/restatedev/restate)