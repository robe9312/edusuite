from __future__ import annotations
from typing import Any, Optional


class SpreadsheetDelegate:
    def create_editor(self, row: int, col: int, value: Any) -> "QWidget":
        return None

    def set_editor_data(self, editor: "QWidget", value: Any) -> None:
        pass

    def get_editor_data(self, editor: "QWidget") -> Any:
        return None

    def paint(self, painter: "QPainter", rect: "QRect",
              value: Any, selected: bool, editing: bool) -> None:
        pass
