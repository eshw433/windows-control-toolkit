from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from wct.core.i18n import t


class DownloadsPage(QWidget):
    folder_changed = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._selected_folder: str = ""
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        header_row = QHBoxLayout()
        self._title = QLabel(t("downloads"))
        self._title.setStyleSheet("font-size: 22px; font-weight: 700; color: #e0e0e0;")
        header_row.addWidget(self._title)
        header_row.addStretch()

        self.btn_choose = QPushButton(t("choose_scan_folder"))
        self.btn_choose.clicked.connect(self._pick_folder)
        header_row.addWidget(self.btn_choose)

        self.btn_scan = QPushButton(t("scan_now"))
        self.btn_scan.setObjectName("btnPrimary")
        header_row.addWidget(self.btn_scan)

        self.btn_apply_all = QPushButton(t("apply_all"))
        self.btn_apply_all.setObjectName("btnSuccess")
        header_row.addWidget(self.btn_apply_all)

        root.addLayout(header_row)

        folder_row = QHBoxLayout()
        self._folder_label = QLabel(t("no_folder"))
        self._folder_label.setStyleSheet("color: #8892b0; font-size: 13px;")
        folder_row.addWidget(self._folder_label)
        folder_row.addStretch()

        self.status_label = QLabel(t("ready"))
        self.status_label.setStyleSheet("color: #27ae60; font-weight: 500;")
        folder_row.addWidget(self.status_label)
        root.addLayout(folder_row)

        self.table = QTableWidget(0, 7)
        self._dl_headers = ["col_name", "col_type", "col_size", "col_source", "col_action", "col_target"]
        self.table.setHorizontalHeaderLabels([t(k) for k in self._dl_headers] + ["%"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 220)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 140)
        self.table.setColumnWidth(5, 180)
        root.addWidget(self.table, stretch=1)

        bottom = QHBoxLayout()
        bottom.addStretch()
        self.btn_apply_selected = QPushButton(t("apply_selected"))
        bottom.addWidget(self.btn_apply_selected)
        root.addLayout(bottom)

    def _pick_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, t("choose_scan_folder"))
        if folder:
            self._selected_folder = folder
            self._folder_label.setText(f"{t('selected_folder')}: {folder}")
            self._folder_label.setStyleSheet("color: #00d2ff; font-size: 13px;")
            self.folder_changed.emit(folder)

    def get_selected_folder(self) -> str:
        return self._selected_folder

    def retranslate(self) -> None:
        self._title.setText(t("downloads"))
        self.btn_choose.setText(t("choose_scan_folder"))
        self.btn_scan.setText(t("scan_now"))
        self.btn_apply_all.setText(t("apply_all"))
        self.btn_apply_selected.setText(t("apply_selected"))
        self.status_label.setText(t("ready"))
        if self._selected_folder:
            self._folder_label.setText(f"{t('selected_folder')}: {self._selected_folder}")
        else:
            self._folder_label.setText(t("no_folder"))
        self.table.setHorizontalHeaderLabels([t(k) for k in self._dl_headers] + ["%"])

    def set_planned_actions(self, actions: list[dict]) -> None:
        self.table.setRowCount(0)
        for a in actions:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(a.get("name", "")))
            self.table.setItem(row, 1, QTableWidgetItem(a.get("category", "")))
            self.table.setItem(row, 2, QTableWidgetItem(a.get("size_display", "")))
            self.table.setItem(row, 3, QTableWidgetItem(a.get("source", "")))
            self.table.setItem(row, 4, QTableWidgetItem(a.get("action", "")))
            self.table.setItem(row, 5, QTableWidgetItem(a.get("target", "")))

            conf = a.get("confidence", 1.0)
            conf_item = QTableWidgetItem(f"{conf:.0%}")
            if conf >= 0.9:
                conf_item.setForeground(Qt.GlobalColor.green)
            elif conf >= 0.5:
                conf_item.setForeground(Qt.GlobalColor.yellow)
            else:
                conf_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(row, 6, conf_item)

    def set_status(self, text: str, color: str = "#27ae60") -> None:
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: 500;")
