# Marvin Contact Extractor Agent (A2A Sample)

This sample demonstrates an agent using the [Marvin](https://github.com/prefecthq/marvin) framework to extract structured contact information from text, integrated with the Agent2Agent (A2A) protocol.

## Overview

The agent receives text, attempts to extract contact details (name, email, phone, etc.) into a structured format using Marvin. It manages conversational state across multiple turns to gather required information (name, email) before confirming the extracted data. The agent's response includes both a textual summary/question and the structured data via A2A.


## Key Components

-   **Marvin `ExtractorAgent` (`agent.py`)**: Core logic using `marvin` for extraction and managing multi-turn state via a dictionary.
-   **A2A `AgentTaskManager` (`task_manager.py`)**: Integrates the agent with the A2A protocol, managing task state (including streaming via SSE) and response formatting.
-   **A2A Server (`__main__.py`)**: Hosts the agent and task manager.

## Prerequisites

-   Python 3.12+
-   [uv](https://docs.astral.sh/uv/getting-started/installation/)
-   `OPENAI_API_KEY` (or other LLM provider creds supported by pydantic-ai)

## Setup & Running

1.  Navigate to the Python samples directory:
    ```bash
    cd samples/python/agents/marvin
    ```

2.  Set an LLM provider API key:
    ```bash
    export OPENAI_API_KEY=your_api_key_here
    ```

3.  Set up the Python environment:
    ```bash
    uv venv
    source .venv/bin/activate
    uv sync
    ```

4.  Run the Marvin agent server:
    ```bash
    # Default host/port (localhost:10030)
    MARVIN_DATABASE_URL=sqlite+aiosqlite:///test.db MARVIN_LOG_LEVEL=DEBUG uv run .

    # Custom host/port
    # uv run . --host 0.0.0.0 --port 8080
    ```

    Without `MARVIN_DATABASE_URL` set, conversation history will not be persisted by session id.

5.  In a separate terminal, run an A2A client (e.g., the sample CLI):
    ```bash
    # Ensure the environment is active (source .venv/bin/activate)
    cd samples/python/hosts/cli
    uv run . --agent http://localhost:10030 # Use the correct agent URL/port
    ```


## Extracted Data Structure

The structured data returned in the `DataPart` is defined as:

```python
class ContactInfo(BaseModel):
    name: str = Field(description="Person's first and last name")
    email: EmailStr
    phone: str = Field(description="standardized phone number")
    organization: str | None = Field(None, description="org if mentioned")
    role: str | None = Field(None, description="title or role if mentioned")
```

with a validator to render things nicely if you want and maybe serialize weird things.

## Learn More

-   [Marvin Documentation](https://www.askmarvin.ai/)
-   [Marvin GitHub Repository](https://github.com/prefecthq/marvin)
-   [A2A Protocol Documentation](https://google.github.io/A2A/#/documentation)
