from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone

from loguru import logger


@dataclass
class UsbDevice:
    device_id: str
    name: str
    drive_letter: str
    size_bytes: int
    status: str
    first_seen: str


def _run_wmic(query: str) -> list[dict]:
    try:
        result = subprocess.run(
            ["wmic", query, "get", "/format:csv"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        lines = result.stdout.strip().splitlines()
        if len(lines) < 2:
            return []
        # First line is header, second is node name, rest are data
        headers = [h.strip() for h in lines[0].split(",")]
        rows = []
        for line in lines[2:]:
            if not line.strip():
                continue
            parts = line.split(",")
            if len(parts) < len(headers):
                continue
            row = {}
            for i, h in enumerate(headers):
                row[h] = parts[i].strip()
            rows.append(row)
        return rows
    except Exception as exc:
        logger.debug("USB wmic query failed: {}", exc)
        return []


def _get_disk_drives() -> list[dict]:
    return _run_wmic("diskdrive where InterfaceType='USB'")


def _get_logical_disks() -> list[dict]:
    return _run_wmic("logicaldisk")


def _get_volume_labels() -> dict[str, str]:
    rows = _run_wmic("logicaldisk")
    return {r.get("DeviceID", "").rstrip(":"): r.get("VolumeName", "") for r in rows if r.get("DeviceID")}


def list_devices() -> list[UsbDevice]:
    drives = _get_disk_drives()
    labels = _get_volume_labels()
    results: list[UsbDevice] = []
    for d in drives:
        size_str = d.get("Size", "0")
        try:
            size = int(size_str)
        except ValueError:
            size = 0
        caption = d.get("Caption", "USB Device")
        device_id = d.get("DeviceID", "")
        status = d.get("Status", "OK")
        # Try to find drive letter from partition association — simplified: just map by caption
        drive_letter = ""
        for letter, label in labels.items():
            if label and label in caption:
                drive_letter = letter
                break
        if not drive_letter:
            # Fallback: try to parse from DeviceID PNPDeviceID
            pnp = d.get("PNPDeviceID", "")
            if "USBSTOR" in pnp:
                # No easy letter mapping without deeper WMI queries
                pass
        results.append(UsbDevice(
            device_id=device_id,
            name=caption or "USB Device",
            drive_letter=drive_letter,
            size_bytes=size,
            status=status,
            first_seen=datetime.now(timezone.utc).isoformat(),
        ))
    return results


def _get_usb_drives_via_psutil() -> list[UsbDevice]:
    try:
        import psutil
    except ImportError:
        return []
    results: list[UsbDevice] = []
    for part in psutil.disk_partitions(all=True):
        if "removable" in part.opts.lower() or "usb" in part.opts.lower():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                size = usage.total
            except Exception:
                size = 0
            results.append(UsbDevice(
                device_id=part.device,
                name=part.mountpoint,
                drive_letter=part.device.rstrip("\\"),
                size_bytes=size,
                status="Connected",
                first_seen=datetime.now(timezone.utc).isoformat(),
            ))
    return results


def list_devices_combined() -> list[UsbDevice]:
    wmic = list_devices()
    psutil = _get_usb_drives_via_psutil()
    # Merge by drive letter if possible
    seen: set[str] = set()
    out: list[UsbDevice] = []
    for d in wmic:
        out.append(d)
        seen.add(d.device_id)
    for d in psutil:
        if d.device_id not in seen:
            out.append(d)
    return out
