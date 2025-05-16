import asyncio
import json
import logging  # Import logging
import os
import tempfile
import time
import uuid
from typing import Any, AsyncIterable

import google.auth  # Import google.auth
from google import genai
from google.adk.agents.llm_agent import LlmAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

try:
    from google.cloud import storage
except ImportError:
    # This will be caught by the __main__.py if GCS upload is attempted.
    storage = None

# Configure logger for this module
# Modules should not call basicConfig. The application entry point (__main__.py) will handle it.
logger = logging.getLogger(__name__)

class VideoGenerationAgent:
    """
    An agent that simulates video generation from a text prompt,
    providing periodic updates and a final GCS URL.
    """

    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']
    VEO_MODEL_NAME = "veo-2.0-generate-001" # Or the specific Veo model you intend to use
    VEO_POLLING_INTERVAL_SECONDS = 5
    VEO_SIMULATED_TOTAL_GENERATION_TIME_SECONDS = 180 # 3 minutes, for simulated progress
    VEO_DEFAULT_PERSON_GENERATION = "dont_allow"
    VEO_DEFAULT_ASPECT_RATIO = "16:9"
    GCS_BUCKET_NAME = "video_gen_output" # Ensure this bucket exists and agent has write access
    SIGNED_URL_EXPIRATION_SECONDS = 3600 # 1 hour for signed URLs
    # Optional: Service account to impersonate for signing URLs.
    # If set, your gcloud user needs 'Service Account Token Creator' role on this SA.
    SIGNER_SERVICE_ACCOUNT_EMAIL_ENV_VAR = "SIGNER_SERVICE_ACCOUNT_EMAIL"

    def __init__(self):
        self.client = genai.Client() # Please make sure GOOGLE_API_KEY is set beforehand.
        
        # Explicitly get ADC for storage client
        logger.info("Initializing VideoGenerationAgent...")
        try:
            self.credentials, self.project_id = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
            logger.info(f"Successfully obtained ADC. Project ID: {self.project_id}")
        except google.auth.exceptions.DefaultCredentialsError:
            logger.error("Could not get Application Default Credentials. Please run 'gcloud auth application-default login'.")
            self.credentials, self.project_id = None, None
        if storage:
            self.storage_client = storage.Client(credentials=self.credentials, project=self.project_id)
            logger.info("Google Cloud Storage client initialized.")
        else:
            self.storage_client = None
            logger.warning("google-cloud-storage library not found. Uploading video bytes to GCS will fail.")
        
        sa_email_from_env = os.getenv(self.SIGNER_SERVICE_ACCOUNT_EMAIL_ENV_VAR)
        if sa_email_from_env:
            self.signer_service_account_email = sa_email_from_env.strip('\'"') # Strip single and double quotes
            logger.debug(f"Raw SA email from env: '{sa_email_from_env}', Cleaned: '{self.signer_service_account_email}'")
        else:
            self.signer_service_account_email = None

        if self.signer_service_account_email:
            print(f"INFO: Will use service account '{self.signer_service_account_email}' for signing GCS URLs.")
        else:
            logger.info("No SIGNER_SERVICE_ACCOUNT_EMAIL set. Will use ambient gcloud credentials for signing GCS URLs.")
        self._agent = self._build_agent()
        self._user_id = 'video_agent_user' # Static user ID for this agent
        # The ADK runner and related services might not be strictly necessary
        # for a fully simulated agent but are kept for consistency with the sample structure.
        # If the LLM's role is minimal, these could be omitted for a simpler simulation.
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    def get_processing_message(self) -> str:
        return 'Veo video generation in progress...'

    def _build_agent(self) -> LlmAgent:
        """Builds the LLM agent for the video generation agent."""
        return LlmAgent(
            model='gemini-1.5-flash-latest', # Or any suitable model
            name='video_generation_orchestrator_agent',
            description=(
                'This agent orchestrates simulated video generation from text prompts.'
            ),
            instruction="""\
            You are an assistant that helps kick off video generation tasks.
            When a user provides a prompt for a video, acknowledge the request
            and state that the video generation process will begin.
            The actual video generation and progress updates will be handled by the system.
            """,
            tools=[], # No specific tools needed for this simple orchestration
        )

    def _upload_bytes_to_gcs(self, video_bytes: bytes, gcs_bucket_name: str, gcs_blob_name: str, content_type: str = 'video/mp4') -> str:
        if not self.storage_client:
            logger.error("GCS upload attempted but storage_client is not initialized.")
            raise RuntimeError("Google Cloud Storage client not initialized. Is 'google-cloud-storage' installed?")
        
        bucket = self.storage_client.bucket(gcs_bucket_name)
        blob = bucket.blob(gcs_blob_name)

        logger.info(f"Attempting to upload video bytes to gs://{gcs_bucket_name}/{gcs_blob_name} with content_type: {content_type}")
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, gcs_blob_name.split('/')[-1])

        try:
            with open(temp_file_path, 'wb') as f:
                f.write(video_bytes)
            blob.upload_from_filename(temp_file_path, content_type=content_type)
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        logger.info(f"Successfully uploaded to gs://{gcs_bucket_name}/{gcs_blob_name}")
        return f"gs://{gcs_bucket_name}/{gcs_blob_name}" # Return the GCS URI

    def _generate_signed_url(self, blob_name: str, bucket_name: str, expiration_seconds: int) -> str:
        if not self.storage_client:
            # This case should ideally be prevented by checks during initialization or before calling.
            logger.error("Google Cloud Storage client not initialized. Cannot generate signed URL.")
            return f"gs://{bucket_name}/{blob_name}" # Fallback to GCS URI

        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        try:
            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=expiration_seconds,
                method="GET",
                # Use the instance variable set in __init__
                service_account_email=self.signer_service_account_email
            )
            logger.info(f"Successfully generated signed URL for gs://{bucket_name}/{blob_name}")
            return signed_url
        except Exception as e:
            logger.error(f"Error generating signed URL for gs://{bucket_name}/{blob_name}: {e}. Check permissions (e.g., 'Service Account Token Creator' if using impersonation).")
            return f"gs://{bucket_name}/{blob_name}" # Fallback to GCS URI

    def invoke(self, prompt: str, session_id: str) -> str:
        """
        Handles non-streaming requests. For video generation, this would
        initiate Veo generation and return the final GCS URL upon completion.
        """
        logger.info(f"VideoGenerationAgent: invoke called for session {session_id} with prompt: '{prompt}'")
        try:
            operation = self.client.models.generate_videos(
                model=self.VEO_MODEL_NAME,
                prompt=prompt,
                config=genai_types.GenerateVideosConfig(
                    person_generation=self.VEO_DEFAULT_PERSON_GENERATION,
                    aspect_ratio=self.VEO_DEFAULT_ASPECT_RATIO,
                ),
            )
            logger.info(f"VideoGenerationAgent invoke: Veo operation started: {operation.name}")

            while not operation.done:
                time.sleep(self.VEO_POLLING_INTERVAL_SECONDS) # Standard blocking sleep
                operation = self.client.operations.get(operation) # Pass the operation object
                logger.info(f"VideoGenerationAgent invoke: Polling Veo operation status: {operation.name}, Done: {operation.done}")

            if operation.error:
                error_message = f"Veo video generation failed: {operation.error.message}"
                logger.error(f"VideoGenerationAgent invoke: {error_message}")
                return error_message
            
            logger.debug(f"VideoGenerationAgent invoke: Veo operation completed. Response object: {operation.response}")
            if operation.response and operation.response.generated_videos:
                # Assuming we use the first generated video
                generated_video_info = operation.response.generated_videos[0]
                video_obj = generated_video_info.video
                logger.debug(f"VideoGenerationAgent invoke: video_obj: {video_obj}")

                if video_obj:
                    if video_obj.uri:
                        final_url = video_obj.uri
                        if not final_url.startswith("gs://"):
                             logger.warning(f"VideoGenerationAgent invoke: Received non-GCS URI '{final_url}'. Consider uploading to your GCS.")
                             # Forcing GCS upload for consistency if bytes are also available
                             if video_obj.video_bytes:
                                print("Video bytes also available, preferring GCS upload.")
                                video_filename = f"video_{session_id}_{uuid.uuid4()}.mp4"
                                gcs_blob_name = f"{session_id}/{video_filename}"
                                final_url = self._upload_bytes_to_gcs(video_obj.video_bytes, self.GCS_BUCKET_NAME, gcs_blob_name, video_obj.mime_type)
                    elif video_obj.video_bytes:
                        logger.info(f"VideoGenerationAgent invoke: Video URI is None, but video_bytes are present. Uploading to GCS.")
                        video_filename = f"video_{session_id}_{uuid.uuid4()}.mp4"
                        gcs_blob_name = f"{session_id}/{video_filename}"
                        final_url = self._upload_bytes_to_gcs(video_obj.video_bytes, self.GCS_BUCKET_NAME, gcs_blob_name, video_obj.mime_type)
                    else:
                        final_url = None # No URI and no bytes

                    if final_url:
                        logger.info(f"VideoGenerationAgent invoke: Video generation complete. GCS URI: {final_url}")
                        display_url_invoke = final_url # Default to original GCS URI
                        if final_url.startswith("gs://"):
                            try:
                                parts_invoke = final_url[5:].split("/", 1)
                                if len(parts_invoke) == 2:
                                    gcs_bucket_for_signing_invoke = parts_invoke[0]
                                    gcs_blob_for_signing_invoke = parts_invoke[1]
                                    display_url_invoke = self._generate_signed_url(
                                        gcs_blob_for_signing_invoke,
                                        gcs_bucket_for_signing_invoke,
                                        self.SIGNED_URL_EXPIRATION_SECONDS
                                    )
                                    logger.info(f"VideoGenerationAgent invoke: Generated signed URL: {display_url_invoke}")
                                else:
                                    logger.warning(f"VideoGenerationAgent invoke: Could not parse GCS URI for signing: {final_url}")
                            except Exception as e_sign_invoke:
                                logger.error(f"Error generating signed URL in invoke for {final_url}: {e_sign_invoke}")
                        return display_url_invoke # Return signed URL or original GCS URI if signing failed
                else:
                    error_message = "Veo video generation completed (invoke), but the video URI is missing."
                    logger.error(f"VideoGenerationAgent invoke: Full response object: {operation.response}")
                    logger.error(f"VideoGenerationAgent invoke: {error_message}")
                    return error_message
            else:
                logger.warning(f"VideoGenerationAgent invoke: Full response object: {operation.response}")
                if hasattr(operation.response, 'rai_media_filtered_count') and operation.response.rai_media_filtered_count > 0:
                    reasons = getattr(operation.response, 'rai_media_filtered_reasons', ['Unknown safety filter.'])
                    error_message = f"Video generation was blocked by safety filters. Reasons: {', '.join(reasons)}"
                else:
                    error_message = "Veo video generation completed (invoke), but no video was returned in the response."
                logger.error(f"VideoGenerationAgent invoke: {error_message}")
                return error_message

        except Exception as e:
            error_message = f"Error during Veo video generation (invoke): {e}"
            logger.exception(error_message) # Log with traceback
            return error_message

    async def stream(self, prompt: str, session_id: str) -> AsyncIterable[dict[str, Any]]:
        """
        Handles streaming requests, providing periodic updates during
        video generation and a final GCS URL.
        """
        logger.info(f"VideoGenerationAgent: stream called for session {session_id} with prompt: '{prompt}'")

        initial_message = f"Received prompt: '{prompt}'. Starting Veo video generation."
        # Yield initial message with 0% progress
        yield {'is_task_complete': False, 'updates': initial_message, 'progress_percent': 0}
        logger.info(f"VideoGenerationAgent stream: {initial_message}")

        start_time = time.monotonic() # For simulated progress calculation
        
        try:
            operation = await asyncio.to_thread(
                self.client.models.generate_videos,
                model=self.VEO_MODEL_NAME,
                prompt=prompt,
                config=genai_types.GenerateVideosConfig(
                    person_generation=self.VEO_DEFAULT_PERSON_GENERATION,
                    aspect_ratio=self.VEO_DEFAULT_ASPECT_RATIO,
                )
            )
            # Yield operation started message with a small initial progress
            initial_simulated_progress = 5 
            yield {'is_task_complete': False, 'updates': f"Veo operation started: {operation.name}. Polling for completion...", 'progress_percent': initial_simulated_progress}

            while not operation.done:
                await asyncio.sleep(self.VEO_POLLING_INTERVAL_SECONDS)
                operation = await asyncio.to_thread(self.client.operations.get, operation) # Pass the operation object
                elapsed_time = time.monotonic() - start_time
                
                # Log specific, non-binary parts of the operation for debugging
                logger.debug(f"VideoGenerationAgent stream: Polled operation. Name: {operation.name}, Done: {operation.done}, Error: {operation.error is not None}")
                metadata_str = str(operation.metadata)
                # Log the full metadata string if it's not excessively long, otherwise truncate
                logger.debug(f"VideoGenerationAgent stream: Polled operation. Metadata type: {type(operation.metadata)}, Metadata dir: {dir(operation.metadata)}, Metadata content (first 1000 chars): {metadata_str[:1000]}")
                # Avoid printing the whole 'operation' object if its string representation is too verbose or contains binary data.

                # Calculate simulated progress
                raw_simulated_progress = (elapsed_time / self.VEO_SIMULATED_TOTAL_GENERATION_TIME_SECONDS) * 100
                # Cap at 99% while not done, ensure it's an int, and doesn't decrease from initial reported progress
                current_simulated_progress = max(initial_simulated_progress, min(int(raw_simulated_progress), 99))

                # Default message includes simulated progress
                progress_update_message = f"Veo video generation in progress (polling status for {operation.name}). Simulated progress: {current_simulated_progress}%"

                # If Veo ever provides real progress metadata, this section could be enhanced
                if operation.metadata is not None: # Explicitly check for not None
                    # Use a local variable for clarity within this block
                    metadata_content_str = str(operation.metadata)
                    # Attempt to get more specific progress if available
                    # The exact attributes depend on what Veo provides in metadata.
                    # Common patterns include 'progress_message', 'state_message', or 'progress_percent'.
                    if hasattr(operation.metadata, 'progress_message') and operation.metadata.progress_message:
                        progress_update_message = f"Veo: {operation.metadata.progress_message} (Operation: {operation.name})"
                    # Only use metadata_content_str if it's meaningful and not just the string "None"
                    elif metadata_content_str.strip() and metadata_content_str.strip().lower() != "none":
                        progress_update_message = f"Veo video generation in progress (Operation: {operation.name}, Status: {metadata_content_str[:150]}...)"
                # If operation.metadata is None, or if it's not None but doesn't have specific progress fields,
                # the progress_update_message (with "Simulated progress: X%") remains.
                logger.info(f"VideoGenerationAgent stream: Yielding progress update: '{progress_update_message}'")
                yield {
                    'is_task_complete': False,
                    'updates': progress_update_message,
                    'progress_percent': current_simulated_progress 
                }
                logger.info(f"VideoGenerationAgent stream: Polling Veo operation status: {operation.name}, Done: {operation.done}")

            if operation.error:
                error_details_str = "Unknown error"
                logger.debug(f"VideoGenerationAgent stream: Operation error detected. Type of operation.error: {type(operation.error)}, Content: {operation.error}")
                if isinstance(operation.error, dict):
                    # If operation.error is a dictionary, try to get 'message' key
                    error_details_str = operation.error.get('message', json.dumps(operation.error))
                elif hasattr(operation.error, 'message'):
                    # If it's an object with a 'message' attribute (like google.rpc.Status)
                    error_details_str = operation.error.message
                else:
                    # Fallback if it's some other type
                    error_details_str = str(operation.error)
                error_message = f"Veo video generation failed: {error_details_str}"
                logger.error(f"VideoGenerationAgent stream: {error_message} (Raw error: {operation.error})")
                # Yield final error with 100% progress (task is considered done)
                yield {'is_task_complete': True, 'content': error_message, 'final_message_text': error_message, 'progress_percent': 100}
                return

            logger.debug(f"VideoGenerationAgent stream: Veo operation completed. Response object: {operation.response}, Progress: 100%")
            if operation.response and operation.response.generated_videos:
                generated_video_info = operation.response.generated_videos[0] # Using the first video
                video_obj = generated_video_info.video
                final_url = None
                description = "Link to generated video"

                logger.debug(f"VideoGenerationAgent stream: video_obj: {video_obj}")
                if video_obj:
                    if video_obj.uri:
                        final_url = video_obj.uri
                        if not final_url.startswith("gs://"):
                            logger.warning(f"VideoGenerationAgent stream: Received non-GCS URI '{final_url}'.")
                            # If bytes are also available, prefer uploading them for a consistent GCS link
                            if video_obj.video_bytes:
                                logger.info("Video bytes also available, preferring GCS upload.")
                                video_filename_base = f"veo_video_{session_id}_{uuid.uuid4()}.mp4"
                                gcs_blob_name = f"{session_id}/{video_filename_base}"
                                final_url = self._upload_bytes_to_gcs(video_obj.video_bytes, self.GCS_BUCKET_NAME, gcs_blob_name, video_obj.mime_type)
                                description = f'Link to Veo generated video (uploaded from bytes to GCS: {final_url}). Original non-GCS URI was {video_obj.uri}.'
                        else: # It was already a gs:// URI
                            description = f'GCS URI to Veo generated video: {final_url}'
                    elif video_obj.video_bytes:
                        logger.info(f"VideoGenerationAgent stream: Video URI is None, but video_bytes are present. Uploading to GCS.")
                        video_filename_base = f"veo_video_{session_id}_{uuid.uuid4()}.mp4"
                        gcs_blob_name = f"{session_id}/{video_filename_base}"
                        final_url = self._upload_bytes_to_gcs(video_obj.video_bytes, self.GCS_BUCKET_NAME, gcs_blob_name, video_obj.mime_type)
                        description = f'GCS URI to Veo generated video (uploaded from bytes): {final_url}'

                if final_url:
                    display_url = final_url # Default to the GCS URI
                    logger.info(f"VideoGenerationAgent stream: Final GCS URL before signing: {final_url}")
                    # Attempt to generate a signed URL if it's a GCS URI
                    if final_url.startswith("gs://"):
                        try:
                            parts = final_url[5:].split("/", 1)
                            if len(parts) == 2:
                                gcs_bucket_for_signing = parts[0]
                                gcs_blob_for_signing = parts[1]
                                display_url = self._generate_signed_url(
                                    gcs_blob_for_signing,
                                    gcs_bucket_for_signing,
                                    self.SIGNED_URL_EXPIRATION_SECONDS
                                )
                            else:
                                logger.warning(f"VideoGenerationAgent stream: Could not parse GCS URI for signing: {final_url}")
                        except Exception as e_sign:
                            logger.error(f"Error preparing display URL (signing) for {final_url}: {e_sign}")
                            # display_url remains final_url (the GCS URI) if signing fails

                    video_filename = f"veo_video_{session_id}_{uuid.uuid4()}.mp4" # Use .mp4 extension
                    completion_message = f"Veo video generation complete. Access the video (link may expire). GCS URI for reference: {final_url}"
                    # Ensure mime_type is a non-None string
                    actual_mime_type = 'video/mp4' # Default
                    if video_obj and hasattr(video_obj, 'mime_type') and video_obj.mime_type:
                        actual_mime_type = video_obj.mime_type

                    file_part_data = {
                        'uri': display_url, # Use the signed URL (or original GCS URI if signing failed)
                        'mimeType': actual_mime_type # Changed key to camelCase
                    }
                    logger.info(f"VideoGenerationAgent stream: {completion_message}. Display URL: {display_url}")
                    logger.debug(f"VideoGenerationAgent stream: Yielding final success with file_part_data: {file_part_data}")
                    yield {
                        'is_task_complete': True,
                        'file_part_data': file_part_data, # Yield structured data for video part
                        'artifact_name': video_filename, # Artifact name is the video filename
                        'artifact_description': description,
                        'final_message_text': completion_message,
                        'progress_percent': 100 # Task complete
                    }
                else:
                    error_message = "Veo video generation completed, but the video URI is missing."
                    logger.error(f"VideoGenerationAgent stream: {error_message}")
                    logger.error(f"VideoGenerationAgent stream: Full response object: {operation.response}")
                    yield {
                        'is_task_complete': True,
                        'content': error_message,
                        'final_message_text': error_message,
                        'progress_percent': 100 # Task complete
                    }
            else:
                # This block is hit if operation.response is None/falsy OR generated_videos is None/empty
                logger.warning(f"VideoGenerationAgent stream: Full response object: {operation.response}")
                if hasattr(operation.response, 'rai_media_filtered_count') and operation.response.rai_media_filtered_count > 0:
                    reasons = getattr(operation.response, 'rai_media_filtered_reasons', ['Unknown safety filter.'])
                    final_message = f"Video generation was blocked by safety filters. Reasons: {', '.join(reasons)}"
                else:
                    final_message = "Veo video generation completed, but no video was returned."
                logger.error(f"VideoGenerationAgent stream: {final_message}")

                logger.debug(f"VideoGenerationAgent stream: Yielding final completion (no video) with content: '{final_message}'")
                yield {'is_task_complete': True, 'content': final_message, 'final_message_text': final_message, 'progress_percent': 100}

        except Exception as e:
            error_message = f"An error occurred during Veo video generation (stream): {e}"
            logger.exception(error_message) # Log with traceback
            logger.debug(f"VideoGenerationAgent stream: Yielding final error with content: '{error_message}'")
            yield {'is_task_complete': True, 'content': error_message, 'final_message_text': error_message, 'progress_percent': 100}
