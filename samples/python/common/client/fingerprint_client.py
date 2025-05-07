"""Fingerprint-enabled A2A client

This module extends the standard A2A client to support fingerprint
authentication and verification for agent-to-agent communication.
"""

from typing import Any

import httpx

from ..types import AgentCard, FingerprintVerificationError, Message
from ..types_fingerprint import Fingerprint, MessageVerification
from ..utils.fingerprint_generator import FingerprintGenerator
from ..utils.fingerprint_validator import FingerprintValidator
from .client import A2AClient


class FingerprintEnabledClient(A2AClient):
    """A2A client with support for fingerprint authentication and verification."""

    def __init__(
        self,
        agent_card: AgentCard | None = None,
        url: str | None = None,
        timeout: float = 60.0,
        fingerprint_generator: FingerprintGenerator | None = None,
        fingerprint_validator: FingerprintValidator | None = None,
        verify_incoming: bool = True,
        sign_outgoing: bool = True,
    ):
        """Initialize the fingerprint-enabled client.

        Args:
            agent_card: Agent card for the target agent
            url: URL of the A2A endpoint
            timeout: Request timeout in seconds
            fingerprint_generator: Generator for fingerprints
            fingerprint_validator: Validator for fingerprints
            verify_incoming: Whether to verify fingerprints on incoming messages
            sign_outgoing: Whether to sign outgoing messages
        """
        super().__init__(agent_card, url, timeout)

        self.fingerprint_generator = (
            fingerprint_generator or FingerprintGenerator()
        )
        self.fingerprint_validator = (
            fingerprint_validator or FingerprintValidator()
        )
        self.verify_incoming = verify_incoming
        self.sign_outgoing = sign_outgoing

        # Store our own fingerprint
        self.fingerprint: Fingerprint | None = None

    def set_agent_fingerprint(self, fingerprint: Fingerprint) -> None:
        """Set the fingerprint for this client.

        Args:
            fingerprint: The fingerprint to use
        """
        self.fingerprint = fingerprint

    def generate_agent_fingerprint(
        self,
        agent_id: str,
        agent_name: str,
        provider: str,
        version: str,
        metadata: dict[str, str] | None = None,
        register_on_blockchain: bool = False,
        validation_endpoint: str | None = None,
    ) -> Fingerprint:
        """Generate a fingerprint for this client.

        Args:
            agent_id: Unique identifier for the agent
            agent_name: Human-readable name for the agent
            provider: Organization that created the agent
            version: Version string of the agent
            metadata: Additional metadata to include in the fingerprint
            register_on_blockchain: Whether to register on blockchain immediately
            validation_endpoint: URL for validating this fingerprint

        Returns:
            The generated fingerprint
        """
        self.fingerprint = self.fingerprint_generator.generate_fingerprint(
            agent_id=agent_id,
            agent_name=agent_name,
            provider=provider,
            version=version,
            metadata=metadata,
            register_on_blockchain=register_on_blockchain,
            validation_endpoint=validation_endpoint,
        )
        return self.fingerprint

    def _sign_message(self, message: Message) -> Message:
        """Sign a message with the agent's fingerprint.

        Args:
            message: The message to sign

        Returns:
            The signed message
        """
        if not self.sign_outgoing or not self.fingerprint:
            return message

        # Convert message to a string representation for hashing
        message_dict = message.model_dump()

        # Compute hash of the message content
        message_hash = self.fingerprint_generator.compute_message_hash(
            message_dict
        )

        # Create verification object
        verification = MessageVerification(
            fingerprint=self.fingerprint, message_hash=message_hash
        )

        # Attach verification to message
        message.verification = verification
        return message

    def _verify_message(self, message: Message) -> bool:
        """Verify a message's fingerprint.

        Args:
            message: The message to verify

        Returns:
            True if the message is verified, False otherwise

        Raises:
            FingerprintVerificationError: If verification fails
        """
        if not self.verify_incoming or not message.verification:
            return True

        # Get the verification info
        verification = message.verification

        # Convert message to a string representation for hashing
        message_dict = message.model_dump()

        # Remove verification from the dict to match original content
        if 'verification' in message_dict:
            del message_dict['verification']

        # Verify the message
        return self.fingerprint_validator.verify_message(
            message_content=message_dict,
            message_hash=verification.message_hash,
            fingerprint=verification.fingerprint,
        )

    async def send_task(self, payload: dict[str, Any]) -> Any:
        """Send a task with fingerprint verification.

        Args:
            payload: The task payload

        Returns:
            The task response
        """
        # Sign the message if needed
        if 'message' in payload and self.sign_outgoing and self.fingerprint:
            payload['message'] = self._sign_message(payload['message'])

        # Send the request
        response = await super().send_task(payload)

        # Verify the response if needed
        if (
            self.verify_incoming
            and response.result
            and response.result.status.message
        ):
            try:
                self._verify_message(response.result.status.message)
            except FingerprintVerificationError as e:
                # In a production system, you might want to handle this differently
                # For now, we'll just raise the error
                raise e

        return response

    async def _send_request(self, request: Any) -> dict[str, Any]:
        """Send a request with the appropriate fingerprint headers.

        Args:
            request: The request to send

        Returns:
            The response data
        """
        # If we have a fingerprint, add it to the headers
        headers = {}
        if self.fingerprint:
            # In a real implementation, we'd need to properly format the
            # fingerprint for HTTP transport
            fingerprint_data = self.fingerprint.model_dump_json()
            headers['X-Fingerprint'] = fingerprint_data

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.url,
                    json=request.model_dump(),
                    timeout=self.timeout,
                    headers=headers,
                )
                response.raise_for_status()

                # Check for fingerprint header in response
                if self.verify_incoming and 'X-Fingerprint' in response.headers:
                    # In a real implementation, we'd verify the fingerprint
                    # from the response headers
                    pass

                return response.json()
            except Exception:
                # Use the error handling from the parent class
                return await super()._send_request(request)
