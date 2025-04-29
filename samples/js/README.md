# JavaScript Samples

The provided samples are built using [Genkit](https://genkit.dev/) using the Gemini API.

## Agents

- [Movie Agent](src/agents/movie-agent/README.md): Uses TMDB API to search for movie information and answer questions.
- [Coder Agent](src/agents/coder/README.md): Generates full code files as artifacts.

## Testing the Agents

First, follow the instructions in the agent's README file, then run `npx tsx ./cli.ts` to start up a command-line client to talk to the agents. Example:

1. Navigate to the samples/js directory:
    ```bash
    cd samples/js
    ```
2. Run npm install:
    ```bash
    npm install
    ```
3. Run an agent:
```bash
export GEMINI_API_KEY=<your_api_key>
npm run agents:coder

# in a separate terminal
npm run a2a:cli
```
---
**NOTE:** 
This is sample code and not production-quality libraries.
---
