from datetime import datetime
from typing import Any
from uuid import uuid4

from a2a.types import (
    Artifact,
    Message,
    MessageSendParams,
    Part,
    Role,
    Task,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)


def create_task_obj(message_send_params: MessageSendParams) -> Task:
    """Create a new task object."""
    if not message_send_params.message.contextId:
        message_send_params.message.contextId = str(uuid4())

    return Task(
        id=str(uuid4()),
        contextId=message_send_params.message.contextId,
        status=TaskStatus(state=TaskState.submitted),
        history=[message_send_params.message],
    )


def update_task_with_agent_response(
    task: Task, agent_response: dict[str, Any]
) -> None:
    """Updates the provided task with the agent response."""
    task.status.timestamp = datetime.now().isoformat()
    parts: list[Part] = [Part(root=TextPart(text=agent_response['content']))]
    if agent_response['require_user_input']:
        task.status.state = TaskState.input_required
        task.status.message = Message(
            messageId=str(uuid4()),
            role=Role.agent,
            parts=parts,
        )
    else:
        task.status.state = TaskState.completed
        if not task.artifacts:
            task.artifacts = []

        artifact: Artifact = Artifact(parts=parts, artifactId=str(uuid4()))
        task.artifacts.append(artifact)


def process_streaming_agent_response(
    task: Task,
    agent_response: dict[str, Any],
) -> tuple[TaskArtifactUpdateEvent | None, TaskStatusUpdateEvent]:
    """Processes the streaming agent responses and returns TaskArtifactUpdateEvent and TaskStatusUpdateEvent."""
    is_task_complete = agent_response['is_task_complete']
    require_user_input = agent_response['require_user_input']
    parts: list[Part] = [Part(root=TextPart(text=agent_response['content']))]

    end_stream = False
    artifact = None
    message = None

    # responses from this agent can be working/completed/input-required
    if not is_task_complete and not require_user_input:
        task_state = TaskState.working
        message = Message(role=Role.agent, parts=parts, messageId=str(uuid4()))
    elif require_user_input:
        task_state = TaskState.input_required
        message = Message(role=Role.agent, parts=parts, messageId=str(uuid4()))
        end_stream = True
    else:
        task_state = TaskState.completed
        artifact = Artifact(parts=parts, artifactId=str(uuid4()))
        end_stream = True

    task_artifact_update_event = None

    if artifact:
        task_artifact_update_event = TaskArtifactUpdateEvent(
            taskId=task.id,
            artifact=artifact,
            append=False,
            lastChunk=True,
        )

    task_status_event = TaskStatusUpdateEvent(
        taskId=task.id,
        status=TaskStatus(
            state=task_state,
            message=message,
            timestamp=datetime.now().isoformat(),
        ),
        final=end_stream,
    )

    return task_artifact_update_event, task_status_event
