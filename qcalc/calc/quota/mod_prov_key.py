# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.apps import apps
from qutil import check_setting
from .mod_prov_quota import PROVIDERS, ProviderApiQuota


class ProviderApiKey:
    """A user's own API key for one provider of ``PROVIDERS`` (stored encrypted), with the shared system key
    as fallback. ``user`` may be None or anonymous: such a user has no stored key."""

    def __init__(self, user, provider: str):
        if provider not in PROVIDERS:
            raise Exception(f'Unsupported provider: {provider}')
        self.user = user
        self.provider = provider

    @staticmethod
    def choices():
        return {k: v['label'] for k, v in PROVIDERS.items()}

    @staticmethod
    def rows():
        return apps.get_model('calc', 'MyCredential').objects

    @staticmethod
    def _fernet():
        master_key = check_setting(getattr(settings, 'SECRET_KEY', ''), "SECRET_KEY", optional=False)
        digest = hashlib.sha256(master_key.encode('utf-8')).digest()
        return Fernet(base64.urlsafe_b64encode(digest))

    @classmethod
    def encrypt(cls, secret: str) -> dict:
        token = cls._fernet().encrypt(secret.encode('utf-8')).decode('utf-8')
        return {'v': 1, 'alg': 'fernet-sha256', 'ct': token}

    @classmethod
    def decrypt(cls, payload: dict) -> str:
        if not isinstance(payload, dict):
            raise Exception('Invalid credential payload')
        token = payload.get('ct', '')
        if token == '':
            raise Exception('Invalid credential payload')
        try:
            return cls._fernet().decrypt(token.encode('utf-8')).decode('utf-8')
        except InvalidToken:
            raise Exception('Credential decryption failed')

    @property
    def logged_in(self) -> bool:
        return self.user is not None and getattr(self.user, 'is_authenticated', False)

    def personal_active(self) -> bool:
        """Whether the user lets personal keys be used (the default); the user's preference can switch it off."""
        if not self.logged_in:
            return False
        record = apps.get_model('calc', 'MyStuff').objects.filter(
            user=self.user, object_id='pref', item_id='personal_api_keys_active').first()
        return True if record is None else bool(record.item)

    def set(self, api_key: str):
        if not self.logged_in:
            raise Exception('Please login to set API key')
        secret = api_key.strip()
        if secret == '':
            raise Exception('API key cannot be empty')
        self.rows().update_or_create(
            user=self.user,
            provider=self.provider,
            defaults={'secret': self.encrypt(secret), 'suffix4': secret[-4:] if len(secret) >= 4 else ''},
        )

    def delete(self):
        if not self.logged_in:
            raise Exception('Please login to delete API key')
        self.rows().filter(user=self.user, provider=self.provider).delete()

    def has(self) -> bool:
        return self.logged_in and self.rows().filter(user=self.user, provider=self.provider).exists()

    def get(self) -> str:
        if not self.logged_in:
            return ''
        record = self.rows().filter(user=self.user, provider=self.provider).first()
        return '' if record is None else self.decrypt(record.secret)

    def suffix(self) -> str:
        """The last 4 characters of the stored key, to recognise it without showing it."""
        if not self.logged_in:
            return ''
        record = self.rows().filter(user=self.user, provider=self.provider).only('suffix4').first()
        return '' if record is None else (record.suffix4 or '').strip()

    def has_system(self) -> bool:
        name = PROVIDERS[self.provider]['setting']
        return check_setting(getattr(settings, name, ''), name, optional=True) != ''

    def effective(self) -> str:
        """The user's own key if personal keys are active and one is stored, else the system key (counted
        against the system quota)."""
        if self.personal_active():
            user_key = self.get()
            if user_key != '':
                return user_key
        name = PROVIDERS[self.provider]['setting']
        api_key = check_setting(getattr(settings, name, ''), name, optional=False)
        ProviderApiQuota.consume(self.user, self.provider)
        return api_key
