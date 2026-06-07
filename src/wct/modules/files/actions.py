from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from loguru import logger

from wct.config.paths import AppPaths
from wct.db.repositories import FileActionRepository, QuarantineRepository
from wct.modules.files.models import ActionType, PlannedFileAction, RollbackInfo


class FileActionExecutor:
    """Executes planned file actions and records rollback metadata."""

    def __init__(
        self,
        action_repo: FileActionRepository,
        quarantine_repo: QuarantineRepository,
        quarantine_days: int = 30,
    ) -> None:
        self._action_repo = action_repo
        self._quarantine_repo = quarantine_repo
        self._quarantine_days = quarantine_days

    def execute(self, plan: PlannedFileAction, base_target_dir: Path | None = None) -> RollbackInfo | None:
        """Execute a planned action. Returns rollback info on success, None on failure."""
        try:
            if plan.action == ActionType.MOVE:
                return self._do_move(plan, base_target_dir)
            elif plan.action == ActionType.RENAME:
                return self._do_rename(plan)
            elif plan.action == ActionType.QUARANTINE:
                return self._do_quarantine(plan)
            elif plan.action == ActionType.DELETE:
                return self._do_delete(plan)
            elif plan.action == ActionType.IGNORE:
                return None
            else:
                logger.warning("Unknown action type: {}", plan.action)
                return None
        except Exception as exc:
            logger.error("Action failed for {}: {}", plan.file.name, exc)
            self._action_repo.insert(
                action_type=plan.action.value,
                source_path=str(plan.file.path),
                target_path="",
                reversible=False,
                rollback_json={"error": str(exc)},
            )
            return None

    def rollback(self, action_id: int) -> bool:
        """Undo a previously executed action."""
        record = self._action_repo.get(action_id)
        if not record:
            logger.error("Action {} not found", action_id)
            return False

        if not record.get("reversible"):
            logger.error("Action {} is not reversible", action_id)
            return False

        if record["status"] != "completed":
            logger.error("Action {} status is '{}', cannot rollback", action_id, record["status"])
            return False

        rollback_data = json.loads(record["rollback_json"]) if isinstance(record["rollback_json"], str) else record["rollback_json"]

        try:
            target = Path(record["target_path"])
            source = Path(record["source_path"])

            if record["action_type"] in ("move", "rename", "quarantine"):
                if target.exists():
                    if source.exists():
                        # Conflict — rename target with suffix
                        new_name = source.stem + "_restored" + source.suffix
                        source = source.parent / new_name
                    source.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(target), str(source))
                    logger.info("Rolled back: {} -> {}", target, source)
                else:
                    logger.warning("Target file missing, cannot rollback: {}", target)
                    return False

            self._action_repo.mark_rolled_back(action_id)
            return True

        except Exception as exc:
            logger.error("Rollback failed for action {}: {}", action_id, exc)
            return False

    # -- internal action implementations -------------------------------------

    def _do_move(self, plan: PlannedFileAction, base_dir: Path | None) -> RollbackInfo:
        src = Path(plan.file.path).resolve()
        if base_dir:
            target_dir = (base_dir / plan.target_path).resolve()
        else:
            target_dir = (src.parent / plan.target_path).resolve()

        # Security: prevent path traversal — target must not escape src's parent or base_dir
        allowed_root = (base_dir or src.parent).resolve()
        try:
            target_dir.relative_to(allowed_root)
        except ValueError:
            logger.error("Path traversal blocked: {} not under {}", target_dir, allowed_root)
            raise PermissionError(f"Target path escapes allowed directory: {target_dir}")

        target_dir.mkdir(parents=True, exist_ok=True)
        dst = target_dir / src.name

        if dst.exists():
            dst = self._unique_name(dst)

        shutil.move(str(src), str(dst))

        db_id = self._action_repo.insert(
            action_type="move",
            source_path=str(src),
            target_path=str(dst),
            reversible=True,
            rollback_json={"original_path": str(src), "new_path": str(dst)},
        )
        logger.info("Moved: {} -> {}", src, dst)
        return RollbackInfo(action_db_id=db_id, original_path=str(src),
                            new_path=str(dst), action_type="move")

    def _do_rename(self, plan: PlannedFileAction) -> RollbackInfo:
        src = Path(plan.file.path)
        new_name = plan.target_path if plan.target_path else src.name
        dst = src.parent / new_name

        if dst.exists():
            dst = self._unique_name(dst)

        shutil.move(str(src), str(dst))

        db_id = self._action_repo.insert(
            action_type="rename",
            source_path=str(src),
            target_path=str(dst),
            reversible=True,
            rollback_json={"original_path": str(src), "new_path": str(dst),
                           "original_name": src.name},
        )
        logger.info("Renamed: {} -> {}", src.name, dst.name)
        return RollbackInfo(action_db_id=db_id, original_path=str(src),
                            new_path=str(dst), original_name=src.name, action_type="rename")

    def _do_quarantine(self, plan: PlannedFileAction) -> RollbackInfo:
        src = Path(plan.file.path)
        q_dir = AppPaths.quarantine_dir() / uuid.uuid4().hex[:12]
        q_dir.mkdir(parents=True, exist_ok=True)
        dst = q_dir / src.name

        shutil.move(str(src), str(dst))

        expires = datetime.now(timezone.utc) + timedelta(days=self._quarantine_days)
        self._quarantine_repo.insert(
            original_path=str(src),
            quarantine_path=str(dst),
            reason=plan.rule_name,
            expires_at=expires.isoformat(),
        )
        db_id = self._action_repo.insert(
            action_type="quarantine",
            source_path=str(src),
            target_path=str(dst),
            reversible=True,
            rollback_json={"original_path": str(src), "quarantine_path": str(dst)},
        )
        logger.info("Quarantined: {} -> {}", src, dst)
        return RollbackInfo(action_db_id=db_id, original_path=str(src),
                            new_path=str(dst), action_type="quarantine")

    def _do_delete(self, plan: PlannedFileAction) -> RollbackInfo:
        src = Path(plan.file.path)
        # Move to recycle bin via quarantine first for safety
        return self._do_quarantine(plan)

    @staticmethod
    def _unique_name(path: Path) -> Path:
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        counter = 1
        while path.exists():
            path = parent / f"{stem}_{counter}{suffix}"
            counter += 1
        return path
