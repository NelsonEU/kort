import secrets
from datetime import timedelta

from django.db import models
from django.utils import timezone

# No 0/O, 1/l/I: short links get read aloud and retyped by hand.
CODE_ALPHABET = "23456789abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"
CODE_LENGTH = 6
LINK_LIFETIME = timedelta(days=365)


def generate_code():
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


def default_expires_at():
    return timezone.now() + LINK_LIFETIME


class LinkQuerySet(models.QuerySet):
    def active(self):
        return self.filter(models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now()))

    def expired(self):
        return self.filter(expires_at__lte=timezone.now())


class Link(models.Model):
    code = models.CharField(max_length=CODE_LENGTH, unique=True)
    url = models.URLField(max_length=2048)
    created_at = models.DateTimeField(auto_now_add=True)
    # Null means the link never expires (set by hand, e.g. in the Django admin).
    expires_at = models.DateTimeField(default=default_expires_at, null=True, blank=True)

    objects = LinkQuerySet.as_manager()

    def __str__(self):
        return f"{self.code} → {self.url}"

    @classmethod
    def create_with_unique_code(cls, url):
        while True:
            code = generate_code()
            if not cls.objects.filter(code=code).exists():
                return cls.objects.create(code=code, url=url)
