import sys
import os
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, Qt
from PIL import ImageGrab

from wct.app import Application
from wct.ui.main_window import MainWindow
from wct.config.settings import AppSettings


def take_screenshot(filename):
    """Take screenshot of the entire screen."""
    time.sleep(0.5)
    screenshot = ImageGrab.grab()
    screenshot.save(filename)
    print(f"Screenshot saved: {filename}")


def main():
    app = QApplication(sys.argv)

    # Create settings
    settings = AppSettings.load()

    # Create app
    wct_app = Application()
    window = wct_app.window

    # Show window
    window.show()

    # Give time for window to render
    app.processEvents()
    time.sleep(2)

    # Create screenshots directory
    screenshots_dir = Path(__file__).parent.parent / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)

    # Take screenshots of different pages
    pages = [
        ("dashboard", "dashboard.png"),
        ("network", "network.png"),
        ("firewall", "firewall.png"),
        ("bandwidth", "bandwidth.png"),
        ("risk", "risk.png"),
        ("trust", "trust.png"),
        ("downloads", "downloads.png"),
        ("file_rules", "file_rules.png"),
        ("duplicates", "duplicates.png"),
        ("disk_hogs", "disk_hogs.png"),
        ("quarantine", "quarantine.png"),
        ("history", "history.png"),
        ("notifications", "notifications.png"),
        ("process_inspector", "process_inspector.png"),
        ("task_manager", "task_manager.png"),
        ("scheduler", "scheduler.png"),
        ("startup", "startup.png"),
        ("usb", "usb.png"),
        ("content_search", "content_search.png"),
        ("updater", "updater.png"),
        ("settings", "settings.png"),
        ("about", "about.png"),
    ]

    for page_key, filename in pages:
        try:
            window._navigate_to(page_key)
            app.processEvents()
            time.sleep(1)
            take_screenshot(str(screenshots_dir / filename))
        except Exception as e:
            print(f"Failed to screenshot {page_key}: {e}")

    # Close app
    window.close()
    wct_app.shutdown()

    print(f"\nAll screenshots saved to: {screenshots_dir}")


if __name__ == "__main__":
    main()
