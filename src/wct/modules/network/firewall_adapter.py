from __future__ import annotations

import ctypes
import hashlib
import subprocess
from dataclasses import dataclass

from loguru import logger


_CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def is_admin() -> bool:
    try:
        windll = getattr(ctypes, "windll", None)
        if windll is None:
            return False
        return windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


@dataclass
class WinFirewallRule:
    name: str
    direction: str
    action: str
    program: str
    protocol: str = "any"
    remote_addr: str = ""
    remote_port: str = ""
    enabled: bool = True


_PREFIX = "WCT"


def _rule_name(action: str, direction: str, exe_path: str, rule_id: int) -> str:
    """Generate a stable WCT rule name."""
    h = hashlib.sha256(exe_path.encode()).hexdigest()[:8]
    return f"{_PREFIX}_{action.upper()}_{direction.upper()}_{h}_{rule_id}"


class FirewallAdapter:
    """Interface to Windows Firewall via netsh advfirewall."""

    @staticmethod
    def create_rule(name: str, exe_path: str, direction: str = "out",
                    action: str = "block", protocol: str = "any",
                    remote_addr: str = "", remote_port: str = "") -> bool:
        """Create a firewall rule. Returns True on success."""
        if not is_admin():
            logger.error("Cannot create firewall rule without admin rights")
            return False

        # Security: validate exe_path is an existing file on disk
        from pathlib import Path as _Path
        resolved = _Path(exe_path).resolve()
        if not resolved.is_file():
            logger.error("Firewall rule rejected: exe_path is not a valid file: {}", exe_path)
            return False

        dir_map = {"out": "dir=out", "in": "dir=in"}
        act_map = {"block": "action=block", "allow": "action=allow"}

        cmd = [
            "netsh", "advfirewall", "firewall", "add", "rule",
            f"name={name}",
            dir_map.get(direction, "dir=out"),
            act_map.get(action, "action=block"),
            f"program={resolved}",
            "enable=yes",
        ]

        if protocol and protocol != "any":
            cmd.append(f"protocol={protocol}")
        if remote_addr:
            cmd.append(f"remoteip={remote_addr}")
        if remote_port and protocol in ("tcp", "udp"):
            cmd.append(f"remoteport={remote_port}")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=15,
                creationflags=_CREATE_NO_WINDOW,
            )
            if result.returncode == 0:
                logger.info("Firewall rule created: {}", name)
                return True
            logger.error("netsh error: {}", result.stderr.strip())
            return False
        except Exception as exc:
            logger.error("Failed to create firewall rule: {}", exc)
            return False

    @staticmethod
    def delete_rule(name: str) -> bool:
        """Delete a firewall rule by name."""
        if not is_admin():
            logger.error("Cannot delete firewall rule without admin rights")
            return False

        cmd = ["netsh", "advfirewall", "firewall", "delete", "rule", f"name={name}"]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=15,
                creationflags=_CREATE_NO_WINDOW,
            )
            if result.returncode == 0:
                logger.info("Firewall rule deleted: {}", name)
                return True
            logger.error("netsh delete error: {}", result.stderr.strip())
            return False
        except Exception as exc:
            logger.error("Failed to delete firewall rule: {}", exc)
            return False

    @staticmethod
    def list_wct_rules() -> list[str]:
        """List names of all rules created by this app (WCT_ prefix)."""
        cmd = ["netsh", "advfirewall", "firewall", "show", "rule", f"name=all"]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30,
                creationflags=_CREATE_NO_WINDOW,
            )
            names = []
            for line in result.stdout.splitlines():
                if line.startswith("Rule Name:"):
                    rname = line.split(":", 1)[1].strip()
                    if rname.startswith(_PREFIX + "_"):
                        names.append(rname)
            return names
        except Exception as exc:
            logger.error("Failed to list firewall rules: {}", exc)
            return []

    @staticmethod
    def toggle_rule(name: str, enable: bool) -> bool:
        """Enable or disable a firewall rule."""
        if not is_admin():
            return False
        state = "yes" if enable else "no"
        cmd = [
            "netsh", "advfirewall", "firewall", "set", "rule",
            f"name={name}", "new", f"enable={state}",
        ]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=15,
                creationflags=_CREATE_NO_WINDOW,
            )
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    def generate_rule_name(action: str, direction: str, exe_path: str, rule_id: int) -> str:
        return _rule_name(action, direction, exe_path, rule_id)
