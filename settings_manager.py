import json
import os
from pathlib import Path

_SETTINGS_PATH = Path(__file__).parent / "settings.json"

DEFAULT_SETTINGS = {
    "institution_logo_path": "",
    "selected_theme": "oscuro",
    "institution_name": "EduSuite",
    "institution_director": "",
    "institution_address": "",
    "institution_phone": "",
    "institution_email": "",
    "institution_code": "",
    "school_level": "",
    "accent_color": "#5E81F4",
    "accent_hover_color": "#4a6cf7",
    "sidebar_bg": "#080808",
    "sidebar_hover": "#141414",
    "sidebar_active": "#1a1a1a",
    "border_color": "#3a3a3a",
    "success_color": "#38D39F",
    "warning_color": "#F5B942",
    "danger_color": "#FF5A5F",
    "main_bg": "#080808",
    "surface_color": "#0d0d0d",
    "panel_color": "#151515",
    "input_color": "#1a1a1a",
    "hover_color": "#1e1e1e",
    "text_color": "#ffffff",
    "text_muted": "#aaaaaa",
    "text_dim": "#777777",
    "institution_logo_path": ""
}

_loaded = False
_cache = {}


def _ensure():
    global _loaded, _cache
    if _loaded:
        return
    if _SETTINGS_PATH.exists():
        try:
            with open(_SETTINGS_PATH) as f:
                data = json.load(f)
            for k, v in DEFAULT_SETTINGS.items():
                _cache[k] = data.get(k, v)
        except Exception:
            _cache = dict(DEFAULT_SETTINGS)
    else:
        _cache = dict(DEFAULT_SETTINGS)
    _loaded = True


def get(key, default=None):
    _ensure()
    return _cache.get(key, default)


def get_all():
    _ensure()
    return dict(_cache)


def set_many(kwargs):
    _ensure()
    for k, v in kwargs.items():
        if k in DEFAULT_SETTINGS:
            _cache[k] = v
    _save()


def _save():
    try:
        with open(_SETTINGS_PATH, "w") as f:
            json.dump(_cache, f, indent=2)
    except Exception:
        pass


def reset():
    global _loaded, _cache
    _cache = dict(DEFAULT_SETTINGS)
    _save()
