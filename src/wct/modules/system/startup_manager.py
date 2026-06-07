from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

try:
    import winreg  # type: ignore[import-not-found]
    _HAVE_WINREG = True
except ImportError:
    winreg = None  # type: ignore[assignment]
    _HAVE_WINREG = False


@dataclass
class StartupEntry:
    name: str
    command: str
    location: str
    enabled: bool
    entry_type: str  # "registry" | "folder"


# Registry paths to scan
_REG_LOCATIONS = [
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKCU\\Run"),
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce", "HKCU\\RunOnce"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKLM\\Run"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce", "HKLM\\RunOnce"),
]

# Startup folders
_STARTUP_FOLDERS = [
    ("Startup (User)", True),
    ("Startup (Common)", False),
]


def _get_startup_path(user: bool) -> Path | None:
    import ctypes
    csidl = 0x0007 if user else 0x0018  # CSIDL_STARTUP or CSIDL_COMMON_STARTUP
    buf = ctypes.create_unicode_buffer(260)
    ctypes.windll.shell32.SHGetFolderPathW(None, csidl, None, 0, buf)
    p = Path(buf.value)
    if p.exists():
        return p
    return None


def _read_registry_entries() -> list[StartupEntry]:
    results: list[StartupEntry] = []
    if not _HAVE_WINREG:
        return results
    for hive, path, label in _REG_LOCATIONS:
        try:
            key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    i += 1
                    cmd = str(value) if value else ""
                    results.append(StartupEntry(
                        name=name,
                        command=cmd,
                        location=label,
                        enabled=True,
                        entry_type="registry",
                    ))
                except OSError:
                    break
            winreg.CloseKey(key)
        except OSError:
            continue
    return results


def _read_folder_entries() -> list[StartupEntry]:
    results: list[StartupEntry] = []
    for label, user in _STARTUP_FOLDERS:
        path = _get_startup_path(user)
        if not path:
            continue
        for item in path.iterdir():
            if item.is_file() and not item.name.startswith("~$"):
                results.append(StartupEntry(
                    name=item.name,
                    command=str(item),
                    location=label,
                    enabled=True,
                    entry_type="folder",
                ))
    return results


def list_entries() -> list[StartupEntry]:
    return _read_registry_entries() + _read_folder_entries()


def disable_registry_entry(name: str, location: str) -> bool:
    if not _HAVE_WINREG:
        return False
    for hive, path, label in _REG_LOCATIONS:
        if label == location:
            try:
                key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ | winreg.KEY_SET_VALUE)
                try:
                    val, typ = winreg.QueryValueEx(key, name)
                except FileNotFoundError:
                    winreg.CloseKey(key)
                    return False
                # Move to disabled subkey
                disabled_path = path + "-Disabled"
                try:
                    dkey = winreg.CreateKey(hive, disabled_path)
                except OSError:
                    winreg.CloseKey(key)
                    return False
                winreg.SetValueEx(dkey, name, 0, typ, val)
                winreg.CloseKey(dkey)
                winreg.DeleteValue(key, name)
                winreg.CloseKey(key)
                logger.info("Disabled startup entry: {} from {}", name, label)
                return True
            except OSError as exc:
                logger.error("Failed to disable startup entry {}: {}", name, exc)
                return False
    return False


def enable_registry_entry(name: str, location: str) -> bool:
    if not _HAVE_WINREG:
        return False
    for hive, path, label in _REG_LOCATIONS:
        if label == location:
            disabled_path = path + "-Disabled"
            try:
                dkey = winreg.OpenKey(hive, disabled_path, 0, winreg.KEY_READ | winreg.KEY_SET_VALUE)
                val, typ = winreg.QueryValueEx(dkey, name)
                key = winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, name, 0, typ, val)
                winreg.CloseKey(key)
                winreg.DeleteValue(dkey, name)
                winreg.CloseKey(dkey)
                logger.info("Enabled startup entry: {} from {}", name, label)
                return True
            except OSError as exc:
                logger.error("Failed to enable startup entry {}: {}", name, exc)
                return False
    return False


def delete_folder_entry(name: str, location: str) -> bool:
    for label, user in _STARTUP_FOLDERS:
        if label == location:
            path = _get_startup_path(user)
            if not path:
                return False
            target = path / name
            if target.exists():
                try:
                    target.unlink()
                    logger.info("Deleted startup shortcut: {}", target)
                    return True
                except OSError as exc:
                    logger.error("Failed to delete startup shortcut {}: {}", target, exc)
                    return False
    return False


def delete_registry_entry(name: str, location: str) -> bool:
    if not _HAVE_WINREG:
        return False
    for hive, path, label in _REG_LOCATIONS:
        if label == location:
            try:
                key = winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE)
                winreg.DeleteValue(key, name)
                winreg.CloseKey(key)
                logger.info("Deleted startup entry: {} from {}", name, label)
                return True
            except OSError as exc:
                logger.error("Failed to delete startup entry {}: {}", name, exc)
                return False
    return False


def set_enabled(entry: StartupEntry, enabled: bool) -> bool:
    if entry.entry_type == "registry":
        return enable_registry_entry(entry.name, entry.location) if enabled else disable_registry_entry(entry.name, entry.location)
    # Folder entries: move to a disabled subfolder instead of deleting
    if entry.entry_type == "folder":
        for label, user in _STARTUP_FOLDERS:
            if label == entry.location:
                path = _get_startup_path(user)
                if not path:
                    return False
                disabled = path / "Disabled"
                disabled.mkdir(exist_ok=True)
                src = path / entry.name
                dst = disabled / entry.name
                try:
                    if enabled:
                        if dst.exists():
                            shutil.move(str(dst), str(src))
                    else:
                        if src.exists():
                            shutil.move(str(src), str(dst))
                    return True
                except OSError as exc:
                    logger.error("Failed to toggle folder startup entry {}: {}", entry.name, exc)
                    return False
    return False


def delete_entry(entry: StartupEntry) -> bool:
    if entry.entry_type == "registry":
        return delete_registry_entry(entry.name, entry.location)
    if entry.entry_type == "folder":
        return delete_folder_entry(entry.name, entry.location)
    return False
