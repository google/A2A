# AutoGen Currency Agent

A specialized agent for currency conversion built with AutoGen framework, integrated with the Agent-to-Agent (A2A) protocol.

## Features

- **Currency Conversion**: Get exchange rates between different currencies
- **Multi-turn Conversations**: Supports context-aware follow-up questions about exchange rates
- **Real-time Updates**: Streaming responses for immediate feedback
- **Push Notifications**: Support for webhook-based notifications of task status changes
- **API Integration**: Uses the Frankfurter API to fetch real-time currency exchange data

## Prerequisites

- Python 3.10 or higher
- AutoGen
- An OpenAI API key for the language model

## Environment Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   # Create a .env file with your OpenAI API key
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   ```

## Running the Agent

Start the agent server with:

```bash
python -m agents.autogen
```

To specify a host and port:

```bash
python -m agents.autogen --host 0.0.0.0 --port 8000
```

## Using the Agent

### Synchronous Request Example

```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "sendTask",
  "params": {
    "id": "task-001",
    "sessionId": "session-001",
    "message": {
      "role": "user",
      "parts": [
        {
          "type": "text",
          "text": "What is the exchange rate from USD to EUR?"
        }
      ]
    },
    "acceptedOutputModes": ["text/plain"],
    "historyLength": 5
  }
}
```

### Streaming Request Example

```json
{
  "jsonrpc": "2.0",
  "id": "2",
  "method": "sendTaskSubscribe",
  "params": {
    "id": "task-002",
    "sessionId": "session-001",
    "message": {
      "role": "user",
      "parts": [
        {
          "type": "text",
          "text": "What's the exchange rate for JPY to GBP today?"
        }
      ]
    },
    "acceptedOutputModes": ["text/plain"],
    "historyLength": 5
  }
}
```

## Development

The agent uses AutoGen to orchestrate interactions between:
- An assistant agent that interprets user queries
- A user proxy agent with the exchange rate tool function

## License

MIT
