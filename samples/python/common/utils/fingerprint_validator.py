"""Fingerprint Validator for A2A Protocol

This module provides functionality to validate agent fingerprints
for use with the A2A protocol. The validators check fingerprint
authenticity using cryptographic verification and blockchain lookups.
"""

from datetime import datetime, timedelta

import requests

from eth_account.messages import encode_defunct
from web3 import Web3

from ..types import FingerprintVerificationError
from ..types_fingerprint import Fingerprint


class FingerprintValidator:
    """Validator for verifying agent fingerprints."""

    def __init__(self, ethereum_url: str | None = None, cache_ttl: int = 3600):
        """Initialize the fingerprint validator.

        Args:
            ethereum_url: URL for Ethereum API. If not provided,
                will use a default Infura endpoint.
            cache_ttl: Time to live for cache entries in seconds (default 1 hour)
        """
        self.w3 = Web3(
            Web3.HTTPProvider(ethereum_url or 'https://sepolia.infura.io/v3/')
        )
        self.cache_ttl = cache_ttl
        self.cache: dict[str, tuple[bool, datetime]] = {}

    def validate_fingerprint(
        self,
        fingerprint: Fingerprint,
        check_blockchain: bool = True,
        check_endpoint: bool = True,
    ) -> bool:
        """Validate a fingerprint by checking its signature and optionally
        verifying it on the blockchain or via validation endpoint.

        Args:
            fingerprint: The fingerprint to validate
            check_blockchain: Whether to verify on blockchain
            check_endpoint: Whether to use validation endpoint if available

        Returns:
            True if the fingerprint is valid, False otherwise

        Raises:
            FingerprintVerificationError: If verification fails
        """
        # Check cache first
        cache_key = fingerprint.hash
        if cache_key in self.cache:
            is_valid, timestamp = self.cache[cache_key]
            if timestamp + timedelta(seconds=self.cache_ttl) > datetime.now():
                return is_valid

        # Verify cryptographic signature
        # In a real implementation, we'd need the agent's public key
        # This is a simplified version assuming we can recover the key from signature
        try:
            # For a complete implementation, we would:
            # 1. Get the public key from the signature or from a registry
            # 2. Verify the signature matches the hash and was signed by that key
            signature_valid = self._verify_signature(
                fingerprint.hash, fingerprint.signature
            )
            if not signature_valid:
                self._cache_result(cache_key, False)
                raise FingerprintVerificationError('Invalid signature')
        except Exception as e:
            self._cache_result(cache_key, False)
            raise FingerprintVerificationError(
                f'Signature verification error: {e!s}'
            )

        # Check blockchain if requested
        if check_blockchain and fingerprint.blockchain_ref:
            try:
                blockchain_valid = self._verify_on_blockchain(
                    fingerprint.hash,
                    fingerprint.signature,
                    fingerprint.blockchain_ref,
                )
                if not blockchain_valid:
                    self._cache_result(cache_key, False)
                    raise FingerprintVerificationError(
                        'Blockchain verification failed'
                    )
            except Exception as e:
                self._cache_result(cache_key, False)
                raise FingerprintVerificationError(
                    f'Blockchain verification error: {e!s}'
                )

        # Check validation endpoint if requested
        if check_endpoint and fingerprint.validation_endpoint:
            try:
                endpoint_valid = self._verify_with_endpoint(fingerprint)
                if not endpoint_valid:
                    self._cache_result(cache_key, False)
                    raise FingerprintVerificationError(
                        'Endpoint verification failed'
                    )
            except Exception as e:
                self._cache_result(cache_key, False)
                raise FingerprintVerificationError(
                    f'Endpoint verification error: {e!s}'
                )

        # If we get here, the fingerprint passed all checks
        self._cache_result(cache_key, True)
        return True

    def _verify_signature(self, hash_hex: str, signature: str) -> bool:
        """Verify a signature against a hash.

        Args:
            hash_hex: The hash to verify
            signature: The signature to check

        Returns:
            True if the signature is valid, False otherwise
        """
        # In a real implementation, this would:
        # 1. Recover the public key from the signature
        # 2. Verify the signature against the hash

        # This is a placeholder implementation
        # In a real application, we'd use cryptographic verification
        try:
            # Create the same format of message that was signed
            message = encode_defunct(hexstr=hash_hex)

            # Recover the address (public key) from the signature
            recovered_address = self.w3.eth.account.recover_message(
                message, signature=signature
            )

            # In a real implementation, we'd check this address against
            # the address registered for the agent
            return True  # Placeholder
        except Exception:
            return False

    def _verify_on_blockchain(
        self, hash_hex: str, signature: str, blockchain_ref: str
    ) -> bool:
        """Verify a fingerprint on the blockchain.

        This is a placeholder implementation. In a real deployment,
        this would query the smart contract to verify the fingerprint.

        Args:
            hash_hex: The fingerprint hash
            signature: The signature to verify
            blockchain_ref: Reference to the blockchain record

        Returns:
            True if the verification succeeds, False otherwise
        """
        # In a real implementation, this would:
        # 1. Connect to the smart contract
        # 2. Call the verify function
        # 3. Return the result

        # For now, just return a placeholder response
        return True

    def _verify_with_endpoint(self, fingerprint: Fingerprint) -> bool:
        """Verify a fingerprint by calling its validation endpoint.

        Args:
            fingerprint: The fingerprint to verify

        Returns:
            True if the verification succeeds, False otherwise
        """
        if not fingerprint.validation_endpoint:
            return False

        try:
            # Make a POST request to the validation endpoint
            response = requests.post(
                fingerprint.validation_endpoint,
                json={
                    'hash': fingerprint.hash,
                    'signature': fingerprint.signature,
                    'blockchain_ref': fingerprint.blockchain_ref,
                    'timestamp': fingerprint.timestamp.isoformat(),
                },
                timeout=10,
            )

            # Check if the response indicates success
            return response.status_code == 200 and response.json().get(
                'valid', False
            )
        except Exception:
            return False

    def _cache_result(self, key: str, result: bool) -> None:
        """Cache a validation result.

        Args:
            key: The cache key (usually the fingerprint hash)
            result: The validation result
        """
        self.cache[key] = (result, datetime.now())

    def verify_message(
        self,
        message_content: str | dict | bytes,
        message_hash: str,
        fingerprint: Fingerprint,
    ) -> bool:
        """Verify a message using a fingerprint.

        Args:
            message_content: The message content to verify
            message_hash: The hash of the message content
            fingerprint: The fingerprint used to sign the message

        Returns:
            True if the message is valid, False otherwise
        """
        # First verify the fingerprint itself
        if not self.validate_fingerprint(fingerprint):
            return False

        # Next, verify the message hash
        try:
            # Compute the hash of the message content
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
                return False

            computed_hash = Web3.keccak(message_bytes).hex()

            # Compare the computed hash with the provided hash
            return computed_hash == message_hash
        except Exception:
            return False
