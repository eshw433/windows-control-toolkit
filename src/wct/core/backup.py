from __future__ import annotations

import json
import os
import shutil
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger


@dataclass
class BackupInfo:
    path: Path
    size: int
    created_at: str
    tag: str


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def backup_database(db_path: Path, target_dir: Path,
                    *, tag: str = "manual") -> BackupInfo:
    target_dir.mkdir(parents=True, exist_ok=True)
    name = f"wct-db-{_stamp()}-{tag}.sqlite"
    out = target_dir / name
    shutil.copy2(db_path, out)
    size = out.stat().st_size
    info = BackupInfo(path=out, size=size, created_at=_stamp(), tag=tag)
    logger.info("Database backed up to {} ({} bytes)", out, size)
    return info


def backup_settings(settings_path: Path, target_dir: Path,
                    *, tag: str = "manual") -> BackupInfo:
    target_dir.mkdir(parents=True, exist_ok=True)
    name = f"wct-settings-{_stamp()}-{tag}.json"
    out = target_dir / name
    shutil.copy2(settings_path, out)
    return BackupInfo(path=out, size=out.stat().st_size,
                      created_at=_stamp(), tag=tag)


def bundle_backup(paths: list[Path], target_zip: Path,
                  *, tag: str = "bundle") -> BackupInfo:
    target_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in paths:
            if not p.exists():
                continue
            arcname = p.name
            zf.write(p, arcname=arcname)
        meta = {
            "version": 1,
            "tag": tag,
            "created_at": _stamp(),
            "items": [p.name for p in paths if p.exists()],
        }
        zf.writestr("backup_manifest.json", json.dumps(meta, indent=2))
    return BackupInfo(
        path=target_zip,
        size=target_zip.stat().st_size,
        created_at=_stamp(),
        tag=tag,
    )


def list_backups(target_dir: Path, *, pattern: str = "*") -> list[BackupInfo]:
    if not target_dir.exists():
        return []
    items: list[BackupInfo] = []
    for path in sorted(target_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True):
        if not path.is_file():
            continue
        items.append(BackupInfo(
            path=path,
            size=path.stat().st_size,
            created_at=datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
            tag="?",
        ))
    return items


def prune_backups(target_dir: Path, *, keep: int = 10,
                  pattern: str = "*") -> int:
    items = list_backups(target_dir, pattern=pattern)
    removed = 0
    for old in items[keep:]:
        try:
            old.path.unlink()
            removed += 1
        except OSError:
            continue
    return removed


def restore_database(backup_path: Path, db_path: Path) -> bool:
    if not backup_path.exists():
        return False
    try:
        if db_path.exists():
            backup_database(db_path, db_path.parent / "before_restore", tag="pre_restore")
        shutil.copy2(backup_path, db_path)
        logger.info("Database restored from {}", backup_path)
        return True
    except OSError as exc:
        logger.error("Restore failed: {}", exc)
        return False


def verify_backup(backup_path: Path) -> bool:
    if not backup_path.exists() or backup_path.stat().st_size < 16:
        return False
    if backup_path.suffix == ".sqlite":
        with open(backup_path, "rb") as fh:
            header = fh.read(16)
        return header.startswith(b"SQLite format 3")
    if backup_path.suffix == ".zip":
        try:
            with zipfile.ZipFile(backup_path) as zf:
                return zf.testzip() is None
        except zipfile.BadZipFile:
            return False
    return True


def schedule_daily_pruning(target_dir: Path, keep: int = 10) -> int:
    age_limit_days = 30
    removed = 0
    if not target_dir.exists():
        return 0
    now = datetime.now(timezone.utc).timestamp()
    for path in target_dir.iterdir():
        if not path.is_file():
            continue
        age_days = (now - path.stat().st_mtime) / 86400
        if age_days > age_limit_days:
            try:
                path.unlink()
                removed += 1
            except OSError:
                continue
    if keep > 0:
        removed += prune_backups(target_dir, keep=keep)
    return removed
