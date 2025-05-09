An example langgraph agent that helps with currency conversion.

## Getting started

1. Extract the zip file and cd to examples folder

2. Create an environment file with your API key:
   ```bash
   echo "GOOGLE_API_KEY=your_api_key_here" > .env
   ```

3. Start the server
    ```bash
    uv run main.py
    ```

4. Run the test client
    ```bash
    uv run test_client.py
    ```