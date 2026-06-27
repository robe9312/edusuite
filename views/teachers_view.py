from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QMessageBox,
    QFormLayout, QDialog, QFrame,
)
from PySide6.QtCore import Qt

from db.database import (
    save_teacher, get_teacher, get_all_teachers, update_teacher,
    delete_teacher, teacher_code_exists,
)
from config import *
from ui_style import Input, Table, Header


class TeacherDialog(QDialog):
    def __init__(self, parent=None, teacher_data=None):
        super().__init__(parent)
        self.teacher_data = teacher_data
        self.setWindowTitle("Editar Profesor" if teacher_data else "Nuevo Profesor")
        self.setMinimumWidth(480)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background: {COLOR_SURFACE}; }}")
        self._build()

    def _build(self):
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setLabelAlignment(Qt.AlignRight)

        ls = f"color: {COLOR_TEXT_MUTED}; font-size: 12px;"

        self.code_input = Input("Ej: PROF-001")
        lbl = QLabel("Codigo")
        lbl.setStyleSheet(ls)
        layout.addRow(lbl, self.code_input)

        self.name_input = Input("Nombres")
        lbl = QLabel("Nombre(s)")
        lbl.setStyleSheet(ls)
        layout.addRow(lbl, self.name_input)

        self.lastname_input = Input("Apellidos")
        lbl = QLabel("Apellido(s)")
        lbl.setStyleSheet(ls)
        layout.addRow(lbl, self.lastname_input)

        self.specialty_input = Input("Ej: Matematicas")
        lbl = QLabel("Especialidad")
        lbl.setStyleSheet(ls)
        layout.addRow(lbl, self.specialty_input)

        btns = QHBoxLayout()
        save_btn = QPushButton("Guardar")
        save_btn.setStyleSheet(f"""
            QPushButton {{ padding: 0 24px; height: 36px; border: none;
                background: {COLOR_ACCENT}; color: #ffffff; font-size: 13px; }}
            QPushButton:hover {{ background: {COLOR_ACCENT_HOVER}; }}
        """)
        save_btn.clicked.connect(self._accept)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{ padding: 0 24px; height: 36px; border: none;
                background: transparent; color: {COLOR_TEXT_MUTED}; font-size: 13px; }}
            QPushButton:hover {{ background: {COLOR_HOVER}; }}
        """)
        cancel_btn.clicked.connect(self.reject)

        btns.addStretch()
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)
        layout.addRow(btns)

        if self.teacher_data:
            self._populate()

    def _populate(self):
        d = self.teacher_data
        self.code_input.setText(d.get("code", ""))
        self.name_input.setText(d.get("name", ""))
        self.lastname_input.setText(d.get("last_name", ""))
        self.specialty_input.setText(d.get("specialty", ""))

    def _accept(self):
        code = self.code_input.text().strip()
        name = self.name_input.text().strip()
        last_name = self.lastname_input.text().strip()
        if not code or not name or not last_name:
            QMessageBox.warning(self, "Campos requeridos", "Codigo, nombre y apellido son obligatorios.")
            return
        if not self.teacher_data and teacher_code_exists(code):
            QMessageBox.warning(self, "Codigo duplicado", f"El codigo '{code}' ya existe.")
            return
        self.data = {
            "code": code,
            "name": name,
            "last_name": last_name,
            "specialty": self.specialty_input.text().strip(),
        }
        self.accept()


class TeachersView(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        h = Header("Profesores")
        layout.addWidget(h)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        toolbar.addStretch()

        add_btn = QPushButton("Nuevo Profesor")
        add_btn.setStyleSheet(f"""
            QPushButton {{ padding: 0 16px; height: 36px; border: none;
                background: {COLOR_ACCENT}; color: #ffffff; font-size: 13px; }}
            QPushButton:hover {{ background: {COLOR_ACCENT_HOVER}; }}
        """)
        add_btn.clicked.connect(self._add_teacher)
        toolbar.addWidget(add_btn)

        refresh_btn = QPushButton("R")
        refresh_btn.setFixedSize(36, 36)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{ border: 1px solid {COLOR_BORDER};
                background: transparent; color: {COLOR_TEXT_MUTED}; font-size: 12px; }}
            QPushButton:hover {{ background: {COLOR_HOVER}; color: {COLOR_TEXT}; }}
        """)
        refresh_btn.clicked.connect(self.refresh)
        toolbar.addWidget(refresh_btn)

        layout.addLayout(toolbar)

        self.table = Table()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["CODIGO", "NOMBRE", "APELLIDO", "ESPECIALIDAD", "ACCIONES"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

    def _add_teacher(self):
        dlg = TeacherDialog(self)
        if dlg.exec() == QDialog.Accepted:
            d = dlg.data
            try:
                save_teacher(d["code"], d["name"], d["last_name"], d["specialty"])
                self.refresh()
                self.main.refresh_stats()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _edit_teacher(self, teacher_id):
        data = get_teacher(teacher_id)
        if not data:
            return
        dlg = TeacherDialog(self, data)
        if dlg.exec() == QDialog.Accepted:
            try:
                update_teacher(teacher_id, **dlg.data)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _delete_teacher(self, teacher_id, name):
        resp = QMessageBox.question(
            self, "Eliminar profesor",
            f"Eliminar a {name}? Las asignaturas asociadas qudaran sin profesor.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            try:
                delete_teacher(teacher_id)
                self.refresh()
                self.main.refresh_stats()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _populate_table(self, teachers):
        self.table.setRowCount(len(teachers))
        for i, t in enumerate(teachers):
            self.table.setItem(i, 0, QTableWidgetItem(t.get("code", "")))
            self.table.setItem(i, 1, QTableWidgetItem(t.get("name", "")))
            self.table.setItem(i, 2, QTableWidgetItem(t.get("last_name", "")))
            self.table.setItem(i, 3, QTableWidgetItem(t.get("specialty", "")))

            actions = QWidget()
            act_layout = QHBoxLayout(actions)
            act_layout.setContentsMargins(2, 0, 2, 0)
            act_layout.setSpacing(4)

            edit_btn = QPushButton("E")
            edit_btn.setFixedSize(28, 24)
            edit_btn.setStyleSheet(f"""
                QPushButton {{ border: 1px solid {COLOR_BORDER};
                    background: transparent; color: {COLOR_TEXT_MUTED}; font-size: 11px; }}
                QPushButton:hover {{ background: {COLOR_HOVER}; color: {COLOR_TEXT}; }}
            """)
            edit_btn.clicked.connect(lambda checked, tid=t["id"]: self._edit_teacher(tid))
            act_layout.addWidget(edit_btn)

            del_btn = QPushButton("X")
            del_btn.setFixedSize(28, 24)
            del_btn.setStyleSheet(f"""
                QPushButton {{ border: 1px solid {COLOR_BORDER};
                    background: transparent; color: {COLOR_DANGER}; font-size: 11px; }}
                QPushButton:hover {{ background: {COLOR_HOVER}; }}
            """)
            del_btn.clicked.connect(lambda checked, tid=t["id"], nm=t.get("name", ""): self._delete_teacher(tid, nm))
            act_layout.addWidget(del_btn)

            act_layout.addStretch()
            self.table.setCellWidget(i, 4, actions)

    def refresh(self):
        teachers = get_all_teachers()
        self._populate_table(teachers)
