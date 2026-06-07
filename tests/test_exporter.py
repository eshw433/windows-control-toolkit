"""Tests for core/exporter.py"""
import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pathlib import Path
from wct.core.exporter import export_csv, export_json, import_csv, import_json


def test_export_csv_roundtrip(tmp_path):
    rows = [{"name": "file.pdf", "size": 1024}, {"name": "photo.jpg", "size": 2048}]
    target = tmp_path / "out.csv"
    count = export_csv(rows, target)
    assert count == 2
    loaded = import_csv(target)
    assert len(loaded) == 2
    assert loaded[0]["name"] == "file.pdf"


def test_export_csv_empty(tmp_path):
    target = tmp_path / "empty.csv"
    count = export_csv([], target)
    assert count == 0
    assert target.read_text() == ""


def test_export_json_roundtrip(tmp_path):
    data = {"key": "value", "count": 42}
    target = tmp_path / "out.json"
    export_json(data, target)
    loaded = import_json(target)
    assert loaded["key"] == "value"
    assert loaded["count"] == 42


def test_import_json_missing(tmp_path):
    result = import_json(tmp_path / "nonexistent.json")
    assert result is None


def test_import_csv_missing(tmp_path):
    result = import_csv(tmp_path / "nonexistent.csv")
    assert result == []
