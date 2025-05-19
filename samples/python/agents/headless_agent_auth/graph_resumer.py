import asyncio
import inspect
from threading import Event
from typing import Awaitable, Callable, Optional, Dict, Any, List, TypedDict, Union
from auth0_ai.authorizers.ciba import CIBAAuthorizationRequest
from langchain_core.messages import AIMessage
from langgraph.graph.graph import CompiledGraph
from langgraph.types import Interrupt, Command
from langgraph.checkpoint.base import CheckpointTuple


class WatchedThread(TypedDict):
    thread_id: str
    task_id: str
    auth_request: CIBAAuthorizationRequest
    config: Dict[str, Any]
    last_run: float


SyncOrAsyncResumeStart = Union[Callable[[WatchedThread], None], Callable[[WatchedThread], Awaitable[None]]]
SyncOrAsyncResuming = Union[Callable[[WatchedThread, Any], None], Callable[[WatchedThread, Any], Awaitable[None]]]
SyncOrAsyncError = Union[Callable[[Exception], None], Callable[[Exception], Awaitable[None]]]


# If you are using a deployed graph, you can use `GraphResumer` (`from auth0_ai_langchain.ciba import GraphResumer`)
# See https://github.com/auth0-lab/auth0-ai-python/tree/main/packages/auth0-ai-langchain#handling-interrupts
class GraphResumer:
    def __init__(self, graph: CompiledGraph):
        self.graph = graph
        self.map: Dict[str, WatchedThread] = {}
        self._stop_event = Event()
        self._loop_task: Optional[asyncio.Task] = None

        self._resume_start_callbacks: List[SyncOrAsyncResumeStart] = []
        self._resuming_callbacks: List[SyncOrAsyncResuming] = []
        self._error_callbacks: List[SyncOrAsyncError] = []

    def on_resume_start(self, callback: SyncOrAsyncResumeStart) -> 'GraphResumer':
        self._resume_start_callbacks.append(callback)
        return self

    def on_resuming(self, callback: SyncOrAsyncResuming) -> 'GraphResumer':
        self._resuming_callbacks.append(callback)
        return self

    def on_error(self, callback: SyncOrAsyncError) -> 'GraphResumer':
        self._error_callbacks.append(callback)
        return self

    async def _emit_resume_start(self, thread: WatchedThread) -> None:
        for callback in self._resume_start_callbacks:
            if inspect.iscoroutinefunction(callback):
                await callback(thread)
            else:
                callback(thread)

    async def _emit_resuming(self, thread: WatchedThread, item: Any) -> None:
        for callback in self._resuming_callbacks:
            if inspect.iscoroutinefunction(callback):
                await callback(thread, item)
            else:
                callback(thread, item)

    async def _emit_error(self, error: Exception) -> None:
        for callback in self._error_callbacks:
            if inspect.iscoroutinefunction(callback):
                await callback(error)
            else:
                callback(error)

    async def _get_all_interrupted_threads(self) -> List[CheckpointTuple]:
        # Collect the latest checkpoint per thread_id
        latest_by_thread: dict[str, CheckpointTuple] = {}

        async for checkpoint in self.graph.checkpointer.alist(config=None):
            thread_id = checkpoint.config['configurable']['thread_id']
            current = latest_by_thread.get(thread_id)

            if not current or checkpoint.checkpoint['ts'] > current.checkpoint['ts']:
                latest_by_thread[thread_id] = checkpoint

        interrupted_threads = []

        for checkpoint in latest_by_thread.values():
            last_interrupt_op_id = None
            last_resume_op_id = None

            for op_id, name, values in checkpoint.pending_writes:
                if name == '__interrupt__':
                    for value in values:
                        if (
                            isinstance(value, Interrupt)
                            and value.value.get('name') == 'AUTH0_AI_INTERRUPT'
                            and value.value.get('code') in {
                                'CIBA_AUTHORIZATION_PENDING',
                                'CIBA_AUTHORIZATION_POLLING_ERROR',
                            }
                            and value.value.get('_request')
                        ):
                            last_interrupt_op_id = op_id
                elif name == '__resume__':
                    last_resume_op_id = op_id

            # Consider thread interrupted only if the interrupt is newer than any resume
            if last_interrupt_op_id and (not last_resume_op_id or last_interrupt_op_id > last_resume_op_id):
                interrupted_threads.append(checkpoint)

        return interrupted_threads

    async def _resume_thread(self, t: WatchedThread):
        await self._emit_resume_start(t)

        async for item in self.graph.astream(
            Command(resume=[]),
            {'configurable': {'thread_id': t['thread_id']}},
        ):
            await self._emit_resuming(t, item)

        t['last_run'] = asyncio.get_running_loop().time()

    async def loop(self):
        interrupted_threads = await self._get_all_interrupted_threads()
        new_map = {}
        now = asyncio.get_running_loop().time()

        for chk in interrupted_threads:
            thread_id = chk.config['configurable']['thread_id']
            interrupt_obj = next(
                value for _, name, values in chk.pending_writes
                if name == '__interrupt__'
                for value in values
            )

            last_run = self.map.get(thread_id, {}).get('last_run', 0)

            new_map[thread_id] = {
                'thread_id': thread_id,
                'task_id': chk.metadata['task_id'],
                'auth_request': interrupt_obj.value['_request'],
                'config': chk.config,
                'last_run': last_run,
            }

        self.map = new_map
        threads_to_resume = [
            t for t in self.map.values()
            if t['last_run'] + t['auth_request']['interval'] < now
        ]

        await asyncio.gather(*[self._resume_thread(t) for t in threads_to_resume])

    def start(self):
        if self._loop_task and not self._loop_task.done():
            return

        self._stop_event.clear()

        async def _run_loop():
            while not self._stop_event.is_set():
                try:
                    await self.loop()
                except Exception as e:
                    await self._emit_error(e)
                await asyncio.sleep(5)

        self._loop_task = asyncio.create_task(_run_loop())


    def stop(self):
        self._stop_event.set()
        if self._loop_task:
            self._loop_task.cancel()
