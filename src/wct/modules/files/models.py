from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ActionType(str, Enum):
    MOVE = "move"
    RENAME = "rename"
    DELETE = "delete"
    QUARANTINE = "quarantine"
    COPY = "copy"
    IGNORE = "ignore"


class ActionStatus(str, Enum):
    PLANNED = "planned"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class ScannedFile:
    """A file discovered during scan."""
    path: Path
    name: str
    extension: str
    size: int
    category: str = "Misc"
    sha256: str = ""


@dataclass
class PlannedFileAction:
    """What the organizer plans to do with a file."""
    file: ScannedFile
    action: ActionType = ActionType.MOVE
    target_path: str = ""
    rule_name: str = "built-in"
    confidence: float = 1.0


@dataclass
class RollbackInfo:
    """Metadata needed to undo an action."""
    action_db_id: int = 0
    original_path: str = ""
    new_path: str = ""
    original_name: str = ""
    action_type: str = ""
