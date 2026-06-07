from __future__ import annotations

import os
import platform
import socket
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from wct import __author__, __codename__, __license__, __url__, __version__


@dataclass
class BuildInfo:
    version: str
    codename: str
    author: str
    license: str
    url: str
    python_version: str
    python_implementation: str
    platform: str
    hostname: str
    bundle_root: str
    started_at: str

    def to_dict(self) -> dict:
        return asdict(self)


def collect() -> BuildInfo:
    return BuildInfo(
        version=__version__,
        codename=__codename__,
        author=__author__,
        license=__license__,
        url=__url__,
        python_version=sys.version.split()[0],
        python_implementation=platform.python_implementation(),
        platform=platform.platform(),
        hostname=socket.gethostname(),
        bundle_root=str(Path(__file__).resolve().parent.parent),
        started_at=datetime.now(timezone.utc).isoformat(),
    )


def to_text(info: BuildInfo | None = None) -> str:
    b = info or collect()
    return (
        f"Windows Control Toolkit v{b.version} ({b.codename})\n"
        f"Author:     {b.author}\n"
        f"License:    {b.license}\n"
        f"URL:        {b.url}\n"
        f"Python:     {b.python_implementation} {b.python_version}\n"
        f"Platform:   {b.platform}\n"
        f"Host:       {b.hostname}\n"
        f"Started at: {b.started_at}\n"
        f"Root:       {b.bundle_root}\n"
    )


def headline() -> str:
    return f"Windows Control Toolkit v{__version__} \u2014 \u201c{__codename__}\u201d"


def short_info() -> str:
    return f"v{__version__} \u00b7 {platform.python_implementation()} {sys.version.split()[0]}"
