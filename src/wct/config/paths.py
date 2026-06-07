from __future__ import annotations

import os
from pathlib import Path


class AppPaths:

    APP_NAME = "WindowsControlToolkit"

    @classmethod
    def data_dir(cls) -> Path:
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        p = base / cls.APP_NAME
        p.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def db_path(cls) -> Path:
        return cls.data_dir() / "wct.db"

    @classmethod
    def logs_dir(cls) -> Path:
        p = cls.data_dir() / "logs"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def quarantine_dir(cls) -> Path:
        p = cls.data_dir() / "quarantine"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def backups_dir(cls) -> Path:
        p = cls.data_dir() / "backups"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def config_file(cls) -> Path:
        return cls.data_dir() / "settings.json"

    @classmethod
    def cache_dir(cls) -> Path:
        p = cls.data_dir() / "cache"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def plugins_dir(cls) -> Path:
        p = cls.data_dir() / "plugins"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def exports_dir(cls) -> Path:
        p = cls.data_dir() / "exports"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def temp_dir(cls) -> Path:
        p = cls.data_dir() / "tmp"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def config_dir(cls) -> Path:
        p = cls.data_dir() / "config"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def reports_dir(cls) -> Path:
        p = cls.data_dir() / "reports"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def workspace_dir(cls) -> Path:
        p = cls.data_dir() / "workspace"
        p.mkdir(parents=True, exist_ok=True)
        return p
