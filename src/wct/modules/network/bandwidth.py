from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque

import psutil
from loguru import logger


@dataclass
class ProcStat:
    pid: int
    name: str
    exe: str
    bytes_sent: int
    bytes_recv: int


@dataclass
class BandwidthSlice:
    pid: int
    exe: str
    name: str
    delta_sent: int
    delta_recv: int
    rate_sent: float
    rate_recv: float


class BandwidthTracker:
    def __init__(self, history_seconds: int = 600) -> None:
        self._previous: dict[int, tuple[int, int, float]] = {}
        self._history: dict[str, Deque[tuple[float, int, int]]] = defaultdict(
            lambda: deque(maxlen=history_seconds // 2),
        )
        self._totals: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        self._psutil_available = self._has_io_counters()
        self._fallback_warned = False

    @staticmethod
    def _has_io_counters() -> bool:
        try:
            for p in psutil.process_iter(["pid"]):
                if hasattr(p, "io_counters"):
                    p.io_counters()
                    return True
                break
        except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError, OSError):
            pass
        return False

    def sample(self) -> list[BandwidthSlice]:
        now = time.time()
        results: list[BandwidthSlice] = []
        new_state: dict[int, tuple[int, int, float]] = {}

        for proc in psutil.process_iter(["pid", "name", "exe"]):
            pid = proc.info["pid"]
            if pid is None or pid == 0:
                continue
            sent, recv = self._read_counters(proc)
            if sent < 0 or recv < 0:
                continue
            new_state[pid] = (sent, recv, now)

            previous = self._previous.get(pid)
            if not previous:
                continue

            prev_sent, prev_recv, prev_t = previous
            dt = max(now - prev_t, 0.001)
            delta_sent = max(sent - prev_sent, 0)
            delta_recv = max(recv - prev_recv, 0)
            if delta_sent == 0 and delta_recv == 0:
                continue

            exe = proc.info.get("exe") or ""
            name = proc.info.get("name") or ""
            results.append(BandwidthSlice(
                pid=pid,
                exe=exe,
                name=name,
                delta_sent=delta_sent,
                delta_recv=delta_recv,
                rate_sent=delta_sent / dt,
                rate_recv=delta_recv / dt,
            ))

            if exe:
                self._history[exe].append((now, delta_sent, delta_recv))
                totals = self._totals[exe]
                totals[0] += delta_sent
                totals[1] += delta_recv

        self._previous = new_state
        return results

    def history(self, exe: str) -> list[tuple[float, int, int]]:
        return list(self._history.get(exe, []))

    def totals(self) -> dict[str, tuple[int, int]]:
        return {k: (v[0], v[1]) for k, v in self._totals.items()}

    def reset_totals(self) -> None:
        self._totals.clear()

    def known_executables(self) -> list[str]:
        return list(self._history.keys())

    def average_rate(self, exe: str, window_sec: float = 60.0) -> tuple[float, float]:
        h = self._history.get(exe)
        if not h:
            return 0.0, 0.0
        cutoff = time.time() - window_sec
        sent_total = 0
        recv_total = 0
        first_ts = None
        for ts, ds, dr in h:
            if ts < cutoff:
                continue
            if first_ts is None:
                first_ts = ts
            sent_total += ds
            recv_total += dr
        if first_ts is None:
            return 0.0, 0.0
        dt = max(time.time() - first_ts, 0.001)
        return sent_total / dt, recv_total / dt

    def _read_counters(self, proc: psutil.Process) -> tuple[int, int]:
        if self._psutil_available:
            try:
                counters = proc.io_counters()  # type: ignore[attr-defined]
                return int(counters.write_bytes), int(counters.read_bytes)
            except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError, OSError):
                pass
        else:
            if not self._fallback_warned:
                logger.info("Bandwidth: io_counters unavailable, using connection count fallback")
                self._fallback_warned = True
        try:
            count = len(proc.connections(kind="inet"))
            return count * 32, count * 32
        except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
            return -1, -1


class TrafficSummary:
    def __init__(self) -> None:
        self.bytes_sent = 0
        self.bytes_recv = 0
        self.samples = 0
        self._top: dict[str, list[int]] = defaultdict(lambda: [0, 0])

    def add_slice(self, slc: BandwidthSlice) -> None:
        self.bytes_sent += slc.delta_sent
        self.bytes_recv += slc.delta_recv
        self.samples += 1
        if slc.exe:
            t = self._top[slc.exe]
            t[0] += slc.delta_sent
            t[1] += slc.delta_recv

    def top_exes(self, n: int = 10) -> list[tuple[str, int, int]]:
        items = sorted(
            self._top.items(),
            key=lambda kv: kv[1][0] + kv[1][1],
            reverse=True,
        )[:n]
        return [(e, v[0], v[1]) for e, v in items]

    def reset(self) -> None:
        self.bytes_sent = 0
        self.bytes_recv = 0
        self.samples = 0
        self._top.clear()


def aggregate_per_exe(slices: list[BandwidthSlice]) -> dict[str, tuple[int, int]]:
    out: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for s in slices:
        if not s.exe:
            continue
        out[s.exe][0] += s.delta_sent
        out[s.exe][1] += s.delta_recv
    return {k: (v[0], v[1]) for k, v in out.items()}


def compute_total(slices: list[BandwidthSlice]) -> tuple[int, int]:
    sent = sum(s.delta_sent for s in slices)
    recv = sum(s.delta_recv for s in slices)
    return sent, recv
