"""Convience methods to start servers."""

import click

from a2a_mcp.mcp import server


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
def main(command, host, port, transport) -> None:
    # TODO: Add other servers, perhaps dynamic port allocation
    if command == 'mcp-server':
        server.serve(host, port, transport)
    else:
        raise ValueError(f'Unknown run option: {command}')
