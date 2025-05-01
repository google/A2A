# Agent Skills

An agent skill is a set of capabilities the agent can perform. Here's an example of what it would look like for our echo agent.

```ts
{
  id: "my-project-echo-skill"
  name: "Echo Tool",
  description: "Echos the input given",
  tags: ["echo", "repeater"],
  examples: ["I will see this echoed back to me"],
  inputModes: ["text"],
  outputModes: ["text"]
}
```

This conforms to the skills section of the [Agent Card](documentation?id=representation)

```ts
{
  id: string; // unique identifier for the agent's skill
  name: string; //human readable name of the skill
  // description of the skill - will be used by the client or a human
  // as a hint to understand what the skill does.
  description: string;
  // Set of tag words describing classes of capabilities for this specific
  // skill (e.g. "cooking", "customer support", "billing")
  tags: string[];
  // The set of example scenarios that the skill can perform.
  // Will be used by the client as a hint to understand how the skill can be
  // used. (e.g. "I need a recipe for bread")
  examples?: string[]; // example prompts for tasks
  // The set of interaction modes that the skill supports
  // (if different than the default)
  inputModes?: string[]; // supported mime types for input
  outputModes?: string[]; // supported mime types for output
}
```

## Implementation <!-- {docsify-ignore} -->

Let's create this Agent Skill in code. Open up `src/my-project/__init__.py` and replace the contents with the following code

```python
import google_a2a
from google_a2a.common.types import AgentSkill

def main():
  skill = AgentSkill(
    id="my-project-echo-skill",
    name="Echo Tool",
    description="Echos the input given",
    tags=["echo", "repeater"],
    examples=["I will see this echoed back to me"],
    inputModes=["text"],
    outputModes=["text"],
  )
  print(skill)

if __name__ == "__main__":
  main()
```

## Test Run <!-- {docsify-ignore} -->

Let's give this a run.

```bash
uv run my-project
```

The output should look something like this.

```bash
id='my-project-echo-skill' name='Echo Tool' description='Echos the input given' tags=['echo', 'repeater'] examples=['I will see this echoed back to me'] inputModes=['text'] outputModes=['text']
```

<div class="bottom-buttons" style="flex flex-row">
  <a href="#/tutorials/python/3_create_a_project.md" class="back-button">Back</a>
  <a href="#/tutorials/python/5_add_agent_card.md?id=agent-card" class="next-button">Next</a>
</div>
