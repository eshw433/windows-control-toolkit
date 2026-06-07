from __future__ import annotations

import hashlib
import os
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from loguru import logger

_BLOCK = 65536
_QUICK_BYTES = 4096


@dataclass
class DupGroup:
    digest: str
    paths: list[Path] = field(default_factory=list)
    size_each: int = 0

    @property
    def wasted_bytes(self) -> int:
        if not self.paths:
            return 0
        return self.size_each * (len(self.paths) - 1)


def _quick_hash(path: Path) -> str:
    try:
        with open(path, "rb") as f:
            data = f.read(_QUICK_BYTES)
        return hashlib.blake2b(data, digest_size=12).hexdigest()
    except OSError:
        return ""


def _full_hash(path: Path) -> str:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(_BLOCK), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError as exc:
        logger.warning("Cannot hash {}: {}", path, exc)
        return ""


def collect_files(folder: Path, *, recursive: bool = False,
                  min_size: int = 1) -> list[Path]:
    files: list[Path] = []
    if not folder.exists() or not folder.is_dir():
        return files
    iterator = folder.rglob("*") if recursive else folder.iterdir()
    for p in iterator:
        if not p.is_file():
            continue
        try:
            if p.stat().st_size >= min_size:
                files.append(p)
        except OSError:
            continue
    return files


def group_by_size(paths: list[Path]) -> dict[int, list[Path]]:
    out: dict[int, list[Path]] = defaultdict(list)
    for p in paths:
        try:
            out[p.stat().st_size].append(p)
        except OSError:
            continue
    return {k: v for k, v in out.items() if len(v) >= 2}


def find_duplicates_pro(folder: Path, *, recursive: bool = False,
                        min_size: int = 1024,
                        progress: callable | None = None) -> list[DupGroup]:
    paths = collect_files(folder, recursive=recursive, min_size=min_size)
    by_size = group_by_size(paths)
    quick_buckets: dict[tuple[int, str], list[Path]] = defaultdict(list)

    total_candidates = sum(len(v) for v in by_size.values())
    seen = 0
    for size, group in by_size.items():
        for p in group:
            q = _quick_hash(p)
            if q:
                quick_buckets[(size, q)].append(p)
            seen += 1
            if progress and seen % 50 == 0:
                progress(seen, total_candidates)

    groups: list[DupGroup] = []
    for (size, _qh), members in quick_buckets.items():
        if len(members) < 2:
            continue
        full_map: dict[str, list[Path]] = defaultdict(list)
        for p in members:
            digest = _full_hash(p)
            if digest:
                full_map[digest].append(p)
        for digest, items in full_map.items():
            if len(items) >= 2:
                groups.append(DupGroup(digest=digest, paths=items, size_each=size))

    groups.sort(key=lambda g: g.wasted_bytes, reverse=True)
    return groups


def find_duplicates_multi(folders: list[Path], *, recursive: bool = False,
                          min_size: int = 1024) -> list[DupGroup]:
    all_paths: list[Path] = []
    for f in folders:
        all_paths.extend(collect_files(f, recursive=recursive, min_size=min_size))
    by_size = defaultdict(list)
    for p in all_paths:
        try:
            by_size[p.stat().st_size].append(p)
        except OSError:
            pass

    quick: dict[tuple[int, str], list[Path]] = defaultdict(list)
    for size, group in by_size.items():
        if len(group) < 2:
            continue
        for p in group:
            q = _quick_hash(p)
            if q:
                quick[(size, q)].append(p)

    out: list[DupGroup] = []
    for (size, _qh), members in quick.items():
        if len(members) < 2:
            continue
        full: dict[str, list[Path]] = defaultdict(list)
        for p in members:
            d = _full_hash(p)
            if d:
                full[d].append(p)
        for d, items in full.items():
            if len(items) >= 2:
                out.append(DupGroup(digest=d, paths=items, size_each=size))
    return sorted(out, key=lambda g: g.wasted_bytes, reverse=True)


def total_wasted(groups: list[DupGroup]) -> int:
    return sum(g.wasted_bytes for g in groups)


def keep_oldest(group: DupGroup) -> tuple[Path, list[Path]]:
    if not group.paths:
        return Path(), []
    pairs = []
    for p in group.paths:
        try:
            pairs.append((p, p.stat().st_mtime))
        except OSError:
            pairs.append((p, 0.0))
    pairs.sort(key=lambda x: x[1])
    keep = pairs[0][0]
    drop = [p for p, _ in pairs[1:]]
    return keep, drop


def keep_newest(group: DupGroup) -> tuple[Path, list[Path]]:
    keep, _ = keep_oldest(group)
    pairs = []
    for p in group.paths:
        try:
            pairs.append((p, p.stat().st_mtime))
        except OSError:
            pairs.append((p, 0.0))
    pairs.sort(key=lambda x: x[1], reverse=True)
    return pairs[0][0], [p for p, _ in pairs[1:]]


def keep_shortest_path(group: DupGroup) -> tuple[Path, list[Path]]:
    if not group.paths:
        return Path(), []
    paths = sorted(group.paths, key=lambda p: len(str(p)))
    return paths[0], paths[1:]


def remove_duplicates(groups: list[DupGroup], strategy: str = "oldest",
                      *, dry_run: bool = True) -> dict:
    removed: list[str] = []
    failed: list[tuple[str, str]] = []
    freed = 0
    for g in groups:
        if strategy == "newest":
            keep, drop = keep_newest(g)
        elif strategy == "shortest":
            keep, drop = keep_shortest_path(g)
        else:
            keep, drop = keep_oldest(g)
        for d in drop:
            if dry_run:
                removed.append(str(d))
                freed += g.size_each
                continue
            try:
                os.remove(d)
                removed.append(str(d))
                freed += g.size_each
            except OSError as exc:
                failed.append((str(d), str(exc)))
    return {"removed": removed, "failed": failed, "freed": freed, "dry_run": dry_run}


def summarize(groups: list[DupGroup]) -> dict:
    if not groups:
        return {"groups": 0, "files": 0, "wasted": 0}
    files = sum(len(g.paths) for g in groups)
    return {
        "groups": len(groups),
        "files": files,
        "wasted": total_wasted(groups),
        "largest_group": max(groups, key=lambda g: len(g.paths)),
    }
