"""Test cases for the InMemoryCache utility"""

import threading
import time

import pytest


# Assuming your InMemoryCache class is in a file named 'in_memory_cache.py'
# If it's in the same file, you don't need this import line.
from common.utils.in_memory_cache import InMemoryCache


# --- Fixtures ---


@pytest.fixture(scope='function')
def cache_instance():
    """
    Provides a clean InMemoryCache instance for each test function.
    Ensures tests don't interfere with each other's cache state.
    """
    # Get the singleton instance
    instance = InMemoryCache()
    # Clear any state from previous tests
    instance.clear()
    yield instance


# --- Test Cases ---


def test_singleton_instance(cache_instance):
    """Verify that multiple calls to the constructor return the same instance."""
    instance1 = cache_instance
    instance2 = InMemoryCache()
    assert instance1 is instance2
    assert id(instance1) == id(instance2)


def test_set_and_get_basic(cache_instance):
    """Test setting and retrieving a simple value."""
    cache_instance.set('key1', 'value1')
    assert cache_instance.get('key1') == 'value1'


def test_get_non_existent_key(cache_instance):
    """Test retrieving a key that doesn't exist, expecting the default."""
    assert cache_instance.get('non_existent') is None
    assert (
        cache_instance.get('non_existent', default='default_value')
        == 'default_value'
    )


def test_set_overwrite(cache_instance):
    """Test overwriting an existing key."""
    cache_instance.set('key1', 'value1')
    assert cache_instance.get('key1') == 'value1'
    cache_instance.set('key1', 'value2')
    assert cache_instance.get('key1') == 'value2'


def test_delete_key(cache_instance):
    """Test deleting a key."""
    cache_instance.set('key_to_delete', 'some_value')
    assert cache_instance.get('key_to_delete') == 'some_value'
    deleted = cache_instance.delete('key_to_delete')
    assert deleted is True
    assert cache_instance.get('key_to_delete') is None


def test_delete_non_existent_key(cache_instance):
    """Test deleting a key that doesn't exist."""
    deleted = cache_instance.delete('non_existent_to_delete')
    assert deleted is False


def test_clear_cache(cache_instance):
    """Test clearing the entire cache."""
    cache_instance.set('key1', 'value1')
    cache_instance.set('key2', 123, ttl=10)
    assert cache_instance.get('key1') == 'value1'
    assert cache_instance.get('key2') == 123

    cleared = cache_instance.clear()
    assert cleared is True
    assert cache_instance.get('key1') is None
    assert cache_instance.get('key2') is None
    # Also check internal state if possible/needed (though behavior testing is preferred)
    assert not cache_instance._cache_data
    assert not cache_instance._ttl


def test_ttl_expiration(cache_instance):
    """Test that a key expires after its TTL."""
    key = 'ttl_key'
    value = 'expires'
    ttl_seconds = 0.1  # Use a short TTL for testing

    cache_instance.set(key, value, ttl=ttl_seconds)
    assert cache_instance.get(key) == value  # Should exist immediately

    time.sleep(ttl_seconds + 0.05)  # Wait slightly longer than TTL

    assert cache_instance.get(key) is None  # Should have expired


def test_ttl_does_not_expire_early(cache_instance):
    """Test that a key does not expire before its TTL."""
    key = 'long_ttl_key'
    value = 'persistent'
    ttl_seconds = 1

    cache_instance.set(key, value, ttl=ttl_seconds)
    time.sleep(0.1)  # Wait less than TTL
    assert cache_instance.get(key) == value  # Should still exist


def test_ttl_set_no_ttl_removes_ttl(cache_instance):
    """Test that setting a key without TTL removes any existing TTL."""
    key = 'ttl_override_key'
    value1 = 'expiring_soon'
    value2 = 'permanent'
    ttl_seconds = 0.1

    cache_instance.set(key, value1, ttl=ttl_seconds)
    assert cache_instance.get(key) == value1

    # Overwrite without TTL
    cache_instance.set(key, value2)
    assert cache_instance.get(key) == value2  # Value updated

    time.sleep(ttl_seconds + 0.05)  # Wait past original TTL

    # Should still exist because TTL was removed
    assert cache_instance.get(key) == value2


def test_ttl_set_with_ttl_overwrites_no_ttl(cache_instance):
    """Test that setting a key with TTL overwrites a previous non-TTL entry."""
    key = 'add_ttl_key'
    value1 = 'permanent'
    value2 = 'expiring'
    ttl_seconds = 0.1

    cache_instance.set(key, value1)  # No TTL initially
    assert cache_instance.get(key) == value1

    # Overwrite with TTL
    cache_instance.set(key, value2, ttl=ttl_seconds)
    assert cache_instance.get(key) == value2  # Value updated

    time.sleep(ttl_seconds + 0.05)  # Wait past new TTL

    # Should have expired
    assert cache_instance.get(key) is None


def test_different_data_types(cache_instance):
    """Test storing various data types."""
    cache_instance.set('string_key', 'hello')
    cache_instance.set('int_key', 123)
    cache_instance.set('float_key', 45.67)
    cache_instance.set('bool_key', True)
    cache_instance.set('list_key', [1, 2, 3])
    cache_instance.set('dict_key', {'a': 1, 'b': 2})
    cache_instance.set('none_key', None)

    assert cache_instance.get('string_key') == 'hello'
    assert cache_instance.get('int_key') == 123
    assert cache_instance.get('float_key') == 45.67
    assert cache_instance.get('bool_key') is True
    assert cache_instance.get('list_key') == [1, 2, 3]
    assert cache_instance.get('dict_key') == {'a': 1, 'b': 2}
    assert cache_instance.get('none_key') is None


# --- Thread Safety Tests ---


def test_singleton_in_threads():
    """Verify singleton pattern holds when accessed from multiple threads."""
    instances: list[InMemoryCache] = []
    num_threads = 5

    def get_instance():
        instance = InMemoryCache()
        instances.append(instance)

    threads = [
        threading.Thread(target=get_instance) for _ in range(num_threads)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(instances) == num_threads
    first_instance_id = id(instances[0])
    for instance in instances:
        assert id(instance) == first_instance_id


def test_concurrent_set_get_different_keys(cache_instance):
    """
    Test basic thread safety: multiple threads setting/getting *different* keys.
    This tests the data lock mechanism under concurrent access.
    """
    num_threads = 10
    keys_values = {f'thread_key_{i}': f'value_{i}' for i in range(num_threads)}

    def worker(key, value):
        cache_instance.set(key, value)
        retrieved = cache_instance.get(key)
        assert retrieved == value  # Assert within thread for immediate feedback

    threads = [
        threading.Thread(target=worker, args=(k, v))
        for k, v in keys_values.items()
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Final verification in main thread
    for k, v in keys_values.items():
        assert cache_instance.get(k) == v
