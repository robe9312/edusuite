import json
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QInputDialog, QFrame, QDialog, QLineEdit, QFormLayout,
    QDialogButtonBox,
)

from config import (
    COLOR_BG, COLOR_SURFACE, COLOR_PANEL, COLOR_BORDER,
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_ACCENT, COLOR_ACCENT_HOVER,
    COLOR_SUCCESS,
)
from db.database import (
    get_custom_section, get_custom_section_rows,
    add_custom_section_row, update_custom_section_row,
    delete_custom_section_row,
)


class RowEditDialog(QDialog):
    def __init__(self, columns, row_data=None, parent=None):
        super().__init__(parent)
        self.columns = columns
        self.fields = []

        self.setWindowTitle("Editar fila")
        self.setMinimumWidth(400)

        form = QFormLayout(self)

        for col in columns:
            name = col.get("name", "columna")
            edit = QLineEdit()
            if row_data and name in row_data:
                edit.setText(str(row_data[name]))
            form.addRow(name, edit)
            self.fields.append((name, edit))

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def get_data(self):
        return {name: w.text() for name, w in self.fields}


class CustomSectionView(QWidget):
    def __init__(self, section_key, parent=None):
        super().__init__(parent)
        self.section_key = section_key
        self.section = get_custom_section(section_key)
        self.columns = json.loads(self.section["columns_json"]) if self.section else []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        toolbar = QFrame()
        toolbar.setStyleSheet(f"QFrame {{ background: {COLOR_PANEL}; border-radius: 8px; }}")
        h = QHBoxLayout(toolbar)
        h.setContentsMargins(16, 8, 16, 8)

        title = QLabel(self.section["name"] if self.section else section_key)
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {COLOR_TEXT};")
        h.addWidget(title)

        h.addStretch()

        btn_add = QPushButton("+ Añadir fila")
        btn_add.setStyleSheet(f"""
            QPushButton {{ padding: 0 16px; height: 34px; border: none;
                background: {COLOR_SUCCESS}; color: #fff; font-size: 13px; border-radius: 6px; }}
            QPushButton:hover {{ background: #5a7e5a; }}
        """)
        btn_add.clicked.connect(self._add_row)
        h.addWidget(btn_add)

        btn_refresh = QPushButton("↻ Recargar")
        btn_refresh.setStyleSheet(f"""
            QPushButton {{ padding: 0 16px; height: 34px; border: none;
                background: {COLOR_ACCENT}; color: #fff; font-size: 13px; border-radius: 6px; }}
            QPushButton:hover {{ background: {COLOR_ACCENT_HOVER}; }}
        """)
        btn_refresh.clicked.connect(self.load_data)
        h.addWidget(btn_refresh)

        layout.addWidget(toolbar)

        self.table = QTableWidget()
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER};
                border-radius: 8px; gridline-color: {COLOR_BORDER};
                color: {COLOR_TEXT}; font-size: 13px;
            }}
            QTableWidget::item {{ padding: 8px; }}
            QHeaderView::section {{
                background: {COLOR_PANEL}; color: {COLOR_TEXT};
                font-weight: 600; padding: 8px; border: none;
                border-bottom: 1px solid {COLOR_BORDER};
            }}
        """)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        layout.addWidget(self.table)

        self.load_data()

    def load_data(self):
        section = get_custom_section(self.section_key)
        if not section:
            return
        self.section = section
        self.columns = json.loads(section["columns_json"])

        rows = get_custom_section_rows(section["id"])

        cols = len(self.columns) + 2
        self.table.setColumnCount(cols)
        headers = [c.get("name", "?") for c in self.columns] + ["Editar", "Eliminar"]
        self.table.setHorizontalHeaderLabels(headers)

        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            data = json.loads(row["row_data"])
            for j, col in enumerate(self.columns):
                val = data.get(col.get("name", ""), "")
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(i, j, item)

            btn_edit = QPushButton("✏️")
            btn_edit.setStyleSheet(f"border: none; font-size: 14px; background: transparent; color: {COLOR_ACCENT};")
            btn_edit.clicked.connect(lambda _, rid=row["id"], d=data: self._edit_row(rid, d))
            self.table.setCellWidget(i, cols - 2, btn_edit)

            btn_del = QPushButton("🗑️")
            btn_del.setStyleSheet("border: none; font-size: 14px; background: transparent; color: #ef4444;")
            btn_del.clicked.connect(lambda _, rid=row["id"]: self._delete_row(rid))
            self.table.setCellWidget(i, cols - 1, btn_del)

    def _add_row(self):
        dialog = RowEditDialog(self.columns, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            add_custom_section_row(self.section["id"], json.dumps(data))
            self.load_data()

    def _edit_row(self, row_id, current_data):
        dialog = RowEditDialog(self.columns, current_data, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            update_custom_section_row(row_id, json.dumps(data))
            self.load_data()

    def _delete_row(self, row_id):
        reply = QMessageBox.question(
            self, "Confirmar", "¿Eliminar esta fila?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            delete_custom_section_row(row_id)
            self.load_data()
