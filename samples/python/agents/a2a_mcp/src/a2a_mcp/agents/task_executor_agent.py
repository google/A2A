# type: ignore
import asyncio
import enum
import json
import logging
import traceback
from typing import Any, AsyncGenerator, AsyncIterable, Dict, Literal
from uuid import uuid4

import nest_asyncio
from common.client import A2AClient
from common.types import AgentCard, GetTaskResponse, TaskState
from google.adk.agents import Agent
from google.genai import types as genai_types
from pydantic import BaseModel

from a2a_mcp.common import prompts
from a2a_mcp.common.agent_runner import AgentRunner
from a2a_mcp.common.base_agent import BaseAgent
from a2a_mcp.common.types import Task, TaskList, TripInfo
from a2a_mcp.common.utils import config_logger, get_mcp_server_config, init_api_key
from a2a_mcp.mcp import client

logger = logging.getLogger(__name__)
nest_asyncio.apply()


class ExecutionState(enum.Enum):
    INIT = "init"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    ERROR = "error"


class TaskType(enum.Enum):
    PLANNER = "planner"
    TASK = "task"


class TaskExecutionUnit:
    def __init__(self, task: Task, client: A2AClient, type: str, trip_info=None):
        self.state: TaskState = None
        self.task: Task = task
        self.client: A2AClient = client
        self.results: dict = {}
        self.type: str = type
        self.trip_info: TripInfo = trip_info


class TaskExecutionQueue:
    def __init__(self):
        self.ready_queue: list[TaskExecutionUnit] = []
        self.in_progress_unit: TaskExecutionUnit = None
        self.completed_queue: list[TaskExecutionUnit] = []
        self.backlog: list[TaskExecutionUnit] = []
        self.current_status: Literal[
            "init", "planning", "executing", "completed", "error"
        ] = "init"
        self.summary_context_for_replan: str | None = None

    def set_inprogress_unit(self, unit: TaskExecutionUnit):
        self.in_progress_unit = unit

    def get_inprogress_unit(self) -> TaskExecutionUnit:
        return self.in_progress_unit

    def add_to_completed(self, unit: TaskExecutionUnit):
        self.completed_queue.append(unit)

    def add_to_backlog(self, unit: TaskExecutionUnit):
        self.backlog.append(unit)

    def add_to_ready(self, unit: TaskExecutionUnit):
        self.ready_queue.append(unit)

    def get_next_unit(self) -> TaskExecutionUnit:
        if self.in_progress_unit:
            return self.in_progress_unit
        if self.ready_queue:
            execution_unit = self.ready_queue.pop(0)
            return execution_unit
        return None

    def has_next(self) -> bool:
        return self.in_progress_unit or bool(self.ready_queue)

    def set_current_status(self, status: str):
        self.current_status = status


class TripSummary(BaseModel):
    """Trip Summary"""

    user_request: str
    status: str
    total_budget: str
    used_budget: str
    summary: str


class TaskExecutorAgent(BaseAgent):
    def __init__(self):
        init_api_key()
        config_logger(logger=logger)

        logger.info("Initializing TaskExecutorAgent")

        super().__init__(
            agent_name="TaskExecutorAgent",
            description="Find the most relevant agent for a task and execute the task",
            content_types=["text", "text/plain"],
        )
        self.is_plan_generated = False
        self.planner_client = None
        self.execution_state = {}
        self.agent = None

    async def init_planning_agent(self):
        logger.info("Initializing Planning Agent")
        config = get_mcp_server_config()
        logger.info(
            f"Host: {config.host} Port: {config.port} Transport: {config.transport}"
        )
        async with client.init_session(
            config.host, config.port, config.transport
        ) as session:
            response = await client.find_resource(
                session, "resource://agent_cards/planner_agent"
            )
            data = json.loads(response.contents[0].text)
            agent_card = AgentCard(**data["agent_card"][0])
            logger.info(f"Agent Card {agent_card}")
            planner_client = A2AClient(agent_card=agent_card)
            logger.info(f"A2A Client {planner_client.url}")
            self.planner_client = planner_client

    def init_summary_agent(self):
        generate_content_config = genai_types.GenerateContentConfig(temperature=0.0)
        self.agent = Agent(
            name=self.agent_name,
            instruction=prompts.SUMMARY_INSTRUCTIONS,
            output_schema=TripSummary,
            model="gemini-2.0-flash",
            disallow_transfer_to_parent=True,
            disallow_transfer_to_peers=True,
            generate_content_config=generate_content_config,
        )
        self.runner = AgentRunner()

    async def generate_summary(self, session_id) -> str:
        logger.info(f"Generating final summary for session {session_id}")
        if not self.agent:
            self.init_summary_agent()
        query = ""
        for execution_unit in self.execution_state[session_id].completed_queue:
            query = (
                query + f"\n==========={execution_unit.task.description}===========\n"
            )

            query = query + json.dumps(execution_unit.results)

        response = await self.runner.run_agent(self.agent, query, session_id)
        return response

    async def find_agent_for_task(self, task_list: TaskList) -> dict:
        logger.info("Agents for tasks")
        config = get_mcp_server_config()
        async with client.init_session(
            config.host, config.port, config.transport
        ) as session:
            tasks = [
                client.find_agent(session, task.description) for task in task_list.tasks
            ]
            results = await asyncio.gather(*tasks)
            task_agent_map = {
                task.description: result.content[0].text
                for task, result in zip(task_list.tasks, results)
            }
            return task_agent_map

    async def invoke(self, query, session_id) -> dict:
        logger.info(f"Running TaskExecutorAgent for session {session_id}")
        raise NotImplementedError("Please use the streraming function")

    async def invoke_streaming(
        self, query, session_id, task_id, a2a_client
    ) -> AsyncGenerator:
        message = {
            "role": "user",
            "parts": [
                {
                    "type": "text",
                    "text": query,
                }
            ],
        }
        payload = {
            "id": task_id,
            "sessionId": session_id,
            "acceptedOutputModes": ["text", "data"],
            "message": message,
        }
        logger.info(f"Sending streaming request to {a2a_client.url}")

        async for chunk in a2a_client.send_task_streaming(payload):
            yield chunk
        task_result = await a2a_client.get_task({"id": task_id})
        yield {"type": "final_result", "response": task_result}

    async def stream(self, query, session_id) -> AsyncIterable[Dict[str, Any]]:
        if not self.planner_client:
            await self.init_planning_agent()

        logger.info(f"Running TaskExecutorAgent stream for session {session_id}")

        if session_id not in self.execution_state:
            queue = TaskExecutionQueue()
            queue.current_status = ExecutionState.PLANNING
            task = Task(id=0, description=query)
            queue.add_to_ready(
                TaskExecutionUnit(
                    task=task, client=self.planner_client, type=TaskType.PLANNER
                )
            )
            logger.info(f"Planner Task added to queue {task.description}")
            self.execution_state[session_id] = queue

        queue = self.execution_state[session_id]

        if (
            queue.current_status == ExecutionState.PLANNING
            and queue.summary_context_for_replan
        ):
            logger.info(
                f"Re-planning triggered for session {session_id} based on summary feedback."
            )
            replan_query = (
                f"Based on the previous attempt which led to the summary/request: "
                f"'{queue.summary_context_for_replan}'. "
                f"The user now provides the following input/clarification: '{query}'. "
                f"Please generate a revised plan."
                f"You do not have to generate tasks to cancel bookings."
            )
            queue.summary_context_for_replan = None
            queue.ready_queue.clear()
            queue.backlog.clear()
            queue.set_inprogress_unit(None)
            task = Task(id=0, description=replan_query)
            queue.add_to_ready(
                TaskExecutionUnit(
                    task=task, client=self.planner_client, type=TaskType.PLANNER
                )
            )
            logger.info(f"Re-planning Task added to queue: {task.description}")

        try:
            logger.info("Session exists")
            execution_unit = queue.get_next_unit()
            queue.set_inprogress_unit(execution_unit)

            logger.info(f"Running Task {execution_unit.task.description}")

            a2a_client = execution_unit.client
            logger.info(f"Found Client {a2a_client.url}")
            task_id = uuid4().hex
            current_query = (
                query
                if execution_unit.task.description == ""
                else execution_unit.task.description
            )
            if execution_unit.trip_info:
                current_query = f"user_query: {current_query} trip_info: {execution_unit.trip_info.model_dump()}"
            async for chunk in self.invoke_streaming(
                current_query, session_id, task_id, a2a_client
            ):
                if isinstance(chunk, dict) and chunk.get("type") == "final_result":
                    response = chunk["response"]
                    yield self.get_agent_response(response, session_id, queue)
                else:
                    yield {
                        "is_task_complete": False,
                        "require_user_input": False,
                        "content": f"Running: {execution_unit.task.description}",
                    }
            if not queue.get_inprogress_unit() and queue.has_next():
                logger.info("Streaming next task")
                async for sub_result in self.stream("", session_id):
                    yield sub_result

        except Exception as e:
            logger.error(f"Error in stream: {e}")
            logger.error(traceback.format_exc())
            if session_id in self.execution_state:
                self.execution_state.pop(session_id)
            raise e

    def get_agent_response(self, task_result, session_id, queue=None):
        logger.info(f"Response Type {type(task_result)}")
        logger.info("########################################")
        logger.info(f"Send agent response for {task_result}")
        logger.info("########################################")
        if task_result and isinstance(task_result, GetTaskResponse):
            state = task_result.result.status.state
            if state == TaskState.INPUT_REQUIRED:
                execution_unit = queue.get_inprogress_unit().task.description = ""
                return {
                    "response_type": "text",
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": task_result.result.status.message.parts[-1].text,
                }
            elif state == TaskState.FAILED:
                return {
                    "response_type": "text",
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": "Error running task",
                }
            elif state == TaskState.COMPLETED:
                content = task_result.result.artifacts[-1].parts[-1].data
                execution_unit = queue.get_inprogress_unit()
                if isinstance(content, dict):
                    execution_unit.results = content
                else:
                    execution_unit.results = json.loads(content)

                if execution_unit.type == TaskType.PLANNER:
                    logger.info(f"Generated Plan: {execution_unit.results}")
                    task_list = TaskList(**execution_unit.results)
                    task_agent_map = asyncio.run(self.find_agent_for_task(task_list))
                    for task in task_list.tasks:
                        queue.add_to_ready(
                            TaskExecutionUnit(
                                task=task,
                                client=A2AClient(
                                    AgentCard(
                                        **json.loads(task_agent_map[task.description])
                                    )
                                ),
                                type=TaskType.TASK,
                                trip_info=task_list.trip_info,
                            )
                        )

                queue.set_inprogress_unit(None)
                queue.add_to_completed(execution_unit)
                require_user_input = False
                is_task_complete = False
                if queue.has_next():
                    queue.set_current_status(ExecutionState.EXECUTING)
                    is_task_complete = False
                else:
                    is_task_complete = True
                    summary_result = asyncio.run(self.generate_summary(session_id))
                    generated_summary = summary_result.content.parts[0].text
                    content = json.loads(generated_summary)
                    logger.info(f"Summary {content}")
                    if (
                        isinstance(content, dict)
                        and content.get("status") == "input_required"
                    ):
                        logger.info("Summary Generated but needs more information")
                        require_user_input = True
                        is_task_complete = False
                        queue.summary_context_for_replan = content.get("summary")
                        queue.set_current_status(ExecutionState.PLANNING)
                        return {
                            "response_type": "text",  # Send as text prompt
                            "is_task_complete": is_task_complete,
                            "require_user_input": require_user_input,
                            "content": queue.summary_context_for_replan,
                        }
                    else:
                        # content = {"summary": content["summary"]}
                        content = (
                            {"summary": content.get("summary", "Completed.")}
                            if isinstance(content, dict)
                            else {"summary": content}
                        )
                        is_task_complete = True
                        queue.set_current_status(ExecutionState.COMPLETED)
                        queue.summary_context_for_replan = None
                        self.execution_state.pop(session_id, None)
                        # self.execution_state.pop(session_id)
                        # queue.set_current_status(ExecutionState.COMPLETED)

                return {
                    "response_type": "data",
                    "is_task_complete": is_task_complete,
                    "require_user_input": require_user_input,
                    "content": content,
                }
            elif state == TaskState.WORKING:
                return {
                    "response_type": "text",
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": "Processing request...",
                }


async def main(query: str, sessionId: str):
    agent = TaskExecutorAgent()
    async for item in agent.stream(query, sessionId):
        print(item)


if __name__ == "__main__":
    agent = TaskExecutorAgent()
    asyncio.run(main("Plan my trip to London", "1"))
