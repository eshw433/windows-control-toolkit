from __future__ import annotations

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout, QHeaderView, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from wct.core.format import human_size
from wct.core.i18n import t
from wct.modules.system.usb_monitor import list_devices_combined


class _UsbWorker(QThread):
    data_ready = pyqtSignal(list)

    def __init__(self) -> None:
        super().__init__()
        self._running = False

    def run(self) -> None:
        self._running = True
        devices = list_devices_combined()
        rows = [
            {
                "device_id": d.device_id,
                "name": d.name,
                "drive_letter": d.drive_letter,
                "size": d.size_bytes,
                "status": d.status,
                "first_seen": d.first_seen,
            }
            for d in devices
        ]
        self.data_ready.emit(rows)

    def stop(self) -> None:
        self._running = False
        self.wait(3000)


class UsbPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[dict] = []
        self._worker: _UsbWorker | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        hdr = QHBoxLayout()
        self._title = QLabel(t("usb_monitor"))
        self._title.setStyleSheet("font-size: 22px; font-weight: 700; color: #e0e0e0;")
        hdr.addWidget(self._title)
        hdr.addStretch()

        self._count_lbl = QLabel("0")
        self._count_lbl.setStyleSheet("font-size: 18px; font-weight: 700; color: #27ae60;")
        hdr.addWidget(self._count_lbl)
        hdr.addWidget(QLabel(t("devices_connected")))

        self.btn_refresh = QPushButton(t("refresh"))
        self.btn_refresh.setObjectName("btnSecondary")
        self.btn_refresh.clicked.connect(self._refresh)
        hdr.addWidget(self.btn_refresh)

        root.addLayout(hdr)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            t("col_name"), t("col_drive"), t("col_size"), t("col_status"), t("col_device_id"),
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 100)
        root.addWidget(self.table, 1)

    def showEvent(self, event) -> None:
        self._refresh()
        super().showEvent(event)

    def retranslate(self) -> None:
        self._title.setText(t("usb_monitor"))
        self.btn_refresh.setText(t("refresh"))
        self.table.setHorizontalHeaderLabels([
            t("col_name"), t("col_drive"), t("col_size"), t("col_status"), t("col_device_id"),
        ])

    def _refresh(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.stop()
        self._worker = _UsbWorker()
        self._worker.data_ready.connect(self._on_data)
        self._worker.start()

    def _on_data(self, rows: list[dict]) -> None:
        self._rows = rows
        self._count_lbl.setText(str(len(rows)))
        self.table.setRowCount(0)
        for r in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(r["name"]))
            self.table.setItem(row, 1, QTableWidgetItem(r["drive_letter"]))
            self.table.setItem(row, 2, QTableWidgetItem(human_size(r["size"])))
            status_item = QTableWidgetItem(r["status"])
            if r["status"].lower() in ("ok", "connected"):
                status_item.setForeground(Qt.GlobalColor.green)
            self.table.setItem(row, 3, status_item)
            self.table.setItem(row, 4, QTableWidgetItem(r["device_id"]))
