from django.core.management.base import BaseCommand

from calc import update_currency


class Command(BaseCommand):
    help = "Update currency rates"

    def handle(self, *args, **options):
        update_msg = update_currency()
        self.stdout.write(self.style.SUCCESS(update_msg))
