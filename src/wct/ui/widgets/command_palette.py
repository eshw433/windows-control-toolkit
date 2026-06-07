from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from wct.core.command_palette import Command, CommandRegistry
from wct.core.i18n import t


class CommandPalette(QDialog):
    triggered = pyqtSignal(str)

    def __init__(self, registry: CommandRegistry, parent=None) -> None:
        super().__init__(parent)
        self._registry = registry
        self.setWindowTitle(t("palette_open"))
        self.setModal(True)
        self.setMinimumWidth(560)
        self.setMinimumHeight(440)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setStyleSheet(
            "QDialog { background-color: #10172a; border: 1px solid #2b3d68; border-radius: 14px; }"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        self._search = QLineEdit()
        self._search.setPlaceholderText(t("palette_placeholder"))
        self._search.setStyleSheet(
            "QLineEdit { background-color: #0d1428; border: 1px solid #2b3d68; "
            "border-radius: 10px; color: #e6ecf5; padding: 10px 14px; font-size: 15px; }"
            "QLineEdit:focus { border-color: #5cd0ff; }"
        )
        self._search.textChanged.connect(self._on_filter)
        self._search.returnPressed.connect(self._activate_current)
        root.addWidget(self._search)

        self._hint = QLabel(self._format_hint(0))
        self._hint.setStyleSheet("color: #5b6a8a; font-size: 11px; padding: 0 4px;")
        root.addWidget(self._hint)

        self._list = QListWidget()
        self._list.setStyleSheet(
            "QListWidget { background-color: transparent; border: none; }"
            "QListWidget::item { padding: 8px 10px; border-radius: 8px; color: #c0c8d8; }"
            "QListWidget::item:hover { background-color: #19243f; color: #84e1ff; }"
            "QListWidget::item:selected { background-color: #2b3d68; color: #84e1ff; }"
        )
        self._list.itemActivated.connect(self._on_item_activated)
        root.addWidget(self._list, stretch=1)

        self._populate(self._registry.filter())

    def _format_hint(self, count: int) -> str:
        return f"\u2191\u2193  navigate   \u23ce  run   Esc  close   \u00b7  {count} matches"

    def _populate(self, items: list[Command]) -> None:
        self._list.clear()
        for cmd in items:
            label = cmd.title
            if cmd.shortcut:
                label = f"{cmd.title}     {cmd.shortcut}"
            it = QListWidgetItem(f"  {label}")
            it.setData(Qt.ItemDataRole.UserRole, cmd.cid)
            it.setToolTip(f"{cmd.group} · {cmd.cid}")
            self._list.addItem(it)
        self._hint.setText(self._format_hint(len(items)))
        if items:
            self._list.setCurrentRow(0)

    def _on_filter(self, text: str) -> None:
        items = self._registry.filter(text)
        self._populate(items)

    def _on_item_activated(self, item: QListWidgetItem) -> None:
        cid = str(item.data(Qt.ItemDataRole.UserRole) or "")
        if cid:
            self.triggered.emit(cid)
            self.accept()

    def _activate_current(self) -> None:
        it = self._list.currentItem()
        if it is not None:
            self._on_item_activated(it)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            row = self._list.currentRow()
            row = row + (1 if event.key() == Qt.Key.Key_Down else -1)
            row = max(0, min(self._list.count() - 1, row))
            self._list.setCurrentRow(row)
            return
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._search.clear()
        self._search.setFocus()
        self._populate(self._registry.filter())
