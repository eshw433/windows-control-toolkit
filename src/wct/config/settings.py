from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from wct.config.paths import AppPaths


# ---------------------------------------------------------------------------
# Network module defaults
# ---------------------------------------------------------------------------
class NetworkSettings(BaseModel):
    poll_interval_sec: float = Field(default=2.0, ge=0.5, le=30.0)
    resolve_dns: bool = True
    geoip_enabled: bool = False
    learning_mode: bool = True
    system_allowlist: list[str] = Field(default_factory=lambda: [
        "svchost.exe", "System", "lsass.exe", "services.exe",
        "wininit.exe", "csrss.exe", "smss.exe", "dwm.exe",
    ])


# ---------------------------------------------------------------------------
# File organizer defaults
# ---------------------------------------------------------------------------
class FileSettings(BaseModel):
    monitored_folders: list[str] = Field(default_factory=lambda: [
        str(Path.home() / "Downloads"),
        str(Path.home() / "Desktop"),
    ])
    stable_wait_sec: float = Field(default=5.0, ge=1.0, le=60.0)
    auto_mode: bool = False
    quarantine_days: int = Field(default=30, ge=1)
    ignored_extensions: list[str] = Field(default_factory=lambda: [
        ".crdownload", ".part", ".tmp", ".download", ".partial",
    ])


# ---------------------------------------------------------------------------
# General / UI
# ---------------------------------------------------------------------------
class GeneralSettings(BaseModel):
    theme: str = "dark"
    start_minimized: bool = False
    run_at_startup: bool = False
    notifications_enabled: bool = True
    quiet_hours_start: str = "23:00"
    quiet_hours_end: str = "07:00"
    language: str = "en"


# ---------------------------------------------------------------------------
# Root settings model
# ---------------------------------------------------------------------------
class AppSettings(BaseModel):
    general: GeneralSettings = Field(default_factory=GeneralSettings)
    network: NetworkSettings = Field(default_factory=NetworkSettings)
    files: FileSettings = Field(default_factory=FileSettings)

    # -- persistence ---------------------------------------------------------

    @classmethod
    def load(cls) -> "AppSettings":
        path = AppPaths.config_file()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return cls.model_validate(data)
            except Exception:
                pass
        return cls()

    def save(self) -> None:
        path = AppPaths.config_file()
        path.write_text(
            self.model_dump_json(indent=2),
            encoding="utf-8",
        )

    def update(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            section, _, field = key.partition(".")
            obj = getattr(self, section, None)
            if obj is not None and hasattr(obj, field):
                setattr(obj, field, value)
        self.save()
