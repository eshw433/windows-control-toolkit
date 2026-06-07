from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class LiveConnection:
    pid: int
    exe_name: str
    exe_path: str
    local_addr: str
    local_port: int
    remote_addr: str
    remote_port: int
    protocol: str
    status: str
    remote_domain: str = ""
    country: str = ""
    asn: str = ""
    trust_state: str = "unknown"
    process_db_id: int | None = None


@dataclass
class RiskReport:
    exe_path: str
    level: RiskLevel = RiskLevel.LOW
    reasons: list[str] = field(default_factory=list)
    score: int = 0

    def add(self, reason: str, points: int) -> None:
        self.reasons.append(reason)
        self.score += points
        if self.score >= 80:
            self.level = RiskLevel.CRITICAL
        elif self.score >= 50:
            self.level = RiskLevel.HIGH
        elif self.score >= 25:
            self.level = RiskLevel.MEDIUM
