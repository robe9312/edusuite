from __future__ import annotations
from typing import Optional
from .spreadsheet_view import SpreadsheetView


class FrozenView(SpreadsheetView):
    def __init__(self, main_view: SpreadsheetView, frozen_rows: int = 0, frozen_cols: int = 0):
        super().__init__()
        self._main_view = main_view
        self._frozen_rows = frozen_rows
        self._frozen_cols = frozen_cols

    @property
    def frozen_rows(self) -> int:
        return self._frozen_rows

    @property
    def frozen_cols(self) -> int:
        return self._frozen_cols

    def sync_selection(self) -> None:
        pass
