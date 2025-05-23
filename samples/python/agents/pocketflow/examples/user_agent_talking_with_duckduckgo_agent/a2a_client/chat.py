from typing import TypedDict

import colorama

from pocketflow import AsyncFlow, AsyncNode
from pocketflow_a2a.a2a_common.client import A2AClient

from .flow import create_flow
from .nodes.done import DoneNode
from .types import Message
from .types import Shared as FlowShared


class ChatShared(TypedDict):
    chat_history: list[Message]
    a2a_clients: list[A2AClient]


class ChatNode(AsyncNode):
    def __init__(self):
        super().__init__()
        self.flow = create_flow()

    def handle_input_and_check_if_continue(
        self, shared: ChatShared
    ) -> ChatShared | None:
        question = input('You: ')
        if question in ['/exit', ':q']:
            return None
        shared['chat_history'].append(Message(role='user', content=question))
        return shared

    async def prep_async(self, shared: ChatShared):
        return self.handle_input_and_check_if_continue(shared)

    async def exec_async(self, shared: ChatShared | None):
        if shared is None:
            return None
        question = shared['chat_history'][-1]['content']
        a2a_clients = shared['a2a_clients']
        flow_shared = FlowShared(question=question, a2a_clients=a2a_clients)
        await self.flow.run_async(flow_shared)
        response = flow_shared['answer']
        shared['chat_history'].append(
            Message(role='assistant', content=response)
        )

        return response

    async def post_async(
        self, shared: ChatShared | None, _: object, response: str | None
    ) -> ChatShared:
        if response is None:
            print(
                f'{colorama.Fore.CYAN}AI: Thank you for chatting with me!, Bye!{colorama.Style.RESET_ALL}'
            )
            return 'done'
        shared['chat_history'].append(
            Message(role='assistant', content=response)
        )
        print(f'{colorama.Fore.CYAN}AI: {response}{colorama.Style.RESET_ALL}')
        return 'chat'


async def chat(a2a_clients: list[A2AClient]) -> ChatShared:
    chat_node = ChatNode()
    chat_node - 'chat' >> chat_node
    chat_node - 'done' >> DoneNode()
    flow = AsyncFlow(start=chat_node)
    shared = ChatShared(chat_history=[], a2a_clients=a2a_clients)
    await flow.run_async(shared)
    return shared


if __name__ == '__main__':
    import asyncio
    import os

    from loguru import logger

    POCKETFLOW_LOG_LEVEL = os.environ.get('POCKETFLOW_LOG_LEVEL', 'DEBUG')
    if POCKETFLOW_LOG_LEVEL == 'REMOVE':
        logger.remove()
    a2a_clients = [A2AClient(url='http://localhost:10003')]
    shared = asyncio.run(chat(a2a_clients))
