from __future__ import annotations

import getpass
import json
import locale
import os
import platform
import socket
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore[assignment]


@dataclass
class SystemSnapshot:
    os_name: str
    os_release: str
    os_version: str
    machine: str
    processor: str
    cpu_count: int
    cpu_logical: int
    total_ram: int
    available_ram: int
    boot_time: float
    hostname: str
    user: str
    locale: str
    python_version: str
    python_executable: str
    process_pid: int
    cwd: str
    env_path_count: int

    def to_dict(self) -> dict:
        return asdict(self)


def collect() -> SystemSnapshot:
    if psutil is None:
        total = avail = 0
        boot = 0.0
        logical = os.cpu_count() or 1
    else:
        vm = psutil.virtual_memory()
        total = int(vm.total)
        avail = int(vm.available)
        boot = float(psutil.boot_time())
        logical = psutil.cpu_count(logical=True) or 1
    return SystemSnapshot(
        os_name=platform.system(),
        os_release=platform.release(),
        os_version=platform.version(),
        machine=platform.machine(),
        processor=platform.processor() or "n/a",
        cpu_count=os.cpu_count() or 1,
        cpu_logical=logical,
        total_ram=total,
        available_ram=avail,
        boot_time=boot,
        hostname=socket.gethostname(),
        user=_safe_user(),
        locale=_safe_locale(),
        python_version=sys.version.split()[0],
        python_executable=sys.executable,
        process_pid=os.getpid(),
        cwd=os.getcwd(),
        env_path_count=len(os.environ.get("PATH", "").split(os.pathsep)),
    )


def _safe_user() -> str:
    try:
        return getpass.getuser()
    except Exception:
        return os.environ.get("USER", os.environ.get("USERNAME", "unknown"))


def _safe_locale() -> str:
    try:
        lang, enc = locale.getlocale()
        return f"{lang or 'C'}.{enc or 'UTF-8'}"
    except Exception:
        return "C.UTF-8"


def cpu_usage(*, interval: float = 0.5) -> float:
    if psutil is None:
        return 0.0
    return float(psutil.cpu_percent(interval=interval))


def memory_usage_percent() -> float:
    if psutil is None:
        return 0.0
    return float(psutil.virtual_memory().percent)


def disk_usage(path: str | Path) -> tuple[int, int, int]:
    try:
        total, used, free = 0, 0, 0
        if psutil is not None:
            d = psutil.disk_usage(str(path))
            total, used, free = int(d.total), int(d.used), int(d.free)
        else:
            stat = os.statvfs(str(path)) if hasattr(os, "statvfs") else None
            if stat is not None:
                total = stat.f_blocks * stat.f_frsize
                free = stat.f_bavail * stat.f_frsize
                used = total - free
    except OSError:
        return 0, 0, 0
    return total, used, free


def uptime_seconds() -> float:
    if psutil is None:
        return 0.0
    return max(0.0, time.time() - psutil.boot_time())


def process_count() -> int:
    if psutil is None:
        return 0
    try:
        return len(psutil.pids())
    except Exception:
        return 0


def network_interfaces() -> list[dict]:
    out: list[dict] = []
    if psutil is None:
        return out
    try:
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        for name, infos in addrs.items():
            s = stats.get(name)
            entry = {
                "name": name,
                "is_up": bool(s.isup) if s else False,
                "speed": int(s.speed) if s else 0,
                "addresses": [],
            }
            for a in infos:
                entry["addresses"].append({
                    "family": str(a.family),
                    "address": str(a.address),
                    "netmask": str(getattr(a, "netmask", "")),
                })
            out.append(entry)
    except Exception:
        return out
    return out


def public_python_packages() -> list[tuple[str, str]]:
    try:
        from importlib.metadata import distributions  # type: ignore
        items = []
        for d in distributions():
            try:
                items.append((d.metadata["Name"], d.version))
            except Exception:
                continue
        items.sort(key=lambda p: p[0].lower())
        return items
    except Exception:
        return []


def env_summary() -> dict[str, str]:
    keys = ("LANG", "LC_ALL", "USER", "USERNAME", "HOME", "USERPROFILE",
            "APPDATA", "LOCALAPPDATA", "TEMP", "TMP", "SHELL", "PATH")
    return {k: os.environ.get(k, "") for k in keys}


def to_text(snapshot: SystemSnapshot | None = None) -> str:
    snap = snapshot or collect()
    lines = [
        f"OS: {snap.os_name} {snap.os_release} ({snap.os_version})",
        f"Machine: {snap.machine}",
        f"CPU: {snap.processor}",
        f"Cores: {snap.cpu_count} physical / {snap.cpu_logical} logical",
        f"RAM: {snap.total_ram / 1_073_741_824:.1f} GB total, {snap.available_ram / 1_073_741_824:.1f} GB available",
        f"Host: {snap.hostname}",
        f"User: {snap.user}",
        f"Locale: {snap.locale}",
        f"Python: {snap.python_version} ({snap.python_executable})",
        f"PID: {snap.process_pid}",
        f"CWD: {snap.cwd}",
        f"PATH entries: {snap.env_path_count}",
    ]
    return "\n".join(lines)


def to_json() -> str:
    return json.dumps(collect().to_dict(), indent=2)
