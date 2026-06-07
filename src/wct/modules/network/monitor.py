from __future__ import annotations

import socket
from typing import Any

import psutil
from loguru import logger

from wct.modules.network.models import LiveConnection


def _resolve_domain(ip: str) -> str:
    """Best-effort reverse DNS lookup (cached by OS)."""
    if not ip or ip.startswith("0.") or ip.startswith("127.") or ip == "::1":
        return ""
    try:
        host, _, _ = socket.gethostbyaddr(ip)
        return host
    except (socket.herror, socket.gaierror, OSError):
        return ""


class NetworkMonitor:
    """Reads live TCP/UDP connections and maps them to process info."""

    def __init__(self, resolve_dns: bool = True) -> None:
        self._resolve_dns = resolve_dns
        self._process_cache: dict[int, dict[str, Any]] = {}

    def snapshot(self) -> list[LiveConnection]:
        """Return a list of current connections with process metadata."""
        connections: list[LiveConnection] = []
        seen_pids: set[int] = set()

        for conn in psutil.net_connections(kind="inet"):
            if conn.pid is None or conn.pid == 0:
                continue

            proc_info = self._get_process_info(conn.pid)
            if proc_info is None:
                continue

            remote_addr = conn.raddr.ip if conn.raddr else ""
            remote_port = conn.raddr.port if conn.raddr else 0
            local_addr = conn.laddr.ip if conn.laddr else ""
            local_port = conn.laddr.port if conn.laddr else 0

            domain = ""
            if self._resolve_dns and remote_addr:
                domain = _resolve_domain(remote_addr)

            protocol = "tcp" if conn.type == socket.SOCK_STREAM else "udp"

            lc = LiveConnection(
                pid=conn.pid,
                exe_name=proc_info.get("name", ""),
                exe_path=proc_info.get("exe", ""),
                local_addr=local_addr,
                local_port=local_port,
                remote_addr=remote_addr,
                remote_port=remote_port,
                protocol=protocol,
                status=conn.status if hasattr(conn, "status") else "",
                remote_domain=domain,
            )
            connections.append(lc)

        return connections

    def _get_process_info(self, pid: int) -> dict[str, Any] | None:
        if pid in self._process_cache:
            return self._process_cache[pid]
        try:
            proc = psutil.Process(pid)
            info = {
                "name": proc.name(),
                "exe": proc.exe() if proc.exe() else "",
                "pid": pid,
            }
            self._process_cache[pid] = info
            return info
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None

    def clear_cache(self) -> None:
        self._process_cache.clear()
