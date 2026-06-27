from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtWidgets import QApplication


class ClipboardEngine:
    def __init__(self, spreadsheet_view):
        self._view = spreadsheet_view

    def copy(self):
        tables = [self._view.frozen_table, self._view.main_table]
        selection = None
        src_table = None
        for t in tables:
            sm = t.selectionModel()
            if sm and sm.hasSelection():
                selection = sm.selection()
                src_table = t
                break
        if not selection or not src_table:
            return
        model = src_table.model()
        if not model:
            return
        rows = selection[0].rows() if hasattr(selection[0], 'rows') else [selection[0]]
        top_row = min(idx.row() for idx in selection.indexes())
        bot_row = max(idx.row() for idx in selection.indexes())
        left_col = min(idx.column() for idx in selection.indexes())
        right_col = max(idx.column() for idx in selection.indexes())
        lines = []
        for r in range(top_row, bot_row + 1):
            cells = []
            for c in range(left_col, right_col + 1):
                idx = model.index(r, c)
                val = idx.data(Qt.DisplayRole)
                cells.append(str(val) if val is not None else "")
            lines.append("\t".join(cells))
        QApplication.clipboard().setText("\n".join(lines))

    def paste(self):
        text = QApplication.clipboard().text()
        if not text:
            return
        tables = [self._view.frozen_table, self._view.main_table]
        current = None
        for t in tables:
            if t.hasFocus():
                current = t
                break
        if not current:
            current = self._view.main_table
        idx = current.currentIndex()
        if not idx or not idx.isValid():
            return
        model = current.model()
        if not model:
            return
        start_row, start_col = idx.row(), idx.column()
        lines = text.split("\n")
        for ri, line in enumerate(lines):
            if not line.strip():
                continue
            cells = line.split("\t")
            for ci, val in enumerate(cells):
                r = start_row + ri
                c = start_col + ci
                if r >= model.rowCount() or c >= model.columnCount():
                    continue
                midx = model.index(r, c)
                if midx.flags() & Qt.ItemIsEditable:
                    model.setData(midx, val.strip(), Qt.EditRole)

    def cut(self):
        self.copy()
        tables = [self._view.frozen_table, self._view.main_table]
        for t in tables:
            sm = t.selectionModel()
            if sm and sm.hasSelection():
                for idx in sm.selectedIndexes():
                    if idx.flags() & Qt.ItemIsEditable:
                        t.model().setData(idx, "", Qt.EditRole)
                break

    def delete_selection(self):
        tables = [self._view.frozen_table, self._view.main_table]
        for t in tables:
            sm = t.selectionModel()
            if sm and sm.hasSelection():
                for idx in sm.selectedIndexes():
                    if idx.flags() & Qt.ItemIsEditable:
                        t.model().setData(idx, "", Qt.EditRole)
                break
