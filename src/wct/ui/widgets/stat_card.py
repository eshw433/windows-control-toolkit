"""Reusable stat card widget for the dashboard."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout


class StatCard(QFrame):
    """Compact card showing a value and a label."""

    def __init__(self, label: str, value: str = "0", accent: str = "#00d2ff",
                 parent=None) -> None:
        super().__init__(parent)
        self.setProperty("class", "StatCard")
        self.setObjectName("StatCard")
        self.setStyleSheet(
            f"""
            StatCard {{
                background-color: #16213e;
                border: 1px solid #0f3460;
                border-radius: 12px;
                padding: 16px;
            }}
            """
        )
        self.setFixedHeight(110)
        self.setMinimumWidth(160)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        self._value_label = QLabel(value)
        self._value_label.setObjectName("statValue")
        self._value_label.setStyleSheet(
            f"font-size: 28px; font-weight: 700; color: {accent}; background: transparent; border: none;"
        )
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self._text_label = QLabel(label)
        self._text_label.setObjectName("statLabel")
        self._text_label.setStyleSheet(
            "font-size: 12px; color: #8892b0; background: transparent; border: none;"
        )
        self._text_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(self._value_label)
        layout.addWidget(self._text_label)
        layout.addStretch()

    def set_value(self, value: str) -> None:
        self._value_label.setText(value)

    def set_label(self, text: str) -> None:
        self._text_label.setText(text)
