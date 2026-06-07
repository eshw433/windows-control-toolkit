from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from wct.core.i18n import t


_STEPS = [
    ("welcome_step1_title", "welcome_step1_body", "⚡"),
    ("welcome_step2_title", "welcome_step2_body", "⛨"),
    ("welcome_step3_title", "welcome_step3_body", "⤓"),
    ("welcome_step4_title", "welcome_step4_body", "⚙"),
]


class WelcomeScreen(QWidget):
    finished = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._step = 0
        self._build_ui()
        self._show_step()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(80, 60, 80, 60)
        root.setSpacing(24)
        root.addStretch(1)

        self._icon = QLabel()
        self._icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon.setStyleSheet("font-size: 64px; border: none;")
        root.addWidget(self._icon)

        self._title = QLabel()
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setStyleSheet("font-size: 26px; font-weight: 800; color: #e6ecf5;")
        root.addWidget(self._title)

        self._body = QLabel()
        self._body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._body.setWordWrap(True)
        self._body.setStyleSheet("font-size: 14px; color: #8d99b3; max-width: 500px;")
        root.addWidget(self._body)

        # Dots
        dots_row = QHBoxLayout()
        dots_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._dots: list[QLabel] = []
        for _ in _STEPS:
            dot = QLabel("●")
            dot.setStyleSheet("font-size: 10px; color: #2b3d68;")
            dots_row.addWidget(dot)
            self._dots.append(dot)
        root.addLayout(dots_row)

        root.addStretch(1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.addStretch()

        self.btn_skip = QPushButton(t("skip"))
        self.btn_skip.setObjectName("btnGhost")
        self.btn_skip.clicked.connect(self.finished.emit)
        btn_row.addWidget(self.btn_skip)

        self.btn_next = QPushButton(t("next"))
        self.btn_next.setObjectName("btnPrimary")
        self.btn_next.clicked.connect(self._next)
        btn_row.addWidget(self.btn_next)

        root.addLayout(btn_row)

    def _show_step(self) -> None:
        icon, title_key, body_key = (
            _STEPS[self._step][2],
            _STEPS[self._step][0],
            _STEPS[self._step][1],
        )
        self._icon.setText(icon)
        self._title.setText(t(title_key))
        self._body.setText(t(body_key))
        for i, dot in enumerate(self._dots):
            dot.setStyleSheet(
                "font-size: 10px; color: #5cd0ff;" if i == self._step
                else "font-size: 10px; color: #2b3d68;"
            )
        is_last = self._step == len(_STEPS) - 1
        self.btn_next.setText(t("get_started") if is_last else t("next"))

    def _next(self) -> None:
        if self._step < len(_STEPS) - 1:
            self._step += 1
            self._show_step()
        else:
            self.finished.emit()

    def retranslate(self) -> None:
        self._show_step()
        self.btn_skip.setText(t("skip"))
