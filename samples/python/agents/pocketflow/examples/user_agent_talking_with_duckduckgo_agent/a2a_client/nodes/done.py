from a2a_client.types import Shared
from pocketflow import AsyncNode
from loguru import logger


class DoneNode(AsyncNode):
    async def prep_async(self, shared: Shared) -> str:
        logger.info("🏁 Finished workflow")
        return "done"

    async def exec_async(self, shared: Shared) -> str:
        logger.info("✅ Finished workflow")
        return "done"
