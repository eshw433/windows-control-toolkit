from __future__ import annotations

from PyQt6.QtCore import Qt, QKeyCombination
from PyQt6.QtGui import QKeySequence, QShortcut
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

from wct.core.format import human_size, humanize_iso_date
from wct.core.i18n import t
from wct.ui.widgets.search_box import SearchBox
from wct.ui.widgets.stat_card import StatCard


class QuarantinePage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[dict] = []
        self._filter = ""
        self._build_ui()
        self._wire_shortcuts()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        self._header = QLabel(t("quarantine"))
        self._header.setStyleSheet("font-size: 22px; font-weight: 700; color: #e0e0e0;")
        root.addWidget(self._header)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        self.card_count = StatCard(t("quarantine_items"), "0", "#f39c12")
        self.card_size = StatCard(t("quarantine_total_size"), "0 B", "#e74c3c")
        cards_row.addWidget(self.card_count)
        cards_row.addWidget(self.card_size)
        cards_row.addStretch()
        root.addLayout(cards_row)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self.search = SearchBox(t("search_placeholder"))
        self.search.text_changed.connect(self._on_search)
        toolbar.addWidget(self.search, 1)

        self.btn_restore = QPushButton(t("quarantine_restore"))
        self.btn_restore.setObjectName("btnPrimary")
        toolbar.addWidget(self.btn_restore)

        self.btn_purge = QPushButton(t("quarantine_purge"))
        toolbar.addWidget(self.btn_purge)

        self.btn_clean_expired = QPushButton(t("quarantine_clean_expired"))
        toolbar.addWidget(self.btn_clean_expired)

        self.btn_export = QPushButton(t("export"))
        toolbar.addWidget(self.btn_export)

        root.addLayout(toolbar)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            t("col_name"),
            t("col_source"),
            t("col_size"),
            t("col_time"),
            t("quarantine_expires"),
            t("quarantine_reason"),
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

        self.empty_label = QLabel(t("quarantine_empty"))
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #8892b0; padding: 28px; border: none;")
        self.empty_label.setVisible(False)
        root.addWidget(self.empty_label)

    def retranslate(self) -> None:
        self._header.setText(t("quarantine"))
        self.card_count.set_label(t("quarantine_items"))
        self.card_size.set_label(t("quarantine_total_size"))
        self.btn_restore.setText(t("quarantine_restore"))
        self.btn_purge.setText(t("quarantine_purge"))
        self.btn_clean_expired.setText(t("quarantine_clean_expired"))
        self.btn_export.setText(t("export"))
        self.empty_label.setText(t("quarantine_empty"))
        self.table.setHorizontalHeaderLabels([
            t("col_name"),
            t("col_source"),
            t("col_size"),
            t("col_time"),
            t("quarantine_expires"),
            t("quarantine_reason"),
        ])

    def _on_search(self, text: str) -> None:
        self._filter = text.lower()
        self._refresh_table()

    def update_rows(self, rows: list[dict]) -> None:
        self._rows = rows
        total = sum(int(r.get("size", 0)) for r in rows)
        self.card_count.set_value(str(len(rows)))
        self.card_size.set_value(human_size(total))
        self._refresh_table()

    def _refresh_table(self) -> None:
        items = self._rows
        if self._filter:
            items = [
                r for r in items
                if self._filter in str(r.get("original_path", "")).lower()
                or self._filter in str(r.get("reason", "")).lower()
            ]
        self.table.setRowCount(0)
        for r in items:
            row = self.table.rowCount()
            self.table.insertRow(row)
            orig = r.get("original_path", "")
            name = orig.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(orig))
            self.table.setItem(row, 2, QTableWidgetItem(human_size(int(r.get("size", 0)))))
            self.table.setItem(row, 3, QTableWidgetItem(humanize_iso_date(r.get("timestamp", ""))))
            self.table.setItem(row, 4, QTableWidgetItem(humanize_iso_date(r.get("expires_at", ""))))
            self.table.setItem(row, 5, QTableWidgetItem(str(r.get("reason", ""))))
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, r.get("id"))
        self.empty_label.setVisible(self.table.rowCount() == 0)
        self.table.setVisible(self.table.rowCount() > 0)

    def selected_ids(self) -> list[int]:
        ids: list[int] = []
        for idx in self.table.selectionModel().selectedRows():
            item = self.table.item(idx.row(), 0)
            if item is None:
                continue
            value = item.data(Qt.ItemDataRole.UserRole)
            if value is not None:
                ids.append(int(value))
        return ids

    def _wire_shortcuts(self) -> None:
        sc_del = QShortcut(QKeySequence(Qt.Key.Key_Delete), self)
        sc_del.activated.connect(self.btn_purge.click)
        sc_r = QShortcut(QKeySequence("R"), self)
        sc_r.activated.connect(self.btn_restore.click)
