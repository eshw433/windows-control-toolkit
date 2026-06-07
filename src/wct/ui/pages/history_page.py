from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from wct.core.i18n import t


class HistoryPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._all_actions: list[dict] = []
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        hdr = QHBoxLayout()
        self._title = QLabel(t("history"))
        self._title.setStyleSheet("font-size: 22px; font-weight: 700; color: #e0e0e0;")
        hdr.addWidget(self._title)
        hdr.addStretch()
        self.btn_rollback = QPushButton(t("rollback"))
        self.btn_rollback.setObjectName("btnDanger")
        hdr.addWidget(self.btn_rollback)
        root.addLayout(hdr)

        # Filters
        fr = QHBoxLayout()
        fr.setSpacing(8)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(t("search_placeholder"))
        self.search_input.setMinimumWidth(180)
        self.search_input.textChanged.connect(self._apply_filters)
        fr.addWidget(self.search_input)

        self.type_combo = QComboBox()
        self.type_combo.setMinimumWidth(120)
        self.type_combo.currentIndexChanged.connect(self._apply_filters)
        fr.addWidget(self.type_combo)

        self.status_combo = QComboBox()
        self.status_combo.setMinimumWidth(120)
        self.status_combo.currentIndexChanged.connect(self._apply_filters)
        fr.addWidget(self.status_combo)

        self.btn_clear = QPushButton(t("clear_all"))
        self.btn_clear.setObjectName("btnGhost")
        self.btn_clear.clicked.connect(self._clear_filters)
        fr.addWidget(self.btn_clear)
        fr.addStretch()
        root.addLayout(fr)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            t("col_time"), t("col_action"), t("col_source"),
            t("col_target"), t("col_status"), "Reversible"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 160)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 220)
        self.table.setColumnWidth(3, 220)
        root.addWidget(self.table, stretch=1)

        self._rebuild_combos()

    def retranslate(self) -> None:
        self._title.setText(t("history"))
        self.btn_rollback.setText(t("rollback"))
        self.btn_clear.setText(t("clear_all"))
        self.search_input.setPlaceholderText(t("search_placeholder"))
        self.table.setHorizontalHeaderLabels([
            t("col_time"), t("col_action"), t("col_source"),
            t("col_target"), t("col_status"), "Reversible"
        ])

    def set_actions(self, actions: list[dict]) -> None:
        self._all_actions = actions
        self._rebuild_combos()
        self._apply_filters()

    def _rebuild_combos(self) -> None:
        types = sorted({a.get("action_type", "") for a in self._all_actions if a.get("action_type")})
        statuses = sorted({a.get("status", "") for a in self._all_actions if a.get("status")})

        for combo, items, all_label in [
            (self.type_combo, types, t("all_types")),
            (self.status_combo, statuses, t("all_statuses")),
        ]:
            combo.blockSignals(True)
            combo.clear()
            combo.addItem(all_label, "")
            for item in items:
                combo.addItem(item, item)
            combo.blockSignals(False)

    def _apply_filters(self) -> None:
        text = self.search_input.text().lower()
        type_f = self.type_combo.currentData() or ""
        status_f = self.status_combo.currentData() or ""
        rows = self._all_actions
        if text:
            rows = [a for a in rows if text in a.get("source_path", "").lower()
                    or text in a.get("target_path", "").lower()]
        if type_f:
            rows = [a for a in rows if a.get("action_type") == type_f]
        if status_f:
            rows = [a for a in rows if a.get("status") == status_f]
        self._fill_table(rows)

    def _clear_filters(self) -> None:
        self.search_input.clear()
        self.type_combo.setCurrentIndex(0)
        self.status_combo.setCurrentIndex(0)

    def _fill_table(self, actions: list[dict]) -> None:
        self.table.setRowCount(0)
        for a in actions:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(a.get("timestamp", "")))
            self.table.setItem(row, 1, QTableWidgetItem(a.get("action_type", "")))
            self.table.setItem(row, 2, QTableWidgetItem(a.get("source_path", "")))
            self.table.setItem(row, 3, QTableWidgetItem(a.get("target_path", "")))
            st = a.get("status", "")
            status_item = QTableWidgetItem(st)
            if st == "completed":
                status_item.setForeground(Qt.GlobalColor.green)
            elif st == "failed":
                status_item.setForeground(Qt.GlobalColor.red)
            elif st == "rolled_back":
                status_item.setForeground(Qt.GlobalColor.yellow)
            self.table.setItem(row, 4, status_item)
            self.table.setItem(row, 5, QTableWidgetItem("Yes" if a.get("reversible") else "No"))
