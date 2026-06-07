from __future__ import annotations

import re
import time
from pathlib import Path

from wct.modules.files.models import ActionType, PlannedFileAction, ScannedFile
from wct.shared.models import FILE_CATEGORIES


class FileRuleEngine:
    """Evaluates files against a priority-ordered list of rules."""

    def __init__(self, user_rules: list[dict] | None = None) -> None:
        self._user_rules = user_rules or []

    def set_rules(self, rules: list[dict]) -> None:
        self._user_rules = rules

    def evaluate(self, file: ScannedFile) -> PlannedFileAction:
        """Return the best matching action for a file."""
        # 1) User rules first (ordered by priority)
        for rule in self._user_rules:
            if self._matches(file, rule.get("condition_json", {})):
                act_json = rule.get("action_json", {})
                return PlannedFileAction(
                    file=file,
                    action=ActionType(act_json.get("type", "move")),
                    target_path=act_json.get("target", ""),
                    rule_name=rule.get("name", "user rule"),
                    confidence=0.95,
                )

        # 2) Built-in category rules
        for category, extensions in FILE_CATEGORIES.items():
            if file.extension.lower() in extensions:
                return PlannedFileAction(
                    file=file,
                    action=ActionType.MOVE,
                    target_path=category,
                    rule_name=f"built-in: {category}",
                    confidence=0.85,
                )

        # 3) Fallback
        return PlannedFileAction(
            file=file,
            action=ActionType.MOVE,
            target_path="Misc",
            rule_name="built-in: fallback",
            confidence=0.5,
        )

    # -- matching helpers ----------------------------------------------------

    @staticmethod
    def _matches(file: ScannedFile, condition: dict) -> bool:
        """Check if a file matches all conditions in a rule."""
        # Extension match
        exts = condition.get("extensions")
        if exts and file.extension.lower() not in [e.lower() for e in exts]:
            return False

        # Filename contains
        pattern = condition.get("filename_contains")
        if pattern and pattern.lower() not in file.name.lower():
            return False

        # Regex match
        regex = condition.get("regex")
        if regex:
            try:
                if not re.search(regex, file.name, re.IGNORECASE):
                    return False
            except re.error:
                return False

        # Min size (MB)
        min_mb = condition.get("min_size_mb")
        if min_mb and file.size < min_mb * 1024 * 1024:
            return False

        # Max size (MB)
        max_mb = condition.get("max_size_mb")
        if max_mb and file.size > max_mb * 1024 * 1024:
            return False

        # Older than N days
        older_days = condition.get("older_than_days")
        if older_days:
            try:
                mtime = Path(file.path).stat().st_mtime
                age_days = (time.time() - mtime) / 86400
                if age_days < older_days:
                    return False
            except OSError:
                pass

        return True
