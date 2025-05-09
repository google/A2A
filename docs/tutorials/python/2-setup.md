# Set up Your Environment

## What You'll Need

- A code editor such as Visual Studio Code (VS Code).
- A command prompt/terminal (e.g., Terminal on Linux/macOS, Command Prompt or PowerShell on Windows, or the integrated terminal in VS Code).
- Python 3.10 or newer. You can download it from [python.org](https://www.python.org/downloads/). To check your Python version, open your terminal and type `python --version` or `python3 --version`.

## Project Setup

1. **Clone the Repository:**
    First, clone the A2A repository which contains the Python SDK and examples:

    ```bash
    git clone https://github.com/google/A2A.git
    cd A2A/a2a-python-sdk
    ```

    This tutorial will primarily use the `a2a-python-sdk` directory.

2. **Create and Activate a Virtual Environment:**
    It's highly recommended to use a virtual environment to manage your project's dependencies. This isolates your project's packages from your global Python installation.

    Navigate to the `a2a-python-sdk` directory if you're not already there.

    ```bash
    # If you're in the A2A/ root, run:
    # cd a2a-python-sdk
    ```

    Create a virtual environment (we'll call it `.venv`):

    ```bash
    python -m venv .venv
    ```

    Activate the virtual environment:
    - On macOS and Linux:

        ```bash
        source .venv/bin/activate
        ```

    - On Windows (Command Prompt):

        ```bash
        .\.venv\Scripts\activate.bat
        ```

    - On Windows (PowerShell):

        ```bash
        .\.venv\Scripts\Activate.ps1
        ```

    Your terminal prompt should now indicate that you are in the virtual environment (e.g., `(.venv) ...`). If you open a new terminal window, remember to activate the virtual environment again.

3. **Install the A2A Python SDK:**
    With the virtual environment activated, install the A2A Python SDK and its core dependencies from the `a2a-python-sdk` directory:

    ```bash
    pip install .
    ```

    This command installs the SDK defined in the `pyproject.toml` file located in the current directory.

## Check Your Setup

Run the following command to ensure Python is working correctly within your virtual environment and the SDK's core modules are importable:

```bash
python -c "import a2a.server; import a2a.client; import a2a.types; print('A2A SDK basic imports successful!')"
```

If you see the message "A2A SDK basic imports successful!", you are ready to proceed to the next step.
