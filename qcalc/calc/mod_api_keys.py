# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""Bearer API keys for /calc/api/. Only a SHA-256 of the key is stored, so a lost key must be replaced."""

import hashlib
import hmac
import secrets
from datetime import timedelta

from django.utils import timezone

KEY_TAG = 'qck'
_PREFIX_LEN = 8
_LAST_USED_REFRESH = timedelta(minutes=5)


class ApiKeyError(ValueError):
    pass


def _hash_key(raw_key: str) -> str:
    # | keys are 192-bit random values, so an unsalted fast hash is sufficient
    return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()


def create_api_key(user, name='', max_active=None):
    """Create a key for ``user`` and return ``(APIKey, raw_key)``. The raw key cannot be recovered later.

    With ``max_active`` set, ``ApiKeyError`` is raised when the user already has that many active keys or already
    has a key with the same name."""
    from .models import APIKey

    name = (name or '').strip()[:60]
    if max_active is not None:
        if not name:
            raise ApiKeyError('A key name is required')
        mine = APIKey.objects.filter(user=user)
        if mine.filter(name__iexact=name).exists():
            raise ApiKeyError(f"You already have a key named '{name}'")
        if mine.filter(is_active=True).count() >= max_active:
            raise ApiKeyError(f'You can have at most {max_active} active API keys. Revoke or delete one first.')

    prefix = secrets.token_hex(_PREFIX_LEN // 2)
    raw_key = f'{KEY_TAG}_{prefix}_{secrets.token_urlsafe(24)}'
    record = APIKey.objects.create(user=user, name=name, prefix=prefix, key_hash=_hash_key(raw_key))
    return record, raw_key


def list_api_keys(user):
    from .models import APIKey

    return list(APIKey.objects.filter(user=user).order_by('added_on'))


def _owned_key(user, prefix):
    from .models import APIKey

    record = APIKey.objects.filter(user=user, prefix=(prefix or '').strip()).first()
    if record is None:
        raise ApiKeyError(f"No API key with prefix '{prefix}'")
    return record


def revoke_api_key(user, prefix):
    record = _owned_key(user, prefix)
    record.is_active = False
    record.save(update_fields=['is_active'])
    return record


def delete_api_key(user, prefix):
    record = _owned_key(user, prefix)
    record.delete()
    return record


def authenticate_api_key(raw_key: str):
    """Return the active ``APIKey`` for a raw key, or None."""
    from .models import APIKey

    parts = (raw_key or '').split('_', 2)
    if len(parts) != 3 or parts[0] != KEY_TAG:
        return None

    record = APIKey.objects.select_related('user').filter(prefix=parts[1], is_active=True).first()
    if record is None or not record.user.is_active:
        return None
    if not hmac.compare_digest(record.key_hash, _hash_key(raw_key)):
        return None

    now = timezone.now()
    if record.last_used_on is None or now - record.last_used_on > _LAST_USED_REFRESH:
        record.last_used_on = now
        record.save(update_fields=['last_used_on'])
    return record
