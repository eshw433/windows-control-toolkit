"""Tests for modules/files/rule_engine.py"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from wct.modules.files.rule_engine import RuleEngine
from wct.shared.models import FileInfo


def _make_file(name: str, ext: str, size: int = 1024) -> FileInfo:
    return FileInfo(path=f"C:/Downloads/{name}", name=name, extension=ext, size=size)


def test_extension_match():
    engine = RuleEngine()
    engine.add_rule({
        "name": "PDFs",
        "priority": 100,
        "enabled": True,
        "condition_json": {"extensions": [".pdf"]},
        "action_json": {"type": "move", "target": "Documents"},
    })
    f = _make_file("report.pdf", ".pdf")
    actions = engine.evaluate(f)
    assert len(actions) == 1
    assert actions[0].action.value == "move"


def test_no_match():
    engine = RuleEngine()
    engine.add_rule({
        "name": "PDFs",
        "priority": 100,
        "enabled": True,
        "condition_json": {"extensions": [".pdf"]},
        "action_json": {"type": "move", "target": "Documents"},
    })
    f = _make_file("photo.jpg", ".jpg")
    actions = engine.evaluate(f)
    assert len(actions) == 0


def test_disabled_rule_skipped():
    engine = RuleEngine()
    engine.add_rule({
        "name": "PDFs",
        "priority": 100,
        "enabled": False,
        "condition_json": {"extensions": [".pdf"]},
        "action_json": {"type": "move", "target": "Documents"},
    })
    f = _make_file("report.pdf", ".pdf")
    actions = engine.evaluate(f)
    assert len(actions) == 0


def test_filename_contains():
    engine = RuleEngine()
    engine.add_rule({
        "name": "Invoices",
        "priority": 100,
        "enabled": True,
        "condition_json": {"filename_contains": "invoice"},
        "action_json": {"type": "move", "target": "Finance"},
    })
    f = _make_file("invoice_2024.pdf", ".pdf")
    actions = engine.evaluate(f)
    assert len(actions) == 1
