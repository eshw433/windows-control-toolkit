from __future__ import annotations


BUILTIN_TEMPLATES: list[dict] = [
    {
        "name": "Move installers to Installers folder",
        "category": "downloads",
        "description": "Move setup .exe and .msi files to Installers/",
        "payload": {
            "condition": {"extensions": [".exe", ".msi", ".bat"]},
            "action": {"type": "move", "target": "Installers"},
            "priority": 30,
        },
    },
    {
        "name": "Move archives",
        "category": "downloads",
        "description": "Auto-move .zip, .rar, .7z to Archives/",
        "payload": {
            "condition": {"extensions": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"]},
            "action": {"type": "move", "target": "Archives"},
            "priority": 35,
        },
    },
    {
        "name": "Quarantine suspicious .bat/.scr",
        "category": "security",
        "description": "Send scripts and screensavers to quarantine for review.",
        "payload": {
            "condition": {"extensions": [".bat", ".scr", ".vbs", ".ps1"]},
            "action": {"type": "quarantine"},
            "priority": 10,
        },
    },
    {
        "name": "Documents to Documents",
        "category": "general",
        "description": "PDF, DOCX, XLSX into Documents/",
        "payload": {
            "condition": {"extensions": [".pdf", ".docx", ".doc", ".xls", ".xlsx", ".odt"]},
            "action": {"type": "move", "target": "Documents"},
            "priority": 50,
        },
    },
    {
        "name": "Images to Images",
        "category": "general",
        "description": "Common image extensions into Images/",
        "payload": {
            "condition": {"extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]},
            "action": {"type": "move", "target": "Images"},
            "priority": 50,
        },
    },
    {
        "name": "Videos to Videos",
        "category": "general",
        "description": "Common video extensions into Videos/",
        "payload": {
            "condition": {"extensions": [".mp4", ".mkv", ".avi", ".mov", ".webm"]},
            "action": {"type": "move", "target": "Videos"},
            "priority": 50,
        },
    },
    {
        "name": "Audio to Music",
        "category": "general",
        "description": "MP3, WAV, FLAC into Music/",
        "payload": {
            "condition": {"extensions": [".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg"]},
            "action": {"type": "move", "target": "Music"},
            "priority": 50,
        },
    },
    {
        "name": "Quarantine large unknown",
        "category": "security",
        "description": "Quarantine large files over 200MB whose extension we don't know.",
        "payload": {
            "condition": {"min_size_mb": 200, "extensions": [".dat", ".bin", ".unknown"]},
            "action": {"type": "quarantine"},
            "priority": 20,
        },
    },
    {
        "name": "Delete old screenshots",
        "category": "cleanup",
        "description": "Auto-delete PNG/JPG screenshots older than 90 days containing 'Screenshot' in name.",
        "payload": {
            "condition": {
                "extensions": [".png", ".jpg", ".jpeg"],
                "filename_contains": "screenshot",
                "older_than_days": 90,
            },
            "action": {"type": "delete"},
            "priority": 40,
        },
    },
    {
        "name": "Move torrents to Torrents",
        "category": "downloads",
        "description": ".torrent files to Torrents/",
        "payload": {
            "condition": {"extensions": [".torrent"]},
            "action": {"type": "move", "target": "Torrents"},
            "priority": 45,
        },
    },
    {
        "name": "Move ISO/IMG to ISO",
        "category": "downloads",
        "description": "Disc images into ISO/",
        "payload": {
            "condition": {"extensions": [".iso", ".img", ".vhd", ".vmdk"]},
            "action": {"type": "move", "target": "ISO"},
            "priority": 32,
        },
    },
    {
        "name": "Code files to Code",
        "category": "general",
        "description": "Programming files into Code/",
        "payload": {
            "condition": {"extensions": [".py", ".js", ".ts", ".cs", ".cpp", ".c", ".h", ".java"]},
            "action": {"type": "move", "target": "Code"},
            "priority": 55,
        },
    },
    {
        "name": "Mark .crdownload as ignored",
        "category": "system",
        "description": "Avoid touching incomplete downloads",
        "payload": {
            "condition": {"extensions": [".crdownload", ".part", ".tmp"]},
            "action": {"type": "ignore"},
            "priority": 5,
        },
    },
    {
        "name": "Old large files cleanup",
        "category": "cleanup",
        "description": "Quarantine files larger than 500MB and older than 1 year.",
        "payload": {
            "condition": {"min_size_mb": 500, "older_than_days": 365},
            "action": {"type": "quarantine"},
            "priority": 25,
        },
    },
    {
        "name": "Rename random-named installers",
        "category": "downloads",
        "description": "If filename matches typical random installer (e.g. setup_<hash>.exe)",
        "payload": {
            "condition": {
                "extensions": [".exe"],
                "regex": r"setup[_-][a-f0-9]{8,}\\.exe",
            },
            "action": {"type": "rename"},
            "priority": 28,
        },
    },
    {
        "name": "Archive old PDFs",
        "category": "cleanup",
        "description": "Move PDFs older than 180 days to Documents/Archive",
        "payload": {
            "condition": {
                "extensions": [".pdf"],
                "older_than_days": 180,
            },
            "action": {"type": "move", "target": "Documents/Archive"},
            "priority": 60,
        },
    },
]


def template_names() -> list[str]:
    return [t["name"] for t in BUILTIN_TEMPLATES]


def find(name: str) -> dict | None:
    for t in BUILTIN_TEMPLATES:
        if t["name"] == name:
            return t
    return None


def by_category(category: str) -> list[dict]:
    return [t for t in BUILTIN_TEMPLATES if t["category"] == category]


def categories() -> list[str]:
    return sorted({t["category"] for t in BUILTIN_TEMPLATES})


def apply_to_rule_repo(repo, template: dict) -> int:
    payload = template["payload"]
    return repo.insert(
        name=template["name"],
        condition_json=payload.get("condition", {}),
        action_json=payload.get("action", {}),
        priority=payload.get("priority", 100),
        note=template.get("description", ""),
    )
