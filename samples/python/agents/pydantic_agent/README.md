# Pydantic Agent - SummarizerAgent

This module contains an example agent, `SummarizerAgent`, built using Pydantic AI. This agent is designed to take a text input and generate a concise summary of that text as output.

## How to Run

1.  **Navigate to the Directory:**
```
bash
    cd samples/python/agents/pydantic_agent
    
```
2.  **Run the Agent:**

    Execute the `__main__.py` file using Python:
```
bash
    python __main__.py
    
```
This will start an A2A server, hosting the `SummarizerAgent`.

3.  **Using the agent**:
    To use the agent, you will need to connect to it using an a2a client, or using the demo UI, after adding the agent using the agent card url.

    You will be able to send messages to the agent, and the agent will return a summary of the text provided.