# LangGraph Currency Agent with A2A Protocol

This sample demonstrates a currency conversion agent exposed through the A2A protocol. It showcases conversational interactions with support for multi-turn dialogue and streaming responses.

## How It Works

This agent uses the Frankfurter API to provide currency exchange information. The A2A protocol enables standardized interaction with the agent, allowing clients to send requests and receive real-time updates.

## Prerequisites

- Go 1.21 or higher
- Access to an OpenAI API Key

## Setup & Running

1. Set up your environment variables:

```bash
export OPENAI_API_KEY=your_api_key_here
```

2. Run the agent:

```bash
# Basic run on default port 10000
go run .

# On custom host/port
go run . --host 0.0.0.0 --port 8080
```

3. In a separate terminal, run an A2A client:

```bash
cd ../../hosts/cli
go run . --agent http://localhost:10000
```

## Key Features

- Multi-turn Conversations: Agent can request additional information when needed
- Real-time Streaming: Provides status updates during processing
- Currency Exchange Tool: Integrates with Frankfurter API for real-time rates
- Conversational Memory: Maintains context across interactions

## Limitations

- Only supports text-based input/output (no multi-modal support)
- Uses Frankfurter API which has limited currency options
- Memory is session-based and not persisted between server restarts
