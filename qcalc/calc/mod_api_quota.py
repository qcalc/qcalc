# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""Rate limits for /calc/api/ run calls (database backed, shares the SystemKeyUsage counters).

Limits come from ``DEFAULT_LIMITS`` and can be overridden with the ``QCALC_API_KEY_QUOTA`` setting/env variable, e.g.
``QCALC_API_KEY_QUOTA="key_day=500,key_month=10000,user_day=1000,global_day=20000"``. A ``0`` limit means unlimited.
``key_*`` counts one API key, ``user_day`` counts all keys of the owner together, ``global_*`` counts every key.
"""

from datetime import datetime, timedelta, timezone as dt_timezone
from functools import lru_cache
import logging
import random

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from qutil import css2dict
from .mod_cred_quota import _ensure_row, _period_key, _usage, purge_old_usage

logger = logging.getLogger(__name__)

PROVIDER = 'qcalc'
DEFAULT_LIMITS = {'key_day': 500, 'key_month': 10000, 'user_day': 1000, 'global_day': 0, 'global_month': 0}
RULES = (  # (limit key, scope, period kind); fixed order keeps row locking consistent
    ('global_month', 'global', 'month'),
    ('global_day', 'global', 'day'),
    ('user_day', 'user', 'day'),
    ('key_month', 'key', 'month'),
    ('key_day', 'key', 'day'),
)
_PURGE_PROBABILITY = 0.01
_PERIOD_LABEL = {'day': 'daily', 'month': 'monthly'}
_SCOPE_LABEL = {'global': 'The API', 'user': 'Your account', 'key': 'This API key'}


class ApiQuotaExceeded(Exception):
    def __init__(self, scope: str, limit: int, period_kind: str, retry_after: int):
        self.scope = scope
        self.limit = limit
        self.period_kind = period_kind
        self.retry_after = retry_after
        super().__init__(
            f'{_SCOPE_LABEL[scope]} has reached its {_PERIOD_LABEL[period_kind]} limit ({limit} runs). '
            f'Try again in {max(1, retry_after // 60)} min (limits reset at 00:00 UTC).'
        )


@lru_cache(maxsize=8)
def _parse_limits(text: str) -> dict:
    limits = dict(DEFAULT_LIMITS)
    for key, value in css2dict(text).items():
        if key not in DEFAULT_LIMITS or not value.isdigit():
            logger.warning('Ignoring invalid entry %r in QCALC_API_KEY_QUOTA', f'{key}={value}')
            continue
        limits[key] = int(value)
    return limits


def api_limits() -> dict:
    return _parse_limits(getattr(settings, 'QCALC_API_KEY_QUOTA', '') or '')


def _seconds_until_reset(kind: str, now: datetime) -> int:
    now = now.astimezone(dt_timezone.utc)
    if kind == 'day':
        end = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        end = (now.replace(day=1) + timedelta(days=32)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return int((end - now).total_seconds())


def _subjects(api_key) -> dict:
    return {'global': '', 'user': str(api_key.user_id), 'key': str(api_key.pk)}


def consume_api_quota(api_key) -> None:
    """Count one run for ``api_key``; raise ApiQuotaExceeded if any limit is already reached.

    All counters are incremented in one transaction, so a rejected call does not consume any quota."""
    if random.random() < _PURGE_PROBABILITY:
        try:
            purge_old_usage()
        except Exception:
            logger.exception('Purging old API usage failed')

    limits = api_limits()
    subjects = _subjects(api_key)
    now = timezone.now()
    checks = [
        (scope, subjects[scope], _period_key(kind, now), int(limits[limit_key]), kind)
        for limit_key, scope, kind in RULES if limits.get(limit_key)
    ]
    if not checks:
        return
    for scope, subject, period, _limit, _kind in checks:
        _ensure_row(PROVIDER, scope, subject, period)
    with transaction.atomic():
        for scope, subject, period, limit, kind in checks:
            allowed = _usage().filter(
                provider=PROVIDER, scope=scope, subject=subject, period=period, count__lt=limit
            ).update(count=F('count') + 1)
            if not allowed:
                raise ApiQuotaExceeded(scope, limit, kind, _seconds_until_reset(kind, now))  # rolls back


def key_usage(api_key_ids) -> dict:
    """``{key_id: {'day': runs today, 'month': runs this month}}`` (UTC) for the given key ids."""
    now = timezone.now()
    ids = [str(pk) for pk in api_key_ids]
    usage = {pk: {'day': 0, 'month': 0} for pk in ids}
    periods = {_period_key('day', now): 'day', _period_key('month', now): 'month'}
    rows = _usage().filter(provider=PROVIDER, scope='key', subject__in=ids, period__in=list(periods))
    for row in rows:
        usage[row.subject][periods[row.period]] = row.count
    return usage
