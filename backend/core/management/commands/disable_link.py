from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from core.models import Link


class Command(BaseCommand):
    help = "Disable a short link (e.g. reported abuse) so it stops redirecting."

    def add_arguments(self, parser):
        parser.add_argument("code")

    def handle(self, *args, code, **options):
        updated = Link.objects.filter(code=code, disabled_at__isnull=True).update(disabled_at=timezone.now())
        if not updated:
            raise CommandError(f"No enabled link with code {code}.")
        self.stdout.write(f"Disabled {code}.")
