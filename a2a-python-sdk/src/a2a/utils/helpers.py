import logging

from a2a.types import Artifact, Part, Task, TaskArtifactUpdateEvent, TextPart


logger = logging.getLogger(__name__)


def append_artifact_to_task(task: Task, event: TaskArtifactUpdateEvent) -> None:
    """Helper method for updating Task with new artifact data."""
    if not task.artifacts:
        task.artifacts = []

    new_artifact_data: Artifact = event.artifact
    artifact_id: str = new_artifact_data.artifactId
    append_parts: bool = event.append or False

    existing_artifact: Artifact | None = None
    existing_artifact_list_index: int | None = None

    # Find existing artifact by its id
    for i, art in enumerate(task.artifacts):
        if hasattr(art, 'artifactId') and art.artifactId == artifact_id:
            existing_artifact = art
            existing_artifact_list_index = i
            break

    if not append_parts:
        # This represents the first chunk for this artifact index.
        if existing_artifact_list_index is not None:
            # Replace the existing artifact entirely with the new data
            logger.debug(
                f'Replacing artifact at id {artifact_id} for task {task.id}'
            )
            task.artifacts[existing_artifact_list_index] = new_artifact_data
        else:
            # Append the new artifact since no artifact with this index exists yet
            logger.debug(
                f'Adding new artifact with id {artifact_id} for task {task.id}'
            )
            task.artifacts.append(new_artifact_data)
    elif existing_artifact:
        # Append new parts to the existing artifact's parts list
        logger.debug(
            f'Appending parts to artifact id {artifact_id} for task {task.id}'
        )
        existing_artifact.parts.extend(new_artifact_data.parts)
    else:
        # We received a chunk to append, but we don't have an existing artifact.
        # we will ignore this chunk
        logger.warning(
            f'Received append=True for non-existent artifact index {artifact_id} in task {task.id}. Ignoring chunk.'
        )


def build_text_artifact(text: str, artifact_id: str) -> Artifact:
    """Helper to convert agent text to artifact."""
    text_part = TextPart(text=text)
    part = Part(root=text_part)
    return Artifact(parts=[part], artifactId=artifact_id)
