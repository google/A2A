"""
Tests for the Fingerprint functionality in the A2A protocol.

This module contains unit tests for the Fingerprint types, generation,
validation, and integration with the A2A client.
"""

from datetime import datetime
from unittest.mock import patch

import pytest

from eth_account import Account

from samples.python.common.types import Message, TextPart
from samples.python.common.types_fingerprint import (
    Fingerprint,
    MessageVerification,
)
from samples.python.common.utils.fingerprint_generator import (
    FingerprintGenerator,
)
from samples.python.common.utils.fingerprint_validator import (
    FingerprintValidator,
)


@pytest.fixture
def test_account():
    """Create a test Ethereum account."""
    return Account.create()


@pytest.fixture
def fingerprint_generator(test_account):
    """Create a fingerprint generator with a test account."""
    generator = FingerprintGenerator()
    # Override the account with our test account
    generator.account = test_account
    return generator


@pytest.fixture
def fingerprint_validator():
    """Create a fingerprint validator."""
    return FingerprintValidator()


@pytest.fixture
def sample_fingerprint(fingerprint_generator):
    """Generate a sample fingerprint for testing."""
    return fingerprint_generator.generate_fingerprint(
        agent_id='test-agent',
        agent_name='Test Agent',
        provider='Test Provider',
        version='1.0.0',
        register_on_blockchain=False,
    )


@pytest.fixture
def sample_message():
    """Create a sample message for testing."""
    return Message(
        role='agent', parts=[TextPart(text='Hello, I am a test agent.')]
    )


def test_fingerprint_generation(fingerprint_generator):
    """Test that fingerprints can be generated correctly."""
    # Generate a fingerprint
    fingerprint = fingerprint_generator.generate_fingerprint(
        agent_id='test-agent',
        agent_name='Test Agent',
        provider='Test Provider',
        version='1.0.0',
    )

    # Verify the fingerprint properties
    assert fingerprint.hash is not None
    assert fingerprint.signature is not None
    assert isinstance(fingerprint.timestamp, datetime)

    # Test with additional metadata
    fingerprint_with_metadata = fingerprint_generator.generate_fingerprint(
        agent_id='test-agent',
        agent_name='Test Agent',
        provider='Test Provider',
        version='1.0.0',
        metadata={'key1': 'value1', 'key2': 'value2'},
    )

    # Verify that different metadata produces a different hash
    assert fingerprint.hash != fingerprint_with_metadata.hash


def test_fingerprint_verification(
    fingerprint_generator, fingerprint_validator, sample_fingerprint
):
    """Test that fingerprints can be verified correctly."""
    # Verify a valid fingerprint
    with patch.object(
        fingerprint_validator, '_verify_signature', return_value=True
    ):
        with patch.object(
            fingerprint_validator, '_verify_on_blockchain', return_value=True
        ):
            assert (
                fingerprint_validator.validate_fingerprint(sample_fingerprint)
                is True
            )

    # Test with invalid signature
    with patch.object(
        fingerprint_validator, '_verify_signature', return_value=False
    ):
        with pytest.raises(Exception) as excinfo:
            fingerprint_validator.validate_fingerprint(sample_fingerprint)
        assert 'Invalid signature' in str(excinfo.value)

    # Test with invalid blockchain verification
    with patch.object(
        fingerprint_validator, '_verify_signature', return_value=True
    ):
        with patch.object(
            fingerprint_validator, '_verify_on_blockchain', return_value=False
        ):
            sample_fingerprint.blockchain_ref = 'test-ref'
            with pytest.raises(Exception) as excinfo:
                fingerprint_validator.validate_fingerprint(sample_fingerprint)
            assert 'Blockchain verification failed' in str(excinfo.value)


def test_message_signing_and_verification(
    fingerprint_generator,
    fingerprint_validator,
    sample_fingerprint,
    sample_message,
):
    """Test that messages can be signed and verified."""
    # Compute a message hash
    message_dict = sample_message.model_dump()
    message_hash = fingerprint_generator.compute_message_hash(message_dict)

    # Create a verification object
    verification = MessageVerification(
        fingerprint=sample_fingerprint, message_hash=message_hash
    )

    # Add verification to the message
    sample_message.verification = verification

    # Verify the message
    with patch.object(
        fingerprint_validator, 'validate_fingerprint', return_value=True
    ):
        assert (
            fingerprint_validator.verify_message(
                message_content=message_dict,
                message_hash=verification.message_hash,
                fingerprint=verification.fingerprint,
            )
            is True
        )

    # Test with modified message content
    modified_message_dict = message_dict.copy()
    modified_message_dict['parts'][0]['text'] = 'Modified text'

    with patch.object(
        fingerprint_validator, 'validate_fingerprint', return_value=True
    ):
        assert (
            fingerprint_validator.verify_message(
                message_content=modified_message_dict,
                message_hash=verification.message_hash,
                fingerprint=verification.fingerprint,
            )
            is False
        )


def test_fingerprint_serialization(sample_fingerprint):
    """Test that fingerprints can be serialized to JSON and back."""
    # Serialize to JSON
    json_str = sample_fingerprint.model_dump_json()

    # Deserialize from JSON
    deserialized = Fingerprint.model_validate_json(json_str)

    # Verify the deserialized object
    assert deserialized.hash == sample_fingerprint.hash
    assert deserialized.signature == sample_fingerprint.signature
    assert deserialized.blockchain_ref == sample_fingerprint.blockchain_ref
    assert (
        deserialized.timestamp.isoformat()
        == sample_fingerprint.timestamp.isoformat()
    )
    assert (
        deserialized.validation_endpoint
        == sample_fingerprint.validation_endpoint
    )
