from __future__ import annotations

import json
import platform
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore[assignment]

from wct import __version__
from wct.config.paths import AppPaths
from wct.core import sysinfo


@dataclass
class DiagnosticSnapshot:
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    app_version: str = __version__
    python_version: str = sys.version
    os_version: str = platform.platform()
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    pid: int = 0
    threads: int = 0
    open_files: int = 0
    fd_count: int = 0
    uptime_sec: float = 0.0

    @classmethod
    def capture(cls) -> "DiagnosticSnapshot":
        if psutil is None:
            return cls()
        try:
            proc = psutil.Process()
            try:
                fd = proc.num_fds()
            except (AttributeError, psutil.AccessDenied):
                fd = 0
            try:
                of = len(proc.open_files())
            except (psutil.AccessDenied, OSError):
                of = 0
            return cls(
                cpu_percent=proc.cpu_percent(interval=0.1),
                memory_mb=proc.memory_info().rss / (1024 * 1024),
                pid=proc.pid,
                threads=proc.num_threads(),
                open_files=of,
                fd_count=fd,
                uptime_sec=sysinfo.uptime_seconds(),
            )
        except Exception:
            return cls()

    def to_dict(self) -> dict:
        return asdict(self)


def _safe_size(path: Path) -> int:
    try:
        if path.is_file():
            return path.stat().st_size
        if path.is_dir():
            total = 0
            for child in path.rglob("*"):
                if child.is_file():
                    try:
                        total += child.stat().st_size
                    except OSError:
                        continue
            return total
    except OSError:
        return 0
    return 0


def db_stats() -> dict:
    db = AppPaths.db_path()
    info = {"path": str(db), "exists": db.exists(), "size": 0, "size_mb": 0.0}
    if db.exists():
        try:
            sz = db.stat().st_size
            info["size"] = int(sz)
            info["size_mb"] = round(sz / (1024 * 1024), 2)
        except OSError:
            pass
    return info


def storage_overview() -> dict:
    info = {}
    info["db"] = db_stats()
    info["quarantine"] = {
        "path": str(AppPaths.quarantine_dir()),
        "size": _safe_size(AppPaths.quarantine_dir()),
    }
    info["logs"] = {
        "path": str(AppPaths.logs_dir()),
        "size": _safe_size(AppPaths.logs_dir()),
    }
    info["backups"] = {
        "path": str(AppPaths.backups_dir()),
        "size": _safe_size(AppPaths.backups_dir()),
    }
    return info


def build_report() -> dict:
    snap = DiagnosticSnapshot.capture()
    sysd = sysinfo.collect().to_dict()
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": __version__,
        "diagnostic": snap.to_dict(),
        "system": sysd,
        "storage": storage_overview(),
        "env": sysinfo.env_summary(),
        "interfaces": sysinfo.network_interfaces(),
    }


def report_to_text() -> str:
    rep = build_report()
    lines = [
        "Windows Control Toolkit — Diagnostic Report",
        f"Generated: {rep['generated_at']}",
        f"Version:   {rep['version']}",
        "",
        "[System]",
        sysinfo.to_text(),
        "",
        "[Process]",
        f"PID:        {rep['diagnostic']['pid']}",
        f"Threads:    {rep['diagnostic']['threads']}",
        f"Open files: {rep['diagnostic']['open_files']}",
        f"FD count:   {rep['diagnostic']['fd_count']}",
        f"CPU %:      {rep['diagnostic']['cpu_percent']:.1f}",
        f"Memory MB:  {rep['diagnostic']['memory_mb']:.1f}",
        f"Uptime sec: {rep['diagnostic']['uptime_sec']:.0f}",
        "",
        "[Storage]",
    ]
    for key, val in rep["storage"].items():
        if isinstance(val, dict):
            sz = val.get("size", 0)
            lines.append(f"{key:>12}: {val.get('path','')} ({sz/1024:.1f} KB)")
    lines.append("")
    lines.append("[Environment]")
    for k, v in rep["env"].items():
        if v:
            short = v if len(v) <= 60 else v[:57] + "..."
            lines.append(f"{k:>14} = {short}")
    return "\n".join(lines)


def report_to_json() -> str:
    return json.dumps(build_report(), indent=2)


def write_report(target: Path | None = None) -> Path:
    target = target or (AppPaths.logs_dir() / f"diagnostic_{int(time.time())}.txt")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(report_to_text(), encoding="utf-8")
    return target
