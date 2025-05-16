"""
A2A agent implementation using AutoGen's RoundRobinGroupChat with a weather tool.
"""

import os 
from typing import Dict, Any, AsyncIterable
 
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_agentchat.messages import ModelClientStreamingChunkEvent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core import CancellationToken  

 

# Weather tool implementation
async def get_weather(location: str, unit: str = "celsius") -> str:
    """
    Get the current weather for a location.
    
    Args:
        location: The city or location to get weather for
        unit: The temperature unit (celsius or fahrenheit)
        
    Returns:
        A string with the weather information
    """
    # This is a dummy implementation - in a real app, you would call a weather API
    weather_data = {
        "New York": {"temp": 22, "condition": "Sunny", "humidity": 60},
        "London": {"temp": 18, "condition": "Cloudy", "humidity": 80},
        "Tokyo": {"temp": 28, "condition": "Rainy", "humidity": 75},
        "Sydney": {"temp": 30, "condition": "Clear", "humidity": 50},
        "Paris": {"temp": 20, "condition": "Partly Cloudy", "humidity": 65},
        "Berlin": {"temp": 16, "condition": "Foggy", "humidity": 70},
        "Moscow": {"temp": 5, "condition": "Snowy", "humidity": 85},
        "Dubai": {"temp": 35, "condition": "Hot", "humidity": 45},
        "San Francisco": {"temp": 19, "condition": "Foggy", "humidity": 75},
        "Chicago": {"temp": 15, "condition": "Windy", "humidity": 60},
    }
     
    location_key = next((k for k in weather_data.keys() if k.lower() == location.lower()), None)
    
    # Default response for unknown locations
    if not location_key:
        return f"Weather data for {location} is not available."
    
    data = weather_data[location_key]
    temp = data["temp"]
    
    # Convert to fahrenheit if requested
    if unit.lower() == "fahrenheit":
        temp = temp * 9/5 + 32
    
    return f"The weather in {location_key} is {data['condition']} with a temperature of {temp}°{'F' if unit.lower() == 'fahrenheit' else 'C'} and humidity of {data['humidity']}%."


class WeatherAgent:
    """A wrapper for AutoGen's RoundRobinGroupChat with a single weather assistant agent."""
    
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]
    
    def __init__(self, api_key: str | None = None):
        """Initialize the weather agent."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        
        # Create OpenAI client
        model_client = OpenAIChatCompletionClient(
            model="gpt-4o-mini",   
            api_key=self.api_key,
        )
        
        # Create assistant agent with weather tool
        weather_assistant = AssistantAgent(
            name="weather_assistant",
            model_client=model_client,
            system_message=(
                "You are a helpful weather assistant that can provide weather information. "
                "Use the get_weather tool to look up current weather. " 
                "If the user asks about anything other than weather, respond to them very briefly but also politely let them know that you can only provide weather information. Once you have responded to the user, end with 'TERMINATE'."
            ),
            tools=[get_weather],
            model_client_stream=False,  # Enable streaming tokens
        )
        
        # Create a team with a single agent
        termination_condition = TextMentionTermination("TERMINATE") | MaxMessageTermination(5)
        self.team = RoundRobinGroupChat(
            [weather_assistant],
            termination_condition=termination_condition
        )
    
    async def invoke(self, query: str, session_id: str) -> str:
        """Process a query and return the response."""
        # Set up cancellation token
        cancellation_token = CancellationToken()
        
        # Run the team
        task_result = await self.team.run(
            task=query,
            cancellation_token=cancellation_token
        )
        
        # Extract the response
        if task_result.messages and len(task_result.messages) > 1:
            # Return the last message from the assistant
            return task_result.messages[-1].to_text()
        else:
            return "I couldn't process your weather request."

    async def stream(self, query: str, session_id: str) -> AsyncIterable[Dict[str, Any]]:
        """Process a query and stream the responses."""
        # Yield the initial "working on it" message
        yield {
            "is_task_complete": False,
            "require_user_input": False,
            "content": "Processing your weather request..."
        }
        
        # Set up cancellation token
        cancellation_token = CancellationToken()
        
        # Stream content from the model
        async for message in self.team.run_stream(task=query, cancellation_token=cancellation_token):
            # If it's a streaming chunk from the model, yield it
            if isinstance(message, ModelClientStreamingChunkEvent):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": message.to_text()
                }
            elif not isinstance(message, TaskResult ):
                # If it's a message from the assistant, yield it
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": message.to_text()
                }
            # If it's the final message, yield it as complete
            elif isinstance(message, TaskResult):
                yield {
                    "is_task_complete": True,
                    "require_user_input": False,
                    "content": f"Task completed successfully. Reason: {message.stop_reason}"
                }