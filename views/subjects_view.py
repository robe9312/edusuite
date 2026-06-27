from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QMessageBox,
    QFormLayout, QDialog, QFrame,
)
from PySide6.QtCore import Qt

from db.database import (
    save_subject, get_subject, get_all_subjects, update_subject,
    delete_subject, get_all_teachers, get_subject as db_get_subject,
)
from config import *
from ui_style import Input, Combo, Table, Header


class SubjectDialog(QDialog):
    def __init__(self, parent=None, subject_data=None):
        super().__init__(parent)
        self.subject_data = subject_data
        self.setWindowTitle("Editar Asignatura" if subject_data else "Nueva Asignatura")
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

        self.name_input = Input("Ej: Matematicas")
        lbl = QLabel("Nombre")
        lbl.setStyleSheet(ls)
        layout.addRow(lbl, self.name_input)

        self.level_input = Input("Ej: 1 (vacio = todos)")
        lbl = QLabel("Nivel")
        lbl.setStyleSheet(ls)
        layout.addRow(lbl, self.level_input)

        self.teacher_combo = Combo()
        self.teacher_combo.addItem("(Sin profesor)", None)
        teachers = get_all_teachers()
        for t in teachers:
            label = f"{t['name']} {t['last_name']} ({t['code']})"
            self.teacher_combo.addItem(label, t["id"])
        lbl = QLabel("Profesor")
        lbl.setStyleSheet(ls)
        layout.addRow(lbl, self.teacher_combo)

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

        if self.subject_data:
            self._populate()

    def _populate(self):
        d = self.subject_data
        self.name_input.setText(d.get("name", ""))
        self.level_input.setText(d.get("grade_level", ""))
        teacher_id = d.get("teacher_id")
        if teacher_id:
            for i in range(self.teacher_combo.count()):
                if self.teacher_combo.itemData(i) == teacher_id:
                    self.teacher_combo.setCurrentIndex(i)
                    break

    def _accept(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Campo requerido", "El nombre de la asignatura es obligatorio.")
            return
        self.data = {
            "name": name,
            "grade_level": self.level_input.text().strip(),
            "teacher_id": self.teacher_combo.currentData(),
        }
        self.accept()


class SubjectsView(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        h = Header("Asignaturas")
        layout.addWidget(h)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        toolbar.addStretch()

        add_btn = QPushButton("Nueva Asignatura")
        add_btn.setStyleSheet(f"""
            QPushButton {{ padding: 0 16px; height: 36px; border: none;
                background: {COLOR_ACCENT}; color: #ffffff; font-size: 13px; }}
            QPushButton:hover {{ background: {COLOR_ACCENT_HOVER}; }}
        """)
        add_btn.clicked.connect(self._add_subject)
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
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["NOMBRE", "NIVEL", "PROFESOR", "ACCIONES"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

    def _add_subject(self):
        dlg = SubjectDialog(self)
        if dlg.exec() == QDialog.Accepted:
            d = dlg.data
            try:
                save_subject(d["name"], d["grade_level"], d["teacher_id"])
                self.refresh()
                self.main.refresh_stats()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _edit_subject(self, subject_id):
        data = db_get_subject(subject_id)
        if not data:
            return
        dlg = SubjectDialog(self, data)
        if dlg.exec() == QDialog.Accepted:
            try:
                update_subject(subject_id, **dlg.data)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _delete_subject(self, subject_id, name):
        resp = QMessageBox.question(
            self, "Eliminar asignatura",
            f"Eliminar '{name}'? Tambien se borraran todas las notas asociadas.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            try:
                delete_subject(subject_id)
                self.refresh()
                self.main.refresh_stats()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _get_teacher_name(self, teacher_id):
        if not teacher_id:
            return ""
        from db.database import get_teacher
        t = get_teacher(teacher_id)
        return f"{t['name']} {t['last_name']}" if t else ""

    def _populate_table(self, subjects):
        self.table.setRowCount(len(subjects))
        for i, s in enumerate(subjects):
            self.table.setItem(i, 0, QTableWidgetItem(s.get("name", "")))
            self.table.setItem(i, 1, QTableWidgetItem(s.get("grade_level", "")))
            self.table.setItem(i, 2, QTableWidgetItem(self._get_teacher_name(s.get("teacher_id"))))

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
            edit_btn.clicked.connect(lambda checked, sid=s["id"]: self._edit_subject(sid))
            act_layout.addWidget(edit_btn)

            del_btn = QPushButton("X")
            del_btn.setFixedSize(28, 24)
            del_btn.setStyleSheet(f"""
                QPushButton {{ border: 1px solid {COLOR_BORDER};
                    background: transparent; color: {COLOR_DANGER}; font-size: 11px; }}
                QPushButton:hover {{ background: {COLOR_HOVER}; }}
            """)
            del_btn.clicked.connect(lambda checked, sid=s["id"], nm=s.get("name", ""): self._delete_subject(sid, nm))
            act_layout.addWidget(del_btn)

            act_layout.addStretch()
            self.table.setCellWidget(i, 3, actions)

    def refresh(self):
        subjects = get_all_subjects()
        self._populate_table(subjects)
