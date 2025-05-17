# 2. Setup Your Environment

## Prerequisites

- Python 3.10 or higher.
- Access to a terminal or command prompt.
- Git, for cloning the repository.
- A code editor (e.g., VS Code) is recommended.

## Clone the Repository

If you haven't already, clone the A2A repository and navigate to the Python SDK directory:

```bash
git clone https://github.com/google/a2a-python.git -b main --depth 1
cd a2a-python
```

## Python Environment & SDK Installation

We recommend using a virtual environment for Python projects. The A2A Python SDK uses `uv` for dependency management, but you can use `pip` with `venv` as well.

1. **Create and activate a virtual environment:**

    Using `venv` (standard library):

    === "Mac/Linux"

        ```sh
        python -m venv .venv
        source .venv/bin/activate
        ```

    === "Windows"

        ```powershell
        python -m venv .venv
        .venv\Scripts\activate
        ```

2. **Install the A2A SDK and its dependencies:**

    The `a2a-python` repository contains the SDK source code. To make it and its dependencies available in your environment, run:

    ```bash
    pip install -e '.[dev]'
    ```

    This command installs the SDK in "editable" mode (`-e`), meaning changes to the SDK source code are immediately available. It also installs development dependencies specified in `pyproject.toml`.

## Verify Installation

After installation, you should be able to import the `a2a` package in a Python interpreter:

```bash
python -c "import a2a; print('A2A SDK imported successfully')"
```

If this command runs without error and prints the success message, your environment is set up correctly.
