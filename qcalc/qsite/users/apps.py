from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "qsite.users"
    verbose_name = _("Users")

    def ready(self):
        try:
            import qsite.users.signals  # noqa F401
        # except ImportError:
        #     pass
        except ImportError as e:
            print(f"ImportError in UsersConfig: {e}")
