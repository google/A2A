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

Next we'll add the sample A2A python libraries from Google. Currently this [pull request](https://github.com/google/A2A/pull/169) has not yet been merged so we'll take the code directly from the pull request. This pull request namespaces the google libraries to prevent naming clashes

```bash
uv add git+https://github.com/djsamseng/A2A#subdirectory=samples/python --branch prefixPythonPackage
```

If you'd prefer you can instead use the code directly from Google's repository.

```bash
uv add git+https://github.com/google/A2A#subdirectory=samples/python
```

However you will have to change the imports going forward such as

```diff
- import google_a2a.common
+ import common
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
