from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from wct.config.settings import AppSettings
from wct.core.autostart import is_autostart_enabled, set_autostart
from wct.core.i18n import t, set_language, get_language


class SettingsPage(QWidget):
    settings_changed = pyqtSignal()
    language_changed = pyqtSignal(str)

    def __init__(self, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self._settings = settings
        self._build_ui()
        self._load_values()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        header_row = QHBoxLayout()
        self._title = QLabel(t("settings"))
        self._title.setStyleSheet("font-size: 22px; font-weight: 700; color: #e0e0e0;")
        header_row.addWidget(self._title)
        header_row.addStretch()

        self.btn_save = QPushButton(t("save"))
        self.btn_save.setObjectName("btnPrimary")
        self.btn_save.clicked.connect(self._on_save)
        header_row.addWidget(self.btn_save)

        self.btn_reset = QPushButton(t("reset"))
        self.btn_reset.clicked.connect(self._on_reset)
        header_row.addWidget(self.btn_reset)

        root.addLayout(header_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        scroll_content = QWidget()
        form_root = QVBoxLayout(scroll_content)
        form_root.setSpacing(16)

        gen_group = QGroupBox(t("general"))
        gen_form = QFormLayout(gen_group)

        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["English", "Русский", "Azərbaycan"])
        gen_form.addRow(t("language") + ":", self.lang_combo)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        gen_form.addRow(t("theme") + ":", self.theme_combo)

        self.chk_start_min = QCheckBox(t("start_minimized"))
        gen_form.addRow(self.chk_start_min)

        self.chk_autostart = QCheckBox(t("run_at_startup"))
        gen_form.addRow(self.chk_autostart)

        self.chk_notifications = QCheckBox(t("enable_notifications"))
        gen_form.addRow(self.chk_notifications)

        form_root.addWidget(gen_group)

        net_group = QGroupBox(t("network_settings"))
        net_form = QFormLayout(net_group)

        self.poll_interval = QDoubleSpinBox()
        self.poll_interval.setRange(0.5, 30.0)
        self.poll_interval.setSuffix(" sec")
        self.poll_interval.setSingleStep(0.5)
        net_form.addRow(t("poll_interval") + ":", self.poll_interval)

        self.chk_resolve_dns = QCheckBox(t("resolve_dns"))
        net_form.addRow(self.chk_resolve_dns)

        self.chk_learning = QCheckBox(t("learning_mode"))
        net_form.addRow(self.chk_learning)

        self.allowlist_edit = QTextEdit()
        self.allowlist_edit.setMaximumHeight(80)
        self.allowlist_edit.setPlaceholderText("svchost.exe, System, lsass.exe ...")
        net_form.addRow("Allowlist:", self.allowlist_edit)

        form_root.addWidget(net_group)

        file_group = QGroupBox(t("file_organizer"))
        file_form = QFormLayout(file_group)

        folders_layout = QVBoxLayout()
        self.folders_list = QListWidget()
        self.folders_list.setMaximumHeight(100)
        folders_layout.addWidget(self.folders_list)

        btn_row = QHBoxLayout()
        self.btn_add_folder = QPushButton(t("add_folder"))
        self.btn_add_folder.clicked.connect(self._pick_folder)
        btn_row.addWidget(self.btn_add_folder)

        self.btn_remove_folder = QPushButton(t("remove_folder"))
        self.btn_remove_folder.clicked.connect(self._remove_folder)
        btn_row.addWidget(self.btn_remove_folder)
        btn_row.addStretch()
        folders_layout.addLayout(btn_row)

        file_form.addRow(t("monitored_folders") + ":", folders_layout)

        self.stable_wait = QDoubleSpinBox()
        self.stable_wait.setRange(1.0, 60.0)
        self.stable_wait.setSuffix(" sec")
        self.stable_wait.setSingleStep(1.0)
        file_form.addRow("Stable wait:", self.stable_wait)

        self.chk_auto = QCheckBox(t("auto_mode"))
        file_form.addRow(self.chk_auto)

        self.quarantine_days = QSpinBox()
        self.quarantine_days.setRange(1, 365)
        self.quarantine_days.setSuffix(" days")
        file_form.addRow(t("quarantine_days") + ":", self.quarantine_days)

        self.ignored_ext_edit = QLineEdit()
        self.ignored_ext_edit.setPlaceholderText(".crdownload, .part, .tmp")
        file_form.addRow("Ignored ext:", self.ignored_ext_edit)

        form_root.addWidget(file_group)
        form_root.addStretch()
        scroll.setWidget(scroll_content)
        root.addWidget(scroll, stretch=1)

    def _pick_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, t("choose_folder"))
        if folder:
            self.folders_list.addItem(folder)

    def _remove_folder(self) -> None:
        row = self.folders_list.currentRow()
        if row >= 0:
            self.folders_list.takeItem(row)

    def _load_values(self) -> None:
        s = self._settings
        lang_map = {"en": 0, "ru": 1, "az": 2}
        self.lang_combo.setCurrentIndex(lang_map.get(s.general.language, 0))
        self.theme_combo.setCurrentText(s.general.theme)
        self.chk_start_min.setChecked(s.general.start_minimized)
        self.chk_autostart.setChecked(is_autostart_enabled())
        self.chk_notifications.setChecked(s.general.notifications_enabled)

        self.poll_interval.setValue(s.network.poll_interval_sec)
        self.chk_resolve_dns.setChecked(s.network.resolve_dns)
        self.chk_learning.setChecked(s.network.learning_mode)
        self.allowlist_edit.setPlainText("\n".join(s.network.system_allowlist))

        self.folders_list.clear()
        for f in s.files.monitored_folders:
            self.folders_list.addItem(f)
        self.stable_wait.setValue(s.files.stable_wait_sec)
        self.chk_auto.setChecked(s.files.auto_mode)
        self.quarantine_days.setValue(s.files.quarantine_days)
        self.ignored_ext_edit.setText(", ".join(s.files.ignored_extensions))

    def _on_save(self) -> None:
        s = self._settings

        lang_map = {0: "en", 1: "ru", 2: "az"}
        new_lang = lang_map.get(self.lang_combo.currentIndex(), "en")
        s.general.language = new_lang
        set_language(new_lang)

        s.general.theme = self.theme_combo.currentText()
        s.general.start_minimized = self.chk_start_min.isChecked()
        s.general.run_at_startup = self.chk_autostart.isChecked()
        set_autostart(s.general.run_at_startup)
        s.general.notifications_enabled = self.chk_notifications.isChecked()

        s.network.poll_interval_sec = self.poll_interval.value()
        s.network.resolve_dns = self.chk_resolve_dns.isChecked()
        s.network.learning_mode = self.chk_learning.isChecked()
        s.network.system_allowlist = [
            x.strip() for x in self.allowlist_edit.toPlainText().splitlines() if x.strip()
        ]

        folders = []
        for i in range(self.folders_list.count()):
            folders.append(self.folders_list.item(i).text())
        s.files.monitored_folders = folders
        s.files.stable_wait_sec = self.stable_wait.value()
        s.files.auto_mode = self.chk_auto.isChecked()
        s.files.quarantine_days = self.quarantine_days.value()
        s.files.ignored_extensions = [
            x.strip() for x in self.ignored_ext_edit.text().split(",") if x.strip()
        ]

        s.save()
        self.language_changed.emit(new_lang)
        self.settings_changed.emit()

    def retranslate(self) -> None:
        self._title.setText(t("settings"))
        self.btn_save.setText(t("save"))
        self.btn_reset.setText(t("reset"))

    def _on_reset(self) -> None:
        self._settings = AppSettings()
        self._load_values()
