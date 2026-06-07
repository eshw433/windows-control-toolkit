from __future__ import annotations

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout, QHeaderView, QLabel, QPushButton,
    QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from wct.core.i18n import t
from wct.ui.widgets.search_box import SearchBox
from wct.ui.widgets.sparkline import Sparkline

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore[assignment]


class _Worker(QThread):
    data_ready = pyqtSignal(list)

    def __init__(self) -> None:
        super().__init__()
        self._running = False

    def run(self) -> None:
        self._running = True
        while self._running:
            if psutil is None:
                self.msleep(2000)
                continue
            rows = []
            for proc in psutil.process_iter(["pid", "name", "cpu_percent",
                                              "memory_info", "status",
                                              "num_threads", "exe"]):
                try:
                    i = proc.info
                    rows.append({
                        "pid": i["pid"],
                        "name": i["name"] or "",
                        "cpu": i["cpu_percent"] or 0.0,
                        "ram": round((i["memory_info"].rss if i["memory_info"] else 0) / 1_048_576, 1),
                        "status": i["status"] or "",
                        "threads": i["num_threads"] or 0,
                        "exe": i["exe"] or "",
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            rows.sort(key=lambda r: r["cpu"], reverse=True)
            self.data_ready.emit(rows)
            self.msleep(2000)

    def stop(self) -> None:
        self._running = False
        self.wait(3000)


class ProcessInspectorPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[dict] = []
        self._filter = ""
        self._cpu_history: dict[int, list[float]] = {}
        self._worker: _Worker | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        hdr = QHBoxLayout()
        self._title = QLabel(t("process_inspector"))
        self._title.setStyleSheet("font-size: 22px; font-weight: 700; color: #e0e0e0;")
        hdr.addWidget(self._title)
        hdr.addStretch()
        self.btn_kill = QPushButton(t("kill_process"))
        self.btn_kill.setObjectName("btnDanger")
        self.btn_kill.clicked.connect(self._kill_selected)
        hdr.addWidget(self.btn_kill)
        root.addLayout(hdr)

        self.search = SearchBox(t("search_placeholder"))
        self.search.text_changed.connect(self._on_search)
        root.addWidget(self.search)

        splitter = QSplitter(Qt.Orientation.Vertical)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "PID", t("col_name"), "CPU %", "RAM MB", t("col_status"), "Threads", "Exe"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 70)
        self.table.setColumnWidth(2, 70)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 90)
        self.table.setColumnWidth(5, 70)
        self.table.itemSelectionChanged.connect(self._on_select)
        splitter.addWidget(self.table)

        detail = QWidget()
        dl = QHBoxLayout(detail)
        dl.setContentsMargins(0, 8, 0, 0)
        self._detail_label = QLabel(t("select_process"))
        self._detail_label.setStyleSheet("color: #8892b0; font-size: 12px;")
        self._detail_label.setWordWrap(True)
        dl.addWidget(self._detail_label, 1)

        spark_box = QVBoxLayout()
        spark_lbl = QLabel("CPU history")
        spark_lbl.setStyleSheet("color: #8892b0; font-size: 11px;")
        spark_box.addWidget(spark_lbl)
        self._sparkline = Sparkline(color="#5cd0ff", fill=True)
        self._sparkline.setMinimumHeight(60)
        self._sparkline.setMinimumWidth(200)
        spark_box.addWidget(self._sparkline)
        dl.addLayout(spark_box)

        splitter.addWidget(detail)
        splitter.setSizes([500, 120])
        root.addWidget(splitter, 1)

    def showEvent(self, event) -> None:
        if self._worker is None or not self._worker.isRunning():
            self._worker = _Worker()
            self._worker.data_ready.connect(self._on_data)
            self._worker.start()
        super().showEvent(event)

    def hideEvent(self, event) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._worker = None
        super().hideEvent(event)

    def _on_data(self, rows: list) -> None:
        self._rows = rows
        self._refresh_table()

    def _on_search(self, text: str) -> None:
        self._filter = text.lower()
        self._refresh_table()

    def _refresh_table(self) -> None:
        items = self._rows
        if self._filter:
            items = [r for r in items if self._filter in r["name"].lower()
                     or self._filter in str(r["pid"])]
        self.table.setRowCount(0)
        for r in items:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(r["pid"])))
            self.table.setItem(row, 1, QTableWidgetItem(r["name"]))
            cpu_item = QTableWidgetItem(f"{r['cpu']:.1f}")
            if r["cpu"] > 50:
                cpu_item.setForeground(Qt.GlobalColor.red)
            elif r["cpu"] > 20:
                cpu_item.setForeground(Qt.GlobalColor.yellow)
            self.table.setItem(row, 2, cpu_item)
            self.table.setItem(row, 3, QTableWidgetItem(str(r["ram"])))
            self.table.setItem(row, 4, QTableWidgetItem(r["status"]))
            self.table.setItem(row, 5, QTableWidgetItem(str(r["threads"])))
            self.table.setItem(row, 6, QTableWidgetItem(r["exe"]))
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, r["pid"])

    def _on_select(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        pid_item = self.table.item(rows[0].row(), 0)
        if pid_item is None:
            return
        pid = pid_item.data(Qt.ItemDataRole.UserRole)
        row_data = next((r for r in self._rows if r["pid"] == pid), None)
        if row_data:
            self._detail_label.setText(
                f"PID: {row_data['pid']}  |  {row_data['name']}\n"
                f"Exe: {row_data['exe']}\n"
                f"Status: {row_data['status']}  |  Threads: {row_data['threads']}"
            )
            hist = self._cpu_history.setdefault(pid, [])
            hist.append(row_data["cpu"])
            if len(hist) > 60:
                hist[:] = hist[-60:]
            self._sparkline.set_values(hist)

    def _kill_selected(self) -> None:
        if psutil is None:
            return
        for idx in self.table.selectionModel().selectedRows():
            pid_item = self.table.item(idx.row(), 0)
            if pid_item is None:
                continue
            pid = pid_item.data(Qt.ItemDataRole.UserRole)
            try:
                psutil.Process(pid).terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    def retranslate(self) -> None:
        self._title.setText(t("process_inspector"))
        self.btn_kill.setText(t("kill_process"))
        self.table.setHorizontalHeaderLabels([
            "PID", t("col_name"), "CPU %", "RAM MB", t("col_status"), "Threads", "Exe"
        ])
