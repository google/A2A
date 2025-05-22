# Auth for Headless Agents

This sample demonstrates how headless agent's tools can leverage [Auth0's Client-Initiated Backchannel Authentication (CIBA) flow](https://auth0.com/docs/get-started/authentication-and-authorization-flow/client-initiated-backchannel-authentication-flow) to request user authorization via push notification and obtain tokens for accessing separate APIs.

Additionally, it shows agent-level authorization via the [OAuth 2.0 Client Credentials flow](https://auth0.com/docs/get-started/authentication-and-authorization-flow/client-credentials-flow).

## How It Works

Allows an A2A client to securely interact with an external HR agent owned by the fictional company Staff0 to verify whether the provided user data corresponds to an active employee.

With the authorization of the employee involved (via push notification), the Staff0 HR agent can access the company's internal HR API to retrieve employment details.

```mermaid
sequenceDiagram
   participant Employee as John Doe
   participant A2AClient as A2A Client
   participant Auth0 as Auth0 (staff0.auth0.com)
   participant HR_Agent as Staff0 HR Agent
   participant HR_API as Staff0 HR API

   A2AClient->>HR_Agent: Get A2A Agent Card
   HR_Agent-->>A2AClient: Agent Card
   A2AClient->>Auth0: Request access token (Client Credentials)
   Auth0-->>A2AClient: Access Token
   A2AClient->>HR_Agent: Does John Doe with email jdoe@staff0.com work at Staff0? (Access Token)
   HR_Agent->>Auth0: Request access token (CIBA)
   Auth0->>Employee: Push notification to approve access
   Employee-->>Auth0: Approves access
   Auth0-->>HR_Agent: Access Token
   HR_Agent->>HR_API: Retrieve employment details (Access Token)
   HR_API-->>HR_Agent: Employment details
   HR_Agent-->>A2AClient: Yes, John Doe is an active employee.
```

## Prerequisites

- Python 3.12 or higher
- [UV](https://docs.astral.sh/uv/)
- [Gemini API key](https://ai.google.dev/gemini-api/docs/api-key)
- An [Auth0](https://auth0.com/) tenant with the following configuration:
  - **APIs**
    - HR API
      - Audience: `https://staff0/api`
      - Permissions: `read:employee`
    - HR Agent
      - Audience: `https://staff0/agent`
      - Permissions: `read:employee_status`
  - **Applications**
    - A2A Client
      - Grant Types: `Client Credentials`
      - APIs: `HR Agent` (enabled permissions: `read:employee_status`)
    - HR Agent
      - Grant Types: `Client Initiated Backchannel Authentication (CIBA)`
      - APIs: `Auth0 Management API` (enabled permissions: `read:users`)
  - Push Notifications using [Auth0 Guardian](https://auth0.com/docs/secure/multi-factor-authentication/auth0-guardian) must be `enabled`.
  - A test user enrolled in Guardian MFA.

## Running the Sample

1. Create a `.env` file by copying [.env.example](.env.example), and provide the required environment variable values.

2. Start HR Agent and HR API:

   ```bash
   uv run --prerelease=allow .
   ```

3. Run the test client:
   ```bash
   uv run --prerelease=allow test_client.py
   ```
