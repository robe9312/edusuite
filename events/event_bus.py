#!/usr/bin/env python3
"""
EventBus minimalista para publicar eventos de dominio.
"""

from typing import Dict, Type, List, Callable
from . import DomainEvent


class EventBus:
    """Bus de eventos minimalista.
    
    Ejemplo de uso:
        bus = EventBus()
        bus.subscribe(SpreadsheetCreatedEvent, lambda e: print(f"Creada: {e.name}"))
        bus.publish(SpreadsheetCreatedEvent(spreadsheet_id=1, name="Notas"))
    """
    
    def __init__(self):
        self._subscribers: Dict[Type[DomainEvent], List[Callable]] = {}

    def subscribe(self, event_type: Type[DomainEvent], handler: Callable):
        """Suscribir un handler a un tipo de evento."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def publish(self, event: DomainEvent):
        """Publicar un evento a todos los handlers suscritos."""
        event_type = type(event)
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                handler(event)

    def clear(self):
        """Limpiar todos los suscriptores."""
        self._subscribers.clear()