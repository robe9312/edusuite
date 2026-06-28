from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QMessageBox,
    QFormLayout, QDialog, QDoubleSpinBox, QDateEdit, QFrame,
)
from PySide6.QtCore import Qt, QDate

from db.database import (
    save_expense, get_expense, get_all_expenses, update_expense, delete_expense,
    get_active_school_year, get_enrollment_stats
)
from config import *
from ui_style import Input, Table, Header


class ExpenseDialog(QDialog):
    def __init__(self, parent=None, expense_data=None):
        super().__init__(parent)
        self.expense_data = expense_data
        self.setWindowTitle("Editar Gasto" if expense_data else "Nuevo Gasto")
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

        self.concept_input = Input("Ej: Compra de marcadores")
        lbl = QLabel("Concepto")
        lbl.setStyleSheet(ls)
        layout.addRow(lbl, self.concept_input)

        spin_s = f"""
            QDoubleSpinBox {{
                padding: 0 12px; height: 36px;
                border: 1px solid {COLOR_BORDER};
                background: {COLOR_INPUT}; color: {COLOR_TEXT}; font-size: 13px;
            }}
            QDoubleSpinBox:focus {{ border-color: {COLOR_ACCENT}; }}
        """
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 999999999)
        self.amount_input.setDecimals(0)
        self.amount_input.setPrefix("XAF ")
        self.amount_input.setValue(0)
        self.amount_input.setStyleSheet(spin_s)
        lbl = QLabel("Monto (Costo)")
        lbl.setStyleSheet(ls)
        layout.addRow(lbl, self.amount_input)

        date_s = f"""
            QDateEdit {{
                padding: 0 12px; height: 36px;
                border: 1px solid {COLOR_BORDER};
                background: {COLOR_INPUT}; color: {COLOR_TEXT}; font-size: 13px;
            }}
            QDateEdit:focus {{ border-color: {COLOR_ACCENT}; }}
        """
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        self.date_input.setStyleSheet(date_s)
        lbl = QLabel("Fecha")
        lbl.setStyleSheet(ls)
        layout.addRow(lbl, self.date_input)

        self.notes_input = Input("Observaciones o notas adicionales")
        lbl = QLabel("Nota")
        lbl.setStyleSheet(ls)
        layout.addRow(lbl, self.notes_input)

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

        if self.expense_data:
            self._populate()

    def _populate(self):
        d = self.expense_data
        self.concept_input.setText(d.get("concept", ""))
        self.amount_input.setValue(d.get("amount", 0))
        dt = QDate.fromString(d.get("date", ""), "yyyy-MM-dd")
        if dt.isValid():
            self.date_input.setDate(dt)
        self.notes_input.setText(d.get("notes", ""))

    def _accept(self):
        concept = self.concept_input.text().strip()
        amount = self.amount_input.value()
        date_str = self.date_input.date().toString("yyyy-MM-dd")
        notes = self.notes_input.text().strip()

        if not concept:
            QMessageBox.warning(self, "Campo requerido", "El concepto del gasto es obligatorio.")
            return
        if amount <= 0:
            QMessageBox.warning(self, "Monto inválido", "El monto del gasto debe ser mayor que 0.")
            return

        self.data = {
            "concept": concept,
            "amount": amount,
            "date": date_str,
            "notes": notes,
        }
        self.accept()


class ExpensesView(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        h = Header("Gastos de la Institución")
        layout.addWidget(h)

        # Dashboard-style stats cards at the top
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)
        layout.addLayout(stats_layout)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        toolbar.addStretch()

        add_btn = QPushButton("Nuevo Gasto")
        add_btn.setStyleSheet(f"""
            QPushButton {{ padding: 0 16px; height: 36px; border: none;
                background: {COLOR_ACCENT}; color: #ffffff; font-size: 13px; }}
            QPushButton:hover {{ background: {COLOR_ACCENT_HOVER}; }}
        """)
        add_btn.clicked.connect(self._add_expense)
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
        self.table.setHorizontalHeaderLabels(["FECHA", "CONCEPTO", "COSTO / VALOR", "NOTA", "ACCIONES"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        layout.addWidget(self.table)

    def _add_expense(self):
        dlg = ExpenseDialog(self)
        if dlg.exec() == QDialog.Accepted:
            d = dlg.data
            try:
                save_expense(d["concept"], d["amount"], d["date"], d["notes"])
                self.refresh()
                self.main.refresh_stats()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _edit_expense(self, expense_id):
        data = get_expense(expense_id)
        if not data:
            return
        dlg = ExpenseDialog(self, data)
        if dlg.exec() == QDialog.Accepted:
            try:
                update_expense(expense_id, **dlg.data)
                self.refresh()
                self.main.refresh_stats()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _delete_expense(self, expense_id, concept):
        resp = QMessageBox.question(
            self, "Eliminar gasto",
            f"¿Estás seguro de eliminar el gasto '{concept}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            try:
                delete_expense(expense_id)
                self.refresh()
                self.main.refresh_stats()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _populate_table(self, expenses):
        self.table.setRowCount(len(expenses))
        total_sum = 0
        for i, e in enumerate(expenses):
            self.table.setItem(i, 0, QTableWidgetItem(e.get("date", "")))
            self.table.setItem(i, 1, QTableWidgetItem(e.get("concept", "")))
            
            amount = e.get("amount", 0)
            total_sum += amount
            amount_item = QTableWidgetItem(f"{amount:,.0f} XAF")
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, 2, amount_item)
            
            self.table.setItem(i, 3, QTableWidgetItem(e.get("notes", "")))

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
            edit_btn.clicked.connect(lambda checked, eid=e["id"]: self._edit_expense(eid))
            act_layout.addWidget(edit_btn)

            del_btn = QPushButton("X")
            del_btn.setFixedSize(28, 24)
            del_btn.setStyleSheet(f"""
                QPushButton {{ border: 1px solid {COLOR_BORDER};
                    background: transparent; color: {COLOR_DANGER}; font-size: 11px; }}
                QPushButton:hover {{ background: {COLOR_HOVER}; }}
            """)
            del_btn.clicked.connect(lambda checked, eid=e["id"], cp=e.get("concept", ""): self._delete_expense(eid, cp))
            act_layout.addWidget(del_btn)

            act_layout.addStretch()
            self.table.setCellWidget(i, 4, actions)
            


    def refresh(self):
        expenses = get_all_expenses()
        self._populate_table(expenses)
