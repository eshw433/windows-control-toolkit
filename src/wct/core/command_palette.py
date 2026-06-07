from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Command:
    cid: str
    title: str
    group: str = "General"
    handler: Callable[[], None] | None = None
    keywords: list[str] = field(default_factory=list)
    shortcut: str = ""
    enabled: bool = True

    def matches(self, query: str) -> bool:
        if not query:
            return True
        q = query.lower().strip()
        haystack = " ".join([self.title, self.group, self.cid, *self.keywords]).lower()
        for token in q.split():
            if token not in haystack:
                return False
        return True


class CommandRegistry:
    def __init__(self) -> None:
        self._commands: dict[str, Command] = {}
        self._recents: list[str] = []
        self._max_recent = 30

    def register(self, command: Command) -> None:
        if not command.cid:
            return
        self._commands[command.cid] = command

    def register_many(self, commands: list[Command]) -> None:
        for c in commands:
            self.register(c)

    def remove(self, cid: str) -> None:
        self._commands.pop(cid, None)
        self._recents = [r for r in self._recents if r != cid]

    def get(self, cid: str) -> Command | None:
        return self._commands.get(cid)

    def all(self) -> list[Command]:
        return list(self._commands.values())

    def groups(self) -> list[str]:
        seen = []
        for c in self._commands.values():
            if c.group not in seen:
                seen.append(c.group)
        return seen

    def filter(self, query: str = "", *, group: str | None = None,
               limit: int = 50) -> list[Command]:
        items = []
        for c in self._commands.values():
            if not c.enabled:
                continue
            if group is not None and c.group != group:
                continue
            if c.matches(query):
                items.append(c)
        items.sort(key=lambda c: (self._recent_rank(c.cid), c.title.lower()))
        return items[:limit]

    def invoke(self, cid: str) -> bool:
        cmd = self._commands.get(cid)
        if not cmd or not cmd.enabled or cmd.handler is None:
            return False
        try:
            cmd.handler()
        except Exception:
            return False
        self._push_recent(cid)
        return True

    def recents(self, limit: int = 10) -> list[Command]:
        out = []
        for cid in self._recents[:limit]:
            c = self._commands.get(cid)
            if c:
                out.append(c)
        return out

    def clear_recents(self) -> None:
        self._recents.clear()

    def _push_recent(self, cid: str) -> None:
        self._recents = [c for c in self._recents if c != cid]
        self._recents.insert(0, cid)
        if len(self._recents) > self._max_recent:
            self._recents = self._recents[: self._max_recent]

    def _recent_rank(self, cid: str) -> int:
        try:
            return self._recents.index(cid)
        except ValueError:
            return 999

    def __len__(self) -> int:
        return len(self._commands)


_default_registry = CommandRegistry()


def get_registry() -> CommandRegistry:
    return _default_registry


def register(command: Command) -> None:
    _default_registry.register(command)


_NAV_TITLES = [
    ("dashboard", "Dashboard"),
    ("network", "Network monitor"),
    ("firewall", "Firewall rules"),
    ("bandwidth", "Bandwidth"),
    ("risk", "Risk center"),
    ("trust", "Trust decisions"),
    ("downloads", "Downloads organizer"),
    ("file_rules", "File rules"),
    ("duplicates", "Duplicate finder"),
    ("disk_hogs", "Disk hogs"),
    ("quarantine", "Quarantine"),
    ("history", "History"),
    ("notifications", "Notifications"),
    ("process_inspector", "Process Inspector"),
    ("task_manager", "Task Manager"),
    ("scheduler", "Scheduler"),
    ("settings", "Settings"),
    ("about", "About"),
]


def populate_defaults(
    registry: CommandRegistry | None = None,
    *,
    navigate: Callable[[str], None] | None = None,
    pages: dict[str, object] | None = None,
    actions: dict[str, Callable[[], None]] | None = None,
) -> CommandRegistry:
    reg = registry if registry is not None else _default_registry
    if navigate is not None:
        keys = pages.keys() if pages else [k for k, _ in _NAV_TITLES]
        title_map = dict(_NAV_TITLES)
        for key in keys:
            title = title_map.get(key, key.replace("_", " ").title())
            reg.register(Command(
                cid=f"nav.{key}",
                title=f"Go to: {title}",
                group="Navigation",
                handler=(lambda k=key: navigate(k)),
                keywords=["go", "open", key],
            ))
    if actions:
        labels = {
            "refresh":      ("Refresh current page",   "View",   "reload f5"),
            "open_data":    ("Open data folder",       "System", "files folder"),
            "open_logs":    ("Open logs folder",       "System", "files folder log"),
            "open_quarantine": ("Open quarantine folder", "System", "files folder qr"),
            "open_backups": ("Open backups folder",    "System", "files folder backup"),
            "copy_diag":    ("Copy diagnostics report","System", "diagnostics report clipboard"),
            "save_diag":    ("Save diagnostics report","System", "diagnostics report file"),
            "check_updates":("Check for updates",      "App",    "update version release"),
            "clear_cache":  ("Clear application cache","System", "cache reset clean"),
            "backup_db":    ("Backup database now",    "System", "backup sqlite save"),
            "export_settings": ("Export settings as JSON", "App", "settings json export"),
            "open_repo":    ("Open GitHub repository", "App",    "github source url"),
            "quit":         ("Quit application",       "App",    "exit close quit"),
        }
        for key, fn in actions.items():
            meta = labels.get(key, (key.replace("_", " ").title(), "Actions", key))
            reg.register(Command(
                cid=f"action.{key}",
                title=meta[0],
                group=meta[1],
                handler=fn,
                keywords=meta[2].split(),
            ))
    return reg
