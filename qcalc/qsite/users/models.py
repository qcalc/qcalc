from django.contrib.auth.models import AbstractUser
from django.db.models import CharField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.contrib import admin


class User(AbstractUser):

    # First Name and Last Name do not cover name patterns
    # around the globe.
    name = CharField(_("Name of User"), blank=True, max_length=255)

    #deb@21.08.26
    class Meta(AbstractUser.Meta):
        permissions = [
            ("can_publish_calculator", "Can publish calculator"),
        ]

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})

    @property
    @admin.display(boolean=True, description="Can Publish")
    def can_publish(self):
        """Returns True if the user has permission to publish calculators, False otherwise."""
        # Django's .has_perm() automatically returns True for superusers
        # and checks custom permissions for normal users.
        return self.has_perm("users.can_publish_calculator")
