from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QLineEdit, QMessageBox,
    QFormLayout, QDialog, QFrame,
)
from PySide6.QtCore import Qt

from db.database import (
    save_student, get_student, get_all_students, update_student,
    deactivate_student, search_students, student_code_exists,
)
from config import *
from ui_style import Input, Combo, Table, Header, Button


class StudentDialog(QDialog):
    def __init__(self, parent=None, student_data=None):
        super().__init__(parent)
        self.student_data = student_data
        self.setWindowTitle("Editar Estudiante" if student_data else "Nuevo Estudiante")
        self.setMinimumWidth(520)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background: {COLOR_SURFACE}; }}")
        self._build()

    def _build(self):
        layout = QFormLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setLabelAlignment(Qt.AlignRight)

        ls = f"color: {COLOR_TEXT_MUTED}; font-size: 12px;"

        self.code_input = Input("Ej: A-001")
        lbl = QLabel("Codigo")
        lbl.setStyleSheet(ls)
        layout.addRow(lbl, self.code_input)

        self.fullname_input = Input("Nombre completo")
        lbl = QLabel("Nombre completo")
        lbl.setStyleSheet(ls)
        layout.addRow(lbl, self.fullname_input)

        sex_row = QHBoxLayout()
        self.sex_combo = Combo()
        self.sex_combo.addItems(["", "M", "V"])
        sex_row.addWidget(self.sex_combo)
        self.age_input = Input("Edad")
        self.age_input.setMaxLength(3)
        self.age_input.setFixedWidth(80)
        sex_row.addWidget(self.age_input)
        lbl = QLabel("Sexo / Edad")
        lbl.setStyleSheet(ls)
        layout.addRow(lbl, sex_row)

        self.tutor_input = Input("Tutor")
        lbl = QLabel("Tutor")
        lbl.setStyleSheet(ls)
        layout.addRow(lbl, self.tutor_input)

        phone_addr = QHBoxLayout()
        self.phone_input = Input("Telefono")
        phone_addr.addWidget(self.phone_input)
        self.address_input = Input("Domicilio")
        phone_addr.addWidget(self.address_input)
        lbl = QLabel("Telefono / Domicilio")
        lbl.setStyleSheet(ls)
        layout.addRow(lbl, phone_addr)

        course_row = QHBoxLayout()
        self.course_combo = Combo()
        self.course_combo.setEditable(True)
        self.course_combo.addItems([
            "1º ESBA A", "1º ESBA B", "1º ESBA C",
            "2º ESBA A", "2º ESBA B", "2º ESBA C",
            "3º ESBA A", "3º ESBA B",
            "4º ESBA",
            "1º BACH A", "1º BACH B",
            "2º BACH A", "2º BACH B",
        ])
        course_row.addWidget(self.course_combo)
        self.shift_combo = Combo()
        self.shift_combo.addItems(["", "MAÑANA", "TARDE"])
        course_row.addWidget(self.shift_combo)
        lbl = QLabel("Curso / Turno")
        lbl.setStyleSheet(ls)
        layout.addRow(lbl, course_row)

        self.transfer_combo = Combo()
        self.transfer_combo.addItems(["", "NO", "SÍ"])
        lbl = QLabel("Traslado")
        lbl.setStyleSheet(ls)
        layout.addRow(lbl, self.transfer_combo)

        self.pending_input = Input("Asignatura(s) pendiente(s)")
        lbl = QLabel("Asig. pendiente")
        lbl.setStyleSheet(ls)
        layout.addRow(lbl, self.pending_input)

        pay_row = QHBoxLayout()
        self.payment_input = Input("Persona o monto")
        pay_row.addWidget(self.payment_input)
        self.pass_combo = Combo()
        self.pass_combo.addItems(["", "SI", "NO"])
        pay_row.addWidget(self.pass_combo)
        lbl = QLabel("Pago / Paso nivel")
        lbl.setStyleSheet(ls)
        layout.addRow(lbl, pay_row)

        self.pending_pay_input = Input("Monto pendiente")
        lbl = QLabel("Pago pendiente")
        lbl.setStyleSheet(ls)
        layout.addRow(lbl, self.pending_pay_input)

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

        if self.student_data:
            self._populate()

    def _populate(self):
        d = self.student_data
        self.code_input.setText(d.get("code", ""))
        self.fullname_input.setText(d.get("nombre", d.get("full_name", "")))
        idx = self.sex_combo.findText(d.get("sexo", d.get("sex", "")))
        if idx >= 0:
            self.sex_combo.setCurrentIndex(idx)
        age = d.get("edad", d.get("age", ""))
        self.age_input.setText(str(age) if age else "")
        self.tutor_input.setText(d.get("tutor", ""))
        self.phone_input.setText(str(d.get("telefono", d.get("phone", ""))))
        self.address_input.setText(d.get("domicilio", d.get("address", "")))
        idx = self.course_combo.findText(d.get("curso", d.get("course", "")))
        if idx >= 0:
            self.course_combo.setCurrentIndex(idx)
        else:
            self.course_combo.setCurrentText(d.get("curso", d.get("course", "")))
        idx = self.shift_combo.findText(d.get("turno", d.get("shift", "")))
        if idx >= 0:
            self.shift_combo.setCurrentIndex(idx)
        idx = self.transfer_combo.findText(d.get("traslado", d.get("transfer", "")))
        if idx >= 0:
            self.transfer_combo.setCurrentIndex(idx)
        self.pending_input.setText(d.get("asig_pendiente", d.get("pending_subject", "")))
        self.payment_input.setText(d.get("pago", d.get("payment", "")))
        idx = self.pass_combo.findText(d.get("paso_nivel", d.get("pass_level", "")))
        if idx >= 0:
            self.pass_combo.setCurrentIndex(idx)
        pp = d.get("pago_pendiente", d.get("pending_payment", ""))
        self.pending_pay_input.setText(str(pp) if pp else "")

    def _accept(self):
        code = self.code_input.text().strip()
        full_name = self.fullname_input.text().strip()
        if not code or not full_name:
            QMessageBox.warning(self, "Campos requeridos", "Codigo y nombre completo son obligatorios.")
            return
        if not self.student_data and student_code_exists(code):
            QMessageBox.warning(self, "Codigo duplicado", f"El codigo '{code}' ya existe.")
            return
        age = self.age_input.text().strip()
        try:
            age = int(age) if age else None
        except ValueError:
            age = None
        self.data = {
            "code": code,
            "full_name": full_name,
            "sex": self.sex_combo.currentText().strip(),
            "age": age,
            "tutor": self.tutor_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "address": self.address_input.text().strip(),
            "course": self.course_combo.currentText().strip(),
            "shift": self.shift_combo.currentText().strip(),
            "transfer": self.transfer_combo.currentText().strip(),
            "pending_subject": self.pending_input.text().strip(),
            "payment": self.payment_input.text().strip(),
            "pass_level": self.pass_combo.currentText().strip(),
            "pending_payment": self.pending_pay_input.text().strip(),
        }
        self.accept()


class StudentsView(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        h = Header("Estudiantes")
        layout.addWidget(h)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        self.search_input = Input("Buscar por nombre, apellido o codigo...")
        self.search_input.textChanged.connect(self._on_search)
        toolbar.addWidget(self.search_input)

        add_btn = QPushButton("Nuevo Estudiante")
        add_btn.setStyleSheet(f"""
            QPushButton {{ padding: 0 16px; height: 36px; border: none;
                background: {COLOR_ACCENT}; color: #ffffff; font-size: 13px; }}
            QPushButton:hover {{ background: {COLOR_ACCENT_HOVER}; }}
        """)
        add_btn.clicked.connect(self._add_student)
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
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(["CODIGO", "NOMBRE COMPLETO", "SEXO", "EDAD", "CURSO", "TURNO", "TUTOR", "TELÉFONO", "PAGO", "ACCIONES"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

    def _on_search(self, text):
        if len(text) < 2:
            self.refresh()
            return
        results = search_students(text)
        self._populate_table(results)

    def _add_student(self):
        dlg = StudentDialog(self)
        if dlg.exec() == QDialog.Accepted:
            d = dlg.data
            try:
                save_student(**d)
                self.refresh()
                self.main.refresh_stats()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _edit_student(self, student_id):
        data = get_student(student_id)
        if not data:
            return
        dlg = StudentDialog(self, data)
        if dlg.exec() == QDialog.Accepted:
            d = dlg.data
            try:
                update_student(student_id, **d)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _delete_student(self, student_id, name):
        resp = QMessageBox.question(
            self, "Archivar estudiante",
            f"Archivar a {name}? Se desactivara pero los datos se conservan.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            try:
                deactivate_student(student_id)
                self.refresh()
                self.main.refresh_stats()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _populate_table(self, students):
        self.table.setRowCount(len(students))
        for i, s in enumerate(students):
            self.table.setItem(i, 0, QTableWidgetItem(s.get("code", "")))
            self.table.setItem(i, 1, QTableWidgetItem(s.get("nombre", "")))
            self.table.setItem(i, 2, QTableWidgetItem(s.get("sexo", "")))
            age = s.get("edad", "")
            self.table.setItem(i, 3, QTableWidgetItem(str(age) if age else ""))
            self.table.setItem(i, 4, QTableWidgetItem(s.get("curso", "")))
            self.table.setItem(i, 5, QTableWidgetItem(s.get("turno", "")))
            self.table.setItem(i, 6, QTableWidgetItem(s.get("tutor", "")))
            self.table.setItem(i, 7, QTableWidgetItem(str(s.get("telefono", ""))))
            self.table.setItem(i, 8, QTableWidgetItem(s.get("pago", "")))

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
            edit_btn.clicked.connect(lambda checked, sid=s["id"]: self._edit_student(sid))
            act_layout.addWidget(edit_btn)

            del_btn = QPushButton("X")
            del_btn.setFixedSize(28, 24)
            del_btn.setStyleSheet(f"""
                QPushButton {{ border: 1px solid {COLOR_BORDER};
                    background: transparent; color: {COLOR_DANGER}; font-size: 11px; }}
                QPushButton:hover {{ background: {COLOR_HOVER}; }}
            """)
            del_btn.clicked.connect(lambda checked, sid=s["id"], nm=s.get("nombre", ""): self._delete_student(sid, nm))
            act_layout.addWidget(del_btn)

            act_layout.addStretch()
            self.table.setCellWidget(i, 9, actions)

    def refresh(self):
        students = get_all_students()
        self._populate_table(students)
