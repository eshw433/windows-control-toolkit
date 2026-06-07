from __future__ import annotations

import hashlib
from collections import defaultdict
from pathlib import Path

from loguru import logger


_CHUNK_SIZE = 65536  # 64 KB


def hash_file(path: Path) -> str:
    """Compute SHA-256 of a file."""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while True:
                chunk = f.read(_CHUNK_SIZE)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except OSError as exc:
        logger.warning("Cannot hash {}: {}", path, exc)
        return ""


def find_duplicates(folder: Path, recursive: bool = False) -> dict[str, list[Path]]:
    """Find duplicate files in a folder by grouping on (size, hash).
    Returns hash -> list of paths with 2+ identical files.
    """
    # Phase 1: group by size
    size_groups: dict[int, list[Path]] = defaultdict(list)
    glob_pattern = "**/*" if recursive else "*"

    for p in folder.glob(glob_pattern):
        if p.is_file():
            try:
                size_groups[p.stat().st_size].append(p)
            except OSError:
                continue

    # Phase 2: hash only groups with >1 file of same size
    hash_groups: dict[str, list[Path]] = defaultdict(list)
    for size, paths in size_groups.items():
        if len(paths) < 2:
            continue
        for p in paths:
            h = hash_file(p)
            if h:
                hash_groups[h].append(p)

    # Phase 3: keep only actual duplicates
    duplicates = {h: paths for h, paths in hash_groups.items() if len(paths) >= 2}
    if duplicates:
        total = sum(len(v) - 1 for v in duplicates.values())
        logger.info("Found {} duplicate groups ({} redundant files) in {}", len(duplicates), total, folder)
    return duplicates
