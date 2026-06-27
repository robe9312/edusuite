import json
from pathlib import Path

_THEMES_DIR = Path(__file__).parent

_loaded_themes = {}
_current_theme_name = "Oscuro"


def list_themes():
    _ensure_loaded()
    return {name: meta.get("name", name)
            for name, meta in _loaded_themes.items()}


def _ensure_loaded():
    if _loaded_themes:
        return
    for f in _THEMES_DIR.glob("theme_*.json"):
        try:
            with open(f) as fh:
                data = json.load(fh)
            name = data.pop("name", f.stem.replace("theme_", "").title())
            key = f.stem.replace("theme_", "")
            _loaded_themes[key] = {"name": name, **data}
        except Exception:
            pass


def get_theme(name=None):
    _ensure_loaded()
    key = name or _current_theme_name.lower()
    for k, v in _loaded_themes.items():
        if k == key or v.get("name", "").lower() == key.lower():
            return dict(v)
    return dict(next(iter(_loaded_themes.values()), {}))


def apply_theme(name):
    global _current_theme_name
    theme = get_theme(name)
    if not theme:
        return False
    _current_theme_name = theme.get("name", name)
    import settings_manager as sset
    sset.set_many(theme)
    return True
