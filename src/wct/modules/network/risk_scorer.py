from __future__ import annotations

import os
from pathlib import Path

from wct.modules.network.models import RiskReport


_TRUSTED_DIRS = {
    os.environ.get("SYSTEMROOT", r"C:\Windows"),
    os.environ.get("PROGRAMFILES", r"C:\Program Files"),
    os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
}

_SUSPICIOUS_DIRS = {"Downloads", "Desktop", "Temp", "AppData\\Local\\Temp"}


class RiskScorer:
    """Evaluate how suspicious a given process is."""

    def score(self, exe_path: str, unique_remote_ips: int = 0,
              is_signed: bool | None = None) -> RiskReport:
        report = RiskReport(exe_path=exe_path)

        if not exe_path:
            report.add("Unknown executable path", 30)
            return report

        p = Path(exe_path)

        # Location checks
        path_str = str(p).lower()
        in_trusted = any(path_str.startswith(td.lower()) for td in _TRUSTED_DIRS if td)
        if not in_trusted:
            report.add("Running outside trusted directories", 15)

        for sus in _SUSPICIOUS_DIRS:
            if sus.lower() in path_str:
                report.add(f"Running from suspicious location ({sus})", 25)
                break

        # Signing
        if is_signed is False:
            report.add("Executable is not digitally signed", 20)

        # Behaviour
        if unique_remote_ips > 20:
            report.add(f"Connecting to {unique_remote_ips} unique remote IPs", 15)
        elif unique_remote_ips > 50:
            report.add(f"Connecting to {unique_remote_ips} unique remote IPs (very high)", 30)

        # Extension tricks
        if p.suffixes and len(p.suffixes) > 1:
            report.add("Double extension detected", 20)

        return report
