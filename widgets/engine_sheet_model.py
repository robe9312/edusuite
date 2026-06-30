from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QColor
from config import COLOR_TEXT


def active_area(grid):
    max_r = max_c = -1
    for r in range(grid.row_count()):
        for c in range(grid.col_count()):
            cell = grid.cell(r, c)
            val = cell.display if hasattr(cell, 'display') else str(cell)
            if val and val.strip():
                if r > max_r: max_r = r
                if c > max_c: max_c = c
    if max_r < 0:
        return 1, 1
    return max_r + 1, max_c + 1


class EngineSheetModel(QAbstractTableModel):
    def __init__(self, engine):
        super().__init__()
        self._engine = engine

    def rowCount(self, parent=QModelIndex()):
        return self._engine.row_count() if self._engine else 0

    def columnCount(self, parent=QModelIndex()):
        return self._engine.col_count() if self._engine else 0

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not self._engine:
            return None
        cell = self._engine.get_cell(index.row(), index.column())
        if cell is None:
            return None
        if role == Qt.DisplayRole:
            return cell.display if cell.display else None
        if role == Qt.ForegroundRole:
            return QColor(COLOR_TEXT)
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            from string import ascii_uppercase
            label = ""
            n = section
            while n >= 0:
                label = ascii_uppercase[n % 26] + label
                n = n // 26 - 1
            return label
        return str(section + 1)

    def refresh(self):
        self.beginResetModel()
        self.endResetModel()
