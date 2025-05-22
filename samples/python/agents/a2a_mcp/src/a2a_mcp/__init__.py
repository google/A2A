# type:ignore
import asyncio

import click

from a2a_mcp.mcp import client, server


@click.command()
@click.option('--run', 'command', default='mcp-server', help='Command to run')
@click.option(
    '--host',
    'host',
    default='localhost',
    help='Host on which the server is started or the client connects to',
)
@click.option(
    '--port',
    'port',
    default=10100,
    help='Port on which the server is started or the client connects to',
)
@click.option(
    '--transport',
    'transport',
    default='stdio',
    help='MCP Transport',
)
@click.option('--find_agent', 'query', help='Query to find an agent')
@click.option(
    '--resource', 'resource_name', help='URI of the resource to locate'
)
@click.option('--prompt', 'prompt', help='Prompt to the agent')
@click.option('--tool', 'tool_name', help='Tool to execute')
def main(
    command, host, port, transport, query, resource_name, prompt, tool_name
) -> None:
    if command == 'mcp-server':
        server.serve(host, port, transport)
    elif command == 'mcp-client':
        asyncio.run(
            client.main(host, port, transport, query, resource_name, tool_name)
        )
    else:
        raise ValueError(f'Unknown run option: {command}')
