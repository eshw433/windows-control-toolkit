from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from loguru import logger


def export_csv(rows: Iterable[dict[str, Any]], target: Path,
               columns: list[str] | None = None) -> int:
    rows_list = list(rows)
    if not rows_list:
        target.write_text("", encoding="utf-8")
        return 0
    if columns is None:
        seen: list[str] = []
        for r in rows_list:
            for k in r.keys():
                if k not in seen:
                    seen.append(k)
        columns = seen
    with target.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows_list)
    return len(rows_list)


def import_csv(source: Path) -> list[dict[str, Any]]:
    if not source.exists():
        return []
    with source.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def export_json(data: Any, target: Path, *, indent: int = 2) -> int:
    payload = json.dumps(data, ensure_ascii=False, indent=indent, default=_default)
    target.write_text(payload, encoding="utf-8")
    return len(payload)


def import_json(source: Path) -> Any:
    if not source.exists():
        return None
    try:
        return json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.error("import_json: invalid file {}: {}", source, exc)
        return None


def export_rules(rules: list[dict[str, Any]], target: Path) -> int:
    bundle = {
        "format": "wct.firewall.rules",
        "version": 1,
        "generated_at": _now_iso(),
        "count": len(rules),
        "items": rules,
    }
    export_json(bundle, target)
    return len(rules)


def import_rules(source: Path) -> list[dict[str, Any]]:
    data = import_json(source)
    if not isinstance(data, dict):
        return []
    if data.get("format") not in (
        "wct.firewall.rules",
        "wct.file.rules",
    ):
        return []
    items = data.get("items")
    if not isinstance(items, list):
        return []
    return [it for it in items if isinstance(it, dict)]


def export_file_rules(rules: list[dict[str, Any]], target: Path) -> int:
    bundle = {
        "format": "wct.file.rules",
        "version": 1,
        "generated_at": _now_iso(),
        "count": len(rules),
        "items": rules,
    }
    export_json(bundle, target)
    return len(rules)


def export_events(rows: list[dict[str, Any]], target: Path) -> int:
    columns = ["timestamp", "module", "severity", "event_type", "title", "message"]
    return export_csv(rows, target, columns=columns)


def export_connections(rows: list[dict[str, Any]], target: Path) -> int:
    columns = [
        "timestamp", "exe_name", "exe_path", "pid", "protocol",
        "local_addr", "local_port", "remote_addr", "remote_port",
        "remote_domain", "country", "service_hint",
    ]
    return export_csv(rows, target, columns=columns)


def export_quarantine(rows: list[dict[str, Any]], target: Path) -> int:
    columns = [
        "id", "original_path", "quarantine_path", "size", "reason",
        "expires_at", "status",
    ]
    return export_csv(rows, target, columns=columns)


def export_bandwidth(rows: list[dict[str, Any]], target: Path) -> int:
    columns = ["day", "exe_name", "exe_path", "bytes_sent", "bytes_recv"]
    return export_csv(rows, target, columns=columns)


def export_file_actions(rows: list[dict[str, Any]], target: Path) -> int:
    columns = [
        "timestamp", "action_type", "source_path", "target_path",
        "status", "reversible", "file_size", "rule_name",
    ]
    return export_csv(rows, target, columns=columns)


def export_text_report(title: str, sections: list[tuple[str, list[str]]],
                       target: Path) -> int:
    lines: list[str] = []
    lines.append(f"{title}")
    lines.append("=" * len(title))
    lines.append(f"Generated: {_now_iso()}")
    lines.append("")
    for name, items in sections:
        lines.append(name)
        lines.append("-" * len(name))
        for it in items:
            lines.append(f"  - {it}")
        lines.append("")
    body = "\n".join(lines)
    target.write_text(body, encoding="utf-8")
    return len(body)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _default(o: Any) -> Any:
    if isinstance(o, datetime):
        return o.isoformat()
    if isinstance(o, Path):
        return str(o)
    if isinstance(o, set):
        return list(o)
    return str(o)


def merge_csvs(sources: list[Path], target: Path) -> int:
    rows: list[dict[str, Any]] = []
    columns: list[str] = []
    for s in sources:
        if not s.exists():
            continue
        with s.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames:
                for col in reader.fieldnames:
                    if col not in columns:
                        columns.append(col)
            for row in reader:
                rows.append(dict(row))
    if not rows:
        target.write_text("", encoding="utf-8")
        return 0
    return export_csv(rows, target, columns=columns)


def chunked_export(rows: Iterable[dict[str, Any]], target_template: Path,
                   chunk_size: int = 5000,
                   columns: list[str] | None = None) -> list[Path]:
    paths: list[Path] = []
    buffer: list[dict[str, Any]] = []
    index = 0
    for r in rows:
        buffer.append(r)
        if len(buffer) >= chunk_size:
            target = target_template.with_name(
                f"{target_template.stem}_{index}{target_template.suffix}"
            )
            export_csv(buffer, target, columns=columns)
            paths.append(target)
            buffer.clear()
            index += 1
    if buffer:
        target = target_template.with_name(
            f"{target_template.stem}_{index}{target_template.suffix}"
        )
        export_csv(buffer, target, columns=columns)
        paths.append(target)
    return paths



def export_pdf(title: str, sections: list[tuple[str, list[str]]], target: "Path") -> int:
    """Export a simple PDF report. Falls back to text if reportlab is unavailable."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
        from reportlab.lib.units import cm

        doc = SimpleDocTemplate(str(target), pagesize=A4,
                                leftMargin=2*cm, rightMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph(title, styles["Title"]))
        story.append(Paragraph(f"Generated: {_now_iso()}", styles["Normal"]))
        story.append(Spacer(1, 0.5*cm))
        for name, items in sections:
            story.append(Paragraph(name, styles["Heading2"]))
            for item in items:
                story.append(Paragraph(f"• {item}", styles["Normal"]))
            story.append(Spacer(1, 0.3*cm))
        doc.build(story)
        return sum(len(items) for _, items in sections)
    except ImportError:
        # Fallback: write as plain text with .pdf extension
        return export_text_report(title, sections, target)
