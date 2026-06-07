from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import QTimer

from loguru import logger


class PeriodicTask:

    def __init__(self, name: str, callback: Callable[[], None], interval_ms: int) -> None:
        self.name = name
        self._callback = callback
        self._timer = QTimer()
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self._run)

    def _run(self) -> None:
        try:
            self._callback()
        except Exception as exc:
            logger.error("PeriodicTask '{}' failed: {}", self.name, exc)

    def start(self) -> None:
        logger.info("Scheduler: starting '{}'  every {} ms", self.name, self._timer.interval())
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()
        logger.info("Scheduler: stopped '{}'", self.name)

    def set_interval(self, ms: int) -> None:
        self._timer.setInterval(ms)

    @property
    def is_active(self) -> bool:
        return self._timer.isActive()


class Scheduler:

    def __init__(self) -> None:
        self._tasks: dict[str, PeriodicTask] = {}

    def register(self, name: str, callback: Callable[[], None], interval_ms: int) -> PeriodicTask:
        task = PeriodicTask(name, callback, interval_ms)
        self._tasks[name] = task
        return task

    def start_all(self) -> None:
        for task in self._tasks.values():
            task.start()

    def stop_all(self) -> None:
        for task in self._tasks.values():
            task.stop()

    def get(self, name: str) -> PeriodicTask | None:
        return self._tasks.get(name)
