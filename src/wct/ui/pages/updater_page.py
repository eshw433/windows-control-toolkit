from __future__ import annotations

from PyQt6.QtCore import Qt, QThread, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QVBoxLayout, QWidget, QMessageBox,
)

from wct import __version__, __url__
from wct.core.i18n import t
from wct.core.updater import check_now, ReleaseInfo


class _CheckWorker(QThread):
    result_ready = pyqtSignal(object)

    def __init__(self) -> None:
        super().__init__()

    def run(self) -> None:
        info = check_now()
        self.result_ready.emit(info)


class UpdaterPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._info: ReleaseInfo | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        self._title = QLabel(t("updater"))
        self._title.setStyleSheet("font-size: 22px; font-weight: 700; color: #e0e0e0;")
        root.addWidget(self._title)

        info_box = QHBoxLayout()
        info_box.setSpacing(16)
        self._current = QLabel(f"{t('current_version')}: {__version__}")
        self._current.setStyleSheet("color: #8892b0; font-size: 14px;")
        info_box.addWidget(self._current)

        self._latest = QLabel(f"{t('latest_version')}: ...")
        self._latest.setStyleSheet("color: #5cd0ff; font-size: 14px; font-weight: 600;")
        info_box.addWidget(self._latest)
        info_box.addStretch()
        root.addLayout(info_box)

        self._status = QLabel(t("ready"))
        self._status.setStyleSheet("color: #8892b0; font-size: 13px;")
        root.addWidget(self._status)

        self._notes = QTextEdit()
        self._notes.setReadOnly(True)
        self._notes.setPlaceholderText(t("release_notes"))
        self._notes.setStyleSheet(
            "background-color: #16213e; border: 1px solid #0f3460; border-radius: 10px; color: #e0e0e0; padding: 8px;"
        )
        self._notes.setMaximumHeight(180)
        root.addWidget(self._notes)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        toolbar.addStretch()

        self.btn_check = QPushButton(t("check_updates"))
        self.btn_check.setObjectName("btnPrimary")
        self.btn_check.clicked.connect(self._check)
        toolbar.addWidget(self.btn_check)

        self.btn_open = QPushButton(t("open_release_page"))
        self.btn_open.setObjectName("btnSecondary")
        self.btn_open.clicked.connect(self._open_release)
        self.btn_open.setEnabled(False)
        toolbar.addWidget(self.btn_open)

        self.btn_download = QPushButton(t("download"))
        self.btn_download.setObjectName("btnPrimary")
        self.btn_download.clicked.connect(self._download)
        self.btn_download.setEnabled(False)
        toolbar.addWidget(self.btn_download)

        root.addLayout(toolbar)
        root.addStretch()

    def retranslate(self) -> None:
        self._title.setText(t("updater"))
        self._current.setText(f"{t('current_version')}: {__version__}")
        self._latest.setText(f"{t('latest_version')}: {self._info.version if self._info else '...'}")
        self._status.setText(t("ready"))
        self._notes.setPlaceholderText(t("release_notes"))
        self.btn_check.setText(t("check_updates"))
        self.btn_open.setText(t("open_release_page"))
        self.btn_download.setText(t("download"))

    def _check(self) -> None:
        self._status.setText(t("checking"))
        self.btn_check.setEnabled(False)
        self._worker = _CheckWorker()
        self._worker.result_ready.connect(self._on_result)
        self._worker.start()

    def _on_result(self, info: ReleaseInfo | None) -> None:
        self.btn_check.setEnabled(True)
        if info is None:
            self._status.setText(t("check_failed"))
            self._latest.setText(f"{t('latest_version')}: —")
            return
        self._info = info
        self._latest.setText(f"{t('latest_version')}: {info.version}")
        if info.is_newer:
            self._status.setText(t("update_available"))
            self._status.setStyleSheet("color: #4dd599; font-weight: 600;")
            self.btn_download.setEnabled(True)
            self.btn_open.setEnabled(True)
        else:
            self._status.setText(t("up_to_date"))
            self._status.setStyleSheet("color: #8892b0; font-size: 13px;")
            self.btn_download.setEnabled(False)
            self.btn_open.setEnabled(True)
        self._notes.setPlainText(info.notes or "")

    def _open_release(self) -> None:
        url = self._info.url if self._info else __url__ + "/releases"
        QDesktopServices.openUrl(QUrl(url))

    def _download(self) -> None:
        if not self._info or not self._info.url:
            return
        QMessageBox.information(
            self,
            t("download"),
            t("download_instructions"),
        )
        QDesktopServices.openUrl(QUrl(self._info.url))
