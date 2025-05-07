# Basic test for Fingerprint feature

from common.utils.fingerprint_generator import FingerprintGenerator
from common.utils.fingerprint_validator import FingerprintValidator


def main():
    print('Testing Fingerprint functionality...')

    # Create a fingerprint generator
    generator = FingerprintGenerator()
    print('Generator created successfully!')

    # Generate a fingerprint
    fingerprint = generator.generate_fingerprint(
        agent_id='test-agent',
        agent_name='Test Agent',
        provider='Test Organization',
        version='1.0.0',
        register_on_blockchain=False,
    )
    print(f'Fingerprint generated: {fingerprint.hash[:10]}...')

    # Create a validator
    validator = FingerprintValidator()
    print('Validator created successfully!')

    # Validate the fingerprint (patching the validation methods to always return True for this test)
    validator._verify_signature = lambda *args, **kwargs: True
    validator._verify_on_blockchain = lambda *args, **kwargs: True

    try:
        result = validator.validate_fingerprint(fingerprint)
        print(f'Validation result: {result}')
    except Exception as e:
        print(f'Validation failed: {e!s}')

    print('Fingerprint test completed!')


if __name__ == '__main__':
    main()
