"""
Task manager implementation for the A2A-MCP Connector Agent.

This module provides the necessary task management functionality to integrate
our agent with the A2A protocol.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, AsyncIterable, Dict, List, Optional, Tuple

# Add the parent directory to the Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from common.types import Message, Part, TextPart, DataPart, TaskState, TaskStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentTaskManager:
    """
    Task manager implementation for the A2A-MCP Connector Agent.
    
    This class handles the creation of tasks and the routing of messages to the agent.
    """

    def __init__(self, agent):
        self.agent = agent
        
    async def process_message(
        self, message: Message, task_id: str, streaming: bool = False
    ) -> AsyncIterable[Tuple[TaskState, Optional[Message], Optional[str]]]:
        """Process a message using the agent."""
        async for result in self.agent.process_message(message, task_id, streaming):
            yield result