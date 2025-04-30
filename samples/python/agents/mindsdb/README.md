## MindsDB Enterprise Data Agent

Powered by Gemini 2.5 flash + MindsDB. This sample uses A2A to connect, query and analyze data across hundreds of federated data sources including databases, data lakes, and SaaS applications.

The agent takes natural language queries from users and translates them into appropriate SQL queries for MindsDB, handling data federation across multiple sources. It can:

- Query data from various sources including databases, data lakes, and SaaS applications
- Perform analytics across federated data sources
- Handle natural language questions about your data
- Return structured results from multiple data sources
<img width="597" alt="image" src="https://github.com/user-attachments/assets/3e070239-f2a1-4771-8840-6517bd0c6545" />

## Prerequisites

- Python 3.9 or higher
- MindsDB account and API credentials (https://mdb.ai)
- Create a MindsDB Mind (an AI model that can query data from a database), by default we use the demo one: `Sales_Data_Expert_Demo_Mind`

## Environment Variables

In mdb.ai, once you create a Mind (an AI model that can query data from a database), you can use it in the agent.

Create a `.env` file in the project directory with the following variables:

```
MINDS_API_KEY=your_mindsdb_api_key
MIND_NAME=your_mindsdb_model_name
```

- `MINDS_API_KEY`: Your MindsDB API key (required)
- `MIND_NAME`: The name of the MindsDB Mind to use (required)

## Running the Sample

1. Navigate to the samples directory:
    ```bash
    cd samples/python/agents/mindsdb
    ```

2. Run the agent:
    ```bash
    uv run .
    ```

3. In a separate terminal, run the A2A client:
    ```bash
    # Connect to the agent (specify the agent URL with correct port)
    cd samples/python/hosts/cli
    uv run . --agent http://localhost:10006

    # If you changed the port when starting the agent, use that port instead
    # uv run . --agent http://localhost:YOUR_PORT
    ```
4. Ask a question to the agent about your data.

## Example Queries

You can ask questions like:

- "What percentage of prospects are executives?"
- "What is the distribution of companies by size?"

The agent will handle the complexity of joining and analyzing data across different sources.
