from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from wct.config.settings import AppSettings
from wct.core.event_bus import EventBus
from wct.db.repositories import (
    EventRepository,
    FileActionRepository,
    FileRuleRepository,
    NotificationRepository,
    QuarantineRepository,
)
from wct.modules.files.actions import FileActionExecutor
from wct.modules.files.models import PlannedFileAction
from wct.modules.files.monitor import FileMonitor
from wct.modules.files.rule_engine import FileRuleEngine
from wct.modules.files.scanner import FolderScanner


class FileService(QObject):
    """High-level file organizer service."""

    scan_complete = pyqtSignal(list)   # list[dict] for UI
    action_complete = pyqtSignal(dict) # single action result

    def __init__(
        self,
        settings: AppSettings,
        file_rules_repo: FileRuleRepository,
        file_actions_repo: FileActionRepository,
        quarantine_repo: QuarantineRepository,
        events_repo: EventRepository,
        notif_repo: NotificationRepository,
    ) -> None:
        super().__init__()
        self._settings = settings
        self._file_rules_repo = file_rules_repo
        self._file_actions_repo = file_actions_repo
        self._quarantine_repo = quarantine_repo
        self._events_repo = events_repo
        self._notif_repo = notif_repo

        # Rule engine
        self._rule_engine = FileRuleEngine()
        self._reload_rules()

        # Scanner
        self._scanner = FolderScanner(
            rule_engine=self._rule_engine,
            ignored_extensions=settings.files.ignored_extensions,
        )

        # Action executor
        self._executor = FileActionExecutor(
            action_repo=self._file_actions_repo,
            quarantine_repo=self._quarantine_repo,
            quarantine_days=settings.files.quarantine_days,
        )

        # File monitor (watchdog)
        self._monitor: FileMonitor | None = None
        self._pending_timer = QTimer()
        self._pending_timer.setInterval(2000)
        self._pending_timer.timeout.connect(self._check_pending)

        # Current scan results
        self._current_plans: list[PlannedFileAction] = []

    # -- public API ----------------------------------------------------------

    def start_monitoring(self) -> None:
        """Start watching configured folders."""
        folders = self._settings.files.monitored_folders
        self._monitor = FileMonitor(
            folders=folders,
            on_stable_file=self._on_new_file,
            stable_wait_sec=self._settings.files.stable_wait_sec,
            ignored_extensions=self._settings.files.ignored_extensions,
        )
        self._monitor.start()
        self._pending_timer.start()
        logger.info("File monitoring started for: {}", folders)

    def stop_monitoring(self) -> None:
        if self._monitor:
            self._monitor.stop()
            self._monitor = None
        self._pending_timer.stop()
        logger.info("File monitoring stopped")

    def scan_now(self, folders: list[str] | None = None) -> list[dict]:
        self._reload_rules()
        target = folders or self._settings.files.monitored_folders
        self._current_plans = self._scanner.scan(target)
        dicts = FolderScanner.plans_to_dicts(self._current_plans)
        self.scan_complete.emit(dicts)
        return dicts

    def apply_all(self) -> int:
        """Execute all planned actions. Returns count of successful actions."""
        count = 0
        for plan in self._current_plans:
            result = self._executor.execute(
                plan, base_target_dir=Path(plan.file.path).parent,
            )
            if result:
                count += 1
                self._events_repo.insert(
                    module="files",
                    severity="info",
                    event_type="file_action",
                    title=f"{plan.action.value}: {plan.file.name}",
                    metadata={"source": str(plan.file.path), "target": result.new_path},
                )
        self._current_plans.clear()
        logger.info("Applied {} file actions", count)
        EventBus.emit("files.actions_applied", count=count)
        return count

    def apply_selected(self, indices: list[int]) -> int:
        """Execute only selected planned actions by index."""
        count = 0
        applied_indices = []
        for idx in sorted(indices, reverse=True):
            if 0 <= idx < len(self._current_plans):
                plan = self._current_plans[idx]
                result = self._executor.execute(
                    plan, base_target_dir=Path(plan.file.path).parent,
                )
                if result:
                    count += 1
                    applied_indices.append(idx)

        # Remove applied plans
        for idx in applied_indices:
            self._current_plans.pop(idx)

        return count

    def rollback_action(self, action_id: int) -> bool:
        return self._executor.rollback(action_id)

    def reload_rules(self) -> None:
        self._reload_rules()

    def restore_quarantine(self, item_id: int) -> bool:
        item = self._quarantine_repo.get(item_id)
        if not item:
            return False
        src = Path(item["quarantine_path"])
        dst = Path(item["original_path"])
        if not src.exists():
            self._quarantine_repo.purge(item_id)
            return False
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            src.replace(dst)
        except OSError as exc:
            logger.warning("Restore failed: {}", exc)
            return False
        self._quarantine_repo.restore(item_id)
        self._events_repo.insert(
            module="quarantine",
            severity="info",
            event_type="restore",
            title=f"Restored {dst.name}",
            metadata={"id": item_id, "target": str(dst)},
        )
        return True

    def purge_quarantine(self, item_id: int) -> bool:
        item = self._quarantine_repo.get(item_id)
        if not item:
            return False
        src = Path(item["quarantine_path"])
        try:
            if src.exists():
                src.unlink()
        except OSError as exc:
            logger.warning("Purge failed: {}", exc)
        self._quarantine_repo.purge(item_id)
        self._events_repo.insert(
            module="quarantine",
            severity="info",
            event_type="purge",
            title=f"Purged item #{item_id}",
        )
        return True

    def purge_expired_quarantine(self) -> int:
        items = self._quarantine_repo.expired()
        count = 0
        for it in items:
            if self.purge_quarantine(it["id"]):
                count += 1
        return count

    # -- internal ------------------------------------------------------------

    def _reload_rules(self) -> None:
        rules = self._file_rules_repo.get_enabled()
        self._rule_engine.set_rules(rules)

    def _on_new_file(self, path: Path) -> None:
        """Called by watchdog handler when a file becomes stable."""
        logger.debug("New stable file detected: {}", path)
        if self._settings.files.auto_mode:
            # Auto-mode: scan and apply immediately
            from wct.modules.files.models import ScannedFile
            sf = ScannedFile(
                path=path,
                name=path.name,
                extension=path.suffix,
                size=path.stat().st_size,
            )
            plan = self._rule_engine.evaluate(sf)
            result = self._executor.execute(plan, base_target_dir=path.parent)
            if result:
                self._events_repo.insert(
                    module="files",
                    severity="info",
                    event_type="auto_action",
                    title=f"Auto {plan.action.value}: {path.name}",
                )
                EventBus.emit("files.auto_action", path=str(path), action=plan.action.value)
        else:
            EventBus.emit("files.new_file", path=str(path))

    def _check_pending(self) -> None:
        if self._monitor:
            self._monitor.check_pending()
