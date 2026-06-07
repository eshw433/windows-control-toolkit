"""Tests for core/stats.py"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from wct.core.stats import Counter, RollingAverage


def test_counter_increment():
    c = Counter()
    c.increment("hits")
    c.increment("hits")
    c.increment("misses")
    assert c.get("hits") == 2
    assert c.get("misses") == 1
    assert c.get("unknown") == 0


def test_counter_reset():
    c = Counter()
    c.increment("x")
    c.reset("x")
    assert c.get("x") == 0


def test_counter_total():
    c = Counter()
    c.increment("a")
    c.increment("a")
    c.increment("b")
    assert c.total() == 3


def test_rolling_average_empty():
    ra = RollingAverage(window=5)
    assert ra.value() == 0.0


def test_rolling_average_basic():
    ra = RollingAverage(window=3)
    ra.add(10)
    ra.add(20)
    ra.add(30)
    assert ra.value() == 20.0


def test_rolling_average_window():
    ra = RollingAverage(window=3)
    for v in [10, 20, 30, 40]:
        ra.add(v)
    # window=3: last 3 are 20,30,40 → avg=30
    assert ra.value() == 30.0
