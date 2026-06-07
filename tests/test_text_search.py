"""Tests for core/text_search.py"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from wct.core.text_search import TextSearch


def test_plain_match():
    ts = TextSearch("hello")
    assert ts.matches("say hello world")


def test_plain_no_match():
    ts = TextSearch("xyz")
    assert not ts.matches("hello world")


def test_case_insensitive():
    ts = TextSearch("HELLO")
    assert ts.matches("hello world")


def test_empty_query_matches_all():
    ts = TextSearch("")
    assert ts.matches("anything")
    assert ts.matches("")


def test_filter_list():
    ts = TextSearch("py")
    items = ["python.exe", "notepad.exe", "pycharm.exe", "chrome.exe"]
    result = ts.filter(items)
    assert "python.exe" in result
    assert "pycharm.exe" in result
    assert "notepad.exe" not in result
    assert "chrome.exe" not in result
