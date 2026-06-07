from __future__ import annotations

import re
from typing import Any, Iterable


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


def tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"[\s/_\-.\\:]+", text.lower()) if t]


def matches_query(query: str, *fields: str) -> bool:
    if not query:
        return True
    q = query.strip().lower()
    haystack = " ".join(f for f in fields if f).lower()
    if " " not in q:
        return q in haystack
    tokens = q.split()
    return all(t in haystack for t in tokens)


def filter_dicts(items: Iterable[dict[str, Any]], query: str,
                 keys: list[str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not query:
        return list(items)
    for it in items:
        if matches_query(query, *[str(it.get(k, "")) for k in keys]):
            out.append(it)
    return out


def highlight(text: str, query: str) -> str:
    if not query:
        return text
    pattern = re.escape(query)
    return re.sub(f"({pattern})", r"<<\1>>", text, flags=re.IGNORECASE)


def fuzzy_score(query: str, candidate: str) -> int:
    if not query:
        return 0
    if not candidate:
        return -1
    q = query.lower()
    c = candidate.lower()
    if q == c:
        return 1000
    if c.startswith(q):
        return 800 - len(c) + len(q)
    if q in c:
        return 600 - c.index(q)
    score = 0
    pos = 0
    for ch in q:
        i = c.find(ch, pos)
        if i < 0:
            return -1
        score += 10 - min(i - pos, 10)
        pos = i + 1
    return score


def fuzzy_filter(items: list[str], query: str, *, limit: int = 50) -> list[tuple[str, int]]:
    if not query:
        return [(s, 0) for s in items[:limit]]
    scored: list[tuple[str, int]] = []
    for it in items:
        s = fuzzy_score(query, it)
        if s >= 0:
            scored.append((it, s))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:limit]


def fuzzy_filter_dicts(items: list[dict[str, Any]], query: str, key: str,
                       *, limit: int = 50) -> list[dict[str, Any]]:
    if not query:
        return items[:limit]
    scored: list[tuple[dict[str, Any], int]] = []
    for it in items:
        s = fuzzy_score(query, str(it.get(key, "")))
        if s >= 0:
            scored.append((it, s))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [it for it, _ in scored[:limit]]


def make_regex(pattern: str, *, case_sensitive: bool = False) -> re.Pattern | None:
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        return re.compile(pattern, flags)
    except re.error:
        return None


def regex_filter(items: list[dict[str, Any]], pattern: str, keys: list[str]) -> list[dict[str, Any]]:
    regex = make_regex(pattern)
    if regex is None:
        return list(items)
    out: list[dict[str, Any]] = []
    for it in items:
        for k in keys:
            if regex.search(str(it.get(k, ""))):
                out.append(it)
                break
    return out
