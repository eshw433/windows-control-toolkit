from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass


@dataclass
class Bucket:
    name: str
    count: int = 0
    total: float = 0.0
    minimum: float = float("inf")
    maximum: float = float("-inf")

    @property
    def mean(self) -> float:
        if self.count == 0:
            return 0.0
        return self.total / self.count


def aggregate_by(rows: list[dict], key: str,
                 value: str = "size") -> list[Bucket]:
    buckets: dict[str, Bucket] = {}
    for r in rows:
        name = str(r.get(key, ""))
        val = float(r.get(value, 0) or 0)
        bucket = buckets.setdefault(name, Bucket(name=name))
        bucket.count += 1
        bucket.total += val
        if val < bucket.minimum:
            bucket.minimum = val
        if val > bucket.maximum:
            bucket.maximum = val
    return sorted(buckets.values(), key=lambda b: b.total, reverse=True)


def histogram(values: list[float], *, bins: int = 10) -> list[tuple[float, float, int]]:
    if not values:
        return []
    lo = min(values)
    hi = max(values)
    if hi <= lo:
        hi = lo + 1.0
    width = (hi - lo) / bins
    counts = [0] * bins
    for v in values:
        idx = min(int((v - lo) / width), bins - 1)
        counts[idx] += 1
    return [(lo + i * width, lo + (i + 1) * width, counts[i]) for i in range(bins)]


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    p = max(0.0, min(1.0, p))
    idx = int(p * (len(s) - 1))
    return s[idx]


def quartiles(values: list[float]) -> tuple[float, float, float]:
    return percentile(values, 0.25), percentile(values, 0.50), percentile(values, 0.75)


def top_n(items: list[dict], *, key: str, n: int = 10,
          ascending: bool = False) -> list[dict]:
    return sorted(items, key=lambda d: d.get(key, 0), reverse=not ascending)[:n]


def count_by(items: list[dict], key: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for it in items:
        counter[str(it.get(key, ""))] += 1
    return dict(counter)


def group_by(items: list[dict], key: str) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for it in items:
        groups[str(it.get(key, ""))].append(it)
    return dict(groups)


def share(value: float, total: float) -> float:
    if total <= 0:
        return 0.0
    return value / total


def percent_of(value: float, total: float) -> float:
    return share(value, total) * 100.0


def running_avg(values: list[float], *, window: int = 5) -> list[float]:
    if window <= 0 or not values:
        return []
    out: list[float] = []
    acc: list[float] = []
    for v in values:
        acc.append(v)
        if len(acc) > window:
            acc.pop(0)
        out.append(sum(acc) / len(acc))
    return out


def rolling_max(values: list[float], *, window: int = 5) -> list[float]:
    if window <= 0 or not values:
        return []
    out: list[float] = []
    acc: list[float] = []
    for v in values:
        acc.append(v)
        if len(acc) > window:
            acc.pop(0)
        out.append(max(acc))
    return out


def variance(values: list[float]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return sum((v - mean) ** 2 for v in values) / len(values)


def stddev(values: list[float]) -> float:
    return variance(values) ** 0.5


def normalized(values: list[float]) -> list[float]:
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi <= lo:
        return [0.0 for _ in values]
    return [(v - lo) / (hi - lo) for v in values]


def severity_breakdown(events: list[dict]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for ev in events:
        counter[str(ev.get("severity", "info"))] += 1
    return dict(counter)


def module_breakdown(events: list[dict]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for ev in events:
        counter[str(ev.get("module", ""))] += 1
    return dict(counter)


def hour_of_day_distribution(timestamps: list[str]) -> dict[int, int]:
    from datetime import datetime
    counter: Counter[int] = Counter()
    for ts in timestamps:
        try:
            if ts.endswith("Z"):
                ts = ts.replace("Z", "+00:00")
            dt = datetime.fromisoformat(ts)
            counter[dt.hour] += 1
        except ValueError:
            continue
    return dict(counter)
