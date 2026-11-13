# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""Usage quotas for system-owned API keys (database backed).

Limits come from ``PROVIDERS[provider]['quota']`` and can be overridden per key with a setting/env variable named
after the API key setting plus ``_QUOTA``, e.g. ``OPENAI_API_KEY_QUOTA="user_day=20,ip_day=50,global_month=2500"``.
Supported limit keys: ``user_day``, ``ip_day``, ``global_day`` and ``global_month``. A missing or ``0`` limit
means unlimited. Invalid entries are ignored with a warning.
"""

from datetime import datetime
import ipaddress
import logging

from django.conf import settings
from django.utils import timezone
from qutil import user_ip
from .mod_quota import QuotaCounter

logger = logging.getLogger(__name__)

PROVIDERS = {
    # quota_default: limits for the shared system key only (0/None = unlimited); a user's own key is never counted.
    # 'quota' (effective limits = defaults + <KEY_SETTING>_QUOTA env overrides) is filled by ProviderApiQuota.load()
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


class QuotaExceeded(Exception):
    def __init__(self, provider: str, scope: str, limit: int, period_kind: str):
        self.provider = provider
        self.scope = scope
        self.limit = limit
        self.period_kind = period_kind
        period = QuotaCounter.PERIOD_LABEL[period_kind]
        if scope == 'global':
            message = (f'The shared {provider} key has reached its {period} limit. '
                       'Please try again later or add your own API key in Preferences.')
        else:
            message = (f'You have reached the {period} limit ({limit}) of the shared '
                       f'{provider} key. Please try again tomorrow (UTC) or add your own API key in Preferences.')
        super().__init__(message)


class ProviderApiQuota(QuotaCounter):
    RULES = QUOTA_RULES
    _loaded = False

    @classmethod
    def load(cls) -> None:
        """Merge the ``<KEY_SETTING>_QUOTA`` overrides into ``PROVIDERS[p]['quota']``; safe to call repeatedly."""
        for provider, info in PROVIDERS.items():
            name = f"{info['setting']}_QUOTA"
            info['quota'] = {**info['quota_default'], **cls.parse_limits(getattr(settings, name, ''), name)}
            logger.info('*** %s quota: %s', provider, info['quota'])
        cls._loaded = True

    @classmethod
    def limits(cls, provider: str) -> dict:
        if not cls._loaded:
            cls.load()
        return PROVIDERS.get(provider, {}).get('quota') or {}

    @staticmethod
    def normalize_ip(ip: str) -> str:
        """IPv6 clients are counted by /64 prefix (one subscriber controls a whole /64); IPv4-mapped IPv6 as IPv4."""
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            return ip[:64]
        if addr.version == 6:
            return str(addr.ipv4_mapped) if addr.ipv4_mapped else str(ipaddress.ip_network(f'{addr}/64', strict=False))
        return str(addr)

    @classmethod
    def subjects(cls, user, ip: str) -> dict:
        subjects = {'global': ''}
        if ip:
            subjects['ip'] = cls.normalize_ip(ip)
        if user is not None and getattr(user, 'is_authenticated', False):
            subjects['user'] = str(user.pk)
        return subjects

    @classmethod
    def exceeded(cls, provider: str, scope: str, limit: int, kind: str, now: datetime) -> QuotaExceeded:
        return QuotaExceeded(provider, scope, limit, kind)

    @classmethod
    def consume(cls, user, provider: str, ip: str | None = None) -> None:
        """Count one use of the system key; raise QuotaExceeded if any applicable limit is already reached."""
        limits = cls.limits(provider)
        subjects = cls.subjects(user, user_ip() if ip is None else ip)
        if 'ip' not in subjects and limits.get('ip_day'):
            logger.warning('No client IP available: ip_day limit of the %s key is not applied', provider)
        cls._consume(provider, limits, subjects)

    @classmethod
    def remaining(cls, user, provider: str, ip: str | None = None) -> dict:
        """Remaining uses per applicable scope, e.g. {'user': 12, 'ip': 30}; unlimited scopes are omitted."""
        limits = cls.limits(provider)
        subjects = cls.subjects(user, user_ip() if ip is None else ip)
        now = timezone.now()
        return {
            scope: max(int(limits[limit_key]) - cls.used(provider, scope, subjects[scope], kind, now), 0)
            for limit_key, scope, kind in cls.RULES if limits.get(limit_key) and scope in subjects
        }
