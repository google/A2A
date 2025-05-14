import asyncio

from collections.abc import AsyncGenerator
from typing import Any

class TalkAgent:
    """Hello World Agent."""

    async def invoke(self,query:str):
        return query

