#!/usr/bin/env python3
"""
Módulo de comandos y CommandBus.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Type, Callable
from events import CommandResult, DomainEvent


class Command(ABC):
    """Interfaz base para todos los comandos."""
    
    @abstractmethod
    def execute(self) -> CommandResult:
        """Ejecutar el comando y retornar resultado con eventos."""
        pass


class CommandBus:
    """Bus de comandos minimalista."""
    
    def __init__(self):
        self._handlers: Dict[Type[Command], Callable] = {}

    def register_handler(self, command_type: Type[Command], handler: Callable):
        """Registrar un handler para un tipo de comando."""
        self._handlers[command_type] = handler

    def execute(self, command: Command) -> CommandResult:
        """Ejecutar un comando y retornar resultado con eventos."""
        command_type = type(command)
        if command_type not in self._handlers:
            raise ValueError(f"No handler registered for command: {command_type}")
        
        handler = self._handlers[command_type]
        return handler(command)