from __future__ import annotations

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from wct import __version__, __codename__, __author__, __url__
from wct.config.paths import AppPaths
from wct.config.settings import AppSettings
from wct.core import preferences, usage
from wct.core.command_palette import CommandRegistry, populate_defaults
from wct.core.glyphs import for_nav
from wct.core.i18n import t, set_language
from wct.ui.widgets.command_palette import CommandPalette
from wct.ui.pages.dashboard_page import DashboardPage
from wct.ui.pages.network_page import NetworkPage
from wct.ui.pages.firewall_rules_page import FirewallRulesPage
from wct.ui.pages.bandwidth_page import BandwidthPage
from wct.ui.pages.downloads_page import DownloadsPage
from wct.ui.pages.file_rules_page import FileRulesPage
from wct.ui.pages.duplicates_page import DuplicatesPage
from wct.ui.pages.disk_hogs_page import DiskHogsPage
from wct.ui.pages.quarantine_page import QuarantinePage
from wct.ui.pages.trust_page import TrustPage
from wct.ui.pages.risk_page import RiskPage
from wct.ui.pages.history_page import HistoryPage
from wct.ui.pages.notifications_page import NotificationsPage
from wct.ui.pages.settings_page import SettingsPage
from wct.ui.pages.about_page import AboutPage
from wct.ui.pages.process_inspector_page import ProcessInspectorPage
from wct.ui.pages.task_manager_page import TaskManagerPage
from wct.ui.pages.scheduler_page import SchedulerPage
from wct.ui.pages.startup_page import StartupPage
from wct.ui.pages.usb_page import UsbPage
from wct.ui.pages.content_search_page import ContentSearchPage
from wct.ui.pages.updater_page import UpdaterPage
from wct.ui.pages.welcome_screen import WelcomeScreen

# Lazy page factory map — imported only when first navigated to
_PAGE_FACTORIES: dict[str, type] = {
    "dashboard":         None,  # filled below after eager imports
    "network":           None,
    "firewall":          None,
    "bandwidth":         None,
    "risk":              None,
    "trust":             None,
    "downloads":         None,
    "file_rules":        None,
    "duplicates":        None,
    "disk_hogs":         None,
    "quarantine":        None,
    "history":           None,
    "notifications":     None,
    "settings":          None,
    "about":             None,
    "process_inspector": ProcessInspectorPage,
    "task_manager":      TaskManagerPage,
    "scheduler":         SchedulerPage,
    "startup":           StartupPage,
    "usb":               UsbPage,
    "content_search":    ContentSearchPage,
    "updater":           UpdaterPage,
}


_NAV_KEYS = [
    ("dashboard", "dashboard"),
    ("network_monitor", "network"),
    ("firewall_rules", "firewall"),
    ("bandwidth", "bandwidth"),
    ("risk_center", "risk"),
    ("trust_decisions", "trust"),
    ("downloads", "downloads"),
    ("file_rules", "file_rules"),
    ("duplicates", "duplicates"),
    ("disk_hogs", "disk_hogs"),
    ("quarantine", "quarantine"),
    ("history", "history"),
    ("notifications", "notifications"),
    ("process_inspector", "process_inspector"),
    ("task_manager", "task_manager"),
    ("scheduler", "scheduler"),
    ("startup_manager", "startup"),
    ("usb_monitor", "usb"),
    ("content_search", "content_search"),
    ("updater", "updater"),
    ("settings", "settings"),
    ("about", "about"),
]


class MainWindow(QMainWindow):
    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self._settings = settings
        set_language(settings.general.language)
        self.setWindowTitle("Windows Control Toolkit")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)

        self._nav_buttons: dict[str, QPushButton] = {}
        self._pages: dict[str, QWidget] = {}
        self._commands = CommandRegistry()
        self._palette: CommandPalette | None = None
        self._prefs = preferences.load()

        ws = self._prefs.window
        try:
            self.resize(int(ws.width), int(ws.height))
            self.move(int(ws.x), int(ws.y))
            if ws.maximized:
                self.showMaximized()
        except (ValueError, TypeError):
            pass

        self._build_ui()
        self._wire_commands()
        self._wire_shortcuts()

        start_page = self._prefs.ui.last_page if self._prefs.ui.last_page in [k for _, k in _NAV_KEYS] else "dashboard"
        self._navigate_to(start_page)
        usage.record("session", "start", version=__version__, codename=__codename__)

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        self._sidebar_layout = QVBoxLayout(sidebar)
        self._sidebar_layout.setContentsMargins(0, 0, 0, 0)
        self._sidebar_layout.setSpacing(2)

        title = QLabel("WCT  Aurora")
        title.setObjectName("appTitle")
        self._sidebar_layout.addWidget(title)

        self._subtitle = QLabel("Windows Control Toolkit")
        self._subtitle.setObjectName("appSubtitle")
        self._sidebar_layout.addWidget(self._subtitle)

        self._sidebar_layout.addSpacing(8)

        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)

        for i18n_key, nav_key in _NAV_KEYS:
            btn = QPushButton(f"  {for_nav(nav_key)}   {t(i18n_key)}")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(38)
            btn.clicked.connect(lambda checked, k=nav_key: self._navigate_to(k))
            self._btn_group.addButton(btn)
            self._nav_buttons[nav_key] = btn
            self._sidebar_layout.addWidget(btn)

        self._sidebar_layout.addStretch()

        ver_label = QLabel(f"v{__version__} · {__codename__} · {__author__}")
        ver_label.setStyleSheet("color: #556680; font-size: 11px; padding: 8px 16px;")
        self._sidebar_layout.addWidget(ver_label)

        hint_label = QLabel("Ctrl\u202fK  ·  palette")
        hint_label.setStyleSheet("color: #3c4a66; font-size: 10px; padding: 0 16px 12px;")
        self._sidebar_layout.addWidget(hint_label)

        main_layout.addWidget(sidebar)

        self._stack = QStackedWidget()
        self._stack.setObjectName("contentStack")
        main_layout.addWidget(self._stack, stretch=1)

        # Eagerly create core pages needed at startup
        self.dashboard_page = DashboardPage()
        self.network_page = NetworkPage()
        self.firewall_page = FirewallRulesPage()
        self.bandwidth_page = BandwidthPage()
        self.risk_page = RiskPage()
        self.trust_page = TrustPage()
        self.downloads_page = DownloadsPage()
        self.file_rules_page = FileRulesPage()
        self.duplicates_page = DuplicatesPage()
        self.disk_hogs_page = DiskHogsPage()
        self.quarantine_page = QuarantinePage()
        self.history_page = HistoryPage()
        self.notifications_page = NotificationsPage()
        self.settings_page = SettingsPage(self._settings)

        # Heavy pages — created immediately but added to stack deferred
        self.about_page = AboutPage()
        self.process_inspector_page = ProcessInspectorPage()
        self.task_manager_page = TaskManagerPage()
        self.scheduler_page = SchedulerPage()
        self.startup_page = StartupPage()
        self.usb_page = UsbPage()
        self.content_search_page = ContentSearchPage()
        self.updater_page = UpdaterPage()

        _core_pages = {
            "dashboard":     self.dashboard_page,
            "network":       self.network_page,
            "firewall":      self.firewall_page,
            "bandwidth":     self.bandwidth_page,
            "risk":          self.risk_page,
            "trust":         self.trust_page,
            "downloads":     self.downloads_page,
            "file_rules":    self.file_rules_page,
            "duplicates":    self.duplicates_page,
            "disk_hogs":     self.disk_hogs_page,
            "quarantine":    self.quarantine_page,
            "history":       self.history_page,
            "notifications": self.notifications_page,
            "settings":      self.settings_page,
            "about":         self.about_page,
            "process_inspector": self.process_inspector_page,
            "task_manager":  self.task_manager_page,
            "scheduler":     self.scheduler_page,
            "startup":       self.startup_page,
            "usb":           self.usb_page,
            "content_search": self.content_search_page,
            "updater":       self.updater_page,
        }

        for key, widget in _core_pages.items():
            self._stack.addWidget(widget)
            self._pages[key] = widget

        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage(t("ready"))

        self.settings_page.language_changed.connect(self._on_language_changed)

    def _wire_commands(self) -> None:
        nav_map = {nav_key: self._pages[nav_key] for _, nav_key in _NAV_KEYS if nav_key in self._pages}
        ap = self.about_page
        actions = {
            "refresh":         self._refresh_current_page,
            "open_data":       lambda: ap._open_path(AppPaths.data_dir()),
            "open_logs":       lambda: ap._open_path(AppPaths.logs_dir()),
            "open_quarantine": lambda: ap._open_path(AppPaths.quarantine_dir()),
            "open_backups":    lambda: ap._open_path(AppPaths.backups_dir()),
            "copy_diag":       ap._copy_diagnostics,
            "save_diag":       ap._save_diagnostics,
            "check_updates":   ap._check_updates,
            "clear_cache":     ap._clear_cache,
            "backup_db":       ap._backup_db,
            "export_settings": ap._export_settings,
            "open_repo":       self._open_repo,
            "quit":            QApplication.quit,
        }
        populate_defaults(self._commands, navigate=self._navigate_to, pages=nav_map, actions=actions)

    def _open_repo(self) -> None:
        from PyQt6.QtCore import QUrl
        from PyQt6.QtGui import QDesktopServices
        QDesktopServices.openUrl(QUrl(__url__))

    def _wire_shortcuts(self) -> None:
        sc_palette = QShortcut(QKeySequence("Ctrl+K"), self)
        sc_palette.activated.connect(self._open_palette)
        sc_quit = QShortcut(QKeySequence("Ctrl+Q"), self)
        sc_quit.activated.connect(QApplication.quit)
        sc_refresh = QShortcut(QKeySequence("Ctrl+R"), self)
        sc_refresh.activated.connect(self._refresh_current_page)

    def _open_palette(self) -> None:
        if self._palette is None:
            self._palette = CommandPalette(self._commands, parent=self)
            self._palette.triggered.connect(self._commands.invoke)
        self._palette.show()
        self._palette.raise_()
        self._palette.activateWindow()

    def _refresh_current_page(self) -> None:
        page = self._stack.currentWidget()
        if page is None:
            return
        for name in ("refresh", "reload", "_refresh_live", "_refresh"):
            fn = getattr(page, name, None)
            if callable(fn):
                try:
                    fn()
                except Exception:
                    pass
                return

    def _navigate_to(self, key: str) -> None:
        page = self._pages.get(key)
        if page:
            self._stack.setCurrentWidget(page)
        btn = self._nav_buttons.get(key)
        if btn:
            btn.setChecked(True)
        self._prefs.ui.last_page = key
        usage.record("nav", key)

    def closeEvent(self, event):  # noqa: N802 - Qt signature
        try:
            g = self.geometry()
            self._prefs.window.x = g.x()
            self._prefs.window.y = g.y()
            self._prefs.window.width = g.width()
            self._prefs.window.height = g.height()
            self._prefs.window.maximized = self.isMaximized()
            preferences.save(self._prefs)
            usage.record("session", "end")
        except Exception:
            pass
        super().closeEvent(event)

    def _on_language_changed(self, lang: str) -> None:
        set_language(lang)
        for (i18n_key, nav_key) in _NAV_KEYS:
            btn = self._nav_buttons.get(nav_key)
            if btn:
                btn.setText(f"  {for_nav(nav_key)}   {t(i18n_key)}")
        self._status_bar.showMessage(t("ready"))
        for page in self._pages.values():
            if hasattr(page, "retranslate"):
                page.retranslate()

    def set_status(self, msg: str) -> None:
        self._status_bar.showMessage(msg)
