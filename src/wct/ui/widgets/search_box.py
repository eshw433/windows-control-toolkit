from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QLineEdit, QHBoxLayout, QPushButton, QWidget


class SearchBox(QWidget):
    text_changed = pyqtSignal(str)
    submitted = pyqtSignal(str)

    def __init__(self, placeholder: str = "Search...", *,
                 debounce_ms: int = 150, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._edit = QLineEdit()
        self._edit.setPlaceholderText(placeholder)
        self._edit.setClearButtonEnabled(True)
        self._edit.setMinimumWidth(220)
        self._edit.setStyleSheet(
            """
            QLineEdit {
                background: #1a2440;
                color: #e6edf7;
                border: 1px solid #25324d;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QLineEdit:focus { border-color: #00d2ff; }
            """
        )
        layout.addWidget(self._edit, 1)

        self._clear_btn = QPushButton("✕")
        self._clear_btn.setFixedSize(28, 28)
        self._clear_btn.setStyleSheet(
            "QPushButton { background: transparent; color: #8892b0; border: none; }"
            "QPushButton:hover { color: #ff5470; }"
        )
        self._clear_btn.clicked.connect(self.clear)
        layout.addWidget(self._clear_btn)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(debounce_ms)
        self._timer.timeout.connect(self._emit_change)

        self._edit.textChanged.connect(self._on_changed)
        self._edit.returnPressed.connect(lambda: self.submitted.emit(self._edit.text()))

        shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut.activated.connect(self.focus)

    def text(self) -> str:
        return self._edit.text()

    def set_text(self, value: str) -> None:
        self._edit.setText(value)

    def clear(self) -> None:
        self._edit.clear()

    def focus(self) -> None:
        self._edit.setFocus()
        self._edit.selectAll()

    def _on_changed(self, _text: str) -> None:
        self._timer.start()

    def _emit_change(self) -> None:
        self.text_changed.emit(self._edit.text())
