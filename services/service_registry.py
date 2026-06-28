from __future__ import annotations
from typing import Optional


class ServiceRegistry:
    _instance: Optional["ServiceRegistry"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._services = {}
        return cls._instance

    def register(self, name: str, service) -> None:
        self._services[name] = service

    def get(self, name: str, default=None):
        return self._services.get(name, default)

    @classmethod
    def instance(cls) -> "ServiceRegistry":
        return cls()

    def statistics(self):
        return self._services.get("statistics")

    def spreadsheet(self):
        return self._services.get("spreadsheet")

    def document(self):
        return self._services.get("document")
