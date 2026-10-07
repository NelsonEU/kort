from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from core import protection
from core.models import Link


class Command(BaseCommand):
    help = "Re-check active links against Google Safe Browsing and disable the flagged ones."

    def handle(self, *args, **options):
        if not settings.SAFE_BROWSING_API_KEY:
            raise CommandError("SAFE_BROWSING_API_KEY is not set.")

        urls = list(Link.objects.active().values_list("url", flat=True).distinct())
        unsafe = protection.find_unsafe_urls(urls)
        disabled = Link.objects.active().filter(url__in=unsafe).update(disabled_at=timezone.now())
        self.stdout.write(f"Checked {len(urls)} URL(s), disabled {disabled} link(s).")
