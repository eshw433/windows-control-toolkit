"""Tests for modules/network/risk.py"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from wct.modules.network.risk import score_connection, RiskLevel


def test_known_safe_port():
    result = score_connection(remote_port=443, remote_ip="8.8.8.8", exe_name="chrome.exe")
    assert result.level in (RiskLevel.LOW, RiskLevel.MEDIUM)


def test_suspicious_port():
    result = score_connection(remote_port=4444, remote_ip="1.2.3.4", exe_name="unknown.exe")
    assert result.score > 0


def test_localhost_is_low_risk():
    result = score_connection(remote_port=8080, remote_ip="127.0.0.1", exe_name="app.exe")
    assert result.level == RiskLevel.LOW


def test_score_returns_risk_result():
    result = score_connection(remote_port=80, remote_ip="93.184.216.34", exe_name="curl.exe")
    assert hasattr(result, "score")
    assert hasattr(result, "level")
    assert 0 <= result.score <= 100
