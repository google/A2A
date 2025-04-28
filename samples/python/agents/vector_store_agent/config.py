"""
Configuration file for the Vector Store Agent.
"""

import os
from typing import Optional, Dict, Any, List

# Default OpenAI API configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
DEFAULT_MODEL = os.environ.get("VECTOR_STORE_MODEL", "gpt-4.1-mini")
VECTOR_STORE_ID = os.environ.get("VECTOR_STORE_ID")
USE_MOCK = VECTOR_STORE_ID is None or VECTOR_STORE_ID == ""

# Server configuration
DEFAULT_HOST = os.environ.get("VECTOR_STORE_HOST", "localhost")
DEFAULT_PORT = int(os.environ.get("VECTOR_STORE_PORT", "10050"))

# Streaming configuration
ENABLE_STREAMING = os.environ.get("VECTOR_STORE_ENABLE_STREAMING", "true").lower() == "true"
STREAMING_CHUNK_SIZE = int(os.environ.get("VECTOR_STORE_CHUNK_SIZE", "20"))

# Agent metadata
AGENT_NAME = "Vector Store Knowledge Agent"
AGENT_DESCRIPTION = (
    "A general-purpose vector store query agent using OpenAI's Responses API"
)
AGENT_VERSION = "0.1.0"
AGENT_ORGANIZATION = "Vector Store Research Team"

# Query configuration
DEFAULT_MAX_RESULTS = int(os.environ.get("VECTOR_STORE_MAX_RESULTS", "5"))
DEFAULT_MODEL_PROMPT = """
Based ONLY on the information provided in the retrieved documents, please answer the following query:

{query}

Provide a well-structured and comprehensive response that includes:
1. A clear and direct answer to the query
2. Key points from the relevant documents
3. Citation of sources used

If the information in the documents is insufficient to answer the query,
please state this clearly and explain what information is missing.
"""

# Mock response configuration (used when no vector store is available)
MOCK_RESPONSE_TEMPLATE = """
# Results for: '{query}'

## Top Relevant Results

1. **Document 1**: Example document title
   - Key information related to the query
   - Additional context from this document

2. **Document 2**: Secondary source
   - Supporting information
   - Additional context

## Summary
This is a simulated response generated when no vector store ID is provided.
To get actual results, please set the VECTOR_STORE_ID environment variable.

*Note: This is a mock response. To get real results, configure a vector store.*
"""
