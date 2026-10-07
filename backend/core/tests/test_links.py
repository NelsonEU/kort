from datetime import timedelta

import pytest
from django.utils import timezone

from core.models import CODE_ALPHABET, CODE_LENGTH, Link


def create(api_client, url="https://example.com/some/long/path", expires_in="1y", **extra):
    payload = {"url": url, "expires_in": expires_in, "turnstile_token": "token", **extra}
    return api_client.post("/api/links/", payload, format="json")


@pytest.mark.django_db
class TestCreateLink:
    def test_creates_link(self, api_client):
        response = create(api_client)
        assert response.status_code == 201
        code = response.data["code"]
        assert len(code) == CODE_LENGTH
        assert set(code) <= set(CODE_ALPHABET)
        assert Link.objects.get(code=code).url == "https://example.com/some/long/path"

    @pytest.mark.parametrize(
        "expires_in, lifetime",
        [("1d", timedelta(days=1)), ("1w", timedelta(weeks=1)), ("1m", timedelta(days=30)), ("1y", timedelta(days=365))],
    )
    def test_sets_chosen_expiry(self, api_client, expires_in, lifetime):
        response = create(api_client, expires_in=expires_in)
        link = Link.objects.get(code=response.data["code"])
        assert abs(link.expires_at - (timezone.now() + lifetime)) < timedelta(minutes=1)

    @pytest.mark.parametrize("expires_in", [None, "", "2y", "forever"])
    def test_requires_a_valid_expiry(self, api_client, expires_in):
        payload = {"url": "https://example.com", "turnstile_token": "token"}
        if expires_in is not None:
            payload["expires_in"] = expires_in
        assert api_client.post("/api/links/", payload, format="json").status_code == 400
        assert not Link.objects.exists()

    @pytest.mark.parametrize(
        "url",
        ["", "not a url", "javascript:alert(1)", "ftp://example.com/file", "https://" + "a" * 2050 + ".com"],
    )
    def test_rejects_invalid_urls(self, api_client, url):
        assert create(api_client, url=url).status_code == 400
        assert not Link.objects.exists()

    @pytest.mark.parametrize(
        "url",
        [
            "https://bit.ly/abc",
            "https://www.tinyurl.com/abc",
            "http://192.168.1.1/admin",
            "http://[::1]/",
        ],
    )
    def test_rejects_blocked_domains(self, api_client, url):
        response = create(api_client, url=url)
        assert response.status_code == 400
        assert response.data == {"error": "blocked_domain"}

    def test_rejects_own_domain(self, api_client):
        payload = {"url": "https://kort.arn0.be/abc234", "expires_in": "1y", "turnstile_token": "token"}
        response = api_client.post("/api/links/", payload, format="json", HTTP_HOST="kort.arn0.be")
        assert response.status_code == 400
        assert response.data == {"error": "blocked_domain"}

    def test_requires_turnstile_token(self, api_client):
        payload = {"url": "https://example.com", "expires_in": "1y"}
        assert api_client.post("/api/links/", payload, format="json").status_code == 400

    def test_rejects_failed_turnstile(self, api_client, network_checks):
        network_checks.turnstile_ok = False
        response = create(api_client)
        assert response.status_code == 400
        assert response.data == {"error": "captcha_failed"}
        assert not Link.objects.exists()

    def test_rejects_unsafe_urls(self, api_client, network_checks):
        network_checks.unsafe = {"https://evil.example/login"}
        response = create(api_client, url="https://evil.example/login")
        assert response.status_code == 400
        assert response.data == {"error": "unsafe_url"}
        assert not Link.objects.exists()

    def test_fails_closed_when_safe_browsing_is_down(self, api_client, network_checks):
        network_checks.safe_browsing_down = True
        response = create(api_client)
        assert response.status_code == 503
        assert response.data == {"error": "safety_check_unavailable"}
        assert not Link.objects.exists()

    def test_is_throttled(self, api_client):
        for _ in range(30):
            assert create(api_client).status_code == 201
        assert create(api_client).status_code == 429


@pytest.mark.django_db
class TestFollowLink:
    def test_redirects(self, client):
        Link.objects.create(code="abc234", url="https://example.com/target")
        response = client.get("/abc234")
        assert response.status_code == 302
        assert response["Location"] == "https://example.com/target"

    def test_unknown_code_is_404(self, client):
        assert client.get("/nope99").status_code == 404

    def test_expired_link_is_404(self, client):
        Link.objects.create(code="old234", url="https://example.com", expires_at=timezone.now() - timedelta(seconds=1))
        assert client.get("/old234").status_code == 404

    def test_disabled_link_is_404(self, client):
        Link.objects.create(code="bad234", url="https://example.com", disabled_at=timezone.now())
        assert client.get("/bad234").status_code == 404

    def test_permanent_link_redirects(self, client):
        Link.objects.create(code="per234", url="https://example.com/forever", expires_at=None)
        response = client.get("/per234")
        assert response.status_code == 302
        assert response["Location"] == "https://example.com/forever"

    def test_unknown_code_serves_spa_when_built(self, client, settings, tmp_path):
        (tmp_path / "index.html").write_text("<div id=root></div>")
        settings.FRONTEND_DIST = tmp_path
        settings.TEMPLATES = [{**settings.TEMPLATES[0], "DIRS": [tmp_path]}]
        response = client.get("/nope99")
        assert response.status_code == 404
        assert b"<div id=root></div>" in response.content
