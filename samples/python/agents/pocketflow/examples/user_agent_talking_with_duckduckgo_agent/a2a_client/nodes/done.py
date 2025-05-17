from loguru import logger
from pocketflow import AsyncNode

from a2a_client.types import Shared


class DoneNode(AsyncNode):
    async def prep_async(self, shared: Shared) -> str:
        logger.info('🏁 Finished workflow')
        return 'done'

    async def exec_async(self, shared: Shared) -> str:
        logger.info('✅ Finished workflow')
        return 'done'
