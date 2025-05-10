# Daytona Sandbox Orchestration Agent

## How to Use Daytona

Follow these steps to run the **Daytona** agent:

1. Provide the folloving environment variables:

    ```
    # Daytona API Configuration
    DAYTONA_API_KEY=your_daytona_api_key_here
    DAYTONA_API_URL=https://app.daytona.io/api
    DAYTONA_TARGET=us

    # A2A Configuration
    A2A_HOST_URL=http://localhost:8080
    GOOGLE_API_KEY=your_google_api_key_here
    ```

2. Start the Daytona agent with the following command:

    ```bash
    cd samples/python && python -m agents.daytona.__main__ --host localhost --port 10004
    ```


## Multiagent demo with the Coder agent


Follow these steps to run the multiagent demo where Coder generates the code you can securely run in Daytona:

1. Run the following commands in separate terminals:

    ```bash
    # Terminal 1: Start the Daytona agent
    cd samples/python && python -m agents.daytona.__main__ --host localhost --port 10004

    # Terminal 2: Start the Coder agent
    cd samples/js && npm run agents:coder

    # Terminal 3: Start the multiagent demo UI
    cd demo/ui && PYTHONPATH=$PYTHONPATH:$(pwd)/../../samples/python python main.py
    ```

3. Open your browser and go to http://localhost:12000

4. Navigate to the "Agents" page in the dashboard

5. Add the following agents by entering their URLs:

   - Daytona agent: http://localhost:10004
   - Coder agent: http://localhost:41241

6. Go to the "Chat" page and enter your prompt, for example:

    ```
    Use the Coder agent to generate Python code that calculates the first 25 numbers of the Fibonacci sequence, then run that code in a new Daytona sendbox via Daytona agent and give me the output.
    ```

The host agent will coordinate between the Coder agent to generate the code and the Daytona agent to run it in a sandbox.
