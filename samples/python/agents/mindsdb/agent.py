import json
import os

from collections.abc import AsyncIterable
from typing import Any

import aiohttp

from dotenv import load_dotenv


# from flat_ai import FlatAI

# Load environment variables from .env file
load_dotenv()


class MindsDBAgent:
    """An agent that data requests from any database, datawarehouse, app."""

    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']
    API_URL = 'https://ai.staging.mindsdb.com/chat/completions'

    def __init__(self):
        self.api_key = os.getenv('MINDS_API_KEY')
        if not self.api_key:
            raise ValueError('MINDS_API_KEY environment variable is not set')

        self.model = os.getenv('MIND_NAME')
        if not self.model:
            self.model = 'Sales_Data_Expert_Demo_Mind'  # default mind

        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
        }

    def invoke(self, query, session_id) -> str:
        return {'content': 'Use stream method to get the results!'}

    async def stream(self, query, session_id) -> AsyncIterable[dict[str, Any]]:
        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': query},
            ],
            'stream': True,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.API_URL, headers=self.headers, json=payload
            ) as response:
                async for line in response.content:
                    if line:
                        # Skip empty lines
                        line = line.decode('utf-8').strip()
                        if not line or not line.startswith('data: '):
                            continue

                        # Parse the JSON data
                        json_str = line[6:]  # Remove "data: " prefix
                        try:
                            data = json.loads(json_str)
                        except json.JSONDecodeError:
                            continue
                        if 'choices' in data:
                            choice = data['choices'][0]
                            delta = choice.get('delta', {})
                            content = delta.get('content')
                            role = delta.get('role', '')
                            parts = [{'type': 'text', 'text': content}]
                            if choice.get('finish_reason') == 'stop':
                                yield {'is_task_complete': True, 'parts': parts}
                                continue

                            subtype = 'analysis'
                            tool_calls = delta.get('tool_calls', [])

                            if role == 'assistant':
                                subtype = 'acknowledge'

                            if tool_calls:
                                tool_call = tool_calls[0]
                                function = tool_call.get('function', {})
                                function_name = str(function.get('name'))
                                arguments = function.get('arguments', {})

                                if function_name == 'sql_db_query':
                                    subtype = 'execute_query'

                                    parts.append(
                                        {'type': 'text', 'text': str(arguments)}
                                    )

                            yield {
                                'is_task_complete': False,
                                'parts': parts,
                                'metadata': {
                                    'type': 'reasoning',
                                    'subtype': subtype,
                                },
                            }
                            continue
