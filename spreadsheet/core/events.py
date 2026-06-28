from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class GridEvent:
    source: str = ""


@dataclass
class CellEvent(GridEvent):
    row: int = -1
    col: int = -1
    old_value: Any = None
    new_value: Any = None
    formula: Optional[str] = None


@dataclass
class RowEvent(GridEvent):
    index: int = -1
    count: int = 1


@dataclass
class ColumnEvent(GridEvent):
    index: int = -1
    count: int = 1


Listener = Callable[[GridEvent], None]


class EventBus:
    def __init__(self):
        self._listeners: Dict[str, List[Listener]] = {}

    def on(self, event_type: str, listener: Listener) -> None:
        self._listeners.setdefault(event_type, []).append(listener)

    def off(self, event_type: str, listener: Listener) -> None:
        self._listeners.get(event_type, []).remove(listener)

    def emit(self, event_type: str, event: GridEvent) -> None:
        for listener in self._listeners.get(event_type, []):
            listener(event)

    def clear(self) -> None:
        self._listeners.clear()
