from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from PySide6.QtGui import QColor, QFont

from .readonly_policy import ReadOnlyPolicy
from .style_renderer import StyleRenderer


class SpreadsheetModel(QAbstractTableModel):
    """
    Modelo Qt puro (Model/View) para un sheet del Workbook.

    Cada celda es un dict Luckysheet: {v, m, f, bg, fc, bl, it, fs, ff, ht, vt, ...}.
    Expone DisplayRole, FontRole, ForegroundRole, BackgroundRole,
    TextAlignmentRole y EditRole.
    """

    cellEdited = Signal(int, int, object)

    def __init__(
        self,
        rows: int,
        cols: int,
        celldata_index: Dict[Tuple[int, int], Dict[str, Any]],
        styles: Optional[StyleRenderer] = None,
        sheet_index: int = 0,
        parent=None,
    ):
        super().__init__(parent)
        self._rows = rows
        self._cols = cols
        self._index = celldata_index
        self._styles = styles or StyleRenderer()
        self.sheet_index = sheet_index

    # -----------------------------------------------------------------
    # QAbstractTableModel interface
    # -----------------------------------------------------------------

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return self._rows if not parent.isValid() else 0

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return self._cols if not parent.isValid() else 0

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return None
        cell = self._index.get((index.row(), index.column()))
        if cell is None:
            return None

        if role == Qt.DisplayRole:
            return self._styles.display_value(cell)

        if role == Qt.FontRole:
            return self._styles.cell_font(cell)

        if role == Qt.ForegroundRole:
            return self._styles.cell_foreground(cell)

        if role == Qt.BackgroundRole:
            return self._styles.cell_background(cell)

        if role == Qt.TextAlignmentRole:
            return int(self._styles.cell_alignment(cell))

        if role == Qt.ToolTipRole:
            return self._styles.display_value(cell)

        return None

    def setData(
        self, index: QModelIndex, value: Any, role: int = Qt.EditRole
    ) -> bool:
        if role == Qt.EditRole and index.isValid():
            r, c = index.row(), index.column()
            text = str(value) if value is not None else ""
            self._index[(r, c)] = {"v": text, "m": text}
            self.dataChanged.emit(index, index, [Qt.DisplayRole])
            self.cellEdited.emit(r, c, value)
            return True
        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.NoItemFlags
        cell = self._index.get((index.row(), index.column()))
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if ReadOnlyPolicy.is_editable(cell):
            flags |= Qt.ItemIsEditable
        return flags

    # -----------------------------------------------------------------
    # Public helpers
    # -----------------------------------------------------------------

    def cell_at(self, row: int, col: int) -> Optional[Dict[str, Any]]:
        return self._index.get((row, col))

    def update_cells(self, cells: List[Dict[str, Any]]) -> None:
        if not cells:
            return
        min_r = max_r = cells[0].get("r", 0)
        min_c = max_c = cells[0].get("c", 0)
        for cell in cells:
            r = cell.get("r")
            c = cell.get("c")
            v = cell.get("v")
            if r is None or c is None:
                continue
            if not isinstance(v, dict):
                v = {"v": v}
            self._index[(r, c)] = v
            if r < min_r: min_r = r
            if r > max_r: max_r = r
            if c < min_c: min_c = c
            if c > max_c: max_c = c
        top_left = self.createIndex(min_r, min_c)
        bottom_right = self.createIndex(max_r, max_c)
        self.dataChanged.emit(
            top_left, bottom_right,
            [
                Qt.DisplayRole, Qt.FontRole, Qt.ForegroundRole,
                Qt.BackgroundRole, Qt.TextAlignmentRole,
            ],
        )
