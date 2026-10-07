import io
import json
import urllib.error

import pytest

from core import protection
from core.protection import find_unsafe_urls, is_blocked_host, verify_turnstile


def fake_urlopen(monkeypatch, payload=None, error=None):
    requests = []

    def urlopen(request, data=None, timeout=None):
        requests.append(request)
        if error:
            raise error
        return io.BytesIO(json.dumps(payload).encode())

    monkeypatch.setattr(protection.urllib.request, "urlopen", urlopen)
    return requests


@pytest.mark.parametrize(
    "host, blocked",
    [
        ("example.com", False),
        ("notbit.ly", False),
        ("bit.ly", True),
        ("BIT.LY.", True),
        ("www.tinyurl.com", True),
        ("10.0.0.1", True),
        ("::1", True),
        ("kort.arn0.be", True),
        ("sub.kort.arn0.be", True),
        ("arn0.be", False),
    ],
)
def test_is_blocked_host(host, blocked):
    assert is_blocked_host(host, "kort.arn0.be:443") is blocked


class TestVerifyTurnstile:
    def test_success(self, monkeypatch):
        fake_urlopen(monkeypatch, {"success": True})
        assert verify_turnstile("token") is True

    def test_failure(self, monkeypatch):
        fake_urlopen(monkeypatch, {"success": False, "error-codes": ["invalid-input-response"]})
        assert verify_turnstile("token") is False

    def test_network_error_fails_closed(self, monkeypatch):
        fake_urlopen(monkeypatch, error=urllib.error.URLError("down"))
        assert verify_turnstile("token") is False


class TestFindUnsafeUrls:
    def test_returns_matches(self, monkeypatch, settings):
        settings.SAFE_BROWSING_API_KEY = "key"
        requests = fake_urlopen(monkeypatch, {"matches": [{"threat": {"url": "https://evil.example/"}}]})
        assert find_unsafe_urls(["https://evil.example/", "https://example.com/"]) == {"https://evil.example/"}
        sent = json.loads(requests[0].data)
        assert [entry["url"] for entry in sent["threatInfo"]["threatEntries"]] == [
            "https://evil.example/",
            "https://example.com/",
        ]

    def test_no_matches(self, monkeypatch, settings):
        settings.SAFE_BROWSING_API_KEY = "key"
        fake_urlopen(monkeypatch, {})
        assert find_unsafe_urls(["https://example.com/"]) == set()

    def test_network_error_raises(self, monkeypatch, settings):
        settings.SAFE_BROWSING_API_KEY = "key"
        fake_urlopen(monkeypatch, error=urllib.error.URLError("down"))
        with pytest.raises(protection.SafeBrowsingUnavailable):
            find_unsafe_urls(["https://example.com/"])

    def test_skipped_without_api_key(self, monkeypatch, settings):
        settings.SAFE_BROWSING_API_KEY = ""
        requests = fake_urlopen(monkeypatch, {})
        assert find_unsafe_urls(["https://example.com/"]) == set()
        assert requests == []
