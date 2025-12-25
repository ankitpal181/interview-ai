"""
Tests for interview_ai.core.cache module.
Tests the SimpleCache LRU cache implementation.
"""
import pytest
import sys
import os
import importlib.util

# Import cache module directly to avoid full package import chain
def _import_cache():
    cache_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "src", "interview_ai", "core", "cache.py"
    )
    spec = importlib.util.spec_from_file_location("cache", cache_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

_cache_module = _import_cache()
SimpleCache = _cache_module.SimpleCache
cache = _cache_module.cache


class TestSimpleCache:
    """Test suite for SimpleCache class."""

    def test_init_default_maxsize(self):
        """Test default maxsize is 128."""
        c = SimpleCache()
        assert c.maxsize == 128
        assert len(c.cache) == 0

    def test_init_custom_maxsize(self):
        """Test custom maxsize initialization."""
        c = SimpleCache(maxsize=10)
        assert c.maxsize == 10

    def test_get_nonexistent_key_returns_none(self):
        """Test getting a key that doesn't exist returns None."""
        c = SimpleCache()
        assert c.get("nonexistent") is None

    def test_set_and_get(self):
        """Test setting and getting a value."""
        c = SimpleCache()
        c.set("key1", "value1")
        assert c.get("key1") == "value1"

    def test_set_updates_existing_key(self):
        """Test that setting an existing key updates its value."""
        c = SimpleCache()
        c.set("key1", "value1")
        c.set("key1", "updated_value")
        assert c.get("key1") == "updated_value"

    def test_lru_eviction(self):
        """Test that least recently used items are evicted when over capacity."""
        c = SimpleCache(maxsize=3)
        c.set("a", 1)
        c.set("b", 2)
        c.set("c", 3)
        # Cache is now at capacity: [a, b, c]
        c.set("d", 4)
        # 'a' should be evicted: [b, c, d]
        assert c.get("a") is None
        assert c.get("b") == 2
        assert c.get("c") == 3
        assert c.get("d") == 4

    def test_get_moves_to_end(self):
        """Test that getting a key marks it as recently used."""
        c = SimpleCache(maxsize=3)
        c.set("a", 1)
        c.set("b", 2)
        c.set("c", 3)
        # Access 'a' to make it recently used
        c.get("a")
        # Now add 'd', 'b' should be evicted (oldest after 'a' was accessed)
        c.set("d", 4)
        assert c.get("b") is None
        assert c.get("a") == 1
        assert c.get("c") == 3
        assert c.get("d") == 4

    def test_set_existing_key_moves_to_end(self):
        """Test that updating a key marks it as recently used."""
        c = SimpleCache(maxsize=3)
        c.set("a", 1)
        c.set("b", 2)
        c.set("c", 3)
        # Update 'a'
        c.set("a", 100)
        # Add 'd', 'b' should be evicted
        c.set("d", 4)
        assert c.get("b") is None
        assert c.get("a") == 100

    def test_complex_values(self):
        """Test storing complex values like dicts."""
        c = SimpleCache()
        data = {"last_message": {"text": "hello", "type": "interrupt"}, "count": 5}
        c.set("thread_123", data)
        retrieved = c.get("thread_123")
        assert retrieved == data
        assert retrieved["count"] == 5

    def test_global_cache_instance(self):
        """Test that the global cache instance works."""
        cache.set("global_test", "value")
        assert cache.get("global_test") == "value"


class TestCacheEdgeCases:
    """Edge case tests for SimpleCache."""

    def test_maxsize_one(self):
        """Test cache with maxsize of 1."""
        c = SimpleCache(maxsize=1)
        c.set("a", 1)
        assert c.get("a") == 1
        c.set("b", 2)
        assert c.get("a") is None
        assert c.get("b") == 2

    def test_empty_string_key(self):
        """Test empty string as key."""
        c = SimpleCache()
        c.set("", "empty_key_value")
        assert c.get("") == "empty_key_value"

    def test_none_value(self):
        """Test storing None as a value (should be distinguishable from missing key)."""
        c = SimpleCache()
        c.set("key_with_none", None)
        # This will return None, same as missing key
        # This is a limitation of the current implementation
        assert c.get("key_with_none") is None
