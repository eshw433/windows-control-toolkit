from __future__ import annotations

import importlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from loguru import logger


@dataclass
class PluginInfo:
    plugin_id: str
    name: str = ""
    version: str = "0.0.0"
    author: str = ""
    description: str = ""
    module: str = ""
    enabled: bool = True
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, PluginInfo] = {}
        self._instances: dict[str, object] = {}
        self._failed: dict[str, str] = {}

    def register(self, info: PluginInfo) -> None:
        if not info.plugin_id:
            return
        self._plugins[info.plugin_id] = info

    def builtin(self) -> list[PluginInfo]:
        items = [
            PluginInfo(
                plugin_id="net.bandwidth",
                name="Bandwidth tracker",
                version="1.2.0",
                author="WCT core",
                description="Per-process bandwidth sampling with daily aggregation.",
                module="wct.modules.network.bandwidth_service",
                tags=["network", "metrics"],
            ),
            PluginInfo(
                plugin_id="net.geoip",
                name="Offline GeoIP",
                version="1.0.0",
                author="WCT core",
                description="Maps IP addresses to ASN, country and known service.",
                module="wct.modules.network.geoip",
                tags=["network", "geoip"],
            ),
            PluginInfo(
                plugin_id="net.ports",
                name="Port registry",
                version="1.0.0",
                author="WCT core",
                description="Well-known TCP/UDP ports and protocol labels.",
                module="wct.modules.network.port_registry",
                tags=["network"],
            ),
            PluginInfo(
                plugin_id="net.dns_cache",
                name="DNS cache",
                version="1.0.0",
                author="WCT core",
                description="Thread-safe in-process DNS resolver cache.",
                module="wct.modules.network.dns_cache",
                tags=["network"],
            ),
            PluginInfo(
                plugin_id="net.risk",
                name="Risk scorer",
                version="1.1.0",
                author="WCT core",
                description="Scores executables for suspicious indicators.",
                module="wct.modules.network.risk",
                tags=["security"],
            ),
            PluginInfo(
                plugin_id="files.dedupe_pro",
                name="Deduplicator (advanced)",
                version="1.1.0",
                author="WCT core",
                description="Two-stage SHA-256 deduplicator with policy strategies.",
                module="wct.modules.files.dedupe_pro",
                tags=["files"],
            ),
            PluginInfo(
                plugin_id="files.size_analyzer",
                name="Size analyzer",
                version="1.0.0",
                author="WCT core",
                description="Identifies largest, oldest and zero-byte files.",
                module="wct.modules.files.size_analyzer",
                tags=["files"],
            ),
            PluginInfo(
                plugin_id="files.templates",
                name="Rule templates",
                version="1.0.0",
                author="WCT core",
                description="16 built-in rule templates for common categories.",
                module="wct.modules.files.templates",
                tags=["files"],
            ),
            PluginInfo(
                plugin_id="core.backup",
                name="Backup engine",
                version="1.0.0",
                author="WCT core",
                description="Snapshot, prune and restore database backups.",
                module="wct.core.backup",
                tags=["data"],
            ),
            PluginInfo(
                plugin_id="core.stats",
                name="Statistics aggregator",
                version="1.0.0",
                author="WCT core",
                description="Histograms, percentiles, top-N and rolling averages.",
                module="wct.core.stats",
                tags=["analytics"],
            ),
            PluginInfo(
                plugin_id="core.tray",
                name="System tray",
                version="1.0.0",
                author="WCT core",
                description="System tray integration with show/hide/pause controls.",
                module="wct.core.tray",
                tags=["ui"],
            ),
            PluginInfo(
                plugin_id="core.exporter",
                name="Exporter",
                version="1.0.0",
                author="WCT core",
                description="CSV/JSON export for tables, rules and history.",
                module="wct.core.exporter",
                tags=["data"],
            ),
        ]
        for it in items:
            self.register(it)
        return list(self._plugins.values())

    def all(self) -> list[PluginInfo]:
        if not self._plugins:
            self.builtin()
        return list(self._plugins.values())

    def find(self, plugin_id: str) -> PluginInfo | None:
        return self._plugins.get(plugin_id)

    def enable(self, plugin_id: str) -> None:
        p = self._plugins.get(plugin_id)
        if p:
            p.enabled = True

    def disable(self, plugin_id: str) -> None:
        p = self._plugins.get(plugin_id)
        if p:
            p.enabled = False

    def load(self, plugin_id: str) -> object | None:
        info = self._plugins.get(plugin_id)
        if not info or not info.module or not info.enabled:
            return None
        if plugin_id in self._instances:
            return self._instances[plugin_id]
        try:
            module = importlib.import_module(info.module)
            self._instances[plugin_id] = module
            return module
        except ImportError as exc:
            self._failed[plugin_id] = str(exc)
            logger.warning("Plugin {} failed to load: {}", plugin_id, exc)
            return None

    def load_external(self, root: Path) -> int:
        if not root.exists() or not root.is_dir():
            return 0
        count = 0
        for manifest in root.glob("*/plugin.json"):
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
                info = PluginInfo(
                    plugin_id=str(data.get("id", manifest.parent.name)),
                    name=str(data.get("name", manifest.parent.name)),
                    version=str(data.get("version", "0.0.0")),
                    author=str(data.get("author", "")),
                    description=str(data.get("description", "")),
                    module=str(data.get("module", "")),
                    enabled=bool(data.get("enabled", True)),
                    tags=list(data.get("tags", [])),
                )
                self.register(info)
                count += 1
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Bad plugin manifest at {}: {}", manifest, exc)
        return count

    def failed(self) -> dict[str, str]:
        return dict(self._failed)

    def to_json(self) -> str:
        return json.dumps([p.to_dict() for p in self.all()], indent=2)

    def __len__(self) -> int:
        return len(self._plugins)


_registry = PluginRegistry()


def get_registry() -> PluginRegistry:
    return _registry
