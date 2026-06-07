from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from loguru import logger
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


class StableFileHandler(FileSystemEventHandler):
    """Waits for files to become stable before emitting events.

    A file is considered stable when its size does not change
    for ``stable_wait_sec`` seconds, and its extension is not
    in the ignored list (e.g. .crdownload, .part).
    """

    def __init__(
        self,
        on_stable_file: Callable[[Path], None],
        stable_wait_sec: float = 5.0,
        ignored_extensions: list[str] | None = None,
    ) -> None:
        super().__init__()
        self._on_stable = on_stable_file
        self._wait = stable_wait_sec
        self._ignored = set(e.lower() for e in (ignored_extensions or []))
        self._pending: dict[str, float] = {}  # path -> last_modified_time

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        self._schedule_check(event.src_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        self._schedule_check(event.src_path)

    def _schedule_check(self, path_str: str) -> None:
        p = Path(path_str)
        if p.suffix.lower() in self._ignored:
            return
        self._pending[path_str] = time.time()

    def check_pending(self) -> None:
        """Called periodically to process files that have stabilised."""
        now = time.time()
        ready: list[str] = []

        for path_str, last_mod in list(self._pending.items()):
            if now - last_mod >= self._wait:
                p = Path(path_str)
                if p.exists() and p.is_file():
                    ready.append(path_str)
                else:
                    # File was removed or is a directory now
                    ready.append(path_str)

        for path_str in ready:
            del self._pending[path_str]
            p = Path(path_str)
            if p.exists() and p.is_file():
                try:
                    self._on_stable(p)
                except Exception as exc:
                    logger.error("Error handling stable file {}: {}", p, exc)


class FileMonitor:
    """Watches multiple folders using watchdog Observer."""

    def __init__(
        self,
        folders: list[str],
        on_stable_file: Callable[[Path], None],
        stable_wait_sec: float = 5.0,
        ignored_extensions: list[str] | None = None,
    ) -> None:
        self._folders = folders
        self._handler = StableFileHandler(
            on_stable_file=on_stable_file,
            stable_wait_sec=stable_wait_sec,
            ignored_extensions=ignored_extensions,
        )
        self._observer = Observer()

    def start(self) -> None:
        for folder in self._folders:
            p = Path(folder)
            if p.exists() and p.is_dir():
                self._observer.schedule(self._handler, str(p), recursive=False)
                logger.info("Watching folder: {}", p)
            else:
                logger.warning("Folder does not exist, skipping: {}", folder)
        self._observer.start()
        logger.info("File monitor started")

    def stop(self) -> None:
        self._observer.stop()
        self._observer.join(timeout=5)
        logger.info("File monitor stopped")

    def check_pending(self) -> None:
        """Must be called periodically from a timer to process stable files."""
        self._handler.check_pending()

    @property
    def handler(self) -> StableFileHandler:
        return self._handler
