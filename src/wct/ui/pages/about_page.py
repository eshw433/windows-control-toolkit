from __future__ import annotations

import shutil
from pathlib import Path

from PyQt6.QtCore import QTimer, QUrl, Qt
from PyQt6.QtGui import QDesktopServices, QGuiApplication
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from loguru import logger

from wct import __author__, __codename__, __license__, __url__, __version__
from wct.config.paths import AppPaths
from wct.config.settings import AppSettings
from wct.core import backup, diagnostics, sysinfo, updater
from wct.core.format import human_duration, human_size
from wct.core.i18n import t
from wct.core.plugins import get_registry as get_plugin_registry


_TECH = [
    ("Python 3.12", "#3776AB"),
    ("PyQt6", "#41CD52"),
    ("SQLite", "#003B57"),
    ("psutil", "#EE7B30"),
    ("watchdog", "#FF6B6B"),
    ("pydantic", "#E92063"),
    ("loguru", "#9b59b6"),
]

_LINKS = [
    ("Repository", __url__),
    ("Issues", f"{__url__}/issues"),
    ("Releases", f"{__url__}/releases"),
    ("License", "https://opensource.org/licenses/MIT"),
]


def _row(label_key: str, value: str, *, accent: str = "#5cd0ff") -> QHBoxLayout:
    h = QHBoxLayout()
    h.setContentsMargins(0, 0, 0, 0)
    lbl = QLabel(t(label_key))
    lbl.setStyleSheet("color: #8d99b3; font-size: 12px; background: transparent; border: none;")
    lbl.setFixedWidth(170)
    h.addWidget(lbl)
    val = QLabel(value)
    val.setStyleSheet(f"color: {accent}; font-size: 13px; font-weight: 600; background: transparent; border: none;")
    val.setWordWrap(True)
    val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    h.addWidget(val, stretch=1)
    return h


def _section_title(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        "color: #8d99b3; font-size: 11px; font-weight: 700; "
        "letter-spacing: 1.5px; padding: 18px 0 6px 0;"
    )
    return lbl


def _card() -> QFrame:
    f = QFrame()
    f.setObjectName("card")
    return f


class AboutPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._sys_value_labels: dict[str, QLabel] = {}
        self._res_value_labels: dict[str, QLabel] = {}
        self._storage_bars: dict[str, tuple[QProgressBar, QLabel]] = {}
        self._update_label: QLabel | None = None
        self._build_ui()
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(2500)
        self._refresh_timer.timeout.connect(self._refresh_live)
        QTimer.singleShot(50, self._refresh_live)

    def showEvent(self, event) -> None:
        self._refresh_timer.start()
        super().showEvent(event)

    def hideEvent(self, event) -> None:
        self._refresh_timer.stop()
        super().hideEvent(event)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        layout.addWidget(self._build_hero())
        layout.addWidget(_section_title(t("about_quick_actions")))
        layout.addWidget(self._build_actions())
        layout.addWidget(_section_title(t("about_system")))
        layout.addLayout(self._build_two_columns(self._build_system_card(), self._build_resources_card()))
        layout.addWidget(_section_title(t("about_storage")))
        layout.addWidget(self._build_storage_card())
        layout.addWidget(_section_title(t("about_plugins")))
        layout.addWidget(self._build_plugins_grid())
        layout.addWidget(_section_title(t("about_shortcuts")))
        layout.addWidget(self._build_shortcuts_card())
        layout.addWidget(_section_title("Tech stack"))
        layout.addWidget(self._build_tech_strip())
        layout.addWidget(_section_title(t("about_links")))
        layout.addWidget(self._build_links_card())
        layout.addWidget(_section_title("✦ Все функции"))
        layout.addWidget(self._build_features_card())
        layout.addWidget(_section_title(t("about_changelog")))
        layout.addWidget(self._build_changelog_card())
        layout.addWidget(_section_title(t("about_license")))
        layout.addWidget(self._build_license_card())
        layout.addSpacing(12)
        layout.addWidget(self._build_footer())
        layout.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll)

    def _build_hero(self) -> QFrame:
        hero = QFrame()
        hero.setStyleSheet(
            "QFrame { "
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
            "stop:0 #10172a, stop:0.5 #1a2447, stop:1 #2b1e5c); "
            "border-radius: 18px; padding: 28px 32px; "
            "border: 1px solid #2b3d68; }"
        )
        hl = QVBoxLayout(hero)
        hl.setSpacing(10)
        title = QLabel(f"Windows Control Toolkit")
        title.setStyleSheet(
            "font-size: 30px; font-weight: 800; color: #84e1ff; letter-spacing: 0.4px; "
            "background: transparent; border: none;"
        )
        hl.addWidget(title)

        sub = QHBoxLayout()
        sub.setSpacing(14)
        v_chip = self._chip(f"v{__version__}", "#5cd0ff")
        c_chip = self._chip(__codename__, "#9a7dff")
        l_chip = self._chip(__license__, "#4dd599")
        sub.addWidget(v_chip)
        sub.addWidget(c_chip)
        sub.addWidget(l_chip)
        sub.addStretch()
        hl.addLayout(sub)

        self._tagline = QLabel(t("about_tagline"))
        self._tagline.setWordWrap(True)
        self._tagline.setStyleSheet(
            "color: #c0c8d8; font-size: 14px; background: transparent; border: none;"
        )
        hl.addWidget(self._tagline)

        self._update_label = QLabel("")
        self._update_label.setWordWrap(True)
        self._update_label.setStyleSheet(
            "color: #8d99b3; font-size: 12px; padding-top: 6px; "
            "background: transparent; border: none;"
        )
        hl.addWidget(self._update_label)
        return hero

    @staticmethod
    def _chip(text: str, color: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {color}; font-size: 12px; font-weight: 700; "
            f"padding: 4px 12px; border: 1px solid {color}55; "
            f"border-radius: 14px; background: rgba(255,255,255,0.04);"
        )
        return lbl

    def _build_actions(self) -> QFrame:
        card = _card()
        grid = QGridLayout(card)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        buttons: list[tuple[str, str, callable]] = [
            ("\U0001f4c1", "about_open_data", lambda: self._open_path(AppPaths.data_dir())),
            ("\U0001f4dc", "about_open_logs", lambda: self._open_path(AppPaths.logs_dir())),
            ("\U0001f6e1\ufe0f", "about_open_quarantine", lambda: self._open_path(AppPaths.quarantine_dir())),
            ("\U0001f4be", "about_open_backups", lambda: self._open_path(AppPaths.backups_dir())),
            ("\U0001f4cb", "about_copy_diag", self._copy_diagnostics),
            ("\U0001f4ce", "about_save_diag", self._save_diagnostics),
            ("\U0001f504", "about_check_updates", self._check_updates),
            ("\U0001f9f9", "about_clear_cache", self._clear_cache),
            ("\U0001f4be", "about_backup_db", self._backup_db),
            ("\U0001f4e4", "about_export_settings", self._export_settings),
            ("\u2197\ufe0f", "about_open_repo", lambda: QDesktopServices.openUrl(QUrl(__url__))),
        ]
        for idx, (icon, key, handler) in enumerate(buttons):
            btn = QPushButton(f"{icon}  {t(key)}")
            btn.setObjectName("btnGhost")
            btn.setMinimumHeight(38)
            btn.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
            btn.clicked.connect(handler)
            grid.addWidget(btn, idx // 3, idx % 3)
        return card

    def _build_two_columns(self, a: QWidget, b: QWidget) -> QHBoxLayout:
        h = QHBoxLayout()
        h.setSpacing(12)
        h.addWidget(a, stretch=1)
        h.addWidget(b, stretch=1)
        return h

    def _build_system_card(self) -> QFrame:
        card = _card()
        v = QVBoxLayout(card)
        v.setSpacing(8)
        rows = [
            ("sys_os", "os"),
            ("sys_machine", "machine"),
            ("sys_cpu", "cpu"),
            ("sys_cores", "cores"),
            ("sys_ram", "ram"),
            ("sys_host", "host"),
            ("sys_user", "user"),
            ("sys_locale", "locale"),
            ("sys_python", "python"),
            ("sys_uptime", "uptime"),
            ("sys_processes", "procs"),
        ]
        for label_key, prop in rows:
            val_lbl = QLabel("…")
            val_lbl.setStyleSheet("color: #84e1ff; font-size: 13px; font-weight: 600; background: transparent; border: none;")
            val_lbl.setWordWrap(True)
            val_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self._sys_value_labels[prop] = val_lbl
            h = QHBoxLayout()
            h.setContentsMargins(0, 0, 0, 0)
            lbl = QLabel(t(label_key))
            lbl.setStyleSheet("color: #8d99b3; font-size: 12px; background: transparent; border: none;")
            lbl.setFixedWidth(170)
            h.addWidget(lbl)
            h.addWidget(val_lbl, stretch=1)
            v.addLayout(h)
        return card

    def _build_resources_card(self) -> QFrame:
        card = _card()
        v = QVBoxLayout(card)
        v.setSpacing(8)
        rows = [
            ("res_pid", "pid"),
            ("res_threads", "threads"),
            ("res_handles", "handles"),
            ("res_mem", "mem"),
            ("res_cpu", "cpu"),
            ("sys_process_uptime", "uptime"),
        ]
        for label_key, prop in rows:
            val_lbl = QLabel("…")
            val_lbl.setStyleSheet("color: #4dd599; font-size: 13px; font-weight: 600; background: transparent; border: none;")
            self._res_value_labels[prop] = val_lbl
            h = QHBoxLayout()
            h.setContentsMargins(0, 0, 0, 0)
            lbl = QLabel(t(label_key))
            lbl.setStyleSheet("color: #8d99b3; font-size: 12px; background: transparent; border: none;")
            lbl.setFixedWidth(170)
            h.addWidget(lbl)
            h.addWidget(val_lbl, stretch=1)
            v.addLayout(h)
        v.addStretch()
        return card

    def _build_storage_card(self) -> QFrame:
        card = _card()
        grid = QGridLayout(card)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        entries = [
            ("storage_db", "db"),
            ("storage_qr", "quarantine"),
            ("storage_logs", "logs"),
            ("storage_backups", "backups"),
        ]
        for i, (label_key, prop) in enumerate(entries):
            block = QVBoxLayout()
            block.setSpacing(4)
            head = QHBoxLayout()
            lbl = QLabel(t(label_key))
            lbl.setStyleSheet("color: #c0c8d8; font-size: 13px; font-weight: 600; background: transparent; border: none;")
            head.addWidget(lbl)
            head.addStretch()
            size_lbl = QLabel("0 B")
            size_lbl.setStyleSheet("color: #84e1ff; font-size: 12px; font-weight: 700; background: transparent; border: none;")
            head.addWidget(size_lbl)
            block.addLayout(head)
            pb = QProgressBar()
            pb.setRange(0, 100)
            pb.setValue(0)
            pb.setTextVisible(False)
            pb.setFixedHeight(8)
            block.addWidget(pb)
            self._storage_bars[prop] = (pb, size_lbl)
            wrap = QWidget()
            wrap.setLayout(block)
            grid.addWidget(wrap, i // 2, i % 2)
        return card

    def _build_plugins_grid(self) -> QFrame:
        card = _card()
        grid = QGridLayout(card)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        reg = get_plugin_registry()
        plugins = reg.all()
        for idx, p in enumerate(plugins):
            tile = QFrame()
            tile.setStyleSheet(
                "QFrame { background-color: #19243f; border: 1px solid #2b3d68; "
                "border-radius: 10px; padding: 12px; }"
            )
            v = QVBoxLayout(tile)
            v.setSpacing(4)
            head = QHBoxLayout()
            n = QLabel(p.name)
            n.setStyleSheet("color: #e6ecf5; font-size: 13px; font-weight: 700; background: transparent; border: none;")
            head.addWidget(n)
            head.addStretch()
            ver = QLabel(f"v{p.version}")
            ver.setStyleSheet("color: #5cd0ff; font-size: 11px; font-weight: 600; background: transparent; border: none;")
            head.addWidget(ver)
            v.addLayout(head)
            desc = QLabel(p.description)
            desc.setWordWrap(True)
            desc.setStyleSheet("color: #8d99b3; font-size: 12px; background: transparent; border: none;")
            v.addWidget(desc)
            tags = QLabel(" \u00b7 ".join(p.tags) if p.tags else p.module)
            tags.setStyleSheet("color: #5b6a8a; font-size: 11px; background: transparent; border: none;")
            v.addWidget(tags)
            grid.addWidget(tile, idx // 3, idx % 3)
        return card

    def _build_shortcuts_card(self) -> QFrame:
        card = _card()
        grid = QGridLayout(card)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        items = [
            ("Ctrl+K", "shortcut_palette"),
            ("Ctrl+F", "shortcut_search"),
            ("Ctrl+R", "shortcut_refresh"),
            ("Ctrl+Q", "shortcut_quit"),
        ]
        for i, (combo, key) in enumerate(items):
            kb = QLabel(combo)
            kb.setStyleSheet(
                "color: #84e1ff; font-size: 12px; font-weight: 700; "
                "padding: 3px 10px; border: 1px solid #2b3d68; "
                "border-radius: 6px; background: #0d1428;"
            )
            kb.setAlignment(Qt.AlignmentFlag.AlignCenter)
            desc = QLabel(t(key))
            desc.setStyleSheet("color: #c0c8d8; font-size: 12px; background: transparent; border: none;")
            grid.addWidget(kb, i, 0)
            grid.addWidget(desc, i, 1, alignment=Qt.AlignmentFlag.AlignLeft)
            grid.setColumnStretch(1, 1)
        return card

    def _build_tech_strip(self) -> QFrame:
        f = QFrame()
        f.setStyleSheet("QFrame { background: transparent; }")
        h = QHBoxLayout(f)
        h.setSpacing(8)
        h.setContentsMargins(0, 0, 0, 0)
        for name, color in _TECH:
            chip = QLabel(name)
            chip.setStyleSheet(
                f"color: {color}; font-size: 12px; font-weight: 700; "
                f"padding: 6px 14px; border: 1px solid {color}55; border-radius: 14px;"
            )
            h.addWidget(chip)
        h.addStretch()
        return f

    def _build_links_card(self) -> QFrame:
        card = _card()
        h = QHBoxLayout(card)
        h.setSpacing(12)
        for label, url in _LINKS:
            btn = QPushButton(f"\U0001f517 {label}")
            btn.setObjectName("btnLink")
            btn.clicked.connect(lambda _=False, u=url: QDesktopServices.openUrl(QUrl(u)))
            h.addWidget(btn)
        h.addStretch()
        return card

    def _build_features_card(self) -> QFrame:
        card = _card()
        v = QVBoxLayout(card)
        v.setSpacing(6)

        _FEATURES = [
            ("⚡", "Сетевой монитор",
             "Отслеживает все активные TCP/UDP соединения в реальном времени. "
             "Показывает приложение, PID, удалённый IP, домен, страну (GeoIP), протокол и статус."),
            ("⛨", "Правила фаервола",
             "Создаёт и управляет правилами Windows Firewall с префиксом WCT_. "
             "Блокировка/разрешение по приложению, направлению, протоколу и порту."),
            ("≈", "Трафик (Bandwidth)",
             "Считает входящий и исходящий трафик по каждому приложению за день. "
             "Показывает скорость в реальном времени и исторические данные."),
            ("▲", "Центр рисков",
             "Автоматически оценивает риск каждого соединения по порту, IP, "
             "имени процесса и поведению. Цветовая индикация: низкий / средний / высокий."),
            ("✓", "Решения по доверию",
             "Хранит историю решений «разрешить / заблокировать» для каждого процесса. "
             "Поддерживает временные разрешения и блокировки."),
            ("⤓", "Загрузки",
             "Сканирует папку Downloads по правилам. Предлагает план организации файлов "
             "с предпросмотром перед применением. Поддерживает авто-режим."),
            ("☰", "Правила файлов",
             "16 встроенных шаблонов + создание своих правил. Условия: расширение, "
             "имя файла, размер, возраст. Действия: переместить, переименовать, карантин, удалить. "
             "Drag & Drop для быстрого создания правила."),
            ("⧉", "Дубликаты",
             "Двухшаговый поиск дубликатов (размер → SHA-256). Показывает группы, "
             "потраченное место. Удаление с выбором стратегии (оставить первый/последний/новейший)."),
            ("◆", "Большие файлы",
             "Анализирует папку и находит самые большие, старые, устаревшие файлы "
             "и нулевые байты. Помогает освободить место на диске."),
            ("⛔", "Карантин",
             "Файлы никогда не удаляются сразу — они перемещаются в карантин. "
             "Полный откат одним кликом. Горячие клавиши: Del = удалить, R = восстановить."),
            ("⟳", "История",
             "Журнал всех файловых операций с фильтрами по типу действия и статусу. "
             "Откат любого действия прямо из таблицы."),
            ("✧", "Уведомления",
             "Центр уведомлений для всех событий системы. "
             "Отметить все прочитанными одним кликом."),
            ("◔", "Инспектор процессов",
             "Детальный просмотр всех запущенных процессов: CPU%, RAM, статус, потоки, "
             "путь к exe. Sparkline-график истории CPU для выбранного процесса. Завершение процесса."),
            ("☰", "Диспетчер задач",
             "Windows-стиль диспетчер: live CPU/RAM шкалы, таблица всех процессов "
             "с сортировкой по CPU, поиск, завершение задач. Работает в фоновом потоке — не лагает."),
            ("⏲", "Планировщик",
             "Управление периодическими задачами: сканирование, резервное копирование, "
             "очистка кэша, проверка обновлений. Запуск/остановка/удаление задач из UI."),
            ("⚙", "Настройки",
             "6 тем оформления (midnight, aurora, solar, amethyst, graphite, light). "
             "3 языка интерфейса (EN/RU/AZ). Автозапуск, тихие часы, интервал опроса сети."),
            ("Ctrl+K", "Командная палитра",
             "31+ команда: навигация по всем страницам, диагностика, экспорт, "
             "резервное копирование, открытие папок. Fuzzy-поиск + история последних команд."),
            ("★", "Онбординг",
             "Welcome screen при первом запуске — 4 шага с описанием ключевых функций. "
             "Показывается один раз, запоминается в локальной БД."),
            ("📊", "Dashboard",
             "Сводная панель с 4 счётчиками и live sparkline-графиками CPU% и RAM% "
             "в реальном времени. Таблица последних событий системы."),
            ("📤", "Экспорт",
             "Экспорт данных в CSV, JSON и PDF (через reportlab). "
             "Поддерживаются: соединения, правила, карантин, трафик, события."),
        ]

        for icon, title, desc in _FEATURES:
            row = QHBoxLayout()
            row.setSpacing(12)
            row.setContentsMargins(0, 4, 0, 4)

            icon_lbl = QLabel(icon)
            icon_lbl.setFixedWidth(28)
            icon_lbl.setStyleSheet("color: #5cd0ff; font-size: 16px; background: transparent; border: none;")
            row.addWidget(icon_lbl)

            text_box = QVBoxLayout()
            text_box.setSpacing(2)
            title_lbl = QLabel(title)
            title_lbl.setStyleSheet("color: #e6ecf5; font-size: 13px; font-weight: 700; background: transparent; border: none;")
            text_box.addWidget(title_lbl)
            desc_lbl = QLabel(desc)
            desc_lbl.setWordWrap(True)
            desc_lbl.setStyleSheet("color: #8d99b3; font-size: 12px; background: transparent; border: none;")
            text_box.addWidget(desc_lbl)
            row.addLayout(text_box, 1)

            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet("color: #1c2945;")

            v.addLayout(row)
            v.addWidget(sep)

        return card

    def _build_changelog_card(self) -> QFrame:
        from wct.core import changelog, markdown_lite
        card = _card()
        v = QVBoxLayout(card)
        v.setSpacing(6)
        latest = changelog.latest()
        head = QLabel(f"{latest.version} \u00b7 {latest.codename} \u00b7 {latest.released}")
        head.setStyleSheet(
            "color: #84e1ff; font-size: 14px; font-weight: 700; background: transparent; border: none;"
        )
        v.addWidget(head)
        body = QLabel(markdown_lite.render(changelog.to_markdown(limit=4)))
        body.setTextFormat(Qt.TextFormat.RichText)
        body.setWordWrap(True)
        body.setOpenExternalLinks(True)
        body.setStyleSheet("color: #c0c8d8; background: transparent; border: none;")
        v.addWidget(body)
        return card

    def _build_license_card(self) -> QFrame:
        card = _card()
        v = QVBoxLayout(card)
        v.setSpacing(8)
        head = QLabel("MIT License")
        head.setStyleSheet("color: #84e1ff; font-size: 14px; font-weight: 700; background: transparent; border: none;")
        v.addWidget(head)
        body = QLabel(
            "Permission is hereby granted, free of charge, to any person obtaining "
            "a copy of this software and associated documentation files, to deal in "
            "the Software without restriction, including without limitation the rights "
            "to use, copy, modify, merge, publish and distribute the Software."
        )
        body.setWordWrap(True)
        body.setStyleSheet("color: #c0c8d8; font-size: 12px; background: transparent; border: none;")
        v.addWidget(body)
        return card

    def _build_footer(self) -> QLabel:
        text = (
            f"\u00a9 2026 {__author__} \u00b7 Python \u00b7 PyQt6 \u00b7 SQLite "
            f"\u00b7 psutil \u00b7 watchdog"
        )
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: #5b6a8a; font-size: 11px; padding: 18px 0;")
        return lbl

    def _refresh_live(self) -> None:
        try:
            snap = sysinfo.collect()
            self._sys_value_labels["os"].setText(f"{snap.os_name} {snap.os_release}")
            self._sys_value_labels["machine"].setText(snap.machine)
            self._sys_value_labels["cpu"].setText(snap.processor[:50])
            self._sys_value_labels["cores"].setText(f"{snap.cpu_count} \u00b7 {snap.cpu_logical} logical")
            ram_total = human_size(snap.total_ram)
            ram_free = human_size(snap.available_ram)
            self._sys_value_labels["ram"].setText(f"{ram_total} ({ram_free} free)")
            self._sys_value_labels["host"].setText(snap.hostname)
            self._sys_value_labels["user"].setText(snap.user)
            self._sys_value_labels["locale"].setText(snap.locale)
            self._sys_value_labels["python"].setText(snap.python_version)
            self._sys_value_labels["uptime"].setText(human_duration(int(sysinfo.uptime_seconds())))
            self._sys_value_labels["procs"].setText(str(sysinfo.process_count()))
        except Exception as exc:
            logger.debug("Sysinfo refresh failed: {}", exc)

        try:
            diag = diagnostics.DiagnosticSnapshot.capture()
            self._res_value_labels["pid"].setText(str(diag.pid))
            self._res_value_labels["threads"].setText(str(diag.threads))
            self._res_value_labels["handles"].setText(f"{diag.open_files} / {diag.fd_count}")
            self._res_value_labels["mem"].setText(f"{diag.memory_mb:.1f} MB")
            self._res_value_labels["cpu"].setText(f"{diag.cpu_percent:.1f} %")
            self._res_value_labels["uptime"].setText(human_duration(int(diag.uptime_sec)))
        except Exception as exc:
            logger.debug("Diag refresh failed: {}", exc)

        try:
            overview = diagnostics.storage_overview()
            sizes = {k: int(v.get("size", 0)) for k, v in overview.items()}
            top = max(sizes.values()) if sizes else 1
            for key, (bar, lbl) in self._storage_bars.items():
                sz = sizes.get(key, 0)
                lbl.setText(human_size(sz))
                ratio = int(min(100, max(0, (sz / top) * 100 if top else 0)))
                bar.setValue(ratio)
        except Exception as exc:
            logger.debug("Storage refresh failed: {}", exc)

    @staticmethod
    def _open_path(path: Path) -> None:
        try:
            path = Path(path)
            path.mkdir(parents=True, exist_ok=True)
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve())))
        except OSError as exc:
            logger.warning("Open path failed: {}", exc)

    def _copy_diagnostics(self) -> None:
        try:
            text = diagnostics.report_to_text()
            cb = QGuiApplication.clipboard()
            cb.setText(text)
            self._toast(t("copied_to_clipboard"))
        except Exception as exc:
            logger.warning("Copy diagnostics failed: {}", exc)

    def _save_diagnostics(self) -> None:
        default = AppPaths.exports_dir() / "diagnostic.txt"
        target, _ = QFileDialog.getSaveFileName(
            self, t("about_save_diag"), str(default), "Text (*.txt);;JSON (*.json)"
        )
        if not target:
            return
        try:
            p = Path(target)
            if p.suffix.lower() == ".json":
                p.write_text(diagnostics.report_to_json(), encoding="utf-8")
            else:
                p.write_text(diagnostics.report_to_text(), encoding="utf-8")
            self._toast(str(p))
        except OSError as exc:
            logger.warning("Save diagnostic failed: {}", exc)

    def _check_updates(self) -> None:
        if self._update_label is None:
            return
        self._update_label.setText(t("updates_checking"))
        QTimer.singleShot(50, self._do_check_updates)

    def _do_check_updates(self) -> None:
        if self._update_label is None:
            return
        info = updater.check_now()
        if info is None:
            self._update_label.setText(t("updates_failed"))
            return
        if info.is_newer:
            self._update_label.setText(t("updates_new").replace("{v}", info.version))
        else:
            self._update_label.setText(t("updates_uptodate"))

    def _clear_cache(self) -> None:
        cache_dir = AppPaths.cache_dir()
        removed = 0
        try:
            for child in cache_dir.iterdir():
                if child.is_file():
                    child.unlink(missing_ok=True)
                    removed += 1
                elif child.is_dir():
                    shutil.rmtree(child, ignore_errors=True)
                    removed += 1
        except OSError as exc:
            logger.warning("Cache clear failed: {}", exc)
        self._toast(f"{t('cache_cleared')} ({removed})")

    def _backup_db(self) -> None:
        try:
            db = AppPaths.db_path()
            if not db.exists():
                self._toast("DB not found")
                return
            info = backup.backup_database(db, AppPaths.backups_dir(), tag="manual")
            self._toast(f"{t('backup_created')}: {info.path.name}")
        except OSError as exc:
            logger.warning("Backup failed: {}", exc)

    def _export_settings(self) -> None:
        target, _ = QFileDialog.getSaveFileName(
            self,
            t("about_export_settings"),
            str(AppPaths.exports_dir() / "wct-settings.json"),
            "JSON (*.json)",
        )
        if not target:
            return
        try:
            cfg = AppSettings.load()
            Path(target).write_text(cfg.model_dump_json(indent=2), encoding="utf-8")
            self._toast(t("settings_exported"))
        except OSError as exc:
            logger.warning("Export settings failed: {}", exc)

    def _toast(self, text: str) -> None:
        QMessageBox.information(self, "WCT", text)

    def retranslate(self) -> None:
        self._tagline.setText(t("about_tagline"))
        QTimer.singleShot(0, self._refresh_live)

    def hideEvent(self, event):  # noqa: N802 - Qt signature
        self._refresh_timer.stop()
        super().hideEvent(event)

    def showEvent(self, event):  # noqa: N802 - Qt signature
        self._refresh_timer.start()
        super().showEvent(event)
