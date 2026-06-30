from __future__ import annotations
from typing import Any, Dict, Optional


class ReadOnlyPolicy:
    """
    Determina si una celda es editable.

    Reglas:
      - Una celda con `v.locked == True` es de sólo lectura.
      - En Luckysheet, `v.v = ''` o `v.v = None` en una celda bloqueada indica placeholder editable.
      - Metadatos personalizados (`v.editable`) tienen precedencia.

    Futuras reglas:
      - Permisos de usuario.
      - Roles.
    """

    @staticmethod
    def is_editable(v: Optional[Dict[str, Any]]) -> bool:
        if not isinstance(v, dict):
            return True

        if "editable" in v:
            return bool(v.get("editable"))

        if v.get("locked") is True:
            return False

        if v.get("lock") is True:
            return False

        return True
