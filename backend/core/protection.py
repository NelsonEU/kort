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


def lookup_variants(url):
    # Safe Browsing only matches path prefixes ending in "/", so ".../malware"
    # misses a ".../malware/" entry, which servers typically redirect to.
    parts = urllib.parse.urlsplit(url)
    if parts.path.endswith("/"):
        return {url}
    return {url, urllib.parse.urlunsplit(parts._replace(path=parts.path + "/"))}


def find_unsafe_urls(urls):
    """Returns the subset of `urls` flagged by Google Safe Browsing."""
    if not settings.SAFE_BROWSING_API_KEY:
        return set()
    originals = {}
    for url in urls:
        for variant in lookup_variants(url):
            originals.setdefault(variant, set()).add(url)
    variants = list(originals)
    unsafe = set()
    for start in range(0, len(variants), SAFE_BROWSING_BATCH_SIZE):
        for match in _lookup(variants[start:start + SAFE_BROWSING_BATCH_SIZE]):
            unsafe |= originals.get(match, set())
    return unsafe


def _lookup(urls):
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
