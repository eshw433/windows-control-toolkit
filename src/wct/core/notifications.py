from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from PyQt6.QtCore import QObject, pyqtSignal
from loguru import logger

from wct.core.i18n import t


_LEVELS = ("info", "warn", "error", "critical")


@dataclass
class NotificationPayload:
    title: str
    body: str = ""
    level: str = "info"
    module: str = ""
    metadata: dict = field(default_factory=dict)


class NotificationCenter(QObject):
    posted = pyqtSignal(object)

    def __init__(self) -> None:
        super().__init__()
        self._subscribers: list[Callable[[NotificationPayload], None]] = []
        self._history: list[NotificationPayload] = []
        self._tray = None
        self._db_repo = None
        self._mute: set[str] = set()
        self._tray_levels = {"warn", "error", "critical"}

    def bind_tray(self, tray) -> None:
        self._tray = tray

    def bind_repo(self, repo) -> None:
        self._db_repo = repo

    def subscribe(self, fn: Callable[[NotificationPayload], None]) -> None:
        self._subscribers.append(fn)

    def mute(self, module: str) -> None:
        self._mute.add(module)

    def unmute(self, module: str) -> None:
        self._mute.discard(module)

    def is_muted(self, module: str) -> bool:
        return module in self._mute

    def post(self, title: str, body: str = "", *,
             level: str = "info", module: str = "",
             metadata: dict | None = None) -> NotificationPayload:
        if level not in _LEVELS:
            level = "info"
        payload = NotificationPayload(
            title=title,
            body=body,
            level=level,
            module=module,
            metadata=metadata or {},
        )
        self._history.append(payload)
        if len(self._history) > 500:
            self._history = self._history[-500:]
        if self.is_muted(module):
            logger.debug("Notification muted ({}): {}", module, title)
            return payload
        try:
            self.posted.emit(payload)
        except Exception as exc:
            logger.warning("NotificationCenter.posted failed: {}", exc)
        for fn in list(self._subscribers):
            try:
                fn(payload)
            except Exception as exc:
                logger.warning("Notification subscriber error: {}", exc)
        if self._tray and level in self._tray_levels:
            try:
                self._tray.notify(title, body, level=level)
            except Exception as exc:
                logger.warning("Tray notification failed: {}", exc)
        if self._db_repo is not None:
            try:
                self._db_repo.insert(
                    module=module or "system",
                    title=title,
                    body=body,
                )
            except Exception as exc:
                logger.warning("Notification persist failed: {}", exc)
        return payload

    def info(self, title: str, body: str = "", **kw) -> NotificationPayload:
        return self.post(title, body, level="info", **kw)

    def warn(self, title: str, body: str = "", **kw) -> NotificationPayload:
        return self.post(title, body, level="warn", **kw)

    def error(self, title: str, body: str = "", **kw) -> NotificationPayload:
        return self.post(title, body, level="error", **kw)

    def critical(self, title: str, body: str = "", **kw) -> NotificationPayload:
        return self.post(title, body, level="critical", **kw)

    def recent(self, limit: int = 50) -> list[NotificationPayload]:
        return self._history[-limit:]

    def clear_history(self) -> None:
        self._history.clear()


_center: NotificationCenter | None = None


def get_center() -> NotificationCenter:
    global _center
    if _center is None:
        _center = NotificationCenter()
    return _center


def post(title: str, body: str = "", *, level: str = "info",
         module: str = "") -> NotificationPayload:
    return get_center().post(title, body, level=level, module=module)


def info(title: str, body: str = "", **kw) -> NotificationPayload:
    return get_center().info(title, body, **kw)


def warn(title: str, body: str = "", **kw) -> NotificationPayload:
    return get_center().warn(title, body, **kw)


def error(title: str, body: str = "", **kw) -> NotificationPayload:
    return get_center().error(title, body, **kw)


def critical(title: str, body: str = "", **kw) -> NotificationPayload:
    return get_center().critical(title, body, **kw)
