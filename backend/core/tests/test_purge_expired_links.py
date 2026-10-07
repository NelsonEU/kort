from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

from core.models import Link


@pytest.mark.django_db
def test_purges_only_expired_links():
    now = timezone.now()
    Link.objects.create(code="old234", url="https://example.com/old", expires_at=now - timedelta(seconds=1))
    Link.objects.create(code="new234", url="https://example.com/new", expires_at=now + timedelta(days=1))
    Link.objects.create(code="per234", url="https://example.com/forever", expires_at=None)

    out = StringIO()
    call_command("purge_expired_links", stdout=out)

    assert set(Link.objects.values_list("code", flat=True)) == {"new234", "per234"}
    assert "Deleted 1 expired link(s)." in out.getvalue()
