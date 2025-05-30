# H2A Profile: Human-to-Agent Interaction Extension for A2A

**Status**: Draft Proposal  
**Author(s)**: Ushur Team  
**Purpose**: Introduce a minimal and secure extension for human-agent intent encoding within the A2A ecosystem.

## Motivation

While A2A facilitates interoperable agent-to-agent collaboration, there is currently no formalized structure for capturing and securely transmitting **human-originated intent**, constraints, or privacy preferences.

This proposal defines a **Human-to-Agent (H2A) Profile** — a lightweight JSON structure that can be embedded in A2A task messages and routed via existing agent mechanisms, while:

- Ensuring **field-level access control**
- Guaranteeing **authenticity** via message signing
- Supporting **goal-driven routing** of user intent

## Spec Summary

An `h2a` object consists of:

| Field              | Type     | Description |
|-------------------|----------|-------------|
| `user_input`       | object   | Human's input (text, form, etc.) |
| `interaction_goals` | array  | List of routing hints or desired outcomes |
| `_acl`             | object   | Access control map: field → [agent IDs] |
| `_sig`             | string   | JWS-style signature over `h2a` payload |

## Example Usage

```json
{
  "messages": [
    {
      "role": "user",
      "parts": [
        {
          "type": "data",
          "data": {
            "h2a": {
              "user_input": {
                "type": "text",
                "value": "I need to update my address"
              },
              "interaction_goals": ["address_change", "confirmation"],
              "_acl": {
                "user_input": ["agent-1", "agent-2"],
                "user_situation": ["agent-1"],
                "user_expectations": "public"
              },
              "_sig": "JWS-signature-of-above"
            }
          }
        }
      ]
    }
  ]
}
```

## Proposed Agent Roles

- **Edge Agent**: Captures H2A message, applies `_acl`, signs the packet.
- **Router Agent**: Validates `_sig`, enforces `_acl`, routes to appropriate agent(s).
- **Business Agent**: Handles task logic and responds via A2A channels.

## Benefits

- **Minimal**: Adds only what A2A doesn’t already cover.
- **Secure**: Built-in signature mechanism for zero-trust routing environments.
- **Compositional**: Can be embedded in existing A2A flows without schema breakage.

## Next Steps

We invite discussion and comments. Reference implementation under way.
