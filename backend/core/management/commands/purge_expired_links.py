from django.core.management.base import BaseCommand

from core.models import Link


class Command(BaseCommand):
    help = "Delete links whose expiry date has passed. Links with no expiry are kept."

    def handle(self, *args, **options):
        deleted, _ = Link.objects.expired().delete()
        self.stdout.write(f"Deleted {deleted} expired link(s).")
