"""
Entry point for the ADK CLI to find and load the agent.
This file is required by the Google ADK.
"""

import os
import sys
import logging

# Add the parent directory to the Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from agent import A2AMCPConnectorAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the agent instance that will be loaded by the ADK
# Note: The ADK expects a specific structure where `agent` is an object
# with a `root_agent` attribute
class AgentContainer:
    def __init__(self):
        self.connector_agent = A2AMCPConnectorAgent()
        self.root_agent = self.connector_agent._agent  # The LLM agent that ADK expects

# This is the exported object that ADK will look for
agent = AgentContainer()