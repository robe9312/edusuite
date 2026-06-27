import time
from functools import wraps


class TTLCache:
    def __init__(self, ttl_seconds=300):
        self._data = {}
        self._ttl = ttl_seconds

    def get(self, key):
        entry = self._data.get(key)
        if entry is None:
            return None
        val, ts = entry
        if time.monotonic() - ts > self._ttl:
            del self._data[key]
            return None
        return val

    def set(self, key, value):
        self._data[key] = (value, time.monotonic())

    def invalidate(self, key=None):
        if key is None:
            self._data.clear()
        else:
            self._data.pop(key, None)

    def __contains__(self, key):
        return self.get(key) is not None


class CacheManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.subjects = TTLCache(600)
            cls._instance.courses = TTLCache(600)
            cls._instance.students = TTLCache(300)
            cls._instance.teachers = TTLCache(600)
            cls._instance.roles = TTLCache(600)
            cls._instance.grades = TTLCache(60)
        return cls._instance

    def invalidate_all(self):
        for attr in vars(self).values():
            if isinstance(attr, TTLCache):
                attr.invalidate()

    def invalidate_grades(self):
        self.grades.invalidate()


def cached(cache_attr, key_fn):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            cm = CacheManager()
            cache = getattr(cm, cache_attr)
            key = key_fn(*args, **kwargs)
            cached_val = cache.get(key)
            if cached_val is not None:
                return cached_val
            result = fn(*args, **kwargs)
            cache.set(key, result)
            return result
        return wrapper
    return decorator
