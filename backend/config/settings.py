import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Only present in the production image (backend/Dockerfile.prod copies the
# built frontend here) — absent in dev, where Vite's own dev server handles
# the frontend and Django never receives HTML-page requests directly.
FRONTEND_DIST = BASE_DIR / "frontend_dist"

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-secret-key")
DEBUG = os.environ.get("DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = [h for h in os.environ.get("ALLOWED_HOSTS", "*").split(",") if h]

CSRF_TRUSTED_ORIGINS = [
    o for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "http://localhost:5173").split(",") if o
]

# Cloudflare's always-pass test secret in dev, paired with the frontend's test site key.
TURNSTILE_SECRET_KEY = os.environ.get("TURNSTILE_SECRET_KEY") or (
    "1x0000000000000000000000000000000AA" if DEBUG else ""
)
# Empty in dev skips the check (Google has no test key).
SAFE_BROWSING_API_KEY = os.environ.get("SAFE_BROWSING_API_KEY", "")

# The dev-friendly defaults above (insecure secret key, wildcard host) are
# fine for local Docker Compose, but would be a real hole if the production
# .env ever forgot to set them. Fail loudly instead of running insecurely.
if not DEBUG:
    from django.core.exceptions import ImproperlyConfigured

    if SECRET_KEY == "dev-only-insecure-secret-key":
        raise ImproperlyConfigured("SECRET_KEY must be set explicitly when DEBUG=False")
    if ALLOWED_HOSTS == ["*"]:
        raise ImproperlyConfigured("ALLOWED_HOSTS must be set explicitly when DEBUG=False")
    if not TURNSTILE_SECRET_KEY:
        raise ImproperlyConfigured("TURNSTILE_SECRET_KEY must be set when DEBUG=False")
    if not SAFE_BROWSING_API_KEY:
        raise ImproperlyConfigured("SAFE_BROWSING_API_KEY must be set when DEBUG=False")

    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # W008: Cloudflare redirects HTTP to HTTPS; redirecting here too would loop
    # if the forwarded-proto header were ever missing. W005/W021: HSTS
    # subdomains/preload are decisions for arn0.be as a whole, not this app.
    SILENCED_SYSTEM_CHECKS = ["security.W008", "security.W005", "security.W021"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [FRONTEND_DIST],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": dj_database_url.config(
        default="sqlite:///" + str(BASE_DIR / "db.sqlite3"),
        conn_max_age=600,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr"
TIME_ZONE = "Europe/Zurich"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/assets/"
# Matches Vite's default build output, which already references /assets/...
# from the site root. Only present in production, hence the existence check
# (see FRONTEND_DIST above).
STATICFILES_DIRS = [FRONTEND_DIST / "assets"] if (FRONTEND_DIST / "assets").is_dir() else []
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
# Serves Vite's public/ files (copied verbatim into frontend_dist/) at the
# site root, as middleware, before the SPA catch-all in urls.py can swallow
# them and return index.html instead.
if FRONTEND_DIST.is_dir():
    WHITENOISE_ROOT = FRONTEND_DIST

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.ScopedRateThrottle"],
    # Anonymous link creation is an open door for spam/phishing; this keeps
    # any one visitor from mass-producing links.
    "DEFAULT_THROTTLE_RATES": {"link-create": "30/hour"},
    # Behind the Cloudflare Tunnel every request reaches Django from the same
    # local address, which would make the throttle above global. Cloudflare
    # appends the real client IP to X-Forwarded-For; trust that one hop.
    "NUM_PROXIES": 1,
}
