An example langgraph agent that helps with currency conversion.
Support the use of multiple model versions.

## Getting started

1. Extract the zip file and cd to examples folder

2. Modify the llm_config.json file and fill in your model configuration information:
```json
{
  "model_name":"your-model-name", 
  "api_key": "your-api-key",
  "base_url": "https://your-base-url/api/v1"
}
```

3. Start the server
```bash
  uv run main.py
```

4. Run the test client
```bash
  uv run test_client.py
```

## License

This project is licensed under the terms of the [Apache 2.0 License](LICENSE).

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines.