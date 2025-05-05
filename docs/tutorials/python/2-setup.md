# Set up Your Environment

## What You'll Need <!-- {docsify-ignore} -->

- A code editor such as Visual Studio Code (VS Code)
- A command prompt such as Terminal (Linux), iTerm (Mac) or just the Terminal in VS Code

## Python Environment <!-- {docsify-ignore} -->

We'll be using [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/getting-started/installation/) as our package manager and to set up our project.

The A2A libraries we'll be using require `python >= 3.12` which [uv can install](https://docs.astral.sh/uv/guides/install-python/) if you don't already have a matching version. We'll be using python 3.12.

## Check <!-- {docsify-ignore} -->

Run the following command to make sure you're ready for the next step.

```bash
echo 'import sys; print(sys.version)' | uv run -
```

If you see something similar to the following, you are ready to proceed!

```bash
3.12.3 (main, Feb  4 2025, 14:48:35) [GCC 13.3.0]
```

<div class="bottom-buttons" style="flex flex-row">
  <a href="#/tutorials/python/1_introduction.md" class="back-button">Back</a>
  <a href="#/tutorials/python/3_create_a_project.md?id=creating-a-project" class="next-button">Next</a>
</div>
