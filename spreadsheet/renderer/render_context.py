from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple


@dataclass
class RenderContext:
    """
    Estado compartido entre todos los renderers del pipeline.

    Contiene:
      - workbook raw JSON (dict completo de Luckysheet)
      - sheet_name (str)
      - area_active (top, left, bottom, right)
      - theme / zoom / config

    Todos los renderers reciben esta estructura.
    Nunca se pasan 20 parámetros sueltos.
    """

    workbook: Dict[str, Any] = field(default_factory=dict)
    sheet_index: int = 0
    sheet_name: str = ""
    sheet_data: Dict[str, Any] = field(default_factory=dict)

    top: int = 0
    left: int = 0
    bottom: int = 0
    right: int = 0

    theme: str = "default"
    zoom: float = 1.0

    config: Dict[str, Any] = field(default_factory=dict)

    def active_area(self) -> Tuple[int, int, int, int]:
        """Retorna (top, left, bottom, right) del área activa."""
        return (self.top, self.left, self.bottom, self.right)

    def rows(self) -> int:
        return max(0, self.bottom - self.top + 1)

    def cols(self) -> int:
        return max(0, self.right - self.left + 1)
