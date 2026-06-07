from __future__ import annotations

import socket
import threading
from typing import Callable


class DnsCache:

    def __init__(self, max_size: int = 10_000) -> None:
        self._cache: dict[str, str] = {}
        self._lock = threading.Lock()
        self._max = max_size

    def get(self, ip: str) -> str | None:
        with self._lock:
            return self._cache.get(ip)

    def put(self, ip: str, hostname: str) -> None:
        with self._lock:
            if len(self._cache) >= self._max:
                oldest = next(iter(self._cache))
                del self._cache[oldest]
            self._cache[ip] = hostname

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()


class BatchDnsResolver:
    """Resolves a batch of IPs in background threads."""

    def __init__(self) -> None:
        self.cache = DnsCache()

    def resolve(self, ip: str) -> str:
        cached = self.cache.get(ip)
        if cached is not None:
            return cached
        try:
            host, _, _ = socket.gethostbyaddr(ip)
        except (socket.herror, socket.gaierror, OSError):
            host = ""
        self.cache.put(ip, host)
        return host

    def resolve_batch(self, ips: list[str], callback: Callable[[dict[str, str]], None] | None = None) -> dict[str, str]:
        results: dict[str, str] = {}
        threads: list[threading.Thread] = []

        def _resolve_one(ip: str) -> None:
            results[ip] = self.resolve(ip)

        for ip in set(ips):
            if not ip or ip.startswith("0.") or ip.startswith("127.") or ip == "::1":
                results[ip] = ""
                continue
            t = threading.Thread(target=_resolve_one, args=(ip,), daemon=True)
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=2.0)

        if callback:
            callback(results)
        return results
