from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class ChangelogEntry:
    version: str
    codename: str
    released: str
    highlights: list[str]
    notes: str = ""


_ENTRIES: list[ChangelogEntry] = [
    ChangelogEntry(
        version="2.0.0",
        codename="Aurora",
        released="2025-12-01",
        highlights=[
            "Five tunable theme presets driven by a single colour palette",
            "Command palette (Ctrl+K) with fuzzy match and recent history",
            "Live About page with system metrics, storage gauges and quick actions",
            "Plugin registry covering 12 built-in modules",
            "Per-session usage telemetry stored locally",
            "Window position, last page and palette history persisted across runs",
            "Markdown-lite renderer used for license and changelog views",
        ],
        notes="Major UI overhaul focused on density, readability and keyboard speed.",
    ),
    ChangelogEntry(
        version="1.5.0",
        codename="Nimbus",
        released="2025-09-20",
        highlights=[
            "Bandwidth tracker with per-process aggregation",
            "Risk scoring engine for network sessions",
            "Trust decisions with cooldowns and provenance",
            "Quarantine workflow for risky downloads",
            "Disk hogs report with size buckets",
        ],
    ),
    ChangelogEntry(
        version="1.2.0",
        codename="Coral",
        released="2025-07-10",
        highlights=[
            "Duplicate finder with two-stage hashing",
            "16 built-in file-organiser rule templates",
            "Local DNS cache for repeated resolutions",
            "Search and exporter helpers for the UI layer",
        ],
    ),
    ChangelogEntry(
        version="1.0.0",
        codename="Origin",
        released="2025-05-04",
        highlights=[
            "Initial release with firewall, downloads, quarantine and history pages",
            "Single SQLite store with migration runner",
            "Three-language UI (en / ru / az)",
        ],
    ),
]


def entries() -> list[ChangelogEntry]:
    return list(_ENTRIES)


def latest() -> ChangelogEntry:
    return _ENTRIES[0]


def find(version: str) -> ChangelogEntry | None:
    for e in _ENTRIES:
        if e.version == version:
            return e
    return None


def to_markdown(limit: int | None = None) -> str:
    lines: list[str] = ["# Changelog", ""]
    chosen = _ENTRIES[:limit] if limit else _ENTRIES
    for e in chosen:
        lines.append(f"## {e.version} \u00b7 {e.codename}")
        lines.append(f"*Released {e.released}*")
        lines.append("")
        for h in e.highlights:
            lines.append(f"- {h}")
        if e.notes:
            lines.append("")
            lines.append(e.notes)
        lines.append("")
    return "\n".join(lines)


def today() -> str:
    return date.today().isoformat()
