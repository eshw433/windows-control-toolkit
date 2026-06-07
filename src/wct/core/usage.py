from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from loguru import logger

from wct.config.paths import AppPaths


@dataclass
class UsageEvent:
    ts: float
    kind: str
    key: str
    payload: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"ts": self.ts, "kind": self.kind, "key": self.key, "payload": self.payload}


def _file_path() -> Path:
    return AppPaths.data_dir() / "usage.jsonl"


def record(kind: str, key: str, **payload) -> None:
    ev = UsageEvent(ts=time.time(), kind=kind, key=key, payload=payload)
    try:
        with _file_path().open("a", encoding="utf-8") as f:
            f.write(json.dumps(ev.to_dict()) + "\n")
    except OSError as exc:
        logger.debug("Usage record failed: {}", exc)


def read_all(limit: int = 5000) -> list[UsageEvent]:
    path = _file_path()
    if not path.exists():
        return []
    out: list[UsageEvent] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    out.append(UsageEvent(
                        ts=float(obj.get("ts", 0.0)),
                        kind=str(obj.get("kind", "")),
                        key=str(obj.get("key", "")),
                        payload=obj.get("payload") or {},
                    ))
                except ValueError:
                    continue
    except OSError as exc:
        logger.debug("Usage read failed: {}", exc)
    if len(out) > limit:
        out = out[-limit:]
    return out


def aggregate(kind: str | None = None) -> dict[str, int]:
    counts: dict[str, int] = {}
    for ev in read_all():
        if kind is not None and ev.kind != kind:
            continue
        counts[ev.key] = counts.get(ev.key, 0) + 1
    return counts


def top_keys(kind: str | None = None, limit: int = 10) -> list[tuple[str, int]]:
    pairs = sorted(aggregate(kind).items(), key=lambda kv: kv[1], reverse=True)
    return pairs[:limit]


def reset() -> None:
    path = _file_path()
    try:
        if path.exists():
            path.unlink()
    except OSError as exc:
        logger.debug("Usage reset failed: {}", exc)


def event_count() -> int:
    path = _file_path()
    if not path.exists():
        return 0
    try:
        with path.open("rb") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0
