#!/usr/bin/env python3
"""
Comandos específicos para operaciones con planillas.
"""

from dataclasses import dataclass
from typing import Optional
from . import Command
from events import (
    CommandResult,
    SpreadsheetCreatedEvent,
    SpreadsheetUpdatedEvent,
    SpreadsheetDeletedEvent,
    CellValueChangedEvent,
    FormulaRecalculatedEvent
)
from db.database import (
    create_custom_section,
    update_section_workbook,
    get_custom_section,
    archive_custom_section
)


@dataclass
class CreateSpreadsheetCommand(Command):
    """Comando para crear una nueva planilla."""
    name: str
    spreadsheet_type: str = "GradeBook"  # "GradeBook", "Attendance", etc.
    initial_data: Optional[dict] = None

    def execute(self) -> CommandResult:
        """Crear una nueva planilla y retornar evento."""
        # Crear estructura inicial de la planilla
        initial_workbook = self.initial_data or {
            "sheets": [
                {
                    "name": "Sheet1",
                    "celldata": [],
                    "config": {},
                    "metadata": {
                        "active_area": {"top": 0, "left": 0, "bottom": 4, "right": 3}
                    }
                }
            ]
        }

        # Guardar en la base de datos
        section_id = create_custom_section(
            name=self.name,
            section_key=self.spreadsheet_type.lower(),
            workbook_json=initial_workbook,
            columns_json="{}"
        )

        # Retornar resultado con evento
        if section_id is None:
            return CommandResult(success=False, data={"error": "No se pudo crear la planilla"})
            
        return CommandResult(
            success=True,
            data={"section_id": section_id},
            events=[
                SpreadsheetCreatedEvent(
                    spreadsheet_id=section_id,
                    name=self.name
                )
            ]
        )


@dataclass
class UpdateSpreadsheetCommand(Command):
    """Comando para actualizar una planilla."""
    section_id: int
    workbook_data: dict

    def execute(self) -> CommandResult:
        """Actualizar una planilla y retornar evento."""
        # Guardar cambios en la base de datos
        update_section_workbook(self.section_id, self.workbook_data)

        # Retornar resultado con evento
        return CommandResult(
            success=True,
            data={"section_id": self.section_id},
            events=[
                SpreadsheetUpdatedEvent(
                    spreadsheet_id=self.section_id,
                    changes=self.workbook_data
                )
            ]
        )


@dataclass
class DeleteSpreadsheetCommand(Command):
    """Comando para eliminar una planilla."""
    section_id: int

    def execute(self) -> CommandResult:
        """Eliminar una planilla y retornar evento."""
        # Obtener nombre antes de eliminar
        section = get_custom_section(self.section_id)
        name = section.get("name", "Sin nombre") if section else "Sin nombre"

        # Archivar la sección
        archive_custom_section(self.section_id)

        # Retornar resultado con evento
        return CommandResult(
            success=True,
            data={"section_id": self.section_id},
            events=[
                SpreadsheetDeletedEvent(
                    spreadsheet_id=self.section_id
                )
            ]
        )


@dataclass
class UpdateCellValueCommand(Command):
    """Comando para actualizar el valor de una celda."""
    section_id: int
    sheet_index: int
    row: int
    col: int
    new_value: str
    old_value: Optional[str] = None

    def execute(self) -> CommandResult:
        """Actualizar el valor de una celda y retornar evento."""
        # Obtener la planilla actual
        section = get_custom_section(self.section_id)
        if not section:
            return CommandResult(success=False, data={"error": "Planilla no encontrada"})

        workbook = section.get("workbook_json", {})
        sheets = workbook.get("sheets", [])
        
        if self.sheet_index >= len(sheets):
            return CommandResult(success=False, data={"error": "Hoja no encontrada"})

        # Actualizar el valor de la celda
        sheet = sheets[self.sheet_index]
        celldata = sheet.get("celldata", [])
        
        # Buscar si la celda ya existe
        cell_updated = False
        for cell in celldata:
            if cell.get("r") == self.row and cell.get("c") == self.col:
                self.old_value = cell.get("v", "")
                cell["v"] = self.new_value
                cell_updated = True
                break

        if not cell_updated:
            # Crear nueva celda
            self.old_value = ""
            celldata.append({
                "r": self.row,
                "c": self.col,
                "v": self.new_value
            })

        # Guardar cambios
        update_section_workbook(self.section_id, workbook)

        # Crear eventos
        events = []
        
        # Evento de cambio de valor
        cell_event = CellValueChangedEvent(
            spreadsheet_id=self.section_id,
            sheet_index=self.sheet_index,
            row=self.row,
            col=self.col,
            old_value=self.old_value,
            new_value=self.new_value
        )
        events.append(cell_event)
        
        # Evento de recálculo si es fórmula
        if self.new_value and self.new_value.startswith("="):
            formula_event = FormulaRecalculatedEvent(
                spreadsheet_id=self.section_id,
                sheet_index=self.sheet_index,
                cell=f"{chr(65 + self.col)}{self.row + 1}",  # Convertir a formato A1
                result=None  # El resultado se calculará después
            )
            events.append(formula_event)

        return CommandResult(
            success=True,
            data={
                "section_id": self.section_id,
                "sheet_index": self.sheet_index,
                "row": self.row,
                "col": self.col
            },
            events=events
        )