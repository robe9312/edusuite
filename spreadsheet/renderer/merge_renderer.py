from __future__ import annotations
from typing import Any, Dict, Iterable, List


class MergeRenderer:
    """
    Interpreta merges de Luckysheet (`mc`) y devuelve rangos para `setSpan()`.
    No aplica nada directamente; solo expone rangos.
    """

    def __init__(self, sheet_data: Dict[str, Any]):
        self.sheet = sheet_data or {}

    def spans(self) -> List[Dict[str, int]]:
        """Devuelve lista de merges: {r, c, rs, cs} (0-indexed)."""
        out: List[Dict[str, int]] = []
        mc = (self.sheet.get("config") or {}).get("merge") or {}
        for _, info in mc.items():
            r = info.get("r")
            c = info.get("c")
            rs = info.get("rs") or 1
            cs = info.get("cs") or 1
            if r is None or c is None:
                continue
            out.append({"r": int(r), "c": int(c), "rs": int(rs), "cs": int(cs)})
        return out
