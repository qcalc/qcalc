# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""Usage quotas for system-owned API keys (database backed).

Limits come from ``PROVIDERS[provider]['quota']`` and can be overridden per key with a setting/env variable named
after the API key setting plus ``_QUOTA``, e.g. ``OPENAI_API_KEY_QUOTA="user_day=20,ip_day=50,global_month=2500"``.
Supported limit keys: ``user_day``, ``ip_day``, ``global_day`` and ``global_month``. A missing or ``0`` limit
means unlimited. Invalid entries are ignored with a warning.
"""

from datetime import datetime, timedelta, timezone as dt_timezone
import ipaddress
import random

from django.apps import apps
from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone
from qutil import user_ip, css2dict
import logging

logger = logging.getLogger(__name__)

PROVIDERS = {
    # quota_default: limits for the shared system key only (0/None = unlimited); a user's own key is never counted.
    # 'quota' (effective limits = defaults + <KEY_SETTING>_QUOTA env overrides) is filled by load_provider_quotas()
    'openai': {'label': 'OpenAI', 'setting': 'OPENAI_API_KEY',
               'quota_default': {'user_day': 20, 'ip_day': 40, 'global_day': 250, 'global_month': 2500}},
    'openweather': {'label': 'OpenWeather', 'setting': 'OPENW_API_KEY',
                    'quota_default': {'user_day': 10, 'ip_day': 20, 'global_day': 100, 'global_month': 1000}},
}

QUOTA_RULES = (  # (limit key, scope, period kind); fixed order keeps row locking consistent
    ('global_month', 'global', 'month'),
    ('global_day', 'global', 'day'),
    ('ip_day', 'ip', 'day'),
    ('user_day', 'user', 'day'),
)
_PERIOD_LABEL = {'day': 'daily', 'month': 'monthly'}
_PURGE_KEEP_DAYS = 62
_PURGE_PROBABILITY = 0.01
_loaded = False


class QuotaExceeded(Exception):
    def __init__(self, provider: str, scope: str, limit: int, period_kind: str):
        self.provider = provider
        self.scope = scope
        self.limit = limit
        self.period_kind = period_kind
        if scope == 'global':
            message = (f'The shared {provider} key has reached its {_PERIOD_LABEL[period_kind]} limit. '
                       'Please try again later or add your own API key in Preferences.')
        else:
            message = (f'You have reached the {_PERIOD_LABEL[period_kind]} limit ({limit}) of the shared '
                       f'{provider} key. Please try again tomorrow (UTC) or add your own API key in Preferences.')
        super().__init__(message)


def _usage():
    return apps.get_model('calc', 'SystemKeyUsage').objects


def _parse_quota(text: str, name: str) -> dict:
    limits = {}
    valid_keys = {rule[0] for rule in QUOTA_RULES}
    for key, value in css2dict(text).items():
        if key not in valid_keys or not value.isdigit():
            logger.warning('Ignoring invalid entry %r in %s', f'{key}={value}', name)
            continue
        limits[key] = int(value)
    return limits


def load_provider_quotas() -> None:
    """Merge the ``<KEY_SETTING>_QUOTA`` overrides into ``PROVIDERS[p]['quota']``; safe to call repeatedly."""
    global _loaded
    for provider, info in PROVIDERS.items():
        name = f"{info['setting']}_QUOTA"
        info['quota'] = {**info['quota_default'], **_parse_quota(getattr(settings, name, ''), name)}
        logger.info('*** %s quota: %s', provider, info['quota'])
    _loaded = True


def _provider_limits(provider: str) -> dict:
    if not _loaded:
        load_provider_quotas()
    return PROVIDERS.get(provider, {}).get('quota') or {}


def _period_key(kind: str, now: datetime | None = None) -> str:
    now = (now or timezone.now()).astimezone(dt_timezone.utc)
    return now.strftime('%Y-%m-%d' if kind == 'day' else '%Y-%m')


def _normalize_ip(ip: str) -> str:
    """IPv6 clients are counted by /64 prefix (one subscriber controls a whole /64); IPv4-mapped IPv6 as IPv4."""
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return ip[:64]
    if addr.version == 6:
        return str(addr.ipv4_mapped) if addr.ipv4_mapped else str(ipaddress.ip_network(f'{addr}/64', strict=False))
    return str(addr)


def _subjects(user, ip: str) -> dict:
    subjects = {'global': ''}
    if ip:
        subjects['ip'] = _normalize_ip(ip)
    if user is not None and getattr(user, 'is_authenticated', False):
        subjects['user'] = str(user.pk)
    return subjects


def _ensure_row(provider: str, scope: str, subject: str, period: str):
    try:
        with transaction.atomic():
            _usage().get_or_create(provider=provider, scope=scope, subject=subject, period=period)
    except IntegrityError:
        pass  # created concurrently by another worker


def consume_system_quota(user, provider: str, ip: str | None = None) -> None:
    """Count one use of the system key; raise QuotaExceeded if any applicable limit is already reached.

    All counters are incremented in one transaction, so a rejected call does not consume any quota."""
    if random.random() < _PURGE_PROBABILITY:
        try:
            purge_old_usage()
        except Exception:
            logger.exception('Purging old system key usage failed')
    limits = _provider_limits(provider)
    subjects = _subjects(user, user_ip() if ip is None else ip)
    if 'ip' not in subjects and limits.get('ip_day'):
        logger.warning('No client IP available: ip_day limit of the %s key is not applied', provider)
    now = timezone.now()
    checks = []
    for limit_key, scope, kind in QUOTA_RULES:
        limit = limits.get(limit_key)
        if limit and scope in subjects:
            checks.append((scope, subjects[scope], _period_key(kind, now), int(limit), kind))
    if not checks:
        return
    for scope, subject, period, _limit, _kind in checks:
        _ensure_row(provider, scope, subject, period)
    with transaction.atomic():
        for scope, subject, period, limit, kind in checks:
            allowed = _usage().filter(
                provider=provider, scope=scope, subject=subject, period=period, count__lt=limit
            ).update(count=F('count') + 1)
            if not allowed:
                raise QuotaExceeded(provider, scope, limit, kind)  # rolls back increments made above


def system_quota_remaining(user, provider: str, ip: str | None = None) -> dict:
    """Remaining uses per applicable scope, e.g. {'user': 12, 'ip': 30}; unlimited scopes are omitted."""
    limits = _provider_limits(provider)
    subjects = _subjects(user, user_ip() if ip is None else ip)
    now = timezone.now()
    remaining = {}
    for limit_key, scope, kind in QUOTA_RULES:
        limit = limits.get(limit_key)
        if not limit or scope not in subjects:
            continue
        row = _usage().filter(
            provider=provider, scope=scope, subject=subjects[scope], period=_period_key(kind, now)
        ).first()
        remaining[scope] = max(int(limit) - (row.count if row else 0), 0)
    return remaining


def purge_old_usage(keep_days: int = _PURGE_KEEP_DAYS) -> int:
    cutoff = _period_key('day', timezone.now() - timedelta(days=keep_days))
    deleted, _ = _usage().filter(period__lt=cutoff).delete()
    return deleted
