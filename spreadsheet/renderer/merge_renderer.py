from __future__ import annotations
from typing import Any, Dict, List


class MergeRenderer:
    """
    Interpreta merges de Luckysheet y devuelve rangos para `setSpan()`.
    No aplica nada directamente; solo expone rangos.

    Formatos soportados:
      - config.merge: dict keyed by "r_c" → {r, c, rs, cs}
      - config.merges: list → [{r, c, rs, cs}, ...]
      - config.merge: list → [{r, c, rs, cs}, ...]
    """

    def __init__(self, sheet_data: Dict[str, Any]):
        self.sheet = sheet_data or {}

    def spans(self) -> List[Dict[str, int]]:
        """Devuelve lista de merges: {r, c, rs, cs} (0-indexed)."""
        out: List[Dict[str, int]] = []
        config = self.sheet.get("config") or {}

        for key in ("merge", "merges", "Merge"):
            raw = config.get(key)
            if raw is None:
                continue
            if isinstance(raw, dict):
                items = raw.values()
            elif isinstance(raw, list):
                items = raw
            else:
                continue
            for info in items:
                if not isinstance(info, dict):
                    continue
                r = info.get("r")
                c = info.get("c")
                rs = info.get("rs") or 1
                cs = info.get("cs") or 1
                if r is None or c is None:
                    continue
                out.append({"r": int(r), "c": int(c), "rs": int(rs), "cs": int(cs)})

        # Deduplicate by (r, c) — keep last wins
        seen: Dict[tuple, Dict[str, int]] = {}
        for span in out:
            seen[(span["r"], span["c"])] = span
        return list(seen.values())
