from __future__ import annotations

from datetime import datetime, timezone, timedelta


_UNITS_BINARY = ["B", "KB", "MB", "GB", "TB", "PB"]
_UNITS_RATE = ["B/s", "KB/s", "MB/s", "GB/s"]


def human_size(size: int | float, *, decimals: int = 1) -> str:
    n = float(size)
    for unit in _UNITS_BINARY:
        if n < 1024 or unit == _UNITS_BINARY[-1]:
            return f"{n:.{decimals}f} {unit}"
        n /= 1024
    return f"{n:.{decimals}f} PB"


def human_rate(bytes_per_sec: int | float) -> str:
    n = float(bytes_per_sec)
    for unit in _UNITS_RATE:
        if n < 1024 or unit == _UNITS_RATE[-1]:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} GB/s"


def human_count(n: int) -> str:
    if abs(n) < 1000:
        return str(n)
    if abs(n) < 1_000_000:
        return f"{n / 1000:.1f}K".replace(".0K", "K")
    if abs(n) < 1_000_000_000:
        return f"{n / 1_000_000:.1f}M".replace(".0M", "M")
    return f"{n / 1_000_000_000:.1f}B".replace(".0B", "B")


def short_path(path: str, max_len: int = 60) -> str:
    if len(path) <= max_len:
        return path
    return "..." + path[-(max_len - 3):]


def parse_iso(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def to_local_str(ts: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    dt = parse_iso(ts)
    if dt is None:
        return ts
    local = dt.astimezone()
    return local.strftime(fmt)


def to_short_time(ts: str) -> str:
    dt = parse_iso(ts)
    if dt is None:
        return ts
    return dt.astimezone().strftime("%H:%M:%S")


def relative_time(ts) -> str:
    if isinstance(ts, (int, float)):
        if ts <= 0:
            return ""
        dt = datetime.fromtimestamp(float(ts), tz=timezone.utc)
    else:
        dt = parse_iso(str(ts))
    if dt is None:
        return str(ts)
    delta = datetime.now(timezone.utc) - dt
    seconds = int(delta.total_seconds())
    if seconds < 0:
        return "just now"
    if seconds < 60:
        return f"{seconds}s ago"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    if days < 30:
        return f"{days}d ago"
    months = days // 30
    if months < 12:
        return f"{months}mo ago"
    years = months // 12
    return f"{years}y ago"


def human_duration(seconds: int | float) -> str:
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    m, s = divmod(s, 60)
    if m < 60:
        return f"{m}m {s}s"
    h, m = divmod(m, 60)
    if h < 24:
        return f"{h}h {m}m"
    d, h = divmod(h, 24)
    return f"{d}d {h}h"


def percentage(part: int | float, total: int | float, *, decimals: int = 1) -> str:
    if total == 0:
        return "0%"
    pct = (float(part) / float(total)) * 100
    return f"{pct:.{decimals}f}%"


def truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "\u2026"


def safe_filename(name: str) -> str:
    bad = '<>:"/\\|?*\x00'
    cleaned = "".join(c if c not in bad else "_" for c in name)
    return cleaned.strip().strip(".") or "untitled"


def join_tags(tags: list[str]) -> str:
    return ", ".join(t.strip() for t in tags if t.strip())


def split_tags(value: str) -> list[str]:
    if not value:
        return []
    parts = [p.strip() for p in value.replace(";", ",").split(",")]
    return [p for p in parts if p]


def color_for_risk(level: str) -> str:
    mapping = {
        "low": "#27ae60",
        "medium": "#f39c12",
        "high": "#e67e22",
        "critical": "#c0392b",
    }
    return mapping.get(level, "#8892b0")


def color_for_trust(state: str) -> str:
    mapping = {
        "allowed": "#27ae60",
        "blocked": "#c0392b",
        "ask": "#f39c12",
        "temp_allow": "#1abc9c",
        "temp_block": "#e74c3c",
        "unknown": "#8892b0",
    }
    return mapping.get(state, "#8892b0")


def humanize_iso_date(ts: str) -> str:
    dt = parse_iso(ts)
    if dt is None:
        return ts
    return dt.astimezone().strftime("%d %b %Y")


def future_iso(days: int) -> str:
    target = datetime.now(timezone.utc) + timedelta(days=days)
    return target.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
