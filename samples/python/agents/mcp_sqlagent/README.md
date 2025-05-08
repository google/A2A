# MCP SQLite Agent

This is an A2A-compatible agent that uses Claude 3 Sonnet to interact with postgres databases through the MCP (Model Context Protocol).

## Features

- SQL database operations and queries
- Streaming responses
- Push notifications
- A2A protocol compatibility
- Claude 3 Sonnet integration

## Prerequisites

- Python 3.8+
- Anthropic API key
- MCP server implementation

## Setup & Running

1. Navigate to the samples directory:

   ```bash
   cd samples/python/agents/mcp-agent
   ```

2. Create an environment file with your API key:

   ```bash
   echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
   ```

3. Run the agent:

   ```bash
   # Basic run on default port 10020
   uv run .

   # On custom host/port
   uv run . --host 0.0.0.0 --port 8080
   ```

## Usage

Start the agent server:

```bash
python -m agents.mcp-a2a --host localhost --port 10020
```

The agent will be available at `http://localhost:10020` and can be discovered by A2A clients.

## Configuration

The agent can be configured through environment variables:

- `ANTHROPIC_API_KEY`: Your Anthropic API key (required)
- `HOST`: Server host (default: localhost)
- `PORT`: Server port (default: 10020)
- `DB_NAME`: test_db
- `DB_USER`:postgres
- `DB_PASSWORD`: postgres
- `DB_HOST`: localhost
- `DB_PORT`: 5432

## API Endpoints

- `/.well-known/jwks.json`: JWKS endpoint for push notification authentication
- Standard A2A protocol endpoints

## Skills

The agent provides the following skills:

- SQL database operations
- SQL query execution
- Database schema inspection
- Data manipulation

## Note
While running this agent if it not able to find the common package then put the common package inside this project and run it again



