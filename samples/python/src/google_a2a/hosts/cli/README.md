## CLI

The CLI is a small host application that demonstrates the capabilities of an A2AClient. It supports reading a server's AgentCard and text-based collaboration with a remote agent. All content received from the A2A server is printed to the console. 

The client will use streaming if the server supports it.

## Prerequisites

- Python 3.12 or higher
- UV
- A running A2A server

## Running the CLI

1. Navigate to the CLI sample directory:
    ```bash
    cd samples/python/hosts/cli
    ```
2. Run the example client
    ```
    uv run . --agent [url-of-your-a2a-server]
    ```

   for example `--agent http://localhost:10000`. More command line options are documented in the source code. 
