## Veo Video Generation ADK Agent

This sample uses the Google Agent Development Kit (ADK) to create a "Video Generation" agent. This agent leverages Google's Veo model to generate videos based on text prompts.

The agent takes text requests from the client, such as "Create a video of a cat playing with a fur ball". The generated video is then uploaded to Google Cloud Storage (GCS), and a signed URL for accessing the video is provided back to the client.
Currently, the Veo API does not provide real-time progress updates during video generation. To enhance user experience, this agent simulates progress updates while the video is being processed.

## Prerequisites

- Python 3.9 or higher
- UV
- Access to a Google Cloud Project and appropriate APIs enabled (e.g., Veo API, Cloud Storage API).
- A Google Cloud Service Account with permissions to:
  - Upload objects to Google Cloud Storage.
  - Generate signed URLs for GCS objects (e.g., "Service Account Token Creator" role for generating signed URLs, or permissions to impersonate a service account that has this role).
  Ensure your environment is authenticated (e.g., via `gcloud auth application-default login`).
- (Optional) If the agent uses an LLM for request understanding: Access to an LLM and its API Key (e.g., Gemini).

## Running the Sample

1. Navigate to the samples directory:
    ```bash
    cd samples/python/agents/veo_videogen_google_adk
    ```
2. Create an environment file if needed (e.g., for an LLM API key):

   ```bash
   # Example for a Google LLM API key
   # echo "GOOGLE_API_KEY=your_api_key_here" > .env
