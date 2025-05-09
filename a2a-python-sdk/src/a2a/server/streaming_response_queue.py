import asyncio

from a2a.types import SendMessageStreamingResponse


class StreamingResponseQueue:
    """Queue for Streaming responses."""

    def __init__(self) -> None:
        self.queue: asyncio.Queue[SendMessageStreamingResponse] = (
            asyncio.Queue()
        )

    def enqueue_event(self, event: SendMessageStreamingResponse):
        self.queue.put_nowait(event)

    async def dequeue_event(self) -> SendMessageStreamingResponse:
        return await self.queue.get()
