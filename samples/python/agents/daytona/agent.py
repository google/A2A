import time
from typing import Any, AsyncIterable, Dict, Optional
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.tool_context import ToolContext
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from daytona_sdk import Daytona, CodeLanguage, SandboxState
from daytona_sdk.daytona import CreateSandboxParams, SandboxResources

def create_sandbox(
    name: Optional[str] = None,
    language: str = "python",
    cpu: int = 1,
    memory: int = 2,
    disk: int = 10,
    env_vars: Optional[Dict[str, str]] = None,
    auto_stop_interval: int = 15,
    tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Create a new sandbox for running code.

    Args:
        name (str, optional): Name for the sandbox. If not provided, a random name will be generated.
        language (str): Programming language for the sandbox. Options: "python", "javascript", "typescript". Default: "python".
        cpu (int): Number of CPU cores to allocate. Default: 1.
        memory (int): Amount of memory in GB to allocate. Default: 2.
        disk (int): Amount of disk space in GB to allocate. Default: 10.
        env_vars (Dict[str, str], optional): Environment variables to set in the sandbox.
        auto_stop_interval (int): Minutes of inactivity before auto-stopping. Set to 0 to disable. Default: 15.

    Returns:
        Dict[str, Any]: Information about the created sandbox.
    """
    try:
        daytona = Daytona()

        language_lower = language.lower()
        language_map = {
            "python": CodeLanguage.PYTHON,
            "javascript": CodeLanguage.JAVASCRIPT,
            "typescript": CodeLanguage.TYPESCRIPT
        }

        if language_lower not in language_map:
            return {"error": f"Unsupported language: {language}. Supported languages are: python, javascript, typescript."}

        resources = SandboxResources(
            cpu=cpu,
            memory=memory,
            disk=disk
        )

        params = CreateSandboxParams(
            language=language_map[language_lower],
            name=name,
            resources=resources,
            env_vars=env_vars or {},
            auto_stop_interval=auto_stop_interval
        )

        sandbox = daytona.create(params)

        return {
            "id": sandbox.info().id,
            "name": sandbox.info().name,
            "language": language_lower,
            "created_at": time.time(),
            "message": f"Sandbox '{sandbox.info().name}' created successfully with ID: {sandbox.info().id}"
        }

    except Exception as e:
        return {"error": f"Failed to create sandbox: {str(e)}"}

def start_sandbox(sandbox_id: str, tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    Start a sandbox.

    Args:
        sandbox_id (str): ID of the sandbox to start.

    Returns:
        Dict[str, Any]: Status of the operation.
    """
    try:
        daytona = Daytona()

        sandbox = daytona.get_current_sandbox(sandbox_id)

        # if not sandbox:
        #     return {"error": f"Sandbox with ID {sandbox_id} not found."}

        sandbox.start()

        return {
            "id": sandbox_id,
            "status": sandbox.info().state,
            "message": f"Sandbox {sandbox_id} started successfully."
        }

    except Exception as e:
        return {"error": f"Failed to start sandbox: {str(e)}"}

def stop_sandbox(sandbox_id: str, tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    Stop a sandbox.

    Args:
        sandbox_id (str): ID of the sandbox to stop.

    Returns:
        Dict[str, Any]: Status of the operation.
    """
    try:

        daytona = Daytona()

        sandbox = daytona.get_current_sandbox(sandbox_id)

        sandbox.stop()

        return {
            "id": sandbox_id,
            "status": sandbox.info().state,
            "message": f"Sandbox {sandbox_id} stopped successfully."
        }

    except Exception as e:
        return {"error": f"Failed to stop sandbox: {str(e)}"}

def destroy_sandbox(sandbox_id: str, tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    Destroy a sandbox.

    Args:
        sandbox_id (str): ID of the sandbox to destroy.

    Returns:
        Dict[str, Any]: Status of the operation.
    """
    try:
        daytona = Daytona()

        sandbox = daytona.get_current_sandbox(sandbox_id)

        daytona.remove(sandbox)

        return {
            "id": sandbox_id,
            "name": sandbox.info().name,
            "status": SandboxState.DESTROYED,
            "message": f"Sandbox {sandbox_id} destroyed successfully."
        }

    except Exception as e:
        return {"error": f"Failed to destroy sandbox: {str(e)}"}

def list_sandboxes(tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    List all sandboxes.

    Returns:
        Dict[str, Any]: List of sandboxes.
    """
    try:
        daytona = Daytona()

        sandboxes = daytona.list()


        sandbox_list = []
        for sandbox in sandboxes:
            sandbox_list.append({
                "id": sandbox.info().id,
                "name": sandbox.info().name,
                "status": sandbox.info().state,
                "created_at": sandbox.info().created
            })

        return {
            "sandboxes": sandbox_list,
            "count": len(sandbox_list)
        }

    except Exception as e:
        return {"error": f"Failed to list sandboxes: {str(e)}"}

def execute_command(
    sandbox_id: str,
    command: str,
    cwd: Optional[str] = None,
    timeout: Optional[int] = 60,
    tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Execute a shell command in a sandbox.

    Args:
        sandbox_id (str): ID of the sandbox to use.
        command (str): Shell command to execute.
        cwd (str, optional): Working directory for command execution.
        timeout (int, optional): Maximum time in seconds to wait for the command to complete. Default: 60.

    Returns:
        Dict[str, Any]: Command execution results.
    """
    try:
        daytona = Daytona()

        sandbox = daytona.get_current_sandbox(sandbox_id)

        # info = sandbox.info()
        # if info.state != SandboxState.STARTED:
        #     return {"error": f"Sandbox {sandbox_id} is not running. Current state: {info.state}"}

        response = sandbox.process.exec(command, cwd=cwd, timeout=timeout)

        return {
            "sandbox_id": sandbox_id,
            "command": command,
            "exit_code": response.exit_code,
            "output": response.artifacts.stdout,
            "success": response.exit_code == 0
        }

    except Exception as e:
        return {"error": f"Failed to execute command: {str(e)}"}

def run_code(
    sandbox_id: str,
    code: str,
    timeout: Optional[int] = 60,
    tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Run code in a sandbox.

    Args:
        sandbox_id (str): ID of the sandbox to use.
        code (str): Code to execute.
        timeout (int, optional): Maximum time in seconds to wait for the code to complete. Default: 60.

    Returns:
        Dict[str, Any]: Code execution results.
    """
    try:
        daytona = Daytona()

        sandbox = daytona.get_current_sandbox(sandbox_id)

        # info = sandbox.info()
        # if info.state != "started":
        #     return {"error": f"Sandbox {sandbox_id} is not running. Current state: {info.state}"}

        response = sandbox.process.code_run(code, timeout=timeout)

        return {
            "sandbox_id": sandbox_id,
            "exit_code": response.exit_code,
            "output": response.artifacts.stdout,
            "success": response.exit_code == 0
        }

    except Exception as e:
        return {"error": f"Failed to run code: {str(e)}"}

class DaytonaSandboxAgent:
    """An agent that orchestrates Daytona sandboxes for running code."""

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        self._agent = self._build_agent()
        self._user_id = "remote_agent"
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    def invoke(self, query, session_id) -> str:
        session = self._runner.session_service.get_session(
            app_name=self._agent.name, user_id=self._user_id, session_id=session_id
        )
        content = types.Content(
            role="user", parts=[types.Part.from_text(text=query)]
        )
        if session is None:
            session = self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
                session_id=session_id,
            )
        events = self._runner.run(
            user_id=self._user_id, session_id=session.id, new_message=content
        )
        if not events or not events[-1].content or not events[-1].content.parts:
            return ""
        return "\n".join([p.text for p in events[-1].content.parts if p.text])

    async def stream(self, query, session_id) -> AsyncIterable[Dict[str, Any]]:
        session = self._runner.session_service.get_session(
            app_name=self._agent.name, user_id=self._user_id, session_id=session_id
        )
        content = types.Content(
            role="user", parts=[types.Part.from_text(text=query)]
        )
        if session is None:
            session = self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
                session_id=session_id,
            )
        async for event in self._runner.run_async(
            user_id=self._user_id, session_id=session.id, new_message=content
        ):
            if event.is_final_response():
                response = ""
                if (
                    event.content
                    and event.content.parts
                    and event.content.parts[0].text
                ):
                    response = "\n".join([p.text for p in event.content.parts if p.text])
                elif (
                    event.content
                    and event.content.parts
                    and any([True for p in event.content.parts if p.function_response])):
                    response = next((p.function_response.model_dump() for p in event.content.parts))
                yield {
                    "is_task_complete": True,
                    "content": response,
                }
            else:
                yield {
                    "is_task_complete": False,
                    "updates": "Processing the sandbox request...",
                }

    def _build_agent(self) -> LlmAgent:
        """Builds the LLM agent for the Daytona sandbox orchestration agent."""
        return LlmAgent(
            model="gemini-2.0-flash-001",
            name="daytona_sandbox_agent",
            description=(
                "This agent orchestrates Daytona sandboxes for running code and executing commands."
            ),
            instruction="""
        You are an agent that helps users create and manage sandboxes for running code.

        You can:
        1. Create new sandboxes with specific configurations
        2. Start and stop existing sandboxes
        3. Execute commands in sandboxes
        4. Run code in sandboxes
        5. List all available sandboxes
        6. Destroy sandboxes when they're no longer needed

        When a user asks you to create a sandbox:
        - Use the create_sandbox tool
        - Choose appropriate resources based on the user's needs
        - Default to Python unless the user specifies another supported language

        When a user asks you to run code:
        - Check if they already have a sandbox (use list_sandboxes)
        - If they don't have a sandbox, create one first
        - Make sure the sandbox is started before running code
        - Use the run_code tool to execute their code
        - Provide the output back to the user

        When a user asks you to execute commands:
        - Check if they already have a sandbox (use list_sandboxes)
        - If they don't have a sandbox, create one first
        - Make sure the sandbox is started before executing commands
        - Use the execute_command tool
        - Provide the output back to the user

        Always keep track of sandbox IDs and provide them to the user for reference.

        When you're done using a sandbox, ask the user if they want to stop it to save resources.
        """,
            tools=[
                create_sandbox,
                start_sandbox,
                stop_sandbox,
                destroy_sandbox,
                list_sandboxes,
                execute_command,
                run_code,
            ],
        )