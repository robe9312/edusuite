import json
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QTabBar, QStackedWidget, QScrollArea,
)
from config import (
    COLOR_BG, COLOR_SURFACE, COLOR_PANEL, COLOR_BORDER,
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_ACCENT, COLOR_ACCENT_HOVER,
)


def _parse_sheet(sheet):
    rows = []
    grid = {}
    max_c = 0
    max_r = 0

    celldata = sheet.get("celldata")
    if isinstance(celldata, list) and len(celldata) > 0:
        for cell in celldata:
            r, c = cell["r"], cell["c"]
            v = cell.get("v", {})
            grid[(r, c)] = v
            if r > max_r: max_r = r
            if c > max_c: max_c = c
    else:
        data = sheet.get("data")
        if isinstance(data, list) and len(data) > 0:
            for r, row in enumerate(data):
                if not isinstance(row, list): continue
                for c, cell in enumerate(row):
                    if cell is not None:
                        d = cell if isinstance(cell, dict) else {"v": cell, "m": str(cell)}
                        grid[(r, c)] = d
                        if r > max_r: max_r = r
                        if c > max_c: max_c = c

    if not grid:
        return [], 0, 0

    for r in range(max_r + 1):
        row_data = []
        max_col_found = max_c
        for c in range(max_col_found + 1):
            cell = grid.get((r, c))
            if cell is not None:
                m = cell.get("m", cell.get("v", ""))
                row_data.append(str(m) if m is not None else "")
            else:
                row_data.append("")
        rows.append(row_data)

    return rows, max_r + 1, max_c + 1


class SheetTable(QTableWidget):
    def __init__(self, rows, parent=None):
        super().__init__(parent)
        if not rows:
            return
        self.setRowCount(len(rows) - 1)
        self.setColumnCount(len(rows[0]) if rows else 0)
        self.setHorizontalHeaderLabels(rows[0] if rows else [])
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setAlternatingRowColors(True)
        self.setStyleSheet(f"""
            QTableWidget {{
                background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER};
                border-radius: 8px; gridline-color: {COLOR_BORDER};
                color: {COLOR_TEXT}; font-size: 13px;
            }}
            QTableWidget::item {{ padding: 6px 10px; }}
            QHeaderView::section {{
                background: {COLOR_PANEL}; color: {COLOR_TEXT};
                font-weight: 600; padding: 8px; border: none;
                border-bottom: 1px solid {COLOR_BORDER};
            }}
        """)
        for i in range(1, len(rows)):
            for j in range(len(rows[i])):
                item = QTableWidgetItem(rows[i][j])
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.setItem(i - 1, j, item)


class WorkbookRenderView(QWidget):
    edit_requested = Signal(str)
    delete_requested = Signal(str)

    def __init__(self, section, parent=None):
        super().__init__(parent)
        self.section = section
        self.sheets = []

        try:
            wb_json = section.get("workbook_json")
            if wb_json:
                self.sheets = json.loads(wb_json) if isinstance(wb_json, str) else wb_json
        except (json.JSONDecodeError, TypeError):
            self.sheets = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        toolbar = self._build_toolbar()
        layout.addWidget(toolbar)

        if not self.sheets:
            empty = QLabel("Esta seccion no tiene datos de workbook")
            empty.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px; padding: 40px;")
            empty.setAlignment(Qt.AlignCenter)
            layout.addWidget(empty)
            return

        self.stack = QStackedWidget()
        for s in self.sheets:
            parsed, _, _ = _parse_sheet(s)
            table = SheetTable(parsed, self)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(table)
            scroll.setStyleSheet(f"QScrollArea {{ border: none; background: transparent; }}")
            self.stack.addWidget(scroll)

        layout.addWidget(self.stack)

        if len(self.sheets) > 1:
            self.tabs = QTabBar()
            self.tabs.setStyleSheet(f"""
                QTabBar {{
                    background: {COLOR_PANEL}; border: none; border-radius: 6px;
                    padding: 2px;
                }}
                QTabBar::tab {{
                    padding: 6px 16px; color: {COLOR_TEXT_MUTED};
                    font-size: 12px; border: none; border-radius: 4px;
                    margin: 2px;
                }}
                QTabBar::tab:selected {{
                    background: {COLOR_SURFACE}; color: {COLOR_TEXT};
                    font-weight: 600;
                }}
            """)
            for s in self.sheets:
                self.tabs.addTab(s.get("name", "Sheet"))
            self.tabs.currentChanged.connect(self.stack.setCurrentIndex)
            layout.addWidget(self.tabs)

    def _build_toolbar(self):
        bar = QFrame()
        bar.setStyleSheet(f"QFrame {{ background: {COLOR_PANEL}; border-radius: 8px; }}")
        h = QHBoxLayout(bar)
        h.setContentsMargins(16, 8, 16, 8)

        sec = self.section
        color = sec.get("color", "#5e81f4")
        icon = sec.get("icon", "📄")

        dot = QLabel()
        dot.setFixedSize(12, 12)
        dot.setStyleSheet(f"background: {color}; border-radius: 6px;")
        h.addWidget(dot)

        title = QLabel(f"{icon} {sec.get('name', 'Seccion')}")
        title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {COLOR_TEXT};")
        h.addWidget(title)

        stype = sec.get("type", "spreadsheet")
        type_badge = QLabel(stype)
        type_badge.setStyleSheet(f"""
            background: {color}33; color: {color};
            font-size: 11px; padding: 2px 10px; border-radius: 10px;
            font-weight: 600;
        """)
        h.addWidget(type_badge)

        desc = sec.get("description", "")
        if desc:
            d = QLabel(desc)
            d.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
            h.addWidget(d)

        h.addStretch()

        sheet_count = QLabel(f"{len(self.sheets)} hoja(s)")
        sheet_count.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px; margin-right: 8px;")
        h.addWidget(sheet_count)

        btn = QPushButton("Editar en LuckySheet")
        btn.setStyleSheet(f"""
            QPushButton {{ padding: 0 16px; height: 34px; border: none;
                background: {COLOR_ACCENT}; color: #fff; font-size: 13px; border-radius: 6px;
                font-weight: 600; }}
            QPushButton:hover {{ background: {COLOR_ACCENT_HOVER}; }}
        """)
        btn.clicked.connect(lambda: self.edit_requested.emit(sec.get("section_key", "")))
        h.addWidget(btn)

        btn_del = QPushButton("Eliminar")
        btn_del.setStyleSheet("""
            QPushButton { padding: 0 12px; height: 34px; border: none;
                background: transparent; color: #ef4444; font-size: 12px; border-radius: 6px; }
            QPushButton:hover { background: #2a1a1a; }
        """)
        btn_del.clicked.connect(lambda: self.delete_requested.emit(sec.get("section_key", "")))
        h.addWidget(btn_del)

        return bar
