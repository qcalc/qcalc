from django.core.management.base import BaseCommand

from calc import update_currency, redis_publish_action


class Command(BaseCommand):
    help = "Update currency rates"

    def handle(self, *args, **options):
        update_msg = update_currency(update_now=True)
        redis_publish_action(
            channel="qcalc_channel",
            action="update_currency",
            update_now=False  # update_now False=already downloaded, upload only
        )
        self.stdout.write(self.style.SUCCESS(update_msg))
