from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from wct.core.format import color_for_trust, humanize_iso_date
from wct.core.i18n import t
from wct.ui.widgets.search_box import SearchBox
from wct.ui.widgets.stat_card import StatCard


class TrustPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[dict] = []
        self._filter = ""
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        self._header = QLabel(t("trust_decisions"))
        self._header.setStyleSheet("font-size: 22px; font-weight: 700; color: #e0e0e0;")
        root.addWidget(self._header)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        self.card_allowed = StatCard(t("trust_allowed"), "0", "#27ae60")
        self.card_blocked = StatCard(t("trust_blocked"), "0", "#e74c3c")
        self.card_ask = StatCard(t("trust_ask"), "0", "#f39c12")
        self.card_total = StatCard(t("col_count"), "0", "#00d2ff")
        for c in (self.card_allowed, self.card_blocked, self.card_ask, self.card_total):
            cards_row.addWidget(c)
        root.addLayout(cards_row)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.search = SearchBox(t("search_placeholder"))
        self.search.text_changed.connect(self._on_search)
        toolbar.addWidget(self.search, 1)

        self.btn_remove = QPushButton(t("trust_remove"))
        toolbar.addWidget(self.btn_remove)
        self.btn_export = QPushButton(t("export"))
        toolbar.addWidget(self.btn_export)

        root.addLayout(toolbar)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            t("col_app"), t("col_path"), t("col_decision"),
            t("trust_scope"), t("col_reason"), t("trust_expires"),
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(320)
        root.addWidget(self.table, 1)

    def retranslate(self) -> None:
        self._header.setText(t("trust_decisions"))
        self.card_allowed.set_label(t("trust_allowed"))
        self.card_blocked.set_label(t("trust_blocked"))
        self.card_ask.set_label(t("trust_ask"))
        self.card_total.set_label(t("col_count"))
        self.btn_remove.setText(t("trust_remove"))
        self.btn_export.setText(t("export"))
        self.table.setHorizontalHeaderLabels([
            t("col_app"), t("col_path"), t("col_decision"),
            t("trust_scope"), t("col_reason"), t("trust_expires"),
        ])

    def _on_search(self, text: str) -> None:
        self._filter = text.lower()
        self._refresh_table()

    def update_rows(self, rows: list[dict]) -> None:
        self._rows = rows
        allowed = sum(1 for r in rows if r.get("decision") == "allowed")
        blocked = sum(1 for r in rows if r.get("decision") == "blocked")
        ask = sum(1 for r in rows if r.get("decision") == "ask")
        self.card_allowed.set_value(str(allowed))
        self.card_blocked.set_value(str(blocked))
        self.card_ask.set_value(str(ask))
        self.card_total.set_value(str(len(rows)))
        self._refresh_table()

    def _decision_label(self, decision: str) -> str:
        return {
            "allowed": t("trust_allowed"),
            "blocked": t("trust_blocked"),
            "ask": t("trust_ask"),
        }.get(decision, t("trust_unknown"))

    def _refresh_table(self) -> None:
        items = self._rows
        if self._filter:
            items = [
                r for r in items
                if self._filter in str(r.get("exe_name", "")).lower()
                or self._filter in str(r.get("exe_path", "")).lower()
            ]
        self.table.setRowCount(0)
        for r in items:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(r.get("exe_name", "")))
            self.table.setItem(row, 1, QTableWidgetItem(r.get("exe_path", "")))
            decision_item = QTableWidgetItem(self._decision_label(r.get("decision", "")))
            decision_item.setForeground(Qt.GlobalColor.white)
            self.table.setItem(row, 2, decision_item)
            self.table.setItem(row, 3, QTableWidgetItem(r.get("scope", "")))
            self.table.setItem(row, 4, QTableWidgetItem(r.get("reason", "")))
            self.table.setItem(row, 5, QTableWidgetItem(humanize_iso_date(r.get("expires_at", ""))))
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, r.get("id"))

    def selected_ids(self) -> list[int]:
        ids: list[int] = []
        for idx in self.table.selectionModel().selectedRows():
            item = self.table.item(idx.row(), 0)
            if item is None:
                continue
            val = item.data(Qt.ItemDataRole.UserRole)
            if val is not None:
                ids.append(int(val))
        return ids
