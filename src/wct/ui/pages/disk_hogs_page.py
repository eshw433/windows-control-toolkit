from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
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

from wct.core.format import human_size, relative_time
from wct.core.i18n import t
from wct.ui.widgets.search_box import SearchBox
from wct.ui.widgets.stat_card import StatCard


class DiskHogsPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._folder = ""
        self._entries: list[dict] = []
        self._filter = ""
        self._mode = "largest"
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        self._header = QLabel(t("disk_analyzer"))
        self._header.setStyleSheet("font-size: 22px; font-weight: 700; color: #e0e0e0;")
        root.addWidget(self._header)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        self.card_total_files = StatCard(t("total_files"), "0", "#00d2ff")
        self.card_total_size = StatCard(t("total_size"), "0 B", "#9b59b6")
        self.card_huge = StatCard(t("huge_files"), "0", "#e74c3c")
        self.card_stale = StatCard(t("stale_files"), "0", "#f39c12")
        for c in (self.card_total_files, self.card_total_size, self.card_huge, self.card_stale):
            cards_row.addWidget(c)
        root.addLayout(cards_row)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self._folder_label = QLabel(t("no_folder"))
        self._folder_label.setStyleSheet("color: #8892b0; border: none;")
        toolbar.addWidget(self._folder_label, 1)

        self.btn_choose = QPushButton(t("choose_folder"))
        self.btn_choose.clicked.connect(self._pick_folder)
        toolbar.addWidget(self.btn_choose)

        self.btn_scan = QPushButton(t("analyze"))
        self.btn_scan.setObjectName("btnPrimary")
        toolbar.addWidget(self.btn_scan)

        root.addLayout(toolbar)

        filters = QHBoxLayout()
        filters.setSpacing(8)

        self.cmb_mode = QComboBox()
        self.cmb_mode.addItem(t("largest_files"), "largest")
        self.cmb_mode.addItem(t("oldest_files"), "oldest")
        self.cmb_mode.addItem(t("stale_files"), "stale")
        self.cmb_mode.addItem(t("huge_files"), "huge")
        self.cmb_mode.addItem(t("zero_byte"), "zero")
        self.cmb_mode.currentIndexChanged.connect(self._on_mode)
        filters.addWidget(self.cmb_mode)

        filters.addStretch()

        self.search = SearchBox(t("search_placeholder"))
        self.search.text_changed.connect(self._on_search)
        filters.addWidget(self.search)

        self.btn_export = QPushButton(t("export"))
        filters.addWidget(self.btn_export)

        root.addLayout(filters)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            t("col_path"), t("col_size"), t("col_extension"), t("col_category"), t("col_mtime"),
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(320)
        root.addWidget(self.table, 1)

    def retranslate(self) -> None:
        self._header.setText(t("disk_analyzer"))
        self.card_total_files.set_label(t("total_files"))
        self.card_total_size.set_label(t("total_size"))
        self.card_huge.set_label(t("huge_files"))
        self.card_stale.set_label(t("stale_files"))
        self.btn_choose.setText(t("choose_folder"))
        self.btn_scan.setText(t("analyze"))
        self.btn_export.setText(t("export"))
        self.cmb_mode.setItemText(0, t("largest_files"))
        self.cmb_mode.setItemText(1, t("oldest_files"))
        self.cmb_mode.setItemText(2, t("stale_files"))
        self.cmb_mode.setItemText(3, t("huge_files"))
        self.cmb_mode.setItemText(4, t("zero_byte"))
        if not self._folder:
            self._folder_label.setText(t("no_folder"))
        self.table.setHorizontalHeaderLabels([
            t("col_path"), t("col_size"), t("col_extension"), t("col_category"), t("col_mtime"),
        ])

    def _on_search(self, text: str) -> None:
        self._filter = text.lower()
        self._refresh_table()

    def _on_mode(self, _idx: int) -> None:
        self._mode = self.cmb_mode.currentData() or "largest"
        self._refresh_table()

    def _pick_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, t("choose_folder"))
        if path:
            self._folder = path
            self._folder_label.setText(path)

    def selected_folder(self) -> str:
        return self._folder

    def selected_mode(self) -> str:
        return self._mode

    def set_summary(self, *, total_files: int, total_size: int,
                    huge: int, stale: int) -> None:
        self.card_total_files.set_value(str(total_files))
        self.card_total_size.set_value(human_size(total_size))
        self.card_huge.set_value(str(huge))
        self.card_stale.set_value(str(stale))

    def set_entries(self, entries: list[dict]) -> None:
        self._entries = entries
        self._refresh_table()

    def _refresh_table(self) -> None:
        items = self._entries
        if self._filter:
            items = [
                e for e in items
                if self._filter in str(e.get("path", "")).lower()
            ]
        self.table.setRowCount(0)
        for e in items:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(e.get("path", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(human_size(int(e.get("size", 0)))))
            self.table.setItem(row, 2, QTableWidgetItem(str(e.get("extension", ""))))
            self.table.setItem(row, 3, QTableWidgetItem(str(e.get("category", ""))))
            self.table.setItem(row, 4, QTableWidgetItem(relative_time(float(e.get("mtime", 0)))))
