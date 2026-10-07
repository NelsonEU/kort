import pytest
from django.core.cache import cache
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    # ScopedRateThrottle counts requests via Django's cache, which — unlike
    # the DB — isn't reset between tests.
    cache.clear()


@pytest.fixture
def api_client():
    return APIClient()
