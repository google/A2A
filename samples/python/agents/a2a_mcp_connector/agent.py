"""
A2A-MCP Connector Agent implementation.

This agent serves as a bridge between A2A (Agent-to-Agent) protocol and MCP (Model Context Protocol),
providing an intuitive interface for connecting to and using MCP tools through A2A.
"""

import json
import logging
import requests
import os
import sys
from typing import Any, AsyncIterable, Dict, List, Optional

# Add the parent directory to the Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.tool_context import ToolContext
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from base_agent import AgentWithTaskManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary to store registered MCP tools
mcp_tools = {}

# Optional path to save MCP tool registry
REGISTRY_PATH = os.getenv("MCP_REGISTRY_PATH", "mcp_tools_registry.json")

def load_registry():
    """Load the MCP tool registry from disk if available."""
    global mcp_tools
    try:
        if os.path.exists(REGISTRY_PATH):
            with open(REGISTRY_PATH, 'r') as f:
                mcp_tools = json.load(f)
                logger.info(f"Loaded {len(mcp_tools)} MCP tools from registry")
    except Exception as e:
        logger.error(f"Error loading MCP tool registry: {e}")

def save_registry():
    """Save the MCP tool registry to disk."""
    try:
        with open(REGISTRY_PATH, 'w') as f:
            json.dump(mcp_tools, f, indent=2)
            logger.info(f"Saved {len(mcp_tools)} MCP tools to registry")
    except Exception as e:
        logger.error(f"Error saving MCP tool registry: {e}")

def register_mcp_tool(tool_id: str, tool_url: str, tool_description: str) -> Dict[str, Any]:
    """
    Register an MCP tool with the connector.
    
    Args:
        tool_id (str): Unique identifier for the MCP tool
        tool_url (str): URL endpoint for the MCP tool
        tool_description (str): Description of what the tool does
        
    Returns:
        Dict[str, Any]: Registration status and tool information
    """
    if tool_id in mcp_tools:
        return {"status": "already_exists", "message": f"Tool '{tool_id}' is already registered"}
    
    # Validate the URL format
    if not tool_url.startswith(("http://", "https://")):
        return {"status": "error", "message": f"Invalid URL format: {tool_url}. URL must start with http:// or https://"}
    
    # Try to validate the MCP endpoint (optional but helpful)
    try:
        # In a production implementation, we might check capabilities or validate the MCP service
        # For this example, we'll just check if the URL is reachable
        response = requests.head(tool_url, timeout=5)
        if response.status_code >= 400:
            logger.warning(f"MCP tool URL returned status code {response.status_code}: {tool_url}")
    except Exception as e:
        logger.warning(f"Could not validate MCP tool URL: {e}")
    
    tool_info = {
        "id": tool_id,
        "url": tool_url,
        "description": tool_description,
        "status": "registered"
    }
    
    mcp_tools[tool_id] = tool_info
    logger.info(f"Registered MCP tool: {tool_id} at {tool_url}")
    
    # Save the updated registry
    save_registry()
    
    return {"status": "success", "tool": tool_info}

def list_mcp_tools() -> Dict[str, Any]:
    """
    List all registered MCP tools.
    
    Returns:
        Dict[str, Any]: Dictionary containing all registered tools
    """
    return {"tools": list(mcp_tools.values())}

def call_mcp_tool(tool_id: str, input_data: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Call an MCP tool with the given input data.
    
    Args:
        tool_id (str): The ID of the MCP tool to call
        input_data (str): The input data for the MCP tool (JSON string or plain text)
        tool_context (ToolContext): The context in which the tool operates
        
    Returns:
        Dict[str, Any]: Results from the MCP tool call
    """
    if tool_id not in mcp_tools:
        return {"status": "error", "message": f"Tool '{tool_id}' is not registered"}
    
    tool_info = mcp_tools[tool_id]
    
    # Let the user know we're processing
    tool_context.actions.thinking(f"Calling MCP tool: {tool_id} at {tool_info['url']}")
    
    # Parse input data - could be JSON string or plain text
    data_to_send = input_data
    if input_data.strip().startswith('{'):
        try:
            data_to_send = json.loads(input_data)
        except json.JSONDecodeError:
            # Not valid JSON, use as plain text
            pass
    
    try:
        # Make the actual request to the MCP service
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            tool_info['url'],
            json={"input": data_to_send},
            headers=headers,
            timeout=30
        )
        
        # Log the response status
        logger.info(f"MCP tool {tool_id} returned status code {response.status_code}")
        
        # Handle successful response
        if response.status_code < 400:
            try:
                result = response.json()
                return {
                    "status": "success",
                    "tool_id": tool_id,
                    "result": result
                }
            except json.JSONDecodeError:
                # If not JSON, return the text
                return {
                    "status": "success",
                    "tool_id": tool_id,
                    "result": response.text
                }
        else:
            # Handle error response
            return {
                "status": "error",
                "tool_id": tool_id,
                "message": f"MCP tool returned error code {response.status_code}",
                "details": response.text
            }
    except Exception as e:
        logger.error(f"Error calling MCP tool: {e}")
        return {
            "status": "error",
            "tool_id": tool_id,
            "message": f"Error calling MCP tool: {str(e)}"
        }


def remove_mcp_tool(tool_id: str) -> Dict[str, Any]:
    """
    Remove a registered MCP tool.
    
    Args:
        tool_id (str): The ID of the MCP tool to remove
        
    Returns:
        Dict[str, Any]: Removal status
    """
    if tool_id not in mcp_tools:
        return {"status": "error", "message": f"Tool '{tool_id}' is not registered"}
    
    tool_info = mcp_tools.pop(tool_id)
    logger.info(f"Removed MCP tool: {tool_id}")
    
    # Save the updated registry
    save_registry()
    
    return {"status": "success", "message": f"Successfully removed tool '{tool_id}'", "removed_tool": tool_info}


class A2AMCPConnectorAgent(AgentWithTaskManager):
    """An agent that connects A2A and MCP protocols with an intuitive interface."""

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain", "application/json"]

    def __init__(self):
        # Load any existing MCP tool registry
        load_registry()
        
        self._agent = self._build_agent()
        self._user_id = "mcp_connector_agent"
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    def get_processing_message(self) -> str:
        return "Processing your request with the A2A-MCP connector..."

    def _build_agent(self) -> LlmAgent:
        """Builds the LLM agent for the A2A-MCP connector."""
        return LlmAgent(
            model="gemini-2.0-flash-001",
            name="a2a_mcp_connector",
            description=(
                "A connector agent that bridges A2A and MCP protocols, "
                "allowing easy registration and interaction with MCP tools."
            ),
            instruction="""
            You are an A2A-MCP Connector Agent, designed to make it easy for users to register and interact with 
            MCP (Model Context Protocol) tools through the A2A (Agent-to-Agent) protocol.
            
            You can help users with the following tasks:
            
            1. Register MCP tools by providing a tool ID, URL, and description using register_mcp_tool()
            2. List all registered MCP tools using list_mcp_tools()
            3. Call MCP tools with specific input data using call_mcp_tool()
            4. Remove MCP tools using remove_mcp_tool()
            
            When a user requests to register a new MCP tool:
            - Ask for the tool ID, URL, and description if not provided
            - Use register_mcp_tool() to register the tool
            - Confirm the successful registration
            
            When a user asks to use or call an MCP tool:
            - Check if the tool is registered using list_mcp_tools()
            - If not registered, suggest registering the tool first
            - If registered, use call_mcp_tool() to invoke the tool with the user's input
            - Return the results to the user
            
            When a user asks to remove a tool:
            - Check if the tool exists
            - Use remove_mcp_tool() to delete it
            - Confirm the successful removal
            
            Always be helpful and explain the steps involved in working with MCP tools.
            Provide clear instructions for how to use the available functions.
            
            IMPORTANT CONCEPTS TO EXPLAIN IF ASKED:
            
            A2A (Agent-to-Agent) Protocol:
            - A standardized way for AI agents to communicate with each other
            - Provides a common interface for agent discovery and task delegation
            - Enables interoperability between different agent frameworks and vendors
            
            MCP (Model Context Protocol):
            - A protocol for structuring tool interactions with AI models
            - Allows models to call external tools and use their results
            - Standardizes the format for tool inputs and outputs
            
            In your role, you bridge these protocols by:
            1. Exposing an A2A interface for other agents to communicate with you
            2. Managing connections to MCP-compatible tools
            3. Simplifying the process of discovering and using MCP tools
            """,
            tools=[
                register_mcp_tool,
                list_mcp_tools,
                call_mcp_tool,
                remove_mcp_tool,
            ],
        )