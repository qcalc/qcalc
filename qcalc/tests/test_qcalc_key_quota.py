# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import qsett

qsett.init()

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection

from calc.quota.mod_qcalc_quota import QCalcApiQuota, ApiQuotaExceeded
from calc.quota.mod_quota import QuotaCounter
from calc.quota.mod_qcalc_key import ApiKeyError, QCalcApiKey


@pytest.fixture(scope="module", autouse=True)
def api_db():
    old_name = connection.settings_dict["NAME"]
    connection.creation.create_test_db(verbosity=0, autoclobber=True)
    yield
    connection.creation.destroy_test_db(old_name, verbosity=0)
    connection.close()  # sqlite keeps the in-memory test db open until closed with the restored name


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    from calc.models import APIKey

    APIKey.objects.all().delete()
    QuotaCounter.rows().all().delete()
    monkeypatch.setattr(QuotaCounter, "PURGE_PROBABILITY", 0)
    monkeypatch.setattr(settings, "QCALC_API_KEY_QUOTA", "", raising=False)


@pytest.fixture
def alice(db_users):
    return db_users("alice")


@pytest.fixture
def bob(db_users):
    return db_users("bob")


@pytest.fixture
def db_users():
    User = get_user_model()

    def make(name):
        user, _ = User.objects.get_or_create(username=name)
        return user

    return make


def _limits(monkeypatch, text):
    monkeypatch.setattr(settings, "QCALC_API_KEY_QUOTA", text, raising=False)


# ---------- key management ----------

def test_create_returns_raw_key_once_and_stores_only_a_hash(alice):
    record, raw = QCalcApiKey.create(alice, "laptop", max_active=5)
    assert raw.startswith(f"qck_{record.prefix}_")
    assert record.key_hash != raw and raw not in record.key_hash
    assert QCalcApiKey.authenticate(raw).pk == record.pk
    assert QCalcApiKey.authenticate(raw + "x") is None


def test_name_required_and_unique_per_user_when_limited(alice, bob):
    with pytest.raises(ApiKeyError, match="name is required"):
        QCalcApiKey.create(alice, "  ", max_active=5)
    QCalcApiKey.create(alice, "Same", max_active=5)
    with pytest.raises(ApiKeyError, match="already have a key named"):
        QCalcApiKey.create(alice, "same", max_active=5)
    QCalcApiKey.create(bob, "Same", max_active=5)  # another user may reuse the name


def test_max_active_keys_enforced_and_revoked_keys_do_not_count(alice):
    records = [QCalcApiKey.create(alice, f"k{i}", max_active=3)[0] for i in range(3)]
    with pytest.raises(ApiKeyError, match="at most 3"):
        QCalcApiKey.create(alice, "k3", max_active=3)
    QCalcApiKey.revoke(alice, records[0].prefix)
    QCalcApiKey.create(alice, "k3", max_active=3)


def test_revoked_key_stops_authenticating_and_delete_removes_it(alice):
    record, raw = QCalcApiKey.create(alice, "temp", max_active=5)
    QCalcApiKey.revoke(alice, record.prefix)
    assert QCalcApiKey.authenticate(raw) is None
    assert [k.prefix for k in QCalcApiKey.list(alice)] == [record.prefix]
    QCalcApiKey.delete(alice, record.prefix)
    assert QCalcApiKey.list(alice) == []


def test_users_cannot_revoke_or_delete_each_others_keys(alice, bob):
    record, raw = QCalcApiKey.create(alice, "mine", max_active=5)
    with pytest.raises(ApiKeyError):
        QCalcApiKey.revoke(bob, record.prefix)
    with pytest.raises(ApiKeyError):
        QCalcApiKey.delete(bob, record.prefix)
    assert QCalcApiKey.authenticate(raw) is not None


def test_inactive_user_key_is_rejected(alice):
    record, raw = QCalcApiKey.create(alice, "x", max_active=5)
    alice.is_active = False
    alice.save()
    try:
        assert QCalcApiKey.authenticate(raw) is None
    finally:
        alice.is_active = True
        alice.save()


# ---------- quota ----------

def test_limits_defaults_overrides_and_invalid_entries(monkeypatch):
    assert QCalcApiQuota.limits() == QCalcApiQuota.DEFAULT_LIMITS
    _limits(monkeypatch, " key_day = 5 , bogus=3, user_day=abc, key_month, global_day=9,, ")
    parsed = QCalcApiQuota.limits()
    assert parsed["key_day"] == 5 and parsed["global_day"] == 9
    assert parsed["user_day"] == QCalcApiQuota.DEFAULT_LIMITS["user_day"]


def test_key_day_limit_blocks_and_reports_retry_after(alice, monkeypatch):
    _limits(monkeypatch, "key_day=2,key_month=0,user_day=0")
    key, _ = QCalcApiKey.create(alice, "limited")
    QCalcApiQuota.consume(key)
    QCalcApiQuota.consume(key)
    with pytest.raises(ApiQuotaExceeded, match="This API key.*daily limit") as info:
        QCalcApiQuota.consume(key)
    assert 0 < info.value.retry_after <= 86400


def test_each_key_has_its_own_counter(alice, monkeypatch):
    _limits(monkeypatch, "key_day=1,key_month=0,user_day=0")
    first, _ = QCalcApiKey.create(alice, "a")
    second, _ = QCalcApiKey.create(alice, "b")
    QCalcApiQuota.consume(first)
    QCalcApiQuota.consume(second)
    with pytest.raises(ApiQuotaExceeded):
        QCalcApiQuota.consume(first)


def test_user_limit_is_shared_across_all_of_a_users_keys(alice, bob, monkeypatch):
    _limits(monkeypatch, "key_day=0,key_month=0,user_day=2")
    first, _ = QCalcApiKey.create(alice, "a")
    second, _ = QCalcApiKey.create(alice, "b")
    other, _ = QCalcApiKey.create(bob, "c")
    QCalcApiQuota.consume(first)
    QCalcApiQuota.consume(second)
    with pytest.raises(ApiQuotaExceeded, match="Your account"):
        QCalcApiQuota.consume(first)
    QCalcApiQuota.consume(other)  # a different user is unaffected


def test_global_and_monthly_limits(alice, bob, monkeypatch):
    _limits(monkeypatch, "key_day=0,key_month=1,user_day=0,global_day=0,global_month=0")
    key, _ = QCalcApiKey.create(alice, "m")
    QCalcApiQuota.consume(key)
    with pytest.raises(ApiQuotaExceeded, match="monthly") as info:
        QCalcApiQuota.consume(key)
    assert info.value.retry_after > 0

    _limits(monkeypatch, "key_day=0,key_month=0,user_day=0,global_day=1")
    QuotaCounter.rows().all().delete()
    other, _ = QCalcApiKey.create(bob, "g")
    QCalcApiQuota.consume(key)
    with pytest.raises(ApiQuotaExceeded, match="The API"):
        QCalcApiQuota.consume(other)


def test_rejected_run_does_not_consume_other_counters(alice, monkeypatch):
    _limits(monkeypatch, "key_day=1,key_month=100,user_day=100")
    key, _ = QCalcApiKey.create(alice, "r")
    QCalcApiQuota.consume(key)
    with pytest.raises(ApiQuotaExceeded):
        QCalcApiQuota.consume(key)
    month = QuotaCounter.rows().get(
        provider=QCalcApiQuota.PROVIDER, scope="key", subject=str(key.pk), period=QuotaCounter.period_key("month"))
    assert month.count == 1


def test_unlimited_when_all_limits_are_zero(alice, monkeypatch):
    _limits(monkeypatch, "key_day=0,key_month=0,user_day=0,global_day=0,global_month=0")
    key, _ = QCalcApiKey.create(alice, "u")
    for _ in range(5):
        QCalcApiQuota.consume(key)
    assert QuotaCounter.rows().filter(provider=QCalcApiQuota.PROVIDER).count() == 0


def test_counter_resets_on_new_day(alice, monkeypatch):
    _limits(monkeypatch, "key_day=1,key_month=0,user_day=0")
    key, _ = QCalcApiKey.create(alice, "d")
    QCalcApiQuota.consume(key)
    monkeypatch.setattr(
        QuotaCounter, "period_key", staticmethod(lambda kind, now=None: "2099-01-01" if kind == "day" else "2099-01"))
    QCalcApiQuota.consume(key)


def test_key_usage_reports_day_and_month_counts(alice, monkeypatch):
    _limits(monkeypatch, "key_day=10,key_month=100,user_day=0")
    key, _ = QCalcApiKey.create(alice, "s")
    unused, _ = QCalcApiKey.create(alice, "t")
    QCalcApiQuota.consume(key)
    QCalcApiQuota.consume(key)
    usage = QCalcApiQuota.key_usage([key.pk, unused.pk])
    assert usage[str(key.pk)] == {"day": 2, "month": 2}
    assert usage[str(unused.pk)] == {"day": 0, "month": 0}


def test_seconds_until_reset_boundaries():
    from datetime import datetime, timezone

    noon = datetime(2026, 12, 31, 12, 0, tzinfo=timezone.utc)
    assert QCalcApiQuota.seconds_until_reset("day", noon) == 12 * 3600
    assert QCalcApiQuota.seconds_until_reset("month", noon) == 12 * 3600  # month rolls into the new year


def test_purge_does_not_break_a_run(alice, monkeypatch):
    monkeypatch.setattr(QuotaCounter, "PURGE_PROBABILITY", 1)
    monkeypatch.setattr(QuotaCounter, "purge", staticmethod(lambda: 1 / 0))
    key, _ = QCalcApiKey.create(alice, "p")
    QCalcApiQuota.consume(key)
