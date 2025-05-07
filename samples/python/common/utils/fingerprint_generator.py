"""Fingerprint Generator for A2A Protocol

This module provides functionality to generate and register agent fingerprints
for use with the A2A protocol. The fingerprints are based on the Ethereum
blockchain and use the keccak256 hashing algorithm.
"""

import hashlib
import time

from datetime import datetime

from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3

from ..types_fingerprint import Fingerprint


class FingerprintGenerator:
    """Generator for creating and registering agent fingerprints."""

    def __init__(
        self, private_key: str | None = None, ethereum_url: str | None = None
    ):
        """Initialize the fingerprint generator.

        Args:
            private_key: Ethereum private key for signing fingerprints.
                If not provided, a new account will be generated.
            ethereum_url: URL for Ethereum API. If not provided,
                will use a default Infura endpoint.
        """
        self.w3 = Web3(
            Web3.HTTPProvider(ethereum_url or 'https://sepolia.infura.io/v3/')
        )

        if private_key:
            self.account = Account.from_key(private_key)
        else:
            self.account = Account.create()

    def generate_fingerprint(
        self,
        agent_id: str,
        agent_name: str,
        provider: str,
        version: str,
        metadata: dict[str, str] | None = None,
        register_on_blockchain: bool = False,
        validation_endpoint: str | None = None,
    ) -> Fingerprint:
        """Generate a unique fingerprint for an agent.

        Args:
            agent_id: Unique identifier for the agent
            agent_name: Human-readable name for the agent
            provider: Organization that created the agent
            version: Version string of the agent
            metadata: Additional metadata to include in the fingerprint
            register_on_blockchain: Whether to register on blockchain immediately
            validation_endpoint: URL for validating this fingerprint

        Returns:
            A Fingerprint object containing the hash and signature
        """
        # Create a string combining all agent details
        timestamp = int(time.time())
        metadata_str = '&'.join(f'{k}={v}' for k, v in (metadata or {}).items())

        fingerprint_data = (
            f'id={agent_id}&'
            f'name={agent_name}&'
            f'provider={provider}&'
            f'version={version}&'
            f'timestamp={timestamp}'
        )

        if metadata_str:
            fingerprint_data += f'&{metadata_str}'

        # Create hash using keccak256
        hash_bytes = Web3.keccak(text=fingerprint_data)
        hash_hex = hash_bytes.hex()

        # Sign the hash with the private key
        message = encode_defunct(hash_bytes)
        signed_message = self.w3.eth.account.sign_message(
            message, private_key=self.account.key
        )
        signature = signed_message.signature.hex()

        # Register on blockchain if requested
        blockchain_ref = None
        if register_on_blockchain:
            blockchain_ref = self._register_on_blockchain(hash_hex, signature)

        return Fingerprint(
            hash=hash_hex,
            signature=signature,
            blockchain_ref=blockchain_ref,
            timestamp=datetime.fromtimestamp(timestamp),
            validation_endpoint=validation_endpoint,
        )

    def _register_on_blockchain(self, hash_hex: str, signature: str) -> str:
        """Register the fingerprint on the blockchain.

        This is a placeholder implementation. In a real deployment,
        this would interact with a smart contract to register the fingerprint.

        Args:
            hash_hex: The fingerprint hash
            signature: The signature of the hash

        Returns:
            A reference to the blockchain transaction or contract
        """
        # In a real implementation, this would:
        # 1. Connect to the smart contract
        # 2. Call the register function
        # 3. Return the transaction hash

        # This is a placeholder that returns a fake transaction hash
        return (
            f'0x{hashlib.sha256((hash_hex + signature).encode()).hexdigest()}'
        )

    def sign_message(self, message: str) -> str:
        """Sign a message using the fingerprint private key.

        Args:
            message: The message to sign

        Returns:
            The signature of the message
        """
        message_bytes = message.encode('utf-8')
        message_hash = Web3.keccak(message_bytes)
        message = encode_defunct(message_hash)
        signed_message = self.w3.eth.account.sign_message(
            message, private_key=self.account.key
        )
        return signed_message.signature.hex()

    def compute_message_hash(self, message_content: str | dict | bytes) -> str:
        """Compute a hash for a message.

        Args:
            message_content: The content to hash (string, dict, or bytes)

        Returns:
            The hash of the message content
        """
        if isinstance(message_content, dict):
            # Convert dict to sorted key-value string to ensure consistent hashing
            message_str = '&'.join(
                f'{k}={v}' for k, v in sorted(message_content.items())
            )
            message_bytes = message_str.encode('utf-8')
        elif isinstance(message_content, str):
            message_bytes = message_content.encode('utf-8')
        elif isinstance(message_content, bytes):
            message_bytes = message_content
        else:
            raise ValueError(
                f'Unsupported message content type: {type(message_content)}'
            )

        message_hash = Web3.keccak(message_bytes)
        return message_hash.hex()
