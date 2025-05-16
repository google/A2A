# travel planner example
> This is a Python implementation that adheres to the A2A (Assume to Answer) protocol. 
> It is a travel assistant in line with the specifications of the OpenAI model, capable of providing you with travel planning services.
> A travel assistant demo implemented based on Google's official a2a-python SDK.

## Getting started

1. update [config.json](config.json) with your own OpenAI API key etc.
```json

{
  "model_name":"qwen3-32b",
  "api_key": "sk-xxxx",
  "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
}

```

2. Start the server
    ```bash
    uv run .
    ```

3. Run the loop client
    ```bash
    uv run loop_client.py
    ```
   

## License

This project is licensed under the terms of the [Apache 2.0 License](/LICENSE).

## Contributing

See [CONTRIBUTING.md](/CONTRIBUTING.md) for contribution guidelines.

