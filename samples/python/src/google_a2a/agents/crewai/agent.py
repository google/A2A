"""Crew AI based sample for A2A protocol.

Handles the agents and also presents the tools required.
"""

import asyncio
import base64
import collections
from io import BytesIO
import os
import re
from typing import Any, AsyncIterable, Dict, List
from uuid import uuid4
from common.utils.in_memory_cache import InMemoryCache
from crewai import Agent, Crew, LLM, Task
from crewai.process import Process
from crewai.tools import tool
from dotenv import load_dotenv
from google import genai
from google.genai import types
import logging
from PIL import Image
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class Imagedata(BaseModel):
  """Represents image data.

  Attributes:
    id: Unique identifier for the image.
    name: Name of the image.
    mime_type: MIME type of the image.
    bytes: Base64 encoded image data.
    error: Error message if there was an issue with the image.
  """

  id: str | None = None
  name: str | None = None
  mime_type: str | None = None
  bytes: str | None = None
  error: str | None = None

def get_api_key() -> str:
  """Helper method to handle API Key."""
  load_dotenv()
  return os.getenv("GOOGLE_API_KEY")


@tool("ImageGenerationTool")
def generate_image_tool(prompt: str, session_id: str, artifact_file_id: str = None) -> str:
  """Image generation tool that generates images or modifies a given image based on a prompt."""

  if not prompt:
    raise ValueError("Prompt cannot be empty")

  client = genai.Client(api_key=get_api_key())
  cache = InMemoryCache()

  text_input = (
      prompt,
      "Ignore any input images if they do not match the request.",
  )

  ref_image = None
  logger.info(f"Session id {session_id}")
  print(f"Session id {session_id}")

  # TODO (rvelicheti) - Change convoluted memory handling logic to a better
  # version.
  # Get the image from the cache and send it back to the model.
  # Assuming the last version of the generated image is applicable.
  # Convert to PIL Image so the context sent to the LLM is not overloaded
  try:
    ref_image_data = None
    # image_id = session_cache[session_id][-1]
    session_image_data = cache.get(session_id)
    if artifact_file_id:
      try:
        ref_image_data = session_image_data[artifact_file_id]
        logger.info(f"Found reference image in prompt input")
      except Exception as e:
        ref_image_data = None
    if not ref_image_data:
      # Insertion order is maintained from python 3.7
      latest_image_key = list(session_image_data.keys())[-1]
      ref_image_data = session_image_data[latest_image_key]

    ref_bytes = base64.b64decode(ref_image_data.bytes)
    ref_image = Image.open(BytesIO(ref_bytes))
  except Exception as e:
    ref_image = None

  if ref_image:
    contents = [text_input, ref_image]
  else:
    contents = text_input

  try:
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp-image-generation",
        contents=contents,
        config=types.GenerateContentConfig(response_modalities=["Text", "Image"]),
    )
  except Exception as e:
    logger.error(f"Error generating image {e}")
    print(f"Exception {e}")
    return -999999999

  for part in response.candidates[0].content.parts:
    if part.inline_data is not None:
      try:
        data = Imagedata(
            bytes=base64.b64encode(part.inline_data.data).decode("utf-8"),
            mime_type=part.inline_data.mime_type,
            name="generated_image.png",
            id=uuid4().hex,
        )
        session_data = cache.get(session_id)
        if session_data is None:
          # Session doesn't exist, create it with the new item
          cache.set(session_id, {data.id: data})
        else:
          # Session exists, update the existing dictionary directly
          session_data[data.id] = data

        return data.id
      except Exception as e:
        logger.error(f"Error unpacking image {e}")
        print(f"Exception {e}")
  return -999999999


class ImageGenerationAgent:
  """Agent that generates images based on user prompts."""

  SUPPORTED_CONTENT_TYPES = ["text", "text/plain", "image/png"]

  def __init__(self):

    self.model = LLM(model="gemini/gemini-2.0-flash", api_key=get_api_key())

    self.image_creator_agent = Agent(
        role="Image Creation Expert",
        goal=(
            "Generate an image based on the user's text prompt.If the prompt is"
            " vague, ask clarifying questions (though the tool currently"
            " doesn't support back-and-forth within one run). Focus on"
            " interpreting the user's request and using the Image Generator"
            " tool effectively."
        ),
        backstory=(
            "You are a digital artist powered by AI. You specialize in taking"
            " textual descriptions and transforming them into visual"
            " representations using a powerful image generation tool. You aim"
            " for accuracy and creativity based on the prompt provided."
        ),
        verbose=False,
        allow_delegation=False,
        tools=[generate_image_tool],
        llm=self.model,
    )

    self.image_creation_task = Task(
        description=(
            "Receive a user prompt: '{user_prompt}'.\nAnalyze the prompt and"
            " identify if you need to create a new image or edit an existing"
            " one. Look for pronouns like this, that etc in the prompt, they"
            " might provide context, rewrite the prompt to include the"
            " context.If creating a new image, ignore any images provided as"
            " input context.Use the 'Image Generator' tool to for your image"
            " creation or modification. The tool will expect a prompt which is"
            " the {user_prompt} and the session_id which is {session_id}."
            " Optionally the tool will also expect an artifact_file_id which is "
            " sent to you as {artifact_file_id}"
        ),
        expected_output="The id of the generated image",
        agent=self.image_creator_agent,
    )

    self.image_crew = Crew(
        agents=[self.image_creator_agent],
        tasks=[self.image_creation_task],
        process=Process.sequential,
        verbose=False,
    )

  def extract_artifact_file_id(self, query):    
    try:
      pattern = r'(?:id|artifact-file-id)\s+([0-9a-f]{32})'
      match = re.search(pattern, query)

      if match:
        return match.group(1)
      else:        
        return None
    except Exception as e:
      return None

  def invoke(self, query, session_id) -> str:
    """Kickoff CrewAI and return the response."""
    artifact_file_id = self.extract_artifact_file_id(query)

    inputs = {"user_prompt": query, "session_id": session_id, "artifact_file_id": artifact_file_id}
    logger.info(f"Inputs {inputs}")
    print(f"Inputs {inputs}")    
    response = self.image_crew.kickoff(inputs)
    return response

  async def stream(self, query: str) -> AsyncIterable[Dict[str, Any]]:
    """Streaming is not supported by CrewAI."""
    raise NotImplementedError("Streaming is not supported by CrewAI.")

  def get_image_data(self, session_id: str, image_key: str) -> Imagedata:
    """Return Imagedata given a key. This is a helper method from the agent."""
    cache = InMemoryCache()
    session_data = cache.get(session_id)
    try:
      cache.get(session_id)
      return session_data[image_key]
    except KeyError:
      logger.error(f"Error generating image")
      return Imagedata(error="Error generating image, please try again.")
