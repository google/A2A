# Creating A Project

Let's first create a project using `uv`. We'll add the `--package` flag in case you want to add tests, or publish your project later

```bash
uv init --package my-project
cd my-project
```

## Using a Virtual Env <!-- {docsify-ignore} -->

We'll create a venv for this project. This only needs to be done once

```bash
uv venv .venv
```

For this and any future terminal windows you open, you'll need to source this venv

```bash
source .venv/bin/activate
```

If you're using a code editor such as VS Code, you'll want to set the Python Interpreter for code completions. In VS Code, press `Ctrl-Shift-P` and select `Python: Select Interpreter`. Then select your project `my-project` followed by the correct python interpreter `Python 3.12.3 ('.venv':venv) ./.venv/bin/python`

The source code should now look similar to this.

```bash
tree .
.
├── pyproject.toml
├── README.md
├── src
│   └── my-project
│       ├── __init__.py
```

## Adding the Google-A2A Python Libraries <!-- {docsify-ignore} -->

Next we'll add the sample A2A python libraries from Google.

```bash
uv add git+https://github.com/google/A2A#subdirectory=samples/python
```

## Setting up the project structure <!-- {docsify-ignore} -->

Let's now create some files we'll later be using

```bash
touch src/my_project/agent.py
touch src/my_project/task_manager.py
```

## Test Run <!-- {docsify-ignore} -->

If everything is setup correctly, you should now be able to run your application.

```bash
uv run my-project
```

The output should look something like this.

```bash
Hello from my-project!
```

<div class="bottom-buttons" style="flex flex-row">
  <a href="#/tutorials/python/2_setup.md" class="back-button">Back</a>
  <a href="#/tutorials/python/4_agent_skills.md?id=agent-skills" class="next-button">Next</a>
</div>
