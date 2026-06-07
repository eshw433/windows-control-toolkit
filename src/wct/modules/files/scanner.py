from __future__ import annotations

from pathlib import Path

from loguru import logger

from wct.modules.files.dedupe import hash_file
from wct.modules.files.models import PlannedFileAction, ScannedFile
from wct.modules.files.rule_engine import FileRuleEngine
from wct.shared.models import FILE_CATEGORIES


def _classify(ext: str) -> str:
    """Return the built-in category for an extension."""
    ext_lower = ext.lower()
    for cat, exts in FILE_CATEGORIES.items():
        if ext_lower in exts:
            return cat
    return "Misc"


def _human_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024  # type: ignore[assignment]
    return f"{size:.1f} TB"


class FolderScanner:
    """Scans a list of folders and produces planned actions."""

    def __init__(self, rule_engine: FileRuleEngine, ignored_extensions: list[str] | None = None) -> None:
        self._rule_engine = rule_engine
        self._ignored = set(e.lower() for e in (ignored_extensions or []))

    def scan(self, folders: list[str], compute_hashes: bool = False) -> list[PlannedFileAction]:
        """Scan all files in the given folders and evaluate rules."""
        plans: list[PlannedFileAction] = []

        for folder_str in folders:
            folder = Path(folder_str)
            if not folder.exists() or not folder.is_dir():
                logger.warning("Scan: folder does not exist: {}", folder)
                continue

            for fp in folder.iterdir():
                if not fp.is_file():
                    continue
                if fp.suffix.lower() in self._ignored:
                    continue
                if fp.name.startswith("."):
                    continue

                try:
                    stat = fp.stat()
                except OSError:
                    continue

                sf = ScannedFile(
                    path=fp,
                    name=fp.name,
                    extension=fp.suffix,
                    size=stat.st_size,
                    category=_classify(fp.suffix),
                    sha256=hash_file(fp) if compute_hashes else "",
                )

                action = self._rule_engine.evaluate(sf)
                plans.append(action)

        logger.info("Scan complete: {} planned actions", len(plans))
        return plans

    @staticmethod
    def plans_to_dicts(plans: list[PlannedFileAction]) -> list[dict]:
        """Convert planned actions to dicts for UI table display."""
        result = []
        for p in plans:
            result.append({
                "name": p.file.name,
                "category": p.file.category,
                "size_display": _human_size(p.file.size),
                "source": str(Path(p.file.path).parent.name),
                "action": p.action.value,
                "target": p.target_path,
                "confidence": p.confidence,
                "path": str(p.file.path),
            })
        return result
