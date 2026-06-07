from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QHBoxLayout, QHeaderView, QLabel, QPushButton,
    QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from wct.core.i18n import t
from wct.core.scheduler import Scheduler


class AddTaskDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(t("add_task"))
        self.setMinimumWidth(380)
        layout = QFormLayout(self)

        self.name_combo = QComboBox()
        self.name_combo.addItems([
            "scan_downloads", "backup_db", "clear_cache",
            "check_updates", "export_events",
        ])
        layout.addRow(t("task_name"), self.name_combo)

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 10080)
        self.interval_spin.setValue(60)
        self.interval_spin.setSuffix(" min")
        layout.addRow(t("task_interval"), self.interval_spin)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def get_data(self) -> dict:
        return {
            "name": self.name_combo.currentText(),
            "interval_ms": self.interval_spin.value() * 60_000,
        }


class SchedulerPage(QWidget):
    def __init__(self, scheduler: Scheduler | None = None, parent=None) -> None:
        super().__init__(parent)
        self._scheduler = scheduler
        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        hdr = QHBoxLayout()
        self._title = QLabel(t("scheduler"))
        self._title.setStyleSheet("font-size: 22px; font-weight: 700; color: #e0e0e0;")
        hdr.addWidget(self._title)
        hdr.addStretch()
        self.btn_add = QPushButton(t("add_task"))
        self.btn_add.setObjectName("btnPrimary")
        self.btn_add.clicked.connect(self._add_task)
        hdr.addWidget(self.btn_add)
        root.addLayout(hdr)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([
            t("task_name"), t("task_interval"), t("col_status"), ""
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        root.addWidget(self.table, 1)

        bottom = QHBoxLayout()
        bottom.addStretch()
        self.btn_toggle = QPushButton(t("toggle"))
        self.btn_toggle.clicked.connect(self._toggle_task)
        bottom.addWidget(self.btn_toggle)
        self.btn_remove = QPushButton(t("delete"))
        self.btn_remove.setObjectName("btnDanger")
        self.btn_remove.clicked.connect(self._remove_task)
        bottom.addWidget(self.btn_remove)
        root.addLayout(bottom)

    def retranslate(self) -> None:
        self._title.setText(t("scheduler"))
        self.btn_add.setText(t("add_task"))
        self.btn_toggle.setText(t("toggle"))
        self.btn_remove.setText(t("delete"))
        self.table.setHorizontalHeaderLabels([
            t("task_name"), t("task_interval"), t("col_status"), ""
        ])

    def set_scheduler(self, scheduler: Scheduler) -> None:
        self._scheduler = scheduler
        self._refresh()

    def _refresh(self) -> None:
        self.table.setRowCount(0)
        if self._scheduler is None:
            return
        for name, task in self._scheduler._tasks.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(name))
            interval_min = task._timer.interval() // 60_000
            self.table.setItem(row, 1, QTableWidgetItem(f"{interval_min} min"))
            status = t("active") if task.is_active else t("stopped")
            self.table.setItem(row, 2, QTableWidgetItem(status))
            self.table.setItem(row, 3, QTableWidgetItem(""))
            self.table.item(row, 0).setData(0x0100, name)  # UserRole

    def _add_task(self) -> None:
        dlg = AddTaskDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.get_data()
        if self._scheduler is None:
            return
        task = self._scheduler.register(data["name"], lambda: None, data["interval_ms"])
        task.start()
        self._refresh()

    def _toggle_task(self) -> None:
        name = self._selected_name()
        if name is None or self._scheduler is None:
            return
        task = self._scheduler.get(name)
        if task is None:
            return
        if task.is_active:
            task.stop()
        else:
            task.start()
        self._refresh()

    def _remove_task(self) -> None:
        name = self._selected_name()
        if name is None or self._scheduler is None:
            return
        task = self._scheduler.get(name)
        if task:
            task.stop()
        self._scheduler._tasks.pop(name, None)
        self._refresh()

    def _selected_name(self) -> str | None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        item = self.table.item(rows[0].row(), 0)
        return item.data(0x0100) if item else None
