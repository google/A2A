from pydantic import BaseModel, Field
from pydantic_ai import AICallable
import os

class SummarizeTool(BaseModel):
    """
    A tool for summarizing text using Pydantic AI.
    """
    api_key: str = Field(default_factory=lambda: os.environ.get("OPENAI_API_KEY", ""))

    @AICallable(max_tokens=500, api_key_field="api_key")
    def summarize(self, text: str) -> str:
        """
        Summarizes the given text.

        Args:
            text: The text to summarize.

        Returns:
            A summary of the text.
        """
        ...