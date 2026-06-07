from __future__ import annotations

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout, QHeaderView, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from wct.core.i18n import t
from wct.ui.widgets.search_box import SearchBox
from wct.modules.system.startup_manager import list_entries, set_enabled, delete_entry


class _StartupWorker(QThread):
    data_ready = pyqtSignal(list)

    def __init__(self) -> None:
        super().__init__()
        self._running = False

    def run(self) -> None:
        self._running = True
        entries = list_entries()
        rows = [
            {
                "name": e.name,
                "command": e.command,
                "location": e.location,
                "enabled": e.enabled,
                "type": e.entry_type,
            }
            for e in entries
        ]
        self.data_ready.emit(rows)

    def stop(self) -> None:
        self._running = False
        self.wait(3000)


class StartupPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[dict] = []
        self._filter = ""
        self._worker: _StartupWorker | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        hdr = QHBoxLayout()
        self._title = QLabel(t("startup_manager"))
        self._title.setStyleSheet("font-size: 22px; font-weight: 700; color: #e0e0e0;")
        hdr.addWidget(self._title)
        hdr.addStretch()

        self.btn_refresh = QPushButton(t("refresh"))
        self.btn_refresh.setObjectName("btnSecondary")
        self.btn_refresh.clicked.connect(self._refresh)
        hdr.addWidget(self.btn_refresh)

        self.btn_disable = QPushButton(t("disable"))
        self.btn_disable.setObjectName("btnDanger")
        self.btn_disable.clicked.connect(self._disable_selected)
        hdr.addWidget(self.btn_disable)

        self.btn_enable = QPushButton(t("enable"))
        self.btn_enable.setObjectName("btnSecondary")
        self.btn_enable.clicked.connect(self._enable_selected)
        hdr.addWidget(self.btn_enable)

        self.btn_delete = QPushButton(t("delete"))
        self.btn_delete.setObjectName("btnDanger")
        self.btn_delete.clicked.connect(self._delete_selected)
        hdr.addWidget(self.btn_delete)

        root.addLayout(hdr)

        self.search = SearchBox(t("search_placeholder"))
        self.search.text_changed.connect(self._on_search)
        root.addWidget(self.search)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            t("col_name"), t("col_command"), t("col_location"), t("col_enabled"), t("col_type"),
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 100)
        root.addWidget(self.table, 1)

    def showEvent(self, event) -> None:
        self._refresh()
        super().showEvent(event)

    def retranslate(self) -> None:
        self._title.setText(t("startup_manager"))
        self.btn_refresh.setText(t("refresh"))
        self.btn_disable.setText(t("disable"))
        self.btn_enable.setText(t("enable"))
        self.btn_delete.setText(t("delete"))
        self.table.setHorizontalHeaderLabels([
            t("col_name"), t("col_command"), t("col_location"), t("col_enabled"), t("col_type"),
        ])

    def _on_search(self, text: str) -> None:
        self._filter = text.lower()
        self._refresh_table()

    def _refresh(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.stop()
        self._worker = _StartupWorker()
        self._worker.data_ready.connect(self._on_data)
        self._worker.start()

    def _on_data(self, rows: list[dict]) -> None:
        self._rows = rows
        self._refresh_table()

    def _refresh_table(self) -> None:
        items = self._rows
        if self._filter:
            items = [r for r in items if self._filter in r["name"].lower() or self._filter in r["command"].lower()]
        self.table.setRowCount(0)
        for r in items:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(r["name"]))
            self.table.setItem(row, 1, QTableWidgetItem(r["command"]))
            self.table.setItem(row, 2, QTableWidgetItem(r["location"]))
            enabled_item = QTableWidgetItem("Yes" if r["enabled"] else "No")
            if not r["enabled"]:
                enabled_item.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(row, 3, enabled_item)
            self.table.setItem(row, 4, QTableWidgetItem(r["type"]))
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, row)

    def _selected_row(self) -> dict | None:
        idx = self.table.currentRow()
        if idx < 0 or idx >= len(self._rows):
            return None
        return self._rows[idx]

    def _disable_selected(self) -> None:
        r = self._selected_row()
        if not r:
            return
        from wct.modules.system.startup_manager import StartupEntry
        e = StartupEntry(name=r["name"], command=r["command"], location=r["location"], enabled=r["enabled"], entry_type=r["type"])
        if set_enabled(e, False):
            r["enabled"] = False
            self._refresh_table()

    def _enable_selected(self) -> None:
        r = self._selected_row()
        if not r:
            return
        from wct.modules.system.startup_manager import StartupEntry
        e = StartupEntry(name=r["name"], command=r["command"], location=r["location"], enabled=r["enabled"], entry_type=r["type"])
        if set_enabled(e, True):
            r["enabled"] = True
            self._refresh_table()

    def _delete_selected(self) -> None:
        r = self._selected_row()
        if not r:
            return
        from wct.modules.system.startup_manager import StartupEntry
        e = StartupEntry(name=r["name"], command=r["command"], location=r["location"], enabled=r["enabled"], entry_type=r["type"])
        if delete_entry(e):
            self._rows.remove(r)
            self._refresh_table()
