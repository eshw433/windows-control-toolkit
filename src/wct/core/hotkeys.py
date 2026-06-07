from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QWidget


@dataclass
class HotkeyBinding:
    key: str
    description: str
    group: str = "General"
    enabled: bool = True


class HotkeyManager:
    def __init__(self, target: QWidget) -> None:
        self._target = target
        self._bindings: dict[str, HotkeyBinding] = {}
        self._shortcuts: dict[str, QShortcut] = {}
        self._handlers: dict[str, Callable[[], None]] = {}

    def bind(self, key: str, description: str, *,
             group: str = "General",
             handler: Callable[[], None] | None = None) -> None:
        if not key:
            return
        normalized = QKeySequence(key).toString()
        self._bindings[normalized] = HotkeyBinding(
            key=normalized, description=description, group=group,
        )
        if handler is None:
            return
        old = self._shortcuts.get(normalized)
        if old is not None:
            old.activated.disconnect()
            old.setParent(None)
        sc = QShortcut(QKeySequence(normalized), self._target)
        sc.setContext(Qt.ShortcutContext.ApplicationShortcut)
        sc.activated.connect(handler)
        self._shortcuts[normalized] = sc
        self._handlers[normalized] = handler

    def list_all(self) -> list[HotkeyBinding]:
        return list(self._bindings.values())

    def list_by_group(self) -> dict[str, list[HotkeyBinding]]:
        out: dict[str, list[HotkeyBinding]] = {}
        for b in self._bindings.values():
            out.setdefault(b.group, []).append(b)
        return out

    def disable(self, key: str) -> None:
        normalized = QKeySequence(key).toString()
        sc = self._shortcuts.get(normalized)
        if sc is not None:
            sc.setEnabled(False)
        b = self._bindings.get(normalized)
        if b is not None:
            b.enabled = False

    def enable(self, key: str) -> None:
        normalized = QKeySequence(key).toString()
        sc = self._shortcuts.get(normalized)
        if sc is not None:
            sc.setEnabled(True)
        b = self._bindings.get(normalized)
        if b is not None:
            b.enabled = True

    def remove(self, key: str) -> None:
        normalized = QKeySequence(key).toString()
        sc = self._shortcuts.pop(normalized, None)
        if sc is not None:
            sc.setParent(None)
        self._handlers.pop(normalized, None)
        self._bindings.pop(normalized, None)

    def clear(self) -> None:
        for sc in self._shortcuts.values():
            sc.setParent(None)
        self._shortcuts.clear()
        self._handlers.clear()
        self._bindings.clear()
