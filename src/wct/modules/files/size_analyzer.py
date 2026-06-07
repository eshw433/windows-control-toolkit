from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from wct.shared.models import FILE_CATEGORIES


@dataclass
class HogEntry:
    path: Path
    size: int
    mtime: float
    extension: str
    category: str


@dataclass
class CategorySummary:
    category: str
    file_count: int
    total_size: int
    avg_size: int


def _classify(ext: str) -> str:
    ext = ext.lower()
    for cat, exts in FILE_CATEGORIES.items():
        if ext in exts:
            return cat
    return "Misc"


def walk_folder(folder: Path, *, recursive: bool = True,
                ignore_hidden: bool = True,
                ignored_exts: set[str] | None = None,
                max_depth: int | None = None) -> list[HogEntry]:
    entries: list[HogEntry] = []
    if not folder.exists() or not folder.is_dir():
        return entries
    ignored_exts = ignored_exts or set()
    root_len = len(folder.parts)

    if recursive:
        iterator: list[tuple[str, list[str], list[str]]] = list(os.walk(folder))
    else:
        iterator = [(str(folder), [], [p.name for p in folder.iterdir() if p.is_file()])]

    for root, _dirs, files in iterator:
        root_path = Path(root)
        if max_depth is not None and len(root_path.parts) - root_len > max_depth:
            continue
        for fname in files:
            if ignore_hidden and fname.startswith("."):
                continue
            ext = Path(fname).suffix.lower()
            if ext in ignored_exts:
                continue
            fp = root_path / fname
            try:
                st = fp.stat()
            except OSError:
                continue
            entries.append(HogEntry(
                path=fp,
                size=st.st_size,
                mtime=st.st_mtime,
                extension=ext,
                category=_classify(ext),
            ))
    return entries


def top_largest(entries: list[HogEntry], n: int = 50) -> list[HogEntry]:
    return sorted(entries, key=lambda e: e.size, reverse=True)[:n]


def top_oldest(entries: list[HogEntry], n: int = 50) -> list[HogEntry]:
    return sorted(entries, key=lambda e: e.mtime)[:n]


def stale_files(entries: list[HogEntry], days: int = 180) -> list[HogEntry]:
    cutoff = time.time() - days * 86400
    return [e for e in entries if e.mtime < cutoff]


def fresh_files(entries: list[HogEntry], days: int = 30) -> list[HogEntry]:
    cutoff = time.time() - days * 86400
    return [e for e in entries if e.mtime >= cutoff]


def by_extension(entries: list[HogEntry]) -> dict[str, list[HogEntry]]:
    grouped: dict[str, list[HogEntry]] = {}
    for e in entries:
        grouped.setdefault(e.extension or "(no ext)", []).append(e)
    return grouped


def category_summary(entries: list[HogEntry]) -> list[CategorySummary]:
    buckets: dict[str, list[int]] = {}
    counts: dict[str, int] = {}
    for e in entries:
        buckets.setdefault(e.category, []).append(e.size)
        counts[e.category] = counts.get(e.category, 0) + 1
    summaries: list[CategorySummary] = []
    for cat, sizes in buckets.items():
        total = sum(sizes)
        summaries.append(CategorySummary(
            category=cat,
            file_count=counts[cat],
            total_size=total,
            avg_size=total // max(counts[cat], 1),
        ))
    return sorted(summaries, key=lambda s: s.total_size, reverse=True)


def total_size(entries: list[HogEntry]) -> int:
    return sum(e.size for e in entries)


def filter_min_size(entries: list[HogEntry], min_bytes: int) -> list[HogEntry]:
    return [e for e in entries if e.size >= min_bytes]


def filter_max_size(entries: list[HogEntry], max_bytes: int) -> list[HogEntry]:
    return [e for e in entries if e.size <= max_bytes]


def filter_by_extension(entries: list[HogEntry], extensions: set[str]) -> list[HogEntry]:
    norm = {e.lower() for e in extensions}
    return [e for e in entries if e.extension in norm]


def filter_by_category(entries: list[HogEntry], category: str) -> list[HogEntry]:
    return [e for e in entries if e.category == category]


def folder_size_breakdown(folder: Path, recursive: bool = True) -> dict[str, int]:
    entries = walk_folder(folder, recursive=recursive)
    out: dict[str, int] = {}
    for e in entries:
        parent = str(e.path.parent.relative_to(folder)) if e.path.parent != folder else "."
        out[parent] = out.get(parent, 0) + e.size
    return dict(sorted(out.items(), key=lambda kv: kv[1], reverse=True))


def find_zero_byte(entries: list[HogEntry]) -> list[HogEntry]:
    return [e for e in entries if e.size == 0]


def find_huge(entries: list[HogEntry], threshold_mb: int = 500) -> list[HogEntry]:
    threshold = threshold_mb * 1024 * 1024
    return [e for e in entries if e.size >= threshold]


def histogram_by_size(entries: list[HogEntry]) -> dict[str, int]:
    buckets = {
        "<1 KB": 0,
        "1 KB - 100 KB": 0,
        "100 KB - 1 MB": 0,
        "1 MB - 10 MB": 0,
        "10 MB - 100 MB": 0,
        "100 MB - 1 GB": 0,
        ">=1 GB": 0,
    }
    for e in entries:
        s = e.size
        if s < 1024:
            buckets["<1 KB"] += 1
        elif s < 100 * 1024:
            buckets["1 KB - 100 KB"] += 1
        elif s < 1024 * 1024:
            buckets["100 KB - 1 MB"] += 1
        elif s < 10 * 1024 * 1024:
            buckets["1 MB - 10 MB"] += 1
        elif s < 100 * 1024 * 1024:
            buckets["10 MB - 100 MB"] += 1
        elif s < 1024 * 1024 * 1024:
            buckets["100 MB - 1 GB"] += 1
        else:
            buckets[">=1 GB"] += 1
    return buckets


def analyze(folder: Path, *, recursive: bool = True,
            ignored_exts: set[str] | None = None) -> dict:
    entries = walk_folder(folder, recursive=recursive, ignored_exts=ignored_exts)
    return {
        "folder": str(folder),
        "total_files": len(entries),
        "total_size": total_size(entries),
        "largest": top_largest(entries, 20),
        "oldest": top_oldest(entries, 20),
        "stale": stale_files(entries, 180),
        "categories": category_summary(entries),
        "histogram": histogram_by_size(entries),
        "zero_byte": find_zero_byte(entries),
        "huge": find_huge(entries, 500),
    }
