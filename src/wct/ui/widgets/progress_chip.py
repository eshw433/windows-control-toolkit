from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
from PyQt6.QtWidgets import QWidget


class ProgressChip(QWidget):
    def __init__(self, *, value: float = 0.0, label: str = "",
                 color: str = "#00d2ff", parent=None) -> None:
        super().__init__(parent)
        self._value = max(0.0, min(1.0, value))
        self._label = label
        self._color = QColor(color)
        self.setMinimumHeight(22)
        self.setFixedHeight(22)
        self.setMinimumWidth(140)

    def set_value(self, value: float) -> None:
        self._value = max(0.0, min(1.0, value))
        self.update()

    def set_label(self, text: str) -> None:
        self._label = text
        self.update()

    def set_color(self, color: str) -> None:
        self._color = QColor(color)
        self.update()

    def paintEvent(self, _ev) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        radius = h / 2

        painter.setBrush(QBrush(QColor("#0e1730")))
        painter.setPen(QPen(QColor("#1f2a44"), 1))
        painter.drawRoundedRect(0, 0, w - 1, h - 1, radius, radius)

        if self._value > 0:
            filled_w = max(int((w - 2) * self._value), int(2 * radius))
            painter.setBrush(QBrush(self._color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(1, 1, filled_w, h - 2, radius - 1, radius - 1)

        if self._label:
            painter.setPen(QColor("#e6edf7"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._label)


class Gauge(QWidget):
    def __init__(self, *, value: float = 0.0, max_value: float = 100.0,
                 color: str = "#00d2ff", parent=None) -> None:
        super().__init__(parent)
        self._value = value
        self._max = max(max_value, 1.0)
        self._color = QColor(color)
        self.setMinimumSize(110, 60)

    def set_value(self, value: float) -> None:
        self._value = value
        self.update()

    def set_max(self, max_value: float) -> None:
        self._max = max(max_value, 1.0)
        self.update()

    def paintEvent(self, _ev) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()

        pct = max(0.0, min(self._value / self._max, 1.0))

        bg = QColor("#1f2a44")
        painter.setBrush(QBrush(bg))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, h - 12, w, 8)

        painter.setBrush(QBrush(self._color))
        painter.drawRect(0, h - 12, int(w * pct), 8)

        painter.setPen(QColor("#e6edf7"))
        painter.drawText(self.rect().adjusted(0, 0, 0, -20),
                         Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter,
                         f"{int(pct * 100)}%")
