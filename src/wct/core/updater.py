from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone

from loguru import logger

from wct import __version__


_RELEASES_URL = "https://api.github.com/repos/eshw433/windows-control-toolkit/releases/latest"


@dataclass
class ReleaseInfo:
    version: str
    published_at: str
    notes: str
    url: str
    is_newer: bool


def _parse_version(v: str) -> tuple[int, ...]:
    cleaned = v.strip().lstrip("vV")
    parts = cleaned.split("-")[0].split(".")
    out: list[int] = []
    for p in parts:
        try:
            out.append(int(p))
        except ValueError:
            out.append(0)
    while len(out) < 3:
        out.append(0)
    return tuple(out[:3])


def is_newer(remote: str, local: str = __version__) -> bool:
    return _parse_version(remote) > _parse_version(local)


def check_now(*, timeout: float = 4.0, url: str = _RELEASES_URL) -> ReleaseInfo | None:
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": f"WCT/{__version__}", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError) as exc:
        logger.debug("Update check failed: {}", exc)
        return None
    version = str(data.get("tag_name", "")).lstrip("v")
    if not version:
        return None
    return ReleaseInfo(
        version=version,
        published_at=str(data.get("published_at", "")),
        notes=str(data.get("body", "")).strip(),
        url=str(data.get("html_url", "")),
        is_newer=is_newer(version),
    )


def offline_status() -> ReleaseInfo:
    return ReleaseInfo(
        version=__version__,
        published_at=datetime.now(timezone.utc).isoformat(),
        notes="Local build",
        url="",
        is_newer=False,
    )


def current_version() -> str:
    return __version__


def cmp_versions(a: str, b: str) -> int:
    va, vb = _parse_version(a), _parse_version(b)
    if va == vb:
        return 0
    return 1 if va > vb else -1
