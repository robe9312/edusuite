#!/usr/bin/env python3
"""
Módulo de eventos de dominio.
Todos los eventos son inmutables (frozen dataclasses).
"""

from dataclasses import dataclass, field
from typing import Any, List


@dataclass(frozen=True)
class DomainEvent:
    """Clase base para todos los eventos de dominio."""
    pass


@dataclass(frozen=True)
class CommandResult:
    """Resultado de la ejecución de un comando.
    Contiene datos y eventos generados.
    """
    success: bool
    data: Any = None
    events: List[DomainEvent] = field(default_factory=list)
    
    def __post_init__(self):
        if self.events is None:
            object.__setattr__(self, 'events', [])


# Eventos específicos del dominio de planillas
@dataclass(frozen=True)
class SpreadsheetCreatedEvent(DomainEvent):
    """Se creó una nueva planilla."""
    spreadsheet_id: int
    name: str


@dataclass(frozen=True)
class SpreadsheetUpdatedEvent(DomainEvent):
    """Se actualizó una planilla."""
    spreadsheet_id: int
    changes: dict  # {'cells': [...], 'formulas': [...]}


@dataclass(frozen=True)
class SpreadsheetDeletedEvent(DomainEvent):
    """Se eliminó una planilla."""
    spreadsheet_id: int


@dataclass(frozen=True)
class CellValueChangedEvent(DomainEvent):
    """Se cambió el valor de una celda."""
    spreadsheet_id: int
    sheet_index: int
    row: int
    col: int
    old_value: Any
    new_value: Any


@dataclass(frozen=True)
class FormulaRecalculatedEvent(DomainEvent):
    """Se recalculó una fórmula."""
    spreadsheet_id: int
    sheet_index: int
    cell: str  # 'A1', 'B2', etc.
    result: Any