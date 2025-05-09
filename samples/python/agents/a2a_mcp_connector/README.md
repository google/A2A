# A2A-MCP Connector Agent

A simple agent that connects Agent-to-Agent (A2A) protocol and Model Context Protocol (MCP) with ease, providing an intuitive and easy-to-use interface. Built with Google ADK (Agent Development Kit).

## Features

- **Easy MCP Tool Registration**: Register MCP tools with a simple interface
- **Tool Discovery**: List and discover registered MCP tools
- **Unified Access**: Call any registered MCP tool through a consistent interface
- **A2A-Compatible**: Fully compliant with the A2A protocol for seamless interoperability
- **Streaming Support**: Provides streaming updates during task processing
- **Persistent Tool Registry**: Tools can be saved to disk and loaded on restart
- **Real MCP Integration**: Actually connects to and calls MCP tools
- **Browser-Friendly Interface**: Helpful web UI when accessed via browser

## Architecture

This agent serves as a bridge between A2A and MCP protocols:

```
User/Agent <--> A2A Protocol <--> A2A-MCP Connector <--> MCP Protocol <--> MCP Tools
```

## Prerequisites

- Python 3.12 or higher
- [UV](https://docs.astral.sh/uv/)
- Access to an LLM (Google Gemini API or Vertex AI)

## Setup & Running

1. Navigate to the agent directory:
   ```bash
   cd samples/python/agents/a2a_mcp_connector
   ```

2. Create an environment file with your API key:

   **Option A: Google AI Studio API Key**
   ```bash
   echo "GOOGLE_API_KEY=your_api_key_here" > .env
   ```

   **Option B: Google Cloud Vertex AI**
   ```bash
   echo "GOOGLE_GENAI_USE_VERTEXAI=TRUE" > .env
   echo "GOOGLE_CLOUD_PROJECT=your_project_id" >> .env
   echo "GOOGLE_CLOUD_LOCATION=your_location" >> .env
   ```
   Note: Ensure you've authenticated with gcloud using `gcloud auth login` first.
   
3. (Optional) Specify a custom path for the tool registry:
   ```bash
   echo "MCP_REGISTRY_PATH=/path/to/my_registry.json" >> .env
   ```

4. Run the agent:
   ```bash
   # Basic run on default port 10004
   uv run .
   
   # On custom host/port
   uv run . --host 0.0.0.0 --port 8080
   
   # To suppress hardlink warnings
   uv run . --link-mode=copy
   ```

   Note: If you see warnings about hardlinks, you can suppress them by using the `--link-mode=copy` flag
   or by setting the environment variable: `$env:UV_LINK_MODE="copy"` (Windows) or 
   `export UV_LINK_MODE=copy` (Linux/macOS).

5. After starting the agent:
   - The Agent Card will be available at: `http://localhost:10004/.well-known/agent.json`
   - Accessing `http://localhost:10004` in a browser will show a helpful landing page
   - A2A protocol interactions should be sent as POST requests to the root endpoint

6. In a new terminal, start an A2A client to interact with the agent:

   **Option A: Command Line**
   ```bash
   cd samples/python/hosts/cli
   uv run . --agent http://localhost:10004
   ```

   **Option B: Demo Web UI**
   ```bash
   cd demo/ui
   echo "GOOGLE_API_KEY=your_api_key_here" > .env
   uv run main.py
   ```
   
   Then navigate to the web UI (typically http://localhost:12000):
   - Click the 'Agents' tab
   - Add the Remote Agent
   - Enter the Agent URL: localhost:10004 (or whatever custom host/port)
   - Click the 'Home' tab (Conversations)
   - Create and start a conversation to test the interaction

## Troubleshooting

If you encounter any of these issues, here are solutions:

### 405 Method Not Allowed
This is expected when accessing the agent via a browser with a GET request. The agent now shows a helpful landing page instead of an error.

### Import or Module Errors
The agent now includes proper package structure for ADK compatibility:
- Make sure you're running the agent from the correct directory
- If you modify the code, ensure the imports maintain proper paths

### Hardlink Warnings
These are just informational messages and won't affect functionality. Use `--link-mode=copy` to suppress them.

## Example Usage

### Registering an MCP Tool

```
Register a new MCP tool with ID "weather-tool" at URL "http://weather-api.example.com/mcp" for checking weather forecasts
```

### Listing Available Tools

```
List all registered MCP tools
```

### Calling an MCP Tool

```
Use the weather-tool to check the forecast for New York
```

### Removing an MCP Tool

```
Remove the weather-tool from the registry
```

## MCP Tool Implementation Guide

To create an MCP-compatible tool that can be used with this connector, your service should:

1. Expose an HTTP endpoint that accepts POST requests
2. Accept JSON input in the format: `{"input": "user query or structured data"}`
3. Return JSON output with your tool's response

Example MCP tool response format:
```json
{
  "result": "Tool response data",
  "metadata": {
    "tool_name": "example-tool",
    "version": "1.0.0"
  }
}
```

## Technical Implementation

- **Google ADK Integration**: Built with Google's Agent Development Kit
- **Streaming Support**: Provides incremental updates during processing
- **A2A Protocol Integration**: Full compliance with A2A specifications
- **MCP Tool Registry**: In-memory registry of MCP tools with metadata
- **Persistent Storage**: Option to save tool registry to disk
- **Real HTTP Integration**: Actually connects to and calls MCP tools via HTTP
- **Web Interface**: Helpful landing page when accessed via browser

## Limitations

- Basic authentication support for MCP tools
- Tool validation is minimal (just checks URL availability)
- Limited error handling for complex MCP tool failures

## Learn More

- [A2A Protocol Documentation](https://google.github.io/A2A/#/documentation)
- [Model Context Protocol (MCP)](https://google.github.io/A2A/#/topics/a2a_and_mcp)
- [Google ADK Documentation](https://github.com/google/A2A/tree/main/samples/python/agents/google_adk)