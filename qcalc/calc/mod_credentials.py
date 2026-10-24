# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.apps import apps
from qutil import check_setting
from .mod_cred_quota import PROVIDERS, consume_system_quota, QuotaExceeded  # noqa: F401


def provider_choices():
    return {k: v['label'] for k, v in PROVIDERS.items()}


def _mycredentials():
    return apps.get_model('calc', 'MyCredential').objects


def _myprefs():
    return apps.get_model('calc', 'MyStuff').objects


def _personal_api_keys_active(user) -> bool:
    if user is None or not getattr(user, 'is_authenticated', False):
        return False
    record = _myprefs().filter(user=user, object_id='pref', item_id='personal_api_keys_active').first()
    if record is None:
        return True
    return bool(record.item)


def _fernet():
    master_key = check_setting(getattr(settings, 'SECRET_KEY', ''), "SECRET_KEY", optional=False)
    digest = hashlib.sha256(master_key.encode('utf-8')).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def _encrypt_secret(secret: str) -> dict:
    token = _fernet().encrypt(secret.encode('utf-8')).decode('utf-8')
    return {'v': 1, 'alg': 'fernet-sha256', 'ct': token}


def _decrypt_secret(payload: dict) -> str:
    if not isinstance(payload, dict):
        raise Exception('Invalid credential payload')
    token = payload.get('ct', '')
    if token == '':
        raise Exception('Invalid credential payload')
    try:
        return _fernet().decrypt(token.encode('utf-8')).decode('utf-8')
    except InvalidToken:
        raise Exception('Credential decryption failed')


def _secret_suffix4(secret: str) -> str:
    return secret[-4:] if len(secret) >= 4 else ''


def set_user_api_key(user, provider: str, api_key: str):
    if user is None or not getattr(user, 'is_authenticated', False):
        raise Exception('Please login to set API key')
    if provider not in PROVIDERS:
        raise Exception(f'Unsupported provider: {provider}')
    secret = api_key.strip()
    if secret == '':
        raise Exception('API key cannot be empty')
    _mycredentials().update_or_create(
        user=user,
        provider=provider,
        defaults={'secret': _encrypt_secret(secret), 'suffix4': _secret_suffix4(secret)},
    )


def delete_user_api_key(user, provider: str):
    if user is None or not getattr(user, 'is_authenticated', False):
        raise Exception('Please login to delete API key')
    if provider not in PROVIDERS:
        raise Exception(f'Unsupported provider: {provider}')
    _mycredentials().filter(user=user, provider=provider).delete()


def has_user_api_key(user, provider: str) -> bool:
    if provider not in PROVIDERS:
        raise Exception(f'Unsupported provider: {provider}')
    if user is None or not getattr(user, 'is_authenticated', False):
        return False
    return _mycredentials().filter(user=user, provider=provider).exists()


def get_user_api_key(user, provider: str) -> str:
    if provider not in PROVIDERS:
        raise Exception(f'Unsupported provider: {provider}')
    if user is None or not getattr(user, 'is_authenticated', False):
        return ''
    record = _mycredentials().filter(user=user, provider=provider).first()
    if record is None:
        return ''
    return _decrypt_secret(record.secret)


def get_user_api_key_suffix(user, provider: str) -> str:
    if provider not in PROVIDERS:
        raise Exception(f'Unsupported provider: {provider}')
    if user is None or not getattr(user, 'is_authenticated', False):
        return ''
    record = _mycredentials().filter(user=user, provider=provider).only('suffix4').first()
    if record is None:
        return ''
    return (record.suffix4 or '').strip()


def has_system_api_key(provider: str) -> bool:
    if provider not in PROVIDERS:
        raise Exception(f'Unsupported provider: {provider}')
    setting_name = PROVIDERS[provider]['setting']
    return check_setting(getattr(settings, setting_name, ''), setting_name, optional=True) != ''


def get_effective_api_key(user, provider: str) -> str:
    if _personal_api_keys_active(user):
        user_key = get_user_api_key(user, provider)
        if user_key != '':
            return user_key
    if provider not in PROVIDERS:
        raise Exception(f'Unsupported provider: {provider}')
    setting_name = PROVIDERS[provider]['setting']
    api_key = check_setting(getattr(settings, setting_name, ''), setting_name, optional=False)
    consume_system_quota(user, provider)
    return api_key
