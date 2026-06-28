from __future__ import annotations
from typing import List, Optional, Callable
from .command import Command


class UndoEngine:
    def __init__(self, max_stack: int = 100):
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []
        self._max_stack = max_stack
        self._listeners: List[Callable] = []

    def execute(self, cmd: Command) -> None:
        cmd.execute()
        self._undo_stack.append(cmd)
        if len(self._undo_stack) > self._max_stack:
            self._undo_stack.pop(0)
        self._redo_stack.clear()
        self._notify()

    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        cmd = self._undo_stack.pop()
        cmd.undo()
        self._redo_stack.append(cmd)
        self._notify()
        return True

    def redo(self) -> bool:
        if not self._redo_stack:
            return False
        cmd = self._redo_stack.pop()
        cmd.redo()
        self._undo_stack.append(cmd)
        self._notify()
        return True

    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    def undo_text(self) -> str:
        return self._undo_stack[-1].description if self._undo_stack else ""

    def redo_text(self) -> str:
        return self._redo_stack[-1].description if self._redo_stack else ""

    def clear(self) -> None:
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._notify()

    def on_change(self, listener: Callable) -> None:
        self._listeners.append(listener)

    def _notify(self) -> None:
        for listener in self._listeners:
            listener()
