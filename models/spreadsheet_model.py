from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QTimer
from PySide6.QtGui import QColor, QUndoStack

from config import heatmap_color, heatmap_text_color, COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_PANEL, COLOR_BORDER
from models.column_definition import ColumnDef, ColumnType


class SpreadsheetTableModel(QAbstractTableModel):
    def __init__(self, columns, data_rows, formula_fn=None, load_cell_fn=None,
                 save_cell_fn=None, undo_stack=None, repo=None):
        super().__init__()
        self._columns = columns
        self._rows = data_rows
        self._formula_fn = formula_fn or (lambda col_id, row: None)
        self._load_cell_fn = load_cell_fn or (lambda row_id, col: None)
        self._save_cell_fn = save_cell_fn
        self._data = {}
        self._dirty = set()
        self._undo_stack = undo_stack or QUndoStack()
        self._repo = repo
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(800)
        self._save_timer.timeout.connect(self._flush_dirty)
        self._load_data()

    def _load_data(self):
        for ri, row in enumerate(self._rows):
            row_id = row.get("id", ri)
            self._data[row_id] = {}
            for col in self._columns:
                if col.col_type in (ColumnType.FROZEN, ColumnType.TEXT):
                    continue
                if col.col_type == ColumnType.GRADE or col.col_type == ColumnType.COMPUTED:
                    val = self._load_cell_fn(row_id, col)
                    if val is not None:
                        self._data[row_id][col.id] = val

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._columns)

    def _column(self, col):
        if 0 <= col < len(self._columns):
            return self._columns[col]
        return None

    def _row(self, row):
        if 0 <= row < len(self._rows):
            return self._rows[row]
        return None

    def _get_value(self, row, col):
        cdef = self._column(col)
        if not cdef:
            return None
        row_data = self._row(row)
        if not row_data:
            return None
        if cdef.col_type == ColumnType.FROZEN or cdef.col_type == ColumnType.TEXT:
            return row_data.get(cdef.id, "")
        if cdef.col_type == ColumnType.COMPUTED:
            if cdef.formula == "avg":
                return self._compute_avg(row, cdef)
            if self._formula_fn:
                return self._formula_fn(cdef.id, row)
            return None
        if cdef.col_type == ColumnType.STATUS:
            return self._compute_status(row, cdef)
        row_id = row_data.get("id", row)
        return self._data.get(row_id, {}).get(cdef.id)

    def _compute_avg(self, row, col_def):
        row_data = self._row(row)
        if not row_data:
            return None
        row_id = row_data.get("id", row)
        vals = []
        group = col_def.group
        for c in self._columns:
            if c.group == group and c.col_type == ColumnType.GRADE:
                v = self._data.get(row_id, {}).get(c.id)
                if v is not None:
                    vals.append(v)
        return round(sum(vals) / len(vals), 1) if vals else None

    def _compute_status(self, row, col_def):
        avg = self._compute_avg(row, col_def)
        if avg is None:
            return "—"
        return "✔" if avg >= 5.0 else "✖"

    def _group_vals(self, group, row_id):
        vals = []
        for c in self._columns:
            if c.group == group and c.col_type == ColumnType.GRADE:
                v = self._data.get(row_id, {}).get(c.id)
                if v is not None:
                    vals.append(v)
        return vals

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row, col = index.row(), index.column()
        cdef = self._column(col)
        if not cdef:
            return None
        row_data = self._row(row)
        if not row_data:
            return None

        if role == Qt.DisplayRole or role == Qt.EditRole:
            return self._get_value(row, col)

        if role == Qt.TextAlignmentRole:
            return {"left": Qt.AlignLeft | Qt.AlignVCenter,
                    "right": Qt.AlignRight | Qt.AlignVCenter}.get(
                cdef.align, Qt.AlignCenter)

        if role == Qt.ForegroundRole:
            if cdef.frozen:
                return QColor(COLOR_TEXT)
            if cdef.heatmap:
                val = self._get_value(row, col)
                return QColor(heatmap_text_color(val))
            return QColor(COLOR_TEXT)

        if role == Qt.BackgroundRole:
            if cdef.frozen:
                return QColor(COLOR_PANEL)
            if cdef.heatmap:
                val = self._get_value(row, col)
                return QColor(heatmap_color(val))
            return QColor(COLOR_PANEL)

        if role == Qt.UserRole:
            return cdef.meta if cdef.meta else None

        if role == Qt.ToolTipRole:
            return cdef.tooltip if cdef.tooltip else cdef.name

        return None

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole:
            return False
        row, col = index.row(), index.column()
        cdef = self._column(col)
        if not cdef or not cdef.editable:
            return False
        row_data = self._row(row)
        if not row_data:
            return False
        try:
            val = float(value)
            if val < cdef.valid_min or val > cdef.valid_max:
                return False
        except (ValueError, TypeError):
            return False
        row_id = row_data.get("id", row)
        old_val = self._data.get(row_id, {}).get(cdef.id)
        if old_val == val:
            return False

        if self._undo_stack:
            from core.undo_commands import SetCellCommand
            cmd = SetCellCommand(cdef.id, row_id, val, old_val, model=self, repo=self._repo)
            self._undo_stack.push(cmd)
        else:
            self._data.setdefault(row_id, {})[cdef.id] = val
            self._mark_dirty(row_id, cdef.id)
            self.dataChanged.emit(index, index)
            self._update_computed(row, col)
        return True

    def _mark_dirty(self, row_id, col_id):
        self._dirty.add((row_id, col_id))
        self._save_timer.start()

    def _flush_dirty(self):
        if not self._dirty:
            return
        if self._save_cell_fn:
            for row_id, col_id in list(self._dirty):
                val = self._data.get(row_id, {}).get(col_id)
                self._save_cell_fn(row_id, col_id, val)
        self._dirty.clear()

    def dirty_count(self):
        return len(self._dirty)

    def save_dirty(self):
        if self._save_timer.isActive():
            self._save_timer.stop()
        self._flush_dirty()

    def _update_computed(self, row, edited_col):
        cdef = self._column(edited_col)
        if not cdef:
            return
        group = cdef.group
        n = self.columnCount()
        top_l = self.index(row, 0)
        bot_r = self.index(row, n - 1)
        self.dataChanged.emit(top_l, bot_r)

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        cdef = self._column(index.column())
        if not cdef:
            return Qt.NoItemFlags
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if cdef.editable:
            flags |= Qt.ItemIsEditable
        return flags

    def sort(self, column, order=Qt.AscendingOrder):
        cdef = self._column(column)
        if not cdef:
            return
        if cdef.frozen or cdef.col_type == ColumnType.FROZEN:
            key_fn = lambda r: str(r.get(cdef.id, ""))
        else:
            def key_fn(r):
                row_id = r.get("id", 0)
                val = self._data.get(row_id, {}).get(cdef.id)
                return val if val is not None else -1
        reverse = order == Qt.DescendingOrder
        self.beginResetModel()
        self._rows.sort(key=key_fn, reverse=reverse)
        self.endResetModel()

    def columns(self):
        return self._columns

    def columns_for_group(self, group):
        return [c for c in self._columns if c.group == group]

    def get_row_data(self, row):
        return self._row(row)

    def update_cell(self, row_id, col_id, value):
        if row_id in self._data:
            self._data[row_id][col_id] = value
            self._mark_dirty(row_id, col_id)
