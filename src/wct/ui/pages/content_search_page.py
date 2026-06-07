from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
    QFileDialog,
)

from wct.core.i18n import t
from wct.modules.files.content_search import search_folder, SearchResult


class _SearchWorker(QThread):
    data_ready = pyqtSignal(list)
    finished = pyqtSignal()

    def __init__(self, folder: str, query: str) -> None:
        super().__init__()
        self.folder = folder
        self.query = query
        self._running = False

    def run(self) -> None:
        self._running = True
        results = search_folder(Path(self.folder), self.query, recursive=True)
        rows = [
            {
                "path": r.path,
                "line": r.line_number,
                "preview": r.preview,
                "matches": r.match_count,
            }
            for r in results
        ]
        self.data_ready.emit(rows)
        self.finished.emit()

    def stop(self) -> None:
        self._running = False
        self.wait(3000)


class ContentSearchPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[dict] = []
        self._worker: _SearchWorker | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        hdr = QHBoxLayout()
        self._title = QLabel(t("content_search"))
        self._title.setStyleSheet("font-size: 22px; font-weight: 700; color: #e0e0e0;")
        hdr.addWidget(self._title)
        hdr.addStretch()
        root.addLayout(hdr)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText(t("choose_folder"))
        self.folder_input.setMinimumWidth(300)
        toolbar.addWidget(self.folder_input, 1)

        self.btn_browse = QPushButton(t("choose_folder"))
        self.btn_browse.setObjectName("btnSecondary")
        self.btn_browse.clicked.connect(self._browse)
        toolbar.addWidget(self.btn_browse)

        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText(t("search_placeholder"))
        self.query_input.setMinimumWidth(200)
        self.query_input.returnPressed.connect(self._start_search)
        toolbar.addWidget(self.query_input, 1)

        self.btn_search = QPushButton(t("search"))
        self.btn_search.setObjectName("btnPrimary")
        self.btn_search.clicked.connect(self._start_search)
        toolbar.addWidget(self.btn_search)

        root.addLayout(toolbar)

        self._status = QLabel(t("ready"))
        self._status.setStyleSheet("color: #8892b0;")
        root.addWidget(self._status)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([
            t("col_path"), t("col_line"), t("col_preview"), t("col_matches"),
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(1, 70)
        self.table.setColumnWidth(3, 80)
        root.addWidget(self.table, 1)

    def retranslate(self) -> None:
        self._title.setText(t("content_search"))
        self.folder_input.setPlaceholderText(t("choose_folder"))
        self.btn_browse.setText(t("choose_folder"))
        self.query_input.setPlaceholderText(t("search_placeholder"))
        self.btn_search.setText(t("search"))
        self._status.setText(t("ready"))
        self.table.setHorizontalHeaderLabels([
            t("col_path"), t("col_line"), t("col_preview"), t("col_matches"),
        ])

    def _browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, t("choose_folder"))
        if folder:
            self.folder_input.setText(folder)

    def _start_search(self) -> None:
        folder = self.folder_input.text().strip()
        query = self.query_input.text().strip()
        if not folder or not query:
            self._status.setText(t("missing_fields"))
            return
        self._status.setText(t("searching"))
        self.table.setRowCount(0)
        if self._worker is not None and self._worker.isRunning():
            self._worker.stop()
        self._worker = _SearchWorker(folder, query)
        self._worker.data_ready.connect(self._on_data)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_data(self, rows: list[dict]) -> None:
        self._rows = rows
        self.table.setRowCount(0)
        for r in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(r["path"]))
            self.table.setItem(row, 1, QTableWidgetItem(str(r["line"])))
            preview = QTableWidgetItem(r["preview"])
            preview.setToolTip(r["preview"])
            self.table.setItem(row, 2, preview)
            self.table.setItem(row, 3, QTableWidgetItem(str(r["matches"])))

    def _on_finished(self) -> None:
        self._status.setText(f"{len(self._rows)} {t('results_found')}")
