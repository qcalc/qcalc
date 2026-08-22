# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from django.contrib.auth import get_user_model, forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from allauth.account.forms import SignupForm as AllauthSignupForm
from utils.qmixins import AntiBotSecurityMixin

User = get_user_model()


class UserChangeForm(forms.UserChangeForm):
    class Meta(forms.UserChangeForm.Meta):
        model = User


class UserCreationForm(forms.UserCreationForm):
    error_message = forms.UserCreationForm.error_messages.update(
        {"duplicate_username": _("This username has already been taken.")}
    )

    class Meta(forms.UserCreationForm.Meta):
        model = User

    def clean_username(self):
        username = self.cleaned_data["username"]

        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username

        raise ValidationError(self.error_messages["duplicate_username"])


# deb@22.08.26
class CustomSignupForm(AntiBotSecurityMixin, AllauthSignupForm):
    """
    Extends the default django-allauth signup form
    with custom dynamic bot-blocking functionality.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Explicit security field names from the Mixin
        security_fields = [
            'captcha_question',
            'captcha_answer',
            'captcha_correct_answer',
            'honeypot',
            'timestamp',
        ]

        # Explicitly pluck and push the security fields to the bottom of the form dictionary registry.
        # This completely bypasses allauth and crispy sequence caching loops.
        for field_name in security_fields:
            if field_name in self.fields:
                self.fields.move_to_end(field_name)

    # Python MRO handles the mixin mechanics completely automatically.
    def save(self, request):
        user = super().save(request)
        # Custom registration actions can be appended here
        return user
