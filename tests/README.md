## Running the tests

1. Run the tests
    ```bash
    uv run pytest -v -s test_a2a_spec.py
    ```

Any time you change `../samples/python/common`, you will need to cleanup the cache like this:

1. `uv clean`
2. `rm -fR .pytest_cache .venv __pycache__`
