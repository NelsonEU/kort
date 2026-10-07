from types import SimpleNamespace

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from core import protection


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    # ScopedRateThrottle counts requests via Django's cache, which — unlike
    # the DB — isn't reset between tests.
    cache.clear()


@pytest.fixture(autouse=True)
def network_checks(monkeypatch):
    """Stands in for Turnstile and Safe Browsing so tests never hit the network."""
    state = SimpleNamespace(turnstile_ok=True, unsafe=set(), safe_browsing_down=False)

    def find_unsafe_urls(urls):
        if state.safe_browsing_down:
            raise protection.SafeBrowsingUnavailable
        return set(urls) & state.unsafe

    monkeypatch.setattr(protection, "verify_turnstile", lambda token: state.turnstile_ok)
    monkeypatch.setattr(protection, "find_unsafe_urls", find_unsafe_urls)
    return state


@pytest.fixture
def api_client():
    return APIClient()
