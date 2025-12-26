from collections import OrderedDict
from typing import Any


class SimpleCache:
    """Simple LRU Cache implementation"""

    def __init__(self, maxsize: int = 128) -> None:
        """
        Initialize the cache with a maximum size.

        Args:
            maxsize (int, optional): Maximum size of the cache. Defaults to 128.

        Returns:
            None
        """
        self.cache = OrderedDict()
        self.maxsize = maxsize

    def get(self, key: str) -> str | None:
        """
        Get the value for a given key from the cache.

        Args:
            key (str): Key to retrieve the value for.

        Returns:
            str | None: Value associated with the key, or None if the key is not in the cache.
        """
        if key not in self.cache: return None

        # Move to end to mark as "Recently Used"
        self.cache.move_to_end(key)
        return self.cache[key]

    def set(self, key: str, value: str | dict | Any) -> None:
        """
        Set the value for a given key in the cache.

        Args:
            key (str): Key to set the value for.
            value (str | dict | Any): Value to set for the key.

        Returns:
            None
        """
        if key in self.cache:
            self.cache.move_to_end(key)

        self.cache[key] = value
        
        # Evict oldest if over capacity
        if len(self.cache) > self.maxsize:
            self.cache.popitem(last=False)

cache = SimpleCache()
