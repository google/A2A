# type:ignore
import asyncio

import click

from .agents.activity_planner_agent import ActivityPlannerAgent
from .agents.task_executor_agent import TaskExecutorAgent
from .mcp import client, server


@click.command()
@click.option("--run", "command", default="mcp-server", help="Command to run")
@click.option(
    "--host",
    "host",
    default="localhost",
    help="Host on which the server is started or the client connects to",
)
@click.option(
    "--port",
    "port",
    default=10100,
    help="Port on which the server is started or the client connects to",
)
@click.option(
    "--transport",
    "transport",
    default="stdio",
    help="MCP Transport",
)
@click.option("--find_agent", "query", help="Query to find an agent")
@click.option("--resource", "resource_name", help="URI of the resource to locate")
@click.option("--prompt", "prompt", help="Prompt to the agent")
@click.option("--tool", "tool_name", help="Tool to execute")
def main(
    command, host, port, transport, query, resource_name, prompt, tool_name
) -> None:
    if command == "mcp-server":
        server.serve(host, port, transport)
    elif command == "mcp-client":
        asyncio.run(client.main(host, port, transport, query, resource_name, tool_name))
    elif command == "generate-plan":
        asyncio.run(ActivityPlannerAgent().generate_plan(prompt))
    elif command == "find-agents":
        task_list = asyncio.run(ActivityPlannerAgent().generate_plan(prompt))
        asyncio.run(
            TaskExecutorAgent().find_agent_for_task(task_list, host, port, transport)
        )
    else:
        raise ValueError(f"Unknown run option: {command}")
