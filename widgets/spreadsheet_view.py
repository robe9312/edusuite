from PySide6.QtWidgets import QTableView, QHeaderView, QWidget, QHBoxLayout, QAbstractItemView
from PySide6.QtCore import Qt, QModelIndex

from config import COLOR_PANEL, COLOR_SURFACE, COLOR_BORDER, COLOR_TEXT, COLOR_TEXT_MUTED
from models.column_definition import ColumnType


class SpreadsheetView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = None
        self._frozen_cols = []
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.frozen_table = QTableView()
        self.frozen_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.frozen_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.frozen_table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.frozen_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.frozen_table.setFocusPolicy(Qt.NoFocus)
        self.frozen_table.setStyleSheet(f"""
            QTableView {{
                background: {COLOR_PANEL}; border: none;
                border-right: 2px solid {COLOR_BORDER};
                font-size: 12px; outline: none;
            }}
            QTableView::item {{
                border: none; border-bottom: 1px solid {COLOR_BORDER};
                padding: 4px 8px;
            }}
            QTableView::item:selected {{
                background: transparent; color: {COLOR_TEXT};
            }}
            QHeaderView::section {{
                background: {COLOR_SURFACE}; color: {COLOR_TEXT_MUTED};
                border: none; border-bottom: 1px solid {COLOR_BORDER};
                padding: 6px 8px; font-size: 11px; font-weight: 500;
            }}
        """)

        self.main_table = QTableView()
        self.main_table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.main_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.main_table.setStyleSheet(f"""
            QTableView {{
                background: {COLOR_PANEL}; border: 1px solid {COLOR_BORDER};
                font-size: 12px; outline: none;
            }}
            QTableView::item {{
                border: none; border-bottom: 1px solid {COLOR_BORDER};
                padding: 4px 6px;
            }}
            QTableView::item:selected {{
                background: transparent; color: {COLOR_TEXT};
            }}
            QHeaderView::section {{
                background: {COLOR_SURFACE}; color: {COLOR_TEXT_MUTED};
                border: none; border-bottom: 1px solid {COLOR_BORDER};
                padding: 6px 6px; font-size: 10px; font-weight: 500;
            }}
        """)

        for t in [self.main_table, self.frozen_table]:
            hh = t.horizontalHeader()
            hh.setStretchLastSection(False)
            hh.setSectionResizeMode(QHeaderView.Interactive)
            vh = t.verticalHeader()
            vh.setDefaultSectionSize(32)
            vh.setVisible(False)

        layout.addWidget(self.frozen_table)
        layout.addWidget(self.main_table, 1)

        self.main_table.verticalScrollBar().valueChanged.connect(
            self.frozen_table.verticalScrollBar().setValue)
        self.frozen_table.verticalScrollBar().valueChanged.connect(
            self.main_table.verticalScrollBar().setValue)

    def setModel(self, model):
        self._model = model
        self.main_table.setModel(model)
        self.frozen_table.setModel(model)
        self._apply_frozen()

    def model(self):
        return self._model

    def _apply_frozen(self):
        if not self._model:
            return
        src = self._model
        if hasattr(src, 'sourceModel') and callable(src.sourceModel):
            sm = src.sourceModel()
            if sm and hasattr(sm, 'columns'):
                src = sm
        cols = src.columns() if hasattr(src, 'columns') else []
        frozen_indices = [i for i, c in enumerate(cols) if c.frozen]
        self._frozen_cols = frozen_indices
        frozen_width = 0
        for i, c in enumerate(cols):
            hidden = i in frozen_indices
            self.frozen_table.setColumnHidden(i, not hidden)
            self.main_table.setColumnHidden(i, hidden)
            if hidden:
                self.frozen_table.setColumnWidth(i, c.width)
                frozen_width += c.width
            else:
                self.main_table.setColumnWidth(i, c.width)
        sb = self.frozen_table.verticalScrollBar()
        self.frozen_table.setFixedWidth(frozen_width + sb.sizeHint().width() + 2)
