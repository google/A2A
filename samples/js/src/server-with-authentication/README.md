# A2A Server with support for global identity and authentication using the Agentic Profile

This folder builds on the work in the ../server folder, and adds support for:

- Decentralized authentication
- Globally unique ids to identify both the agents and the entities they represent, such as people or businesses

The index.ts file starts an HTTP server that authenticates inbound agentic requests using their Agentic Profile.

For more information about the Agentic Profile, see the [What is an Agentic Profile?](#what-is-an-agentic-profile) section below.


## Quickstart

1. Navigate to the samples/js directory:
    ```bash
    cd samples/js
    ```
2. Run npm install:
    ```bash
    npm install
    ```
3. Create agent cards and agentic profiles for testing:
    ```bash
    npm run a2a:setup-auth
    ```
4. Run the agent service that supports authentication.  Don't forget to [create your GEMINI API KEY](https://ai.google.dev/gemini-api/docs/api-key)
    ```bash
    export GEMINI_API_KEY=<your_api_key>
    npm run agents:coder-with-auth
    ```
5. In a separate terminal
    ```bash
    npm run a2a:cli
    ```


## Deeper testing

1. Make sure the server is started:

    ```bash
    export GEMINI_API_KEY=<your_api_key>
    npm run agents:coder-with-auth
    ```

2. For each of the following examples, open a new terminal window. For examples with authentication skip to step #3

    Start the A2A client using the agent card, but still no authentication

    ```bash
    npm run a2a:cli -- -p http://localhost:41241/agents/coder/
    ```

    Start the A2A client using the Agentic Profile, but still no authentication

    ```bash
    npm run a2a:cli -- -p did:web:localhost%3A41241:agents:coder#a2a-coder
    ```

    Start the A2A client with the well-known agent and no authentication

    ```bash
    npm run a2a:cli -- -p http://localhost:41241/
    ```

    Start the A2A client with the well-known agentic profile and no authentication

    ```bash
    npm run a2a:cli -- -p did:web:localhost%3A41241#a2a-coder
    ```

3. In order to use authentication, you must create an agentic profile and keys to authenticate with.  Make sure you have already run the auth-setup script:

    ```bash
    npm run a2a:auth-setup
    ```

    The above script creates a new agentic profile on the test.agenticprofile.ai server, and also stores
    a copy in your filesystem at ~/.agentic/iam/global-me

4. Examples using Agentic Profile authentication

    Start the A2A client with an Agentic Profile and authentication

    ```bash
    npm run a2a:cli -- -p did:web:localhost%3A41241:users:2:coder#a2a-coder -u "#a2a-client"
    ```

    Start the A2A client with the well-known Agentic Profile and authentication

    ```bash
    npm run a2a:cli -- -p did:web:localhost%3A41241#a2a-coder -i "global-me" -u "#a2a-client"
    ```

## How did the CLI command using authentication work?

For the last example from above:

```bash
npm run a2a:cli -- -p did:web:localhost%3A41241#a2a-coder -i "global-me" -u "#a2a-client"
```

- The "--" in the command told **npm run** to pass subsequent command line parameters to the script.
- "-p" is the "peer" agent URI, and can be an HTTP URI for an agent card, or a DID URI for an agentic profile
- "did:web:localhost%3A41241#a2a-coder" references the well-known agentic profile at the service running on localhost
- "-i global-me" says to use the agentic profile at ~/.agentic/iam/global-me 
- "-u #a2a-client" tells the client to use the agentic profile service with an id of "#a2a-client"

 The A2A client performs the following steps:

 1. Uses the DID to fetch the well-known agentic profile at http://localhost:41241/.well-known/did.json
 2. Finds the **service** in the agentic profile with an id of **a2a-coder**
 3. Uses the **serviceEndpoint** to fetch the agent card
 4. When the user starts a task from the cli, a "fishing" HTTP request is made to the agent's endpoint on the A2A server with no authentication
 5. Since the server requires authentication, a 401 response is issued with a challenge
 6. The client finds tbe #a2a-client service of the users agent profile (as specified in the command line)
 7. The client finds the matching private key in the locally stored keyring
 8. The client creates a JWT from the server challenge, the users agent DID, and the private key
 9. The client starts the task again, but this time with an authentication token in the HTTP Authorization header 


## What is an Agentic Profile?

An Agentic Profile is a [W3C DID](https://www.w3.org/TR/did-1.0/) document that:

- Provides a globally unique - user or business scoped - identity
- Supports decentralized authentication


## Globally Unique Identity for Users and Businesses

Current agentic frameworks scope to individual agents, but business and other transactions rely on trust which require knowing who the agent represents and if the agent has the authority to take a particular action on the user or businesses behalf.
 
An Agentic Profile is a JSON document following the [W3C DID](https://www.w3.org/TR/did-1.0/) specification, and represents a person, business, or other entity.  An Agentic Profile lists AI agents that represent the entity, along with information about the agent such as service endpoints and authentication schemes.


## Decentralized Authentication

By default, the Agentic Profile supports decentralized authentication using JWT and public key cryptography.  Each agent listed in the DID document under the **service** property can provide **capabilityInvocation** information.  This information can include a named public key, or a reference to a named public key.

When an agent is challenged, the agent uses its private key to create a JWT which includes both the challenge, and the agent's DID+agent id.  For example the DID did:web:example.com:iam:mike#coder would represent the DID document at https://example.com/iam/mike/did.json and the agent with the id "#coder" in the documents "service" list.


## How does the Agentic Profile integrate with A2A?

Each A2A agent is listed in the **service** array property of the Agentic Profile/DID document using the following conventions:

- The **serviceEndpoint** property is a URL to the A2A agent (when not ending in / or agent.json), or the agent card (when ending in / or agent.json)
- The service **type** is A2A