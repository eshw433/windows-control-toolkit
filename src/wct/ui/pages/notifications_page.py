from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from wct.core.i18n import t


class NotificationsPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        header_row = QHBoxLayout()
        self._title = QLabel(t("notifications"))
        self._title.setStyleSheet("font-size: 22px; font-weight: 700; color: #e0e0e0;")
        header_row.addWidget(self._title)
        header_row.addStretch()

        self.btn_mark_all_read = QPushButton(t("mark_all_read"))
        header_row.addWidget(self.btn_mark_all_read)

        self.btn_clear = QPushButton(t("clear_all"))
        self.btn_clear.setObjectName("btnDanger")
        header_row.addWidget(self.btn_clear)

        root.addLayout(header_row)

        self.table = QTableWidget(0, 4)
        self._n_headers = ["col_time", "Module", "Title", "Message"]
        self.table.setHorizontalHeaderLabels([t(k) if k.startswith("col_") else k for k in self._n_headers])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 160)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 200)
        root.addWidget(self.table, stretch=1)

    def retranslate(self) -> None:
        self._title.setText(t("notifications"))
        self.btn_mark_all_read.setText(t("mark_all_read"))
        self.btn_clear.setText(t("clear_all"))
        self.table.setHorizontalHeaderLabels([t(k) if k.startswith("col_") else k for k in self._n_headers])

    def set_notifications(self, notifs: list[dict]) -> None:
        self.table.setRowCount(0)
        for n in notifs:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(n.get("timestamp", "")))
            self.table.setItem(row, 1, QTableWidgetItem(n.get("module", "")))
            self.table.setItem(row, 2, QTableWidgetItem(n.get("title", "")))
            self.table.setItem(row, 3, QTableWidgetItem(n.get("body", "")))
