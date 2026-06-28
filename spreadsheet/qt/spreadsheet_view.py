from __future__ import annotations
from typing import Any, List, Optional


class SpreadsheetView:
    def __init__(self, model: "SpreadsheetModel" = None):
        self._model = model
        self._selection: List[tuple] = []
        self._editing: bool = False
        self._edit_row: int = -1
        self._edit_col: int = -1

    def set_model(self, model: "SpreadsheetModel") -> None:
        self._model = model

    def model(self) -> Optional["SpreadsheetModel"]:
        return self._model

    def select(self, row: int, col: int) -> None:
        self._selection = [(row, col)]

    def selected(self) -> List[tuple]:
        return self._selection

    def edit(self, row: int, col: int) -> None:
        self._editing = True
        self._edit_row = row
        self._edit_col = col

    def commit(self, value: Any) -> None:
        if self._editing and self._model:
            self._model.set_data(self._edit_row, self._edit_col, value, 0)
        self._editing = False

    def cancel(self) -> None:
        self._editing = False
