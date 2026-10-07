import ipaddress
import json
import urllib.parse
import urllib.request

from django.conf import settings

TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
SAFE_BROWSING_URL = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
SAFE_BROWSING_BATCH_SIZE = 500

SHORTENER_DOMAINS = {
    "adf.ly", "bit.do", "bit.ly", "bitly.com", "buff.ly", "cutt.ly", "goo.gl", "is.gd", "lnkd.in", "ow.ly",
    "rb.gy", "rebrand.ly", "s.id", "shorte.st", "shorturl.at", "t.co", "t.ly", "tiny.cc", "tinyurl.com", "v.gd",
}


class SafeBrowsingUnavailable(Exception):
    pass


def is_blocked_host(host, own_host):
    host = host.lower().rstrip(".")
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        pass
    blocked = SHORTENER_DOMAINS | {own_host.lower().split(":")[0]}
    return any(host == domain or host.endswith("." + domain) for domain in blocked)


def verify_turnstile(token):
    data = urllib.parse.urlencode({"secret": settings.TURNSTILE_SECRET_KEY, "response": token}).encode()
    try:
        with urllib.request.urlopen(TURNSTILE_VERIFY_URL, data=data, timeout=5) as response:
            return json.load(response).get("success") is True
    except (OSError, ValueError):
        return False


def find_unsafe_urls(urls):
    """Returns the subset of `urls` (at most SAFE_BROWSING_BATCH_SIZE) flagged by Google Safe Browsing."""
    if not settings.SAFE_BROWSING_API_KEY:
        return set()
    body = {
        "client": {"clientId": "kort", "clientVersion": "1.0"},
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url} for url in urls],
        },
    }
    request = urllib.request.Request(
        f"{SAFE_BROWSING_URL}?key={settings.SAFE_BROWSING_API_KEY}",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            matches = json.load(response).get("matches", [])
    except (OSError, ValueError) as error:
        raise SafeBrowsingUnavailable from error
    return {match["threat"]["url"] for match in matches}
