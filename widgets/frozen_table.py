from PySide6.QtWidgets import QTableView, QHeaderView, QWidget, QHBoxLayout
from PySide6.QtCore import Qt

from config import COLOR_PANEL, COLOR_SURFACE, COLOR_BORDER, COLOR_TEXT, COLOR_TEXT_MUTED


class FrozenTableView(QWidget):
    def __init__(self, model=None, frozen_count=3):
        super().__init__()
        self._frozen_count = frozen_count
        self._model = model
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.frozen_table = QTableView()
        self.frozen_table.setModel(self._model)
        self.frozen_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.frozen_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.frozen_table.setSelectionBehavior(QTableView.SelectItems)
        self.frozen_table.setSelectionMode(QTableView.SingleSelection)
        self.frozen_table.setFocusPolicy(Qt.NoFocus)
        self.frozen_table.setStyleSheet(f"""
            QTableView {{
                background: {COLOR_PANEL}; border: none;
                border-right: 2px solid {COLOR_BORDER};
                font-size: 12px;
                outline: none;
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
        self.main_table.setModel(self._model)
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

        hh = self.main_table.horizontalHeader()
        hh.setStretchLastSection(False)
        hh.setSectionResizeMode(QHeaderView.Interactive)

        vh_main = self.main_table.verticalHeader()
        vh_main.setDefaultSectionSize(32)
        vh_main.setVisible(False)

        vh_frozen = self.frozen_table.verticalHeader()
        vh_frozen.setDefaultSectionSize(32)
        vh_frozen.setVisible(False)

        for c in range(self._frozen_count):
            self.frozen_table.setColumnHidden(c, False)
            widths = [90, 200, 80]
            self.frozen_table.setColumnWidth(c, widths[c])
            self.main_table.setColumnHidden(c, True)

        layout.addWidget(self.frozen_table)
        layout.addWidget(self.main_table, 1)

        self.main_table.verticalScrollBar().valueChanged.connect(
            self.frozen_table.verticalScrollBar().setValue
        )
        self.frozen_table.verticalScrollBar().valueChanged.connect(
            self.main_table.verticalScrollBar().setValue
        )

    def main_view(self):
        return self.main_table

    def setModel(self, model):
        self._model = model
        self.frozen_table.setModel(model)
        self.main_table.setModel(model)
        for c in range(self._frozen_count):
            self.frozen_table.setColumnHidden(c, False)
            self.main_table.setColumnHidden(c, True)

    def model(self):
        return self._model

    def update_geometry(self):
        self.frozen_table.setFixedWidth(
            sum(self.frozen_table.columnWidth(c) for c in range(self._frozen_count))
            + self.frozen_table.verticalHeader().width()
        )
