# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""Database backed usage counters (``SystemKeyUsage`` rows) shared by the system key and the API key quotas.

A subclass sets ``RULES`` and supplies the limits and subjects of a call. ``_consume`` then counts one use
against every applicable rule in one transaction and raises the error built by ``exceeded``.
"""

from datetime import datetime, timedelta, timezone as dt_timezone
from functools import lru_cache
import logging
import random

from django.apps import apps
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone
from qcore import css2dict

logger = logging.getLogger(__name__)


class QuotaCounter:
    RULES = ()  # (limit key, scope, period kind); fixed order keeps row locking consistent
    PERIOD_LABEL = {'day': 'daily', 'month': 'monthly'}
    PURGE_KEEP_DAYS = 62
    PURGE_PROBABILITY = 0.01

    @staticmethod
    def rows():
        return apps.get_model('calc', 'SystemKeyUsage').objects

    @staticmethod
    def period_key(kind: str, now: datetime | None = None) -> str:
        now = (now or timezone.now()).astimezone(dt_timezone.utc)
        return now.strftime('%Y-%m-%d' if kind == 'day' else '%Y-%m')

    @classmethod
    @lru_cache(maxsize=8)
    def parse_limits(cls, text: str, name: str) -> dict:
        """The valid ``key=number`` entries of ``text``; invalid entries are ignored with a warning."""
        valid_keys = {rule[0] for rule in cls.RULES}
        limits = {}
        for key, value in css2dict(text).items():
            if key not in valid_keys or not value.isdigit():
                logger.warning('Ignoring invalid entry %r in %s', f'{key}={value}', name)
                continue
            limits[key] = int(value)
        return limits

    @classmethod
    def ensure_row(cls, provider: str, scope: str, subject: str, period: str):
        try:
            with transaction.atomic():
                cls.rows().get_or_create(provider=provider, scope=scope, subject=subject, period=period)
        except IntegrityError:
            pass  # created concurrently by another worker

    @classmethod
    def purge(cls, keep_days: int | None = None) -> int:
        days = cls.PURGE_KEEP_DAYS if keep_days is None else keep_days
        cutoff = cls.period_key('day', timezone.now() - timedelta(days=days))
        deleted, _ = cls.rows().filter(period__lt=cutoff).delete()
        return deleted

    @classmethod
    def used(cls, provider: str, scope: str, subject: str, kind: str, now: datetime) -> int:
        row = cls.rows().filter(
            provider=provider, scope=scope, subject=subject, period=cls.period_key(kind, now)
        ).first()
        return row.count if row else 0

    @classmethod
    def exceeded(cls, provider: str, scope: str, limit: int, kind: str, now: datetime) -> Exception:
        raise NotImplementedError

    @classmethod
    def _consume(cls, provider: str, limits: dict, subjects: dict) -> None:
        """Count one use; raise ``exceeded(...)`` if any applicable limit is already reached.

        A rule applies when its limit is not 0 and its scope has a subject. All counters are incremented
        in one transaction, so a rejected call does not consume any quota."""
        if random.random() < cls.PURGE_PROBABILITY:
            try:
                cls.purge()
            except Exception:
                logger.exception('Purging old quota usage failed')
        now = timezone.now()
        checks = [
            (scope, subjects[scope], cls.period_key(kind, now), int(limits[limit_key]), kind)
            for limit_key, scope, kind in cls.RULES if limits.get(limit_key) and scope in subjects
        ]
        if not checks:
            return
        for scope, subject, period, _limit, _kind in checks:
            cls.ensure_row(provider, scope, subject, period)
        with transaction.atomic():
            for scope, subject, period, limit, kind in checks:
                allowed = cls.rows().filter(
                    provider=provider, scope=scope, subject=subject, period=period, count__lt=limit
                ).update(count=F('count') + 1)
                if not allowed:
                    raise cls.exceeded(provider, scope, limit, kind, now)  # rolls back the increments made above
