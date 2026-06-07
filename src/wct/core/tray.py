from __future__ import annotations

from PyQt6.QtCore import QObject
from PyQt6.QtGui import QAction, QIcon, QPixmap, QPainter, QColor, QBrush
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon
from loguru import logger

from wct.core.i18n import t


def _create_icon() -> QIcon:
    pix = QPixmap(32, 32)
    pix.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QColor("#00d2ff"))
    painter.setBrush(QBrush(QColor("#16213e")))
    painter.drawEllipse(2, 2, 28, 28)
    painter.setPen(QColor("#e6edf7"))
    font = painter.font()
    font.setBold(True)
    font.setPixelSize(14)
    painter.setFont(font)
    painter.drawText(pix.rect(), 0x84, "W")
    painter.end()
    return QIcon(pix)


class TrayService(QObject):
    def __init__(self, app) -> None:
        super().__init__()
        self._app = app
        self._available = QSystemTrayIcon.isSystemTrayAvailable()
        if not self._available:
            logger.info("System tray not available on this platform")
            self._icon = None
            return

        self._icon = QSystemTrayIcon()
        self._icon.setIcon(_create_icon())
        self._icon.setToolTip(t("tray_title"))

        menu = QMenu()
        self._act_show = QAction(t("tray_show"), self)
        self._act_show.triggered.connect(self._show_window)
        menu.addAction(self._act_show)

        self._act_hide = QAction(t("tray_hide"), self)
        self._act_hide.triggered.connect(self._hide_window)
        menu.addAction(self._act_hide)

        menu.addSeparator()

        self._act_pause = QAction(t("tray_pause"), self)
        self._act_pause.triggered.connect(self._pause)
        menu.addAction(self._act_pause)

        self._act_resume = QAction(t("tray_resume"), self)
        self._act_resume.triggered.connect(self._resume)
        menu.addAction(self._act_resume)

        menu.addSeparator()

        self._act_quit = QAction(t("tray_quit"), self)
        self._act_quit.triggered.connect(self._quit)
        menu.addAction(self._act_quit)

        self._icon.setContextMenu(menu)
        self._icon.activated.connect(self._on_activated)
        self._icon.show()

    def notify(self, title: str, body: str = "", *,
               level: str = "info", duration_ms: int = 3500) -> None:
        if not self._icon:
            logger.info("Tray notify (no tray): {} - {}", title, body)
            return
        icon_map = {
            "info": QSystemTrayIcon.MessageIcon.Information,
            "warn": QSystemTrayIcon.MessageIcon.Warning,
            "warning": QSystemTrayIcon.MessageIcon.Warning,
            "error": QSystemTrayIcon.MessageIcon.Critical,
            "critical": QSystemTrayIcon.MessageIcon.Critical,
        }
        msg_icon = icon_map.get(level, QSystemTrayIcon.MessageIcon.Information)
        self._icon.showMessage(title, body, msg_icon, duration_ms)

    def shutdown(self) -> None:
        if self._icon:
            self._icon.hide()
            self._icon.deleteLater()
            self._icon = None

    def _show_window(self) -> None:
        w = self._app.window
        w.showNormal()
        w.raise_()
        w.activateWindow()

    def _hide_window(self) -> None:
        self._app.window.hide()

    def _pause(self) -> None:
        try:
            self._app.network_service.pause()
        except Exception as exc:
            logger.warning("Tray pause: {}", exc)

    def _resume(self) -> None:
        try:
            self._app.network_service.resume()
        except Exception as exc:
            logger.warning("Tray resume: {}", exc)

    def _quit(self) -> None:
        app = QApplication.instance()
        if app:
            app.quit()

    def _on_activated(self, reason: int) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._show_window()
