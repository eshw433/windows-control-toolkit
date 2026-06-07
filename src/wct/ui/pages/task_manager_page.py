from __future__ import annotations

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout, QHeaderView, QLabel, QProgressBar,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from wct.core.i18n import t
from wct.ui.widgets.search_box import SearchBox

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore[assignment]


class _Worker(QThread):
    data_ready = pyqtSignal(float, float, int, list)  # cpu%, ram%, proc_count, rows

    def __init__(self) -> None:
        super().__init__()
        self._running = False

    def run(self) -> None:
        self._running = True
        while self._running:
            if psutil is None:
                self.msleep(2000)
                continue
            cpu = psutil.cpu_percent(interval=1)   # 1s blocking — in thread, safe
            vm = psutil.virtual_memory()
            rows = []
            for proc in psutil.process_iter(["pid", "name", "cpu_percent",
                                              "memory_info", "memory_percent",
                                              "status", "num_threads", "username"]):
                try:
                    i = proc.info
                    rows.append({
                        "pid": i["pid"],
                        "name": i["name"] or "",
                        "cpu": i["cpu_percent"] or 0.0,
                        "ram": round((i["memory_info"].rss if i["memory_info"] else 0) / 1_048_576, 1),
                        "ram_pct": round(i["memory_percent"] or 0.0, 1),
                        "status": i["status"] or "",
                        "threads": i["num_threads"] or 0,
                        "user": (i["username"] or "").split("\\")[-1],
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            rows.sort(key=lambda r: r["cpu"], reverse=True)
            self.data_ready.emit(cpu, vm.percent, len(rows), rows)
            self.msleep(1000)

    def stop(self) -> None:
        self._running = False
        self.wait(3000)


class TaskManagerPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._filter = ""
        self._worker: _Worker | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        hdr = QHBoxLayout()
        self._title = QLabel(t("task_manager"))
        self._title.setStyleSheet("font-size: 22px; font-weight: 700; color: #e0e0e0;")
        hdr.addWidget(self._title)
        hdr.addStretch()
        self.btn_end = QPushButton(t("end_task"))
        self.btn_end.setObjectName("btnDanger")
        self.btn_end.clicked.connect(self._end_task)
        hdr.addWidget(self.btn_end)
        root.addLayout(hdr)

        bars = QHBoxLayout()
        bars.setSpacing(16)

        cpu_box = QVBoxLayout()
        self._cpu_lbl = QLabel("CPU: 0%")
        self._cpu_lbl.setStyleSheet("color: #5cd0ff; font-weight: 600;")
        self._cpu_bar = QProgressBar()
        self._cpu_bar.setRange(0, 100)
        self._cpu_bar.setFixedHeight(10)
        cpu_box.addWidget(self._cpu_lbl)
        cpu_box.addWidget(self._cpu_bar)
        bars.addLayout(cpu_box)

        ram_box = QVBoxLayout()
        self._ram_lbl = QLabel("RAM: 0%")
        self._ram_lbl.setStyleSheet("color: #4dd599; font-weight: 600;")
        self._ram_bar = QProgressBar()
        self._ram_bar.setRange(0, 100)
        self._ram_bar.setFixedHeight(10)
        ram_box.addWidget(self._ram_lbl)
        ram_box.addWidget(self._ram_bar)
        bars.addLayout(ram_box)

        self._proc_lbl = QLabel("Processes: 0")
        self._proc_lbl.setStyleSheet("color: #ffb547; font-weight: 600;")
        bars.addWidget(self._proc_lbl)
        bars.addStretch()
        root.addLayout(bars)

        self.search = SearchBox(t("search_placeholder"))
        self.search.text_changed.connect(self._on_search)
        root.addWidget(self.search)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "PID", t("col_name"), "CPU %", "RAM MB", "RAM %",
            t("col_status"), "Threads", "User"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 70)
        self.table.setColumnWidth(2, 70)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 70)
        self.table.setColumnWidth(5, 90)
        self.table.setColumnWidth(6, 70)
        root.addWidget(self.table, 1)

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

    def _on_data(self, cpu: float, ram_pct: float, proc_count: int, rows: list) -> None:
        self._cpu_bar.setValue(int(cpu))
        self._cpu_lbl.setText(f"CPU: {cpu:.1f}%")
        self._ram_bar.setValue(int(ram_pct))
        self._ram_lbl.setText(f"RAM: {ram_pct:.1f}%")
        self._proc_lbl.setText(f"Processes: {proc_count}")

        if self._filter:
            rows = [r for r in rows if self._filter in r["name"].lower()
                    or self._filter in str(r["pid"])]

        self.table.setRowCount(0)
        for r in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(r["pid"])))
            self.table.setItem(row, 1, QTableWidgetItem(r["name"]))
            cpu_item = QTableWidgetItem(f"{r['cpu']:.1f}")
            if r["cpu"] > 50:
                cpu_item.setForeground(Qt.GlobalColor.red)
            elif r["cpu"] > 15:
                cpu_item.setForeground(Qt.GlobalColor.yellow)
            self.table.setItem(row, 2, cpu_item)
            self.table.setItem(row, 3, QTableWidgetItem(str(r["ram"])))
            self.table.setItem(row, 4, QTableWidgetItem(f"{r['ram_pct']:.1f}"))
            self.table.setItem(row, 5, QTableWidgetItem(r["status"]))
            self.table.setItem(row, 6, QTableWidgetItem(str(r["threads"])))
            self.table.setItem(row, 7, QTableWidgetItem(r["user"]))
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, r["pid"])

    def retranslate(self) -> None:
        self._title.setText(t("task_manager"))
        self.btn_end.setText(t("end_task"))
        self.table.setHorizontalHeaderLabels([
            "PID", t("col_name"), "CPU %", "RAM MB", "RAM %",
            t("col_status"), "Threads", "User"
        ])

    def _on_search(self, text: str) -> None:
        self._filter = text.lower()

    def _end_task(self) -> None:
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
