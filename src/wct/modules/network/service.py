from __future__ import annotations

from dataclasses import asdict
from typing import Any

from loguru import logger
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

from wct.config.settings import AppSettings
from wct.core.event_bus import EventBus
from wct.db.repositories import (
    EventRepository,
    NetworkConnectionRepository,
    NotificationRepository,
    ProcessIdentityRepository,
)
from wct.modules.network.monitor import NetworkMonitor
from wct.modules.network.models import LiveConnection


# ---------------------------------------------------------------------------
# Background worker
# ---------------------------------------------------------------------------

class NetworkWorker(QObject):
    """Runs in a QThread — polls psutil periodically."""

    connections_ready = pyqtSignal(list)  # list[dict]
    new_app_detected = pyqtSignal(str, str)  # exe_name, exe_path
    error = pyqtSignal(str)

    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self._settings = settings
        self._monitor = NetworkMonitor(resolve_dns=settings.network.resolve_dns)
        self._running = False
        self._known_paths: set[str] = set()
        self._paused = False

    @pyqtSlot()
    def start_polling(self) -> None:
        import time
        self._running = True
        while self._running:
            if not self._paused:
                try:
                    conns = self._monitor.snapshot()
                    data = self._to_dicts(conns)
                    self.connections_ready.emit(data)

                    # Detect new apps
                    for c in conns:
                        if c.exe_path and c.exe_path not in self._known_paths:
                            self._known_paths.add(c.exe_path)
                            self.new_app_detected.emit(c.exe_name, c.exe_path)
                except Exception as exc:
                    self.error.emit(str(exc))

            time.sleep(self._settings.network.poll_interval_sec)

    def stop(self) -> None:
        self._running = False

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def set_known_paths(self, paths: set[str]) -> None:
        self._known_paths = paths

    @staticmethod
    def _to_dicts(conns: list[LiveConnection]) -> list[dict[str, Any]]:
        return [asdict(c) for c in conns]


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class NetworkService:
    """High-level network module service — owns worker thread and repos."""

    def __init__(
        self,
        settings: AppSettings,
        process_repo: ProcessIdentityRepository,
        conn_repo: NetworkConnectionRepository,
        events_repo: EventRepository,
        notif_repo: NotificationRepository,
    ) -> None:
        self._settings = settings
        self._process_repo = process_repo
        self._conn_repo = conn_repo
        self._events_repo = events_repo
        self._notif_repo = notif_repo

        self._worker = NetworkWorker(settings)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.start_polling)

        # Pre-load known process paths from DB
        known = self._process_repo.get_all()
        self._worker.set_known_paths({p["exe_path"] for p in known})

        # Connect signals
        self._worker.new_app_detected.connect(self._on_new_app)
        self._worker.error.connect(self._on_error)

    def start(self) -> None:
        self._thread.start()
        logger.info("Network service started")

    def stop(self) -> None:
        self._worker.stop()
        self._thread.quit()
        self._thread.wait(3000)
        logger.info("Network service stopped")

    def pause(self) -> None:
        self._worker.pause()

    def resume(self) -> None:
        self._worker.resume()

    @property
    def worker(self) -> NetworkWorker:
        return self._worker

    # -- signal handlers -----------------------------------------------------

    def _on_new_app(self, exe_name: str, exe_path: str) -> None:
        self._process_repo.upsert(exe_path=exe_path, exe_name=exe_name)
        self._events_repo.insert(
            module="network",
            severity="info",
            event_type="new_app",
            title=f"New network app: {exe_name}",
            metadata={"exe_path": exe_path},
        )
        if self._settings.network.learning_mode:
            self._notif_repo.insert(
                module="network",
                title=f"New app detected: {exe_name}",
                body=f"Path: {exe_path}",
                action={"type": "trust_decision", "exe_path": exe_path},
            )
        EventBus.emit("network.new_app", exe_name=exe_name, exe_path=exe_path)
        logger.info("New network app detected: {} ({})", exe_name, exe_path)

    def _on_error(self, msg: str) -> None:
        logger.error("Network worker error: {}", msg)
