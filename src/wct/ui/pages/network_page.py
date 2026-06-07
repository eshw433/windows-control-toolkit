from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from wct.core.i18n import t


class NetworkPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        header_row = QHBoxLayout()
        self._title = QLabel(t("network_monitor"))
        self._title.setStyleSheet("font-size: 22px; font-weight: 700; color: #e0e0e0;")
        header_row.addWidget(self._title)
        header_row.addStretch()

        self.btn_pause = QPushButton(t("pause"))
        header_row.addWidget(self.btn_pause)

        root.addLayout(header_row)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter...")
        self.search_input.setMinimumWidth(250)
        filter_row.addWidget(self.search_input)

        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(["All", "TCP", "UDP"])
        filter_row.addWidget(self.protocol_combo)

        filter_row.addStretch()
        root.addLayout(filter_row)

        splitter = QSplitter(Qt.Orientation.Vertical)

        self.table = QTableWidget(0, 9)
        self._col_headers = [
            "col_app", "col_pid", "col_trust", "col_remote_ip", "col_port",
            "col_protocol", "col_domain", "", "col_status",
        ]
        self.table.setHorizontalHeaderLabels([t(k) if k else "Country" for k in self._col_headers])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 160)
        self.table.setColumnWidth(3, 140)
        self.table.setColumnWidth(6, 180)
        splitter.addWidget(self.table)

        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setContentsMargins(0, 8, 0, 0)

        det_header_row = QHBoxLayout()
        det_header_row.addStretch()

        self.btn_block = QPushButton(t("block"))
        self.btn_block.setObjectName("btnDanger")
        det_header_row.addWidget(self.btn_block)

        self.btn_allow = QPushButton(t("allow"))
        self.btn_allow.setObjectName("btnSuccess")
        det_header_row.addWidget(self.btn_allow)

        details_layout.addLayout(det_header_row)

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(160)
        self.details_text.setStyleSheet("background-color: #0f3460; border-radius: 8px; padding: 10px;")
        details_layout.addWidget(self.details_text)

        splitter.addWidget(details_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter, stretch=1)

    def retranslate(self) -> None:
        self._title.setText(t("network_monitor"))
        self.btn_pause.setText(t("pause"))
        self.btn_block.setText(t("block"))
        self.btn_allow.setText(t("allow"))
        self.table.setHorizontalHeaderLabels([t(k) if k else "Country" for k in self._col_headers])

    def set_connections(self, connections: list[dict]) -> None:
        self.table.setRowCount(0)
        for c in connections:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(c.get("exe_name", "")))
            self.table.setItem(row, 1, QTableWidgetItem(str(c.get("pid", ""))))
            trust_item = QTableWidgetItem(c.get("trust_state", "unknown"))
            trust = c.get("trust_state", "unknown")
            if trust == "blocked":
                trust_item.setForeground(Qt.GlobalColor.red)
            elif trust == "allowed":
                trust_item.setForeground(Qt.GlobalColor.green)
            self.table.setItem(row, 2, trust_item)
            self.table.setItem(row, 3, QTableWidgetItem(c.get("remote_addr", "")))
            self.table.setItem(row, 4, QTableWidgetItem(str(c.get("remote_port", ""))))
            self.table.setItem(row, 5, QTableWidgetItem(c.get("protocol", "")))
            self.table.setItem(row, 6, QTableWidgetItem(c.get("remote_domain", "")))
            self.table.setItem(row, 7, QTableWidgetItem(c.get("country", "")))
            self.table.setItem(row, 8, QTableWidgetItem(c.get("status", "")))

    def show_details(self, text: str) -> None:
        self.details_text.setPlainText(text)
