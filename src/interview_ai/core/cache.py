from collections import OrderedDict

class SimpleCache:
    def __init__(self, maxsize=128):
        self.cache = OrderedDict()
        self.maxsize = maxsize

    def get(self, key):
        if key not in self.cache:
            return None
        # Move to end to mark as "Recently Used"
        self.cache.move_to_end(key)
        return self.cache[key]

    def set(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        # Evict oldest if over capacity
        if len(self.cache) > self.maxsize:
            self.cache.popitem(last=False)

cache = SimpleCache()
