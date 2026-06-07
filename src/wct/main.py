from __future__ import annotations

import sys

from loguru import logger


def _setup_logging() -> None:
    logger.remove()
    # sys.stderr is None in a windowed frozen exe — only add if available
    if sys.stderr is not None:
        logger.add(sys.stderr, level="DEBUG", format="{time:HH:mm:ss} | {level:<8} | {message}")
    try:
        from wct.config.paths import AppPaths
        log_file = AppPaths.logs_dir() / "wct_{time:YYYY-MM-DD}.log"
        logger.add(
            str(log_file),
            rotation="10 MB",
            retention="14 days",
            level="INFO",
            encoding="utf-8",
        )
    except Exception:
        pass


def main() -> None:
    _setup_logging()
    logger.info("Starting Windows Control Toolkit")

    from PyQt6.QtWidgets import QApplication
    from wct.ui.theme import stylesheet_for, list_presets
    from wct.config.settings import AppSettings
    from wct.app import Application

    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("Windows Control Toolkit")
    qt_app.setOrganizationName("WCT")

    try:
        cfg = AppSettings.load()
        preset = getattr(cfg.general, "theme", "midnight") or "midnight"
    except Exception:
        preset = "midnight"
    if preset not in list_presets():
        preset = "midnight"
    qt_app.setStyleSheet(stylesheet_for(preset))

    app = Application()

    # Show welcome screen on first run, then show main window
    from wct.ui.pages.welcome_screen import WelcomeScreen
    _first_run = app.kv_repo.get("first_run_done") if hasattr(app.kv_repo, "get") else None
    if not _first_run:
        welcome = WelcomeScreen()
        welcome.setWindowTitle("Welcome to Windows Control Toolkit")
        welcome.setStyleSheet(stylesheet_for(preset))
        welcome.resize(640, 500)

        def _on_done():
            welcome.close()
            if hasattr(app.kv_repo, "set"):
                app.kv_repo.set("first_run_done", "1")
            app.show()

        welcome.finished.connect(_on_done)
        welcome.show()
    else:
        app.show()

    exit_code = qt_app.exec()
    app.shutdown()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
