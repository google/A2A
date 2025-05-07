from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_serializer


class Fingerprint(BaseModel):
    """Represents a cryptographic fingerprint for agent verification.

    A fingerprint contains the hash, signature, and blockchain reference
    for verifying an agent's identity.
    """

    hash: str = Field(
        description="SHA-256 hash of the agent's code or identity"
    )
    signature: str = Field(
        description='Cryptographic signature proving ownership'
    )
    blockchain_ref: str | None = Field(
        default=None,
        description='Reference to blockchain transaction or smart contract',
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description='Timestamp of fingerprint creation',
    )
    validation_endpoint: str | None = Field(
        default=None, description='URL endpoint for validating this fingerprint'
    )

    @field_serializer('timestamp')
    def serialize_dt(self, dt: datetime, _info):
        return dt.isoformat()


class MessageVerification(BaseModel):
    """Represents verification information for message integrity.

    Contains the fingerprint and hash of the message content
    for verifying the integrity of the message.
    """

    fingerprint: Fingerprint
    message_hash: str = Field(
        description='Hash of the message content for integrity verification'
    )


class FingerprintAuth(BaseModel):
    """Authentication method using a fingerprint.

    This is used when authenticating with a fingerprint.
    """

    type: Literal['fingerprint'] = 'fingerprint'
    fingerprint: Fingerprint


class FingerprintError(BaseModel):
    """Error response for fingerprint verification failures."""

    code: int = -32008
    message: str = 'Fingerprint verification failed'
    data: dict[str, Any] = Field(default_factory=dict)
