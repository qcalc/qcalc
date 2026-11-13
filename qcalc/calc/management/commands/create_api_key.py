from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from calc.quota.mod_qcalc_key import QCalcApiKey


class Command(BaseCommand):
    help = "Create an API key for /calc/api/. The key is printed once and cannot be recovered."

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('--name', default='', help='Label for the key')

    def handle(self, *args, **options):
        user_model = get_user_model()
        try:
            user = user_model.objects.get(**{user_model.USERNAME_FIELD: options['username']})
        except user_model.DoesNotExist:
            raise CommandError(f"User '{options['username']}' not found")

        record, raw_key = QCalcApiKey.create(user, options['name'])
        self.stdout.write(self.style.SUCCESS(f'API key {record.prefix} created for {user}'))
        self.stdout.write(raw_key)
