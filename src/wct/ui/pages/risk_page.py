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

from wct.core.format import color_for_risk
from wct.core.i18n import t
from wct.ui.widgets.progress_chip import ProgressChip
from wct.ui.widgets.search_box import SearchBox
from wct.ui.widgets.stat_card import StatCard


class RiskPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[dict] = []
        self._filter = ""
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        self._header = QLabel(t("risk_center"))
        self._header.setStyleSheet("font-size: 22px; font-weight: 700; color: #e0e0e0;")
        root.addWidget(self._header)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        self.card_low = StatCard(t("risk_low"), "0", "#27ae60")
        self.card_medium = StatCard(t("risk_medium"), "0", "#f39c12")
        self.card_high = StatCard(t("risk_high"), "0", "#e67e22")
        self.card_critical = StatCard(t("risk_critical"), "0", "#e74c3c")
        for c in (self.card_low, self.card_medium, self.card_high, self.card_critical):
            cards_row.addWidget(c)
        root.addLayout(cards_row)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self.search = SearchBox(t("search_placeholder"))
        self.search.text_changed.connect(self._on_search)
        toolbar.addWidget(self.search, 1)

        self.btn_block = QPushButton(t("set_trust_block"))
        toolbar.addWidget(self.btn_block)
        self.btn_trust = QPushButton(t("set_trust_allow"))
        toolbar.addWidget(self.btn_trust)
        self.btn_details = QPushButton(t("details"))
        toolbar.addWidget(self.btn_details)

        root.addLayout(toolbar)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            t("col_app"), t("col_path"), t("risk_level"), t("risk_score"), t("risk_reasons"),
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(320)
        root.addWidget(self.table, 1)

    def retranslate(self) -> None:
        self._header.setText(t("risk_center"))
        self.card_low.set_label(t("risk_low"))
        self.card_medium.set_label(t("risk_medium"))
        self.card_high.set_label(t("risk_high"))
        self.card_critical.set_label(t("risk_critical"))
        self.btn_block.setText(t("set_trust_block"))
        self.btn_trust.setText(t("set_trust_allow"))
        self.btn_details.setText(t("details"))
        self.table.setHorizontalHeaderLabels([
            t("col_app"), t("col_path"), t("risk_level"), t("risk_score"), t("risk_reasons"),
        ])

    def _on_search(self, text: str) -> None:
        self._filter = text.lower()
        self._refresh_table()

    def _level_label(self, level: str) -> str:
        return {
            "low": t("risk_low"),
            "medium": t("risk_medium"),
            "high": t("risk_high"),
            "critical": t("risk_critical"),
        }.get(level, t("risk_unknown"))

    def update_rows(self, rows: list[dict]) -> None:
        self._rows = rows
        low = sum(1 for r in rows if r.get("risk_level") == "low")
        med = sum(1 for r in rows if r.get("risk_level") == "medium")
        high = sum(1 for r in rows if r.get("risk_level") == "high")
        crit = sum(1 for r in rows if r.get("risk_level") == "critical")
        self.card_low.set_value(str(low))
        self.card_medium.set_value(str(med))
        self.card_high.set_value(str(high))
        self.card_critical.set_value(str(crit))
        self._refresh_table()

    def _refresh_table(self) -> None:
        items = self._rows
        if self._filter:
            items = [
                r for r in items
                if self._filter in str(r.get("exe_name", "")).lower()
                or self._filter in str(r.get("exe_path", "")).lower()
            ]
        items = sorted(items, key=lambda r: int(r.get("risk_score", 0)), reverse=True)
        self.table.setRowCount(0)
        for r in items:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(r.get("exe_name", "")))
            self.table.setItem(row, 1, QTableWidgetItem(r.get("exe_path", "")))
            level_item = QTableWidgetItem(self._level_label(r.get("risk_level", "")))
            level_item.setForeground(QColor(color_for_risk(r.get("risk_level", ""))))
            self.table.setItem(row, 2, level_item)
            score = int(r.get("risk_score", 0))
            self.table.setItem(row, 3, QTableWidgetItem(str(score)))
            self.table.setItem(row, 4, QTableWidgetItem(str(r.get("note", ""))))
