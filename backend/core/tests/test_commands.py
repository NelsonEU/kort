from io import StringIO

import pytest
from django.core.management import CommandError, call_command
from django.utils import timezone

from core.models import Link


def run(command, *args):
    out = StringIO()
    call_command(command, *args, stdout=out)
    return out.getvalue()


@pytest.mark.django_db
class TestDisableLink:
    def test_disables_link(self):
        Link.objects.create(code="bad234", url="https://example.com")
        assert "Disabled bad234." in run("disable_link", "bad234")
        assert Link.objects.get(code="bad234").disabled_at is not None

    def test_unknown_code_fails(self):
        with pytest.raises(CommandError):
            run("disable_link", "nope99")


@pytest.mark.django_db
class TestCheckLinks:
    def test_disables_flagged_links(self, settings, network_checks):
        settings.SAFE_BROWSING_API_KEY = "key"
        network_checks.unsafe = {"https://evil.example/"}
        Link.objects.create(code="bad234", url="https://evil.example/")
        Link.objects.create(code="ok2345", url="https://example.com/")

        assert "Checked 2 URL(s), disabled 1 link(s)." in run("check_links")
        assert Link.objects.get(code="bad234").disabled_at is not None
        assert Link.objects.get(code="ok2345").disabled_at is None

    def test_requires_api_key(self, settings):
        settings.SAFE_BROWSING_API_KEY = ""
        with pytest.raises(CommandError):
            run("check_links")

    def test_skips_already_disabled_links(self, settings, network_checks):
        settings.SAFE_BROWSING_API_KEY = "key"
        network_checks.unsafe = {"https://evil.example/"}
        Link.objects.create(code="bad234", url="https://evil.example/", disabled_at=timezone.now())
        assert "Checked 0 URL(s), disabled 0 link(s)." in run("check_links")
