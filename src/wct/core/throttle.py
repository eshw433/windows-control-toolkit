from __future__ import annotations

import functools
import time
from collections import defaultdict
from typing import Any, Callable


def throttle(seconds: float) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    state: dict[Callable[..., Any], float] = {}

    def wrap(fn: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(fn)
        def inner(*args: Any, **kwargs: Any):
            now = time.monotonic()
            last = state.get(fn, 0.0)
            if now - last < seconds:
                return None
            state[fn] = now
            return fn(*args, **kwargs)
        return inner
    return wrap


def debounce_last(seconds: float) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """NOTE: Use SearchBox (QTimer-based debounce) for UI. This is for non-UI use only."""
    state: dict[Callable[..., Any], float] = {}

    def wrap(fn: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(fn)
        def inner(*args: Any, **kwargs: Any):
            state[fn] = time.monotonic()
            # Non-blocking: just record the call time; caller must check
            return None
        return inner
    return wrap


def rate_limit(per_second: int) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    counters: dict[Callable[..., Any], list[float]] = defaultdict(list)

    def wrap(fn: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(fn)
        def inner(*args: Any, **kwargs: Any):
            now = time.monotonic()
            window = counters[fn]
            cutoff = now - 1.0
            while window and window[0] < cutoff:
                window.pop(0)
            if len(window) >= per_second:
                return None
            window.append(now)
            return fn(*args, **kwargs)
        return inner
    return wrap


class Cooldown:
    def __init__(self, seconds: float) -> None:
        self._seconds = seconds
        self._last: dict[str, float] = {}

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        last = self._last.get(key, 0.0)
        if now - last < self._seconds:
            return False
        self._last[key] = now
        return True

    def reset(self, key: str | None = None) -> None:
        if key is None:
            self._last.clear()
        else:
            self._last.pop(key, None)
