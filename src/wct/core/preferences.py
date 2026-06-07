from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from pathlib import Path

from loguru import logger

from wct.config.paths import AppPaths


@dataclass
class WindowState:
    x: int = 100
    y: int = 100
    width: int = 1280
    height: int = 800
    maximized: bool = False


@dataclass
class UIPreferences:
    last_page: str = "dashboard"
    sidebar_collapsed: bool = False
    show_status_bar: bool = True
    show_tray_hint: bool = True
    confirm_destructive: bool = True
    table_density: str = "comfortable"
    accent_intensity: int = 100
    animation_speed: int = 200


@dataclass
class Preferences:
    window: WindowState = field(default_factory=WindowState)
    ui: UIPreferences = field(default_factory=UIPreferences)
    palette_recents: list[str] = field(default_factory=list)
    favorite_pages: list[str] = field(default_factory=list)
    recent_searches: list[str] = field(default_factory=list)


def _prefs_path() -> Path:
    return AppPaths.config_dir() / "preferences.json"


def load() -> Preferences:
    path = _prefs_path()
    if not path.exists():
        return Preferences()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        logger.debug("Preferences load failed: {}", exc)
        return Preferences()

    p = Preferences()
    win = raw.get("window", {})
    if isinstance(win, dict):
        for k, v in win.items():
            if hasattr(p.window, k):
                setattr(p.window, k, v)
    ui = raw.get("ui", {})
    if isinstance(ui, dict):
        for k, v in ui.items():
            if hasattr(p.ui, k):
                setattr(p.ui, k, v)
    p.palette_recents = [str(x) for x in raw.get("palette_recents", []) if isinstance(x, str)]
    p.favorite_pages = [str(x) for x in raw.get("favorite_pages", []) if isinstance(x, str)]
    p.recent_searches = [str(x) for x in raw.get("recent_searches", []) if isinstance(x, str)]
    return p


def save(prefs: Preferences) -> None:
    path = _prefs_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "window": asdict(prefs.window),
            "ui": asdict(prefs.ui),
            "palette_recents": prefs.palette_recents[:50],
            "favorite_pages": prefs.favorite_pages[:20],
            "recent_searches": prefs.recent_searches[:50],
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError as exc:
        logger.warning("Preferences save failed: {}", exc)


def push_recent_search(prefs: Preferences, query: str, limit: int = 25) -> None:
    if not query.strip():
        return
    prefs.recent_searches = [q for q in prefs.recent_searches if q != query]
    prefs.recent_searches.insert(0, query)
    prefs.recent_searches = prefs.recent_searches[:limit]


def push_palette_recent(prefs: Preferences, cid: str, limit: int = 30) -> None:
    if not cid:
        return
    prefs.palette_recents = [c for c in prefs.palette_recents if c != cid]
    prefs.palette_recents.insert(0, cid)
    prefs.palette_recents = prefs.palette_recents[:limit]


def toggle_favorite(prefs: Preferences, key: str) -> bool:
    if key in prefs.favorite_pages:
        prefs.favorite_pages.remove(key)
        return False
    prefs.favorite_pages.append(key)
    return True


def reset_ui(prefs: Preferences) -> None:
    prefs.ui = UIPreferences()
    prefs.window = WindowState()
