import builtins
import io
import sys
import os
import json
import contextlib
import importlib.util
from unittest import mock
from types import SimpleNamespace

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

spec = importlib.util.spec_from_file_location("ghtr", os.path.join(ROOT, "GhostTR.py"))
ghtr = importlib.util.module_from_spec(spec)
with mock.patch("os.system"):
    spec.loader.exec_module(ghtr)


def run_with_input(func, *answers):
    """Run an option function with mocked user input, return captured stdout."""
    answers = iter(answers)
    builtins.input = lambda *a: next(answers)
    buf = io.StringIO()
    with mock.patch("os.system"), contextlib.redirect_stdout(buf):
        func()
    return buf.getvalue()


def fake_response(json_data=None, text="", status_code=200):
    """Mock a requests.Response. If json_data is given, .text carries its JSON."""
    resp = SimpleNamespace()
    resp.text = json.dumps(json_data) if json_data is not None else text
    resp.status_code = status_code
    return resp


IPWHOIS_OK = {
    "success": True, "type": "IPv4", "country": "Germany", "country_code": "DE",
    "city": "Aachen", "continent": "Europe", "continent_code": "EU",
    "region": "North Rhine-Westphalia", "region_code": "NW",
    "latitude": 50.7753, "longitude": 6.0839, "is_eu": True, "postal": "52062",
    "calling_code": "49", "capital": "Berlin", "borders": [],
    "flag": {"emoji": "DE"},
    "connection": {"asn": 3320, "org": "Deutsche Telekom", "isp": "Telekom", "domain": "telekom.de"},
    "timezone": {"id": "Europe/Berlin", "abbr": "CET", "is_dst": False,
                 "offset": 3600, "utc": "+01:00", "current_time": "2026-09-13T12:00"},
}


# ---------- utilities ----------

def test_safe_get_nested():
    assert ghtr.safe_get(IPWHOIS_OK, "connection", "isp") == "Telekom"


def test_safe_get_missing_returns_default():
    assert ghtr.safe_get(IPWHOIS_OK, "connection", "nope", default="N/A") == "N/A"
    assert ghtr.safe_get(IPWHOIS_OK, "nope", "deeper") == "N/A"


def test_safe_get_empty_value_returns_default():
    data = {"flag": {"emoji": ""}}
    assert ghtr.safe_get(data, "flag", "emoji") == "N/A"


# ---------- IP Tracker ----------

def test_ip_track_success():
    with mock.patch.object(ghtr.requests, "get", return_value=fake_response(IPWHOIS_OK)):
        out = run_with_input(ghtr.IP_Track, "85.1.2.3")
    assert "Aachen" in out
    assert "50.7753,6.0839" in out  # full float precision kept in maps link


def test_ip_track_api_failure_no_crash():
    bad = {"success": False, "message": "invalid IP"}
    with mock.patch.object(ghtr.requests, "get", return_value=fake_response(bad)):
        out = run_with_input(ghtr.IP_Track, "999.999.999.999")
    assert "invalid IP" in out


def test_ip_track_network_error_no_crash():
    with mock.patch.object(ghtr.requests, "get", side_effect=requests.ConnectionError("boom")):
        out = run_with_input(ghtr.IP_Track, "1.2.3.4")
    assert "Failed" in out


def test_ip_track_uses_https():
    with mock.patch.object(ghtr.requests, "get", return_value=fake_response(IPWHOIS_OK)) as m:
        run_with_input(ghtr.IP_Track, "8.8.8.8")
    assert m.call_args.args[0].startswith("https://")


def test_ip_track_uses_timeout():
    with mock.patch.object(ghtr.requests, "get", return_value=fake_response(IPWHOIS_OK)) as m:
        run_with_input(ghtr.IP_Track, "8.8.8.8")
    assert m.call_args.kwargs.get("timeout") == ghtr.REQUEST_TIMEOUT


# ---------- Phone Tracker ----------

def test_phone_track_valid_german_number():
    out = run_with_input(ghtr.phoneGW, "+4915123456789", "DE")
    assert "Germany" in out
    assert "True" in out  # valid-number flag


def test_phone_track_invalid_number_no_crash():
    out = run_with_input(ghtr.phoneGW, "not-a-phone", "DE")
    assert "Invalid phone number" in out


# ---------- Username Tracker ----------

def test_username_track_found_and_not_found():
    class FakeSession:
        headers = {}

        def get(self, url, timeout=None, allow_redirects=None):
            status = 200 if url == "https://www.github.com/testuser" else 404
            return SimpleNamespace(status_code=status)

    with mock.patch.object(ghtr.requests, "Session", lambda: FakeSession()):
        out = run_with_input(ghtr.TrackLu, "testuser")
    assert "https://www.github.com/testuser" in out
    assert "not found" in out  # every other site is 404 in this mock


def test_username_tracker_uses_session_with_timeout():
    captured = {}

    class FakeSession:
        headers = {}

        def get(self, url, timeout=None, allow_redirects=None):
            captured.setdefault("urls", []).append(url)
            captured["timeout"] = timeout
            return SimpleNamespace(status_code=404)

    with mock.patch.object(ghtr.requests, "Session", lambda: FakeSession()):
        run_with_input(ghtr.TrackLu, "someone")
    assert len(captured["urls"]) > 10      # scans many sites
    assert captured["timeout"] == ghtr.REQUEST_TIMEOUT


def test_username_track_has_browser_user_agent():
    assert "Mozilla" in ghtr.BROWSER_HEADERS["User-Agent"]


def test_site_list_has_no_duplicates_or_dead_sites():
    import re
    source = open(os.path.join(ROOT, "GhostTR.py")).read()
    block = re.search(r"social_media = \[(.*?)\]", source, re.S).group(1)
    names = re.findall(r'"name": "([^"]+)"', block)
    assert len(names) == len(set(names))  # no duplicate entries
    for dead in ("Periscope", "StumbleUpon", "Ello", "We Heart It"):
        assert dead not in names


# ---------- Show IP ----------

def test_show_ip():
    with mock.patch.object(ghtr.requests, "get", return_value=fake_response(text="203.0.113.7")):
        out = run_with_input(ghtr.showIP)
    assert "203.0.113.7" in out


def test_show_ip_network_error_no_crash():
    with mock.patch.object(ghtr.requests, "get", side_effect=requests.Timeout("slow")):
        out = run_with_input(ghtr.showIP)
    assert "Failed" in out


# ---------- options ----------

def test_options_cover_all_features():
    nums = {o["num"] for o in ghtr.options}
    assert nums == {0, 1, 2, 3, 4}
    texts = " ".join(o["text"] for o in ghtr.options)
    assert "IP Tracker" in texts and "Phone" in texts and "Username" in texts


def test_is_in_options():
    assert ghtr.is_in_options(0) is True
    assert ghtr.is_in_options(4) is True
    assert ghtr.is_in_options(99) is False


# ---------- version ----------

def test_version_flag():
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        assert ghtr.handle_version_args(['--version']) is True
    assert f"v{ghtr.__version__}" in out.getvalue()


def test_no_version_flag_runs_through():
    assert ghtr.handle_version_args([]) is False


# ---------- NO_COLOR (preview feature) ----------

def test_no_color_strips_ansi_codes(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    ghtr.apply_no_color()
    assert ghtr.Gr == "" and ghtr.Wh == "" and ghtr.Re == ""
    monkeypatch.delenv("NO_COLOR")
    import importlib
    spec2 = importlib.util.spec_from_file_location("ghtr2", os.path.join(ROOT, "GhostTR.py"))
    m2 = importlib.util.module_from_spec(spec2)
    with mock.patch("os.system"):
        spec2.loader.exec_module(m2)
    assert m2.Gr != ""  # colors restored on fresh import
    ghtr.Gr = m2.Gr  # restore for other tests in the same session
    ghtr.Wh = m2.Wh
    ghtr.Re = m2.Re
