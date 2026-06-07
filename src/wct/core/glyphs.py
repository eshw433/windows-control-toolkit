from __future__ import annotations


_NAV: dict[str, str] = {
    "dashboard":        "\u25a3",
    "network":          "\u26a1",
    "firewall":         "\u26e8",
    "bandwidth":        "\u2248",
    "risk":             "\u25b3",
    "trust":            "\u2713",
    "downloads":        "\u2913",
    "file_rules":       "\u2630",
    "duplicates":       "\u29c9",
    "disk_hogs":        "\u25c6",
    "quarantine":       "\u26d4",
    "history":          "\u27f3",
    "notifications":    "\u2767",
    "settings":         "\u2699",
    "about":            "\u2139",
    "process_inspector":"\u25d4",
    "task_manager":     "\u2630",
    "scheduler":        "\u23f2",
    "startup":          "\u2605",
    "usb":              "\u26a1",
    "content_search":   "\u26b2",
    "updater":          "\u2191",
    "welcome":          "\u2605",
    "search":           "\u26b2",
    "refresh":          "\u21bb",
    "plus":             "\u2795",
    "minus":            "\u2796",
    "cross":            "\u2715",
    "check":            "\u2713",
    "arrow_right":      "\u2192",
    "arrow_left":       "\u2190",
    "arrow_up":         "\u2191",
    "arrow_down":       "\u2193",
}


def for_nav(key: str) -> str:
    return _NAV.get(key, "\u2022")


def has(name: str) -> bool:
    return name in _NAV


def all_glyphs() -> dict[str, str]:
    return dict(_NAV)


def label(nav_key: str, text: str, *, with_space: bool = True) -> str:
    glyph = for_nav(nav_key)
    sep = "  " if with_space else " "
    return f"{glyph}{sep}{text}"
