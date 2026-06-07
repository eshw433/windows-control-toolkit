from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


# ---------------------------------------------------------------------------
# Severity / trust enums
# ---------------------------------------------------------------------------

class Severity(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class TrustState(str, Enum):
    UNKNOWN = "unknown"
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    ASK = "ask"
    TEMP_ALLOW = "temp_allow"
    TEMP_BLOCK = "temp_block"


class FileActionType(str, Enum):
    MOVE = "move"
    RENAME = "rename"
    DELETE = "delete"
    QUARANTINE = "quarantine"
    COPY = "copy"
    IGNORE = "ignore"


class ConnectionProtocol(str, Enum):
    TCP = "tcp"
    UDP = "udp"
    ANY = "any"


# ---------------------------------------------------------------------------
# Network domain objects
# ---------------------------------------------------------------------------

@dataclass
class ProcessInfo:
    pid: int
    name: str
    exe_path: str
    publisher: str = ""
    file_hash: str = ""
    trust_state: TrustState = TrustState.UNKNOWN


@dataclass
class NetworkConnectionInfo:
    process: ProcessInfo
    local_addr: str = ""
    local_port: int = 0
    remote_addr: str = ""
    remote_port: int = 0
    protocol: str = "tcp"
    status: str = ""
    remote_domain: str = ""
    country: str = ""
    asn: str = ""


# ---------------------------------------------------------------------------
# File domain objects
# ---------------------------------------------------------------------------

@dataclass
class FileInfo:
    path: str
    name: str
    extension: str
    size: int = 0
    sha256: str = ""


@dataclass
class PlannedAction:
    file: FileInfo
    action: FileActionType
    target_path: str = ""
    rule_name: str = ""
    confidence: float = 1.0


# ---------------------------------------------------------------------------
# Built-in file categories
# ---------------------------------------------------------------------------

FILE_CATEGORIES: dict[str, list[str]] = {
    "Documents":   [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
                    ".odt", ".ods", ".odp", ".txt", ".rtf", ".csv", ".md"],
    "Images":      [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp",
                    ".ico", ".tiff", ".heic", ".heif", ".raw", ".psd", ".ai"],
    "Videos":      [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"],
    "Audio":       [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a", ".opus"],
    "Archives":    [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso"],
    "Installers":  [".exe", ".msi", ".msix", ".appx"],
    "Code":        [".py", ".js", ".ts", ".html", ".css", ".java", ".cpp", ".c",
                    ".h", ".cs", ".go", ".rs", ".rb", ".php", ".json", ".xml", ".yaml", ".yml"],
    "Torrents":    [".torrent", ".magnet"],
    "Fonts":       [".ttf", ".otf", ".woff", ".woff2"],
    "Databases":   [".db", ".sqlite", ".sql", ".mdb"],
}
