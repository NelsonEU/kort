from datetime import timedelta

import pytest
from django.utils import timezone

from core.models import CODE_ALPHABET, CODE_LENGTH, Link


@pytest.mark.django_db
class TestCreateLink:
    def test_creates_link(self, api_client):
        response = api_client.post("/api/links/", {"url": "https://example.com/some/long/path"}, format="json")
        assert response.status_code == 201
        code = response.data["code"]
        assert len(code) == CODE_LENGTH
        assert set(code) <= set(CODE_ALPHABET)
        link = Link.objects.get(code=code)
        assert link.url == "https://example.com/some/long/path"

    def test_expires_in_a_year(self, api_client):
        response = api_client.post("/api/links/", {"url": "https://example.com"}, format="json")
        link = Link.objects.get(code=response.data["code"])
        assert abs(link.expires_at - (timezone.now() + timedelta(days=365))) < timedelta(minutes=1)

    @pytest.mark.parametrize(
        "url",
        ["", "not a url", "javascript:alert(1)", "ftp://example.com/file", "https://" + "a" * 2050 + ".com"],
    )
    def test_rejects_invalid_urls(self, api_client, url):
        response = api_client.post("/api/links/", {"url": url}, format="json")
        assert response.status_code == 400
        assert not Link.objects.exists()

    def test_is_throttled(self, api_client):
        for _ in range(30):
            assert api_client.post("/api/links/", {"url": "https://example.com"}, format="json").status_code == 201
        assert api_client.post("/api/links/", {"url": "https://example.com"}, format="json").status_code == 429


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
