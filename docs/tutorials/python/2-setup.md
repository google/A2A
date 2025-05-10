
# 2. Setup Your Environment

## Prerequisites

- Python 3.10 or higher.
- Access to a terminal or command prompt.
- Git, for cloning the repository.
- A code editor (e.g., VS Code) is recommended.

## Clone the Repository

If you haven't already, clone the A2A repository and navigate to the Python SDK directory:

```bash
git clone https://github.com/google/A2A.git
cd A2A/a2a-python-sdk
```

## Python Environment & SDK Installation

We recommend using a virtual environment for Python projects. The A2A Python SDK uses `uv` for dependency management, but you can use `pip` with `venv` as well.

1. **Create and activate a virtual environment:**

    Using `venv` (standard library):

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

    Or, if you have `uv` installed ([see uv installation](https://docs.astral.sh/uv/getting-started/installation/)):

    ```bash
    uv venv
    source .venv/bin/activate # On Windows: .venv\Scripts\activate
    ```

2. **Install the A2A SDK and its dependencies:**

    The `a2a-python-sdk` directory contains the SDK source code. To make it and its dependencies available in your environment, run:

    ```bash
    pip install -e .[dev]
    ```

    This command installs the SDK in "editable" mode (`-e`), meaning changes to the SDK source code are immediately available. It also installs development dependencies specified in `pyproject.toml`.

    If you are using `uv`, it will use the `uv.lock` file to install dependencies:

    ```bash
    uv sync --dev
    ```

## Verify Installation

After installation, you should be able to import the `a2a` package in a Python interpreter:

```bash
python -c "import a2a; print('A2A SDK imported successfully!')"
```

If this command runs without error and prints the success message, your environment is set up correctly.
