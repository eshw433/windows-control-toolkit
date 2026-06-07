from __future__ import annotations

import os
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


_TRUSTED_PATH_HINTS = (
    "windows\\system32",
    "windows/system32",
    "windows\\syswow64",
    "windows/syswow64",
    "program files",
    "program files (x86)",
    "/usr/bin",
    "/usr/sbin",
    "/usr/local/bin",
    "/bin",
    "/sbin",
)

_RISKY_PATH_HINTS = (
    "appdata\\roaming",
    "appdata/roaming",
    "appdata\\local\\temp",
    "appdata/local/temp",
    "\\temp\\",
    "/tmp/",
    "downloads",
    "desktop",
    "documents",
    "users\\public",
    "users/public",
)

_RANDOM_NAME = re.compile(r"^[a-z0-9]{8,}(\.exe)?$", re.IGNORECASE)
_HEXY = re.compile(r"^[0-9a-f]{12,}$", re.IGNORECASE)
_SETUPISH = re.compile(r"setup[_-][0-9a-f]{6,}\.exe$", re.IGNORECASE)


@dataclass
class RiskReport:
    score: int
    level: str
    reasons: list[str]


def assess(exe_path: str, *, is_signed: bool | None = None,
           has_publisher: bool | None = None,
           remote_ports: list[int] | None = None) -> RiskReport:
    p = (exe_path or "").lower()
    reasons: list[str] = []
    score = 0

    if not p:
        return RiskReport(score=0, level="low", reasons=[])

    if any(h in p for h in _TRUSTED_PATH_HINTS):
        score -= 30
        reasons.append("Trusted system path")

    if any(h in p for h in _RISKY_PATH_HINTS):
        score += 40
        reasons.append("Risky path (Temp/AppData/Downloads)")

    name = Path(p).name
    if _RANDOM_NAME.match(name):
        score += 25
        reasons.append("Random-looking filename")
    if _HEXY.match(name.split(".", 1)[0]):
        score += 20
        reasons.append("Hexadecimal filename")
    if _SETUPISH.search(name):
        score += 15
        reasons.append("Installer-like random name")

    if is_signed is False:
        score += 40
        reasons.append("Unsigned executable")
    elif is_signed is True:
        score -= 15
        reasons.append("Signed executable")

    if has_publisher is False:
        score += 10
        reasons.append("No publisher info")

    for port in remote_ports or []:
        if port in {23, 4444, 6667, 31337, 8888}:
            score += 25
            reasons.append(f"Suspicious port {port}")
        if 1024 <= port <= 4999:
            score += 5

    score = max(0, min(score, 100))
    level = _level_for(score)
    return RiskReport(score=score, level=level, reasons=reasons)


def _level_for(score: int) -> str:
    if score >= 70:
        return "critical"
    if score >= 45:
        return "high"
    if score >= 20:
        return "medium"
    return "low"


def assess_many(processes: list[dict]) -> list[dict]:
    out: list[dict] = []
    for p in processes:
        report = assess(p.get("exe_path", ""), is_signed=p.get("signed"))
        d = dict(p)
        d["risk_score"] = report.score
        d["risk_level"] = report.level
        d["note"] = ", ".join(report.reasons)
        out.append(d)
    return out


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskResult:
    score: int
    level: str
    reasons: list[str]


def score_connection(remote_port: int = 0, remote_ip: str = "", exe_name: str = "") -> RiskResult:
    report = assess(exe_name, remote_ports=[remote_port])
    return RiskResult(score=report.score, level=report.level, reasons=report.reasons)


def color_for_score(score: int) -> str:
    if score >= 70:
        return "#e74c3c"
    if score >= 45:
        return "#e67e22"
    if score >= 20:
        return "#f39c12"
    return "#27ae60"
