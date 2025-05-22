import json
import sys
import os

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from collections.abc import AsyncGenerator

class TravelPlannerAgent:
    """ travel planner Agent."""

    def __init__(self):
        """Initialize the travel dialogue model"""
        try:
            with open("config.json") as f:
                config = json.load(f)
            if not os.getenv(config["api_key"]):
                print(f'{config["api_key"]} environment variable not set.')
                sys.exit(1)
            api_key = os.getenv(config["api_key"])

            self.model = ChatOpenAI(
                model=config["model_name"],
                base_url=config["base_url"],
                api_key=api_key,
                temperature=0.7  # Control the generation randomness (0-2, higher values indicate greater randomness)
            )
        except FileNotFoundError:
            print("Error: The configuration file config.json cannot be found.")
            exit()
        except KeyError as e:
            print(f"The configuration file is missing required fields: {e}")
            exit()

    async def stream(self, query: str) -> AsyncGenerator[str, None]:

        """Stream the response of the large model back to the client. """
        try:
            # Initialize the conversation history (system messages can be added)
            messages = [
                SystemMessage(
                    content="""
                You are an expert travel assistant specializing in trip planning, destination information, 
                and travel recommendations. Your goal is to help users plan enjoyable, safe, and 
                realistic trips based on their preferences and constraints.
                
                When providing information:
                - Be specific and practical with your advice
                - Consider seasonality, budget constraints, and travel logistics
                - Highlight cultural experiences and authentic local activities
                - Include practical travel tips relevant to the destination
                - Format information clearly with headings and bullet points when appropriate
                
                For itineraries:
                - Create realistic day-by-day plans that account for travel time between attractions
                - Balance popular tourist sites with off-the-beaten-path experiences
                - Include approximate timing and practical logistics
                - Suggest meal options highlighting local cuisine
                - Consider weather, local events, and opening hours in your planning
                
                Always maintain a helpful, enthusiastic but realistic tone and acknowledge 
                any limitations in your knowledge when appropriate.
                """
                )
            ]

            # Add the user message to the history.
            messages.append(HumanMessage(content=query))

            # Invoke the model in streaming mode to generate a response.
            for chunk in self.model.stream(messages):
                # Return the text content block.
                if hasattr(chunk, 'content') and chunk.content:
                    yield {'content': chunk.content, 'done': False}
            yield {'content': '', 'done': True}

        except Exception as e:
            print(f"error：{str(e)}")
            yield {'content': 'Sorry, an error occurred while processing your request.', 'done': True}


