from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

try:
    import winreg  # type: ignore[import-not-found]
    _HAVE_WINREG = True
except ImportError:
    winreg = None  # type: ignore[assignment]
    _HAVE_WINREG = False


_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
_APP_KEY = "WindowsControlToolkit"


def _get_launch_command() -> str:
    python = sys.executable
    module_root = str(Path(__file__).resolve().parents[1])
    return f'"{python}" -m wct.main'


def _ensure_supported() -> bool:
    if not _HAVE_WINREG:
        logger.debug("Autostart: winreg not available on this platform")
        return False
    return True


def is_autostart_enabled() -> bool:
    if not _ensure_supported():
        return False
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, _APP_KEY)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except OSError:
        return False


def enable_autostart() -> bool:
    if not _ensure_supported():
        return False
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_SET_VALUE)
        cmd = _get_launch_command()
        winreg.SetValueEx(key, _APP_KEY, 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
        logger.info("Autostart enabled: {}", cmd)
        return True
    except OSError as exc:
        logger.error("Failed to enable autostart: {}", exc)
        return False


def disable_autostart() -> bool:
    if not _ensure_supported():
        return False
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_SET_VALUE)
        try:
            winreg.DeleteValue(key, _APP_KEY)
            logger.info("Autostart disabled")
        except FileNotFoundError:
            pass
        winreg.CloseKey(key)
        return True
    except OSError as exc:
        logger.error("Failed to disable autostart: {}", exc)
        return False


def set_autostart(enabled: bool) -> bool:
    return enable_autostart() if enabled else disable_autostart()


def get_launch_command_str() -> str:
    return _get_launch_command()


def is_platform_supported() -> bool:
    return _HAVE_WINREG
