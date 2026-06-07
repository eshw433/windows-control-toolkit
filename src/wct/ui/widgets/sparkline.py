from __future__ import annotations

from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QLinearGradient
from PyQt6.QtWidgets import QWidget


class Sparkline(QWidget):
    def __init__(self, values: list[float] | None = None, *,
                 color: str = "#00d2ff",
                 fill: bool = True,
                 baseline: bool = False,
                 parent=None) -> None:
        super().__init__(parent)
        self._values: list[float] = list(values or [])
        self._color = QColor(color)
        self._fill = fill
        self._baseline = baseline
        self.setMinimumHeight(36)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

    def set_color(self, color: str) -> None:
        self._color = QColor(color)
        self.update()

    def set_values(self, values: list[float]) -> None:
        self._values = list(values)
        self.update()

    def append(self, value: float, *, max_points: int = 120) -> None:
        self._values.append(value)
        if len(self._values) > max_points:
            self._values = self._values[-max_points:]
        self.update()

    def clear(self) -> None:
        self._values.clear()
        self.update()

    def average(self) -> float:
        if not self._values:
            return 0.0
        return sum(self._values) / len(self._values)

    def maximum(self) -> float:
        return max(self._values) if self._values else 0.0

    def minimum(self) -> float:
        return min(self._values) if self._values else 0.0

    def paintEvent(self, _ev) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()

        if not self._values:
            return

        max_v = max(self._values)
        min_v = min(self._values)
        rng = max(max_v - min_v, 1.0)

        n = len(self._values)
        if n == 1:
            x = w / 2
            y = h / 2
            painter.setPen(QPen(self._color, 2))
            painter.drawPoint(QPointF(x, y))
            return

        step = w / (n - 1)
        points: list[QPointF] = []
        for i, v in enumerate(self._values):
            normalized = (v - min_v) / rng
            x = i * step
            y = h - 4 - normalized * (h - 8)
            points.append(QPointF(x, y))

        if self._fill:
            grad = QLinearGradient(0, 0, 0, h)
            top = QColor(self._color)
            top.setAlpha(120)
            bottom = QColor(self._color)
            bottom.setAlpha(0)
            grad.setColorAt(0.0, top)
            grad.setColorAt(1.0, bottom)
            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.PenStyle.NoPen)
            fill_pts = list(points) + [QPointF(w, h), QPointF(0, h)]
            painter.drawPolygon(fill_pts)

        pen = QPen(self._color, 2)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        for a, b in zip(points, points[1:]):
            painter.drawLine(a, b)

        if self._baseline:
            painter.setPen(QPen(QColor("#1f2a44"), 1))
            painter.drawLine(0, h - 2, w, h - 2)
