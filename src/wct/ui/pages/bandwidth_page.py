from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from wct.core.format import human_rate, human_size
from wct.core.i18n import t
from wct.ui.widgets.search_box import SearchBox
from wct.ui.widgets.sparkline import Sparkline
from wct.ui.widgets.stat_card import StatCard


class BandwidthPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._rows: list[dict] = []
        self._filter = ""

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        self._header = QLabel(t("bandwidth_monitor"))
        self._header.setStyleSheet("font-size: 22px; font-weight: 700; color: #e0e0e0;")
        root.addWidget(self._header)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        self.card_sent = StatCard(t("bandwidth_sent"), "0 B", "#00d2ff")
        self.card_recv = StatCard(t("bandwidth_received"), "0 B", "#27ae60")
        self.card_rate_sent = StatCard(t("rate_sent"), "0 B/s", "#f39c12")
        self.card_rate_recv = StatCard(t("rate_recv"), "0 B/s", "#9b59b6")
        for c in (self.card_sent, self.card_recv, self.card_rate_sent, self.card_rate_recv):
            cards_row.addWidget(c)
        root.addLayout(cards_row)

        chart_frame = QFrame()
        chart_frame.setStyleSheet(
            "background-color: #16213e; border: 1px solid #0f3460; border-radius: 10px; padding: 12px;"
        )
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setSpacing(8)
        self._chart_label = QLabel(t("bandwidth_chart_title"))
        self._chart_label.setStyleSheet("color: #8892b0; border: none; font-weight: 600;")
        chart_layout.addWidget(self._chart_label)

        sparks_row = QHBoxLayout()
        self.spark_sent = Sparkline(color="#00d2ff", fill=True)
        self.spark_recv = Sparkline(color="#27ae60", fill=True)
        sparks_row.addWidget(self.spark_sent, 1)
        sparks_row.addWidget(self.spark_recv, 1)
        chart_layout.addLayout(sparks_row)
        root.addWidget(chart_frame)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self.search = SearchBox(t("search_placeholder"))
        self.search.text_changed.connect(self._on_search)
        toolbar.addWidget(self.search, 1)

        self.btn_reset = QPushButton(t("bandwidth_reset"))
        self.btn_reset.setObjectName("btnSecondary")
        toolbar.addWidget(self.btn_reset)

        self.btn_export = QPushButton(t("export"))
        toolbar.addWidget(self.btn_export)

        root.addLayout(toolbar)

        self._processes_label = QLabel(t("bandwidth_top"))
        self._processes_label.setStyleSheet("font-weight: 600; color: #e0e0e0;")
        root.addWidget(self._processes_label)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            t("col_app"), t("col_path"), t("rate_sent"), t("rate_recv"), t("bandwidth_total"),
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(260)
        root.addWidget(self.table, 1)

    def retranslate(self) -> None:
        self._header.setText(t("bandwidth_monitor"))
        self.card_sent.set_label(t("bandwidth_sent"))
        self.card_recv.set_label(t("bandwidth_received"))
        self.card_rate_sent.set_label(t("rate_sent"))
        self.card_rate_recv.set_label(t("rate_recv"))
        self._chart_label.setText(t("bandwidth_chart_title"))
        self.btn_reset.setText(t("bandwidth_reset"))
        self.btn_export.setText(t("export"))
        self._processes_label.setText(t("bandwidth_top"))
        self.table.setHorizontalHeaderLabels([
            t("col_app"), t("col_path"), t("rate_sent"), t("rate_recv"), t("bandwidth_total"),
        ])

    def _on_search(self, text: str) -> None:
        self._filter = text.lower()
        self._refresh_table()

    def update_totals(self, *, sent: int, recv: int, rate_sent: float,
                      rate_recv: float) -> None:
        self.card_sent.set_value(human_size(sent))
        self.card_recv.set_value(human_size(recv))
        self.card_rate_sent.set_value(human_rate(rate_sent))
        self.card_rate_recv.set_value(human_rate(rate_recv))
        self.spark_sent.append(rate_sent, max_points=60)
        self.spark_recv.append(rate_recv, max_points=60)

    def update_rows(self, rows: list[dict]) -> None:
        self._rows = rows
        self._refresh_table()

    def _refresh_table(self) -> None:
        items = self._rows
        if self._filter:
            items = [
                r for r in items
                if self._filter in str(r.get("name", "")).lower()
                or self._filter in str(r.get("exe", "")).lower()
            ]
        self.table.setRowCount(0)
        for r in items:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(r.get("name", "")))
            self.table.setItem(row, 1, QTableWidgetItem(r.get("exe", "")))
            self.table.setItem(row, 2, QTableWidgetItem(human_rate(r.get("rate_sent", 0.0))))
            self.table.setItem(row, 3, QTableWidgetItem(human_rate(r.get("rate_recv", 0.0))))
            total = r.get("total_sent", 0) + r.get("total_recv", 0)
            self.table.setItem(row, 4, QTableWidgetItem(human_size(total)))

    def clear_charts(self) -> None:
        self.spark_sent.clear()
        self.spark_recv.clear()
