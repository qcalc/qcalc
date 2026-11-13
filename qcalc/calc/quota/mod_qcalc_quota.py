# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""Rate limits for /calc/api/ run calls (database backed, shares the SystemKeyUsage counters).

Limits come from ``DEFAULT_LIMITS`` and can be overridden with the ``QCALC_API_KEY_QUOTA`` setting/env variable, e.g.
``QCALC_API_KEY_QUOTA="key_day=500,key_month=10000,user_day=1000,global_day=20000"``. A ``0`` limit means unlimited.
``key_*`` counts one API key, ``user_day`` counts all keys of the owner together, ``global_*`` counts every key.
"""

from datetime import datetime, timedelta, timezone as dt_timezone

from django.conf import settings
from django.utils import timezone
from .mod_quota import QuotaCounter

_SCOPE_LABEL = {'global': 'The API', 'user': 'Your account', 'key': 'This API key'}


class ApiQuotaExceeded(Exception):
    def __init__(self, scope: str, limit: int, period_kind: str, retry_after: int):
        self.scope = scope
        self.limit = limit
        self.period_kind = period_kind
        self.retry_after = retry_after
        super().__init__(
            f'{_SCOPE_LABEL[scope]} has reached its {QuotaCounter.PERIOD_LABEL[period_kind]} limit ({limit} runs). '
            f'Try again in {max(1, retry_after // 60)} min (limits reset at 00:00 UTC).'
        )


class QCalcApiQuota(QuotaCounter):
    PROVIDER = 'qcalc'
    DEFAULT_LIMITS = {'key_day': 500, 'key_month': 10000, 'user_day': 1000, 'global_day': 0, 'global_month': 0}
    RULES = (
        ('global_month', 'global', 'month'),
        ('global_day', 'global', 'day'),
        ('user_day', 'user', 'day'),
        ('key_month', 'key', 'month'),
        ('key_day', 'key', 'day'),
    )

    @classmethod
    def limits(cls) -> dict:
        name = 'QCALC_API_KEY_QUOTA'
        return {**cls.DEFAULT_LIMITS, **cls.parse_limits(getattr(settings, name, '') or '', name)}

    @staticmethod
    def seconds_until_reset(kind: str, now: datetime) -> int:
        now = now.astimezone(dt_timezone.utc)
        if kind == 'day':
            end = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            end = (now.replace(day=1) + timedelta(days=32)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return int((end - now).total_seconds())

    @staticmethod
    def subjects(api_key) -> dict:
        return {'global': '', 'user': str(api_key.user_id), 'key': str(api_key.pk)}

    @classmethod
    def exceeded(cls, provider: str, scope: str, limit: int, kind: str, now: datetime) -> ApiQuotaExceeded:
        return ApiQuotaExceeded(scope, limit, kind, cls.seconds_until_reset(kind, now))

    @classmethod
    def consume(cls, api_key) -> None:
        """Count one run for ``api_key``; raise ApiQuotaExceeded if any limit is already reached."""
        cls._consume(cls.PROVIDER, cls.limits(), cls.subjects(api_key))

    @classmethod
    def key_usage(cls, api_key_ids) -> dict:
        """``{key_id: {'day': runs today, 'month': runs this month}}`` (UTC) for the given key ids."""
        now = timezone.now()
        ids = [str(pk) for pk in api_key_ids]
        usage = {pk: {'day': 0, 'month': 0} for pk in ids}
        periods = {cls.period_key('day', now): 'day', cls.period_key('month', now): 'month'}
        rows = cls.rows().filter(provider=cls.PROVIDER, scope='key', subject__in=ids, period__in=list(periods))
        for row in rows:
            usage[row.subject][periods[row.period]] = row.count
        return usage
