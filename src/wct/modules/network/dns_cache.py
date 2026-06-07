from __future__ import annotations

import socket
import threading
import time
from collections import OrderedDict


class DnsCache:
    def __init__(self, *, max_size: int = 4096, ttl_sec: int = 600) -> None:
        self._store: OrderedDict[str, tuple[str, float]] = OrderedDict()
        self._reverse: OrderedDict[str, tuple[str, float]] = OrderedDict()
        self._max = max_size
        self._ttl = ttl_sec
        self._lock = threading.RLock()
        self._stats = {"hits": 0, "misses": 0, "errors": 0}

    def resolve(self, host: str) -> str:
        if not host:
            return ""
        with self._lock:
            cached = self._store.get(host)
            if cached and cached[1] > time.time():
                self._stats["hits"] += 1
                self._store.move_to_end(host)
                return cached[0]
            self._stats["misses"] += 1
        ip = ""
        try:
            ip = socket.gethostbyname(host)
        except OSError:
            with self._lock:
                self._stats["errors"] += 1
        if ip:
            with self._lock:
                self._store[host] = (ip, time.time() + self._ttl)
                self._evict()
        return ip

    def reverse(self, ip: str) -> str:
        if not ip:
            return ""
        with self._lock:
            cached = self._reverse.get(ip)
            if cached and cached[1] > time.time():
                self._stats["hits"] += 1
                self._reverse.move_to_end(ip)
                return cached[0]
            self._stats["misses"] += 1
        host = ""
        try:
            host, _aliases, _addrs = socket.gethostbyaddr(ip)
        except OSError:
            with self._lock:
                self._stats["errors"] += 1
        with self._lock:
            self._reverse[ip] = (host, time.time() + self._ttl)
            self._evict_reverse()
        return host

    def stats(self) -> dict[str, int]:
        with self._lock:
            return dict(self._stats)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            self._reverse.clear()

    def known_hosts(self) -> list[str]:
        with self._lock:
            return list(self._store.keys())

    def known_ips(self) -> list[str]:
        with self._lock:
            return list(self._reverse.keys())

    def remove(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)
            self._reverse.pop(key, None)

    def warm_up(self, hosts: list[str]) -> int:
        success = 0
        for h in hosts:
            if self.resolve(h):
                success += 1
        return success

    def _evict(self) -> None:
        now = time.time()
        keys_to_remove = [k for k, v in self._store.items() if v[1] < now]
        for k in keys_to_remove:
            self._store.pop(k, None)
        while len(self._store) > self._max:
            self._store.popitem(last=False)

    def _evict_reverse(self) -> None:
        now = time.time()
        keys_to_remove = [k for k, v in self._reverse.items() if v[1] < now]
        for k in keys_to_remove:
            self._reverse.pop(k, None)
        while len(self._reverse) > self._max:
            self._reverse.popitem(last=False)


_default = DnsCache()


def resolve(host: str) -> str:
    return _default.resolve(host)


def reverse(ip: str) -> str:
    return _default.reverse(ip)


def clear() -> None:
    _default.clear()


def stats() -> dict[str, int]:
    return _default.stats()
