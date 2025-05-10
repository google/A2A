# CLI

The CLI is a small host application that demonstrates the capabilities of an A2AClient. It supports reading a server's AgentCard and text-based collaboration with a remote agent. All content received from the A2A server is printed to the console. 

The client will use streaming if the server supports it.

## Prerequisites

- Python 3.9 or higher
- UV
- A running A2A server

## Running the CLI

1. Navigate to the CLI sample directory:
    ```bash
    cd samples/python/hosts/cli
    ```
2. Run the example client:
    ```
    uv run . --agent [url-of-your-a2a-server]
    ```
   For example `--agent http://localhost:10000`. More command line options are documented in the source code.

## Fingerprint Demo Client

This directory also includes a special demo client for the Agent Fingerprinting feature:

1. Navigate to the CLI sample directory:
    ```bash
    cd samples/python/hosts/cli
    ```
2. Run the fingerprint demo client:
    ```
    python fingerprint_client_demo.py --agent [url-of-your-a2a-server]
    ```

The fingerprint demo client showcases the following capabilities:
- Generating cryptographic fingerprints for agent identity
- Signing outgoing messages for integrity verification
- Verifying incoming messages from agents
- Optional blockchain registration with the `--blockchain` flag