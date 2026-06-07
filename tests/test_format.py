"""Tests for core/format.py"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from wct.core.format import human_size, humanize_iso_date


def test_human_size_bytes():
    assert human_size(0) == "0 B"
    assert human_size(512) == "512 B"


def test_human_size_kb():
    assert human_size(1024) == "1.0 KB"


def test_human_size_mb():
    assert human_size(1024 * 1024) == "1.0 MB"


def test_human_size_gb():
    assert human_size(1024 ** 3) == "1.0 GB"


def test_humanize_iso_date_empty():
    assert humanize_iso_date("") == ""


def test_humanize_iso_date_valid():
    result = humanize_iso_date("2024-01-15T10:30:00")
    assert "2024" in result or "01" in result or "15" in result
