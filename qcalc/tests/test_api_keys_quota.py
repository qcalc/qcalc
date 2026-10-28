import qsett

qsett.init()

import pytest
from django.contrib.auth import get_user_model
from django.db import connection

import calc.mod_api_quota as aq
import calc.mod_cred_quota as cq
from calc.mod_api_keys import (
    ApiKeyError, authenticate_api_key, create_api_key, delete_api_key, list_api_keys, revoke_api_key,
)


@pytest.fixture(scope="module", autouse=True)
def api_db():
    old_name = connection.settings_dict["NAME"]
    connection.creation.create_test_db(verbosity=0, autoclobber=True)
    yield
    connection.creation.destroy_test_db(old_name, verbosity=0)


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    from calc.models import APIKey

    APIKey.objects.all().delete()
    cq._usage().all().delete()
    monkeypatch.setattr(aq, "_PURGE_PROBABILITY", 0)
    monkeypatch.setattr(aq.settings, "QCALC_API_KEY_QUOTA", "", raising=False)


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
    monkeypatch.setattr(aq.settings, "QCALC_API_KEY_QUOTA", text, raising=False)


# ---------- key management ----------

def test_create_returns_raw_key_once_and_stores_only_a_hash(alice):
    record, raw = create_api_key(alice, "laptop", max_active=5)
    assert raw.startswith(f"qck_{record.prefix}_")
    assert record.key_hash != raw and raw not in record.key_hash
    assert authenticate_api_key(raw).pk == record.pk
    assert authenticate_api_key(raw + "x") is None


def test_name_required_and_unique_per_user_when_limited(alice, bob):
    with pytest.raises(ApiKeyError, match="name is required"):
        create_api_key(alice, "  ", max_active=5)
    create_api_key(alice, "Same", max_active=5)
    with pytest.raises(ApiKeyError, match="already have a key named"):
        create_api_key(alice, "same", max_active=5)
    create_api_key(bob, "Same", max_active=5)  # another user may reuse the name


def test_max_active_keys_enforced_and_revoked_keys_do_not_count(alice):
    records = [create_api_key(alice, f"k{i}", max_active=3)[0] for i in range(3)]
    with pytest.raises(ApiKeyError, match="at most 3"):
        create_api_key(alice, "k3", max_active=3)
    revoke_api_key(alice, records[0].prefix)
    create_api_key(alice, "k3", max_active=3)


def test_revoked_key_stops_authenticating_and_delete_removes_it(alice):
    record, raw = create_api_key(alice, "temp", max_active=5)
    revoke_api_key(alice, record.prefix)
    assert authenticate_api_key(raw) is None
    assert [k.prefix for k in list_api_keys(alice)] == [record.prefix]
    delete_api_key(alice, record.prefix)
    assert list_api_keys(alice) == []


def test_users_cannot_revoke_or_delete_each_others_keys(alice, bob):
    record, raw = create_api_key(alice, "mine", max_active=5)
    with pytest.raises(ApiKeyError):
        revoke_api_key(bob, record.prefix)
    with pytest.raises(ApiKeyError):
        delete_api_key(bob, record.prefix)
    assert authenticate_api_key(raw) is not None


def test_inactive_user_key_is_rejected(alice):
    record, raw = create_api_key(alice, "x", max_active=5)
    alice.is_active = False
    alice.save()
    try:
        assert authenticate_api_key(raw) is None
    finally:
        alice.is_active = True
        alice.save()


# ---------- quota ----------

def test_parse_limits_defaults_overrides_and_invalid_entries():
    assert aq._parse_limits("") == aq.DEFAULT_LIMITS
    parsed = aq._parse_limits(" key_day = 5 , bogus=3, user_day=abc, key_month, global_day=9,, ")
    assert parsed["key_day"] == 5 and parsed["global_day"] == 9
    assert parsed["user_day"] == aq.DEFAULT_LIMITS["user_day"]


def test_key_day_limit_blocks_and_reports_retry_after(alice, monkeypatch):
    _limits(monkeypatch, "key_day=2,key_month=0,user_day=0")
    key, _ = create_api_key(alice, "limited")
    aq.consume_api_quota(key)
    aq.consume_api_quota(key)
    with pytest.raises(aq.ApiQuotaExceeded, match="This API key.*daily limit") as info:
        aq.consume_api_quota(key)
    assert 0 < info.value.retry_after <= 86400


def test_each_key_has_its_own_counter(alice, monkeypatch):
    _limits(monkeypatch, "key_day=1,key_month=0,user_day=0")
    first, _ = create_api_key(alice, "a")
    second, _ = create_api_key(alice, "b")
    aq.consume_api_quota(first)
    aq.consume_api_quota(second)
    with pytest.raises(aq.ApiQuotaExceeded):
        aq.consume_api_quota(first)


def test_user_limit_is_shared_across_all_of_a_users_keys(alice, bob, monkeypatch):
    _limits(monkeypatch, "key_day=0,key_month=0,user_day=2")
    first, _ = create_api_key(alice, "a")
    second, _ = create_api_key(alice, "b")
    other, _ = create_api_key(bob, "c")
    aq.consume_api_quota(first)
    aq.consume_api_quota(second)
    with pytest.raises(aq.ApiQuotaExceeded, match="Your account"):
        aq.consume_api_quota(first)
    aq.consume_api_quota(other)  # a different user is unaffected


def test_global_and_monthly_limits(alice, bob, monkeypatch):
    _limits(monkeypatch, "key_day=0,key_month=1,user_day=0,global_day=0,global_month=0")
    key, _ = create_api_key(alice, "m")
    aq.consume_api_quota(key)
    with pytest.raises(aq.ApiQuotaExceeded, match="monthly") as info:
        aq.consume_api_quota(key)
    assert info.value.retry_after > 0

    _limits(monkeypatch, "key_day=0,key_month=0,user_day=0,global_day=1")
    cq._usage().all().delete()
    other, _ = create_api_key(bob, "g")
    aq.consume_api_quota(key)
    with pytest.raises(aq.ApiQuotaExceeded, match="The API"):
        aq.consume_api_quota(other)


def test_rejected_run_does_not_consume_other_counters(alice, monkeypatch):
    _limits(monkeypatch, "key_day=1,key_month=100,user_day=100")
    key, _ = create_api_key(alice, "r")
    aq.consume_api_quota(key)
    with pytest.raises(aq.ApiQuotaExceeded):
        aq.consume_api_quota(key)
    month = cq._usage().get(provider=aq.PROVIDER, scope="key", subject=str(key.pk), period=cq._period_key("month"))
    assert month.count == 1


def test_unlimited_when_all_limits_are_zero(alice, monkeypatch):
    _limits(monkeypatch, "key_day=0,key_month=0,user_day=0,global_day=0,global_month=0")
    key, _ = create_api_key(alice, "u")
    for _ in range(5):
        aq.consume_api_quota(key)
    assert cq._usage().filter(provider=aq.PROVIDER).count() == 0


def test_counter_resets_on_new_day(alice, monkeypatch):
    _limits(monkeypatch, "key_day=1,key_month=0,user_day=0")
    key, _ = create_api_key(alice, "d")
    aq.consume_api_quota(key)
    monkeypatch.setattr(aq, "_period_key", lambda kind, now=None: "2099-01-01" if kind == "day" else "2099-01")
    aq.consume_api_quota(key)


def test_key_usage_reports_day_and_month_counts(alice, monkeypatch):
    _limits(monkeypatch, "key_day=10,key_month=100,user_day=0")
    key, _ = create_api_key(alice, "s")
    unused, _ = create_api_key(alice, "t")
    aq.consume_api_quota(key)
    aq.consume_api_quota(key)
    usage = aq.key_usage([key.pk, unused.pk])
    assert usage[str(key.pk)] == {"day": 2, "month": 2}
    assert usage[str(unused.pk)] == {"day": 0, "month": 0}


def test_seconds_until_reset_boundaries():
    from datetime import datetime, timezone

    noon = datetime(2026, 12, 31, 12, 0, tzinfo=timezone.utc)
    assert aq._seconds_until_reset("day", noon) == 12 * 3600
    assert aq._seconds_until_reset("month", noon) == 12 * 3600  # month rolls into the new year


def test_purge_does_not_break_a_run(alice, monkeypatch):
    monkeypatch.setattr(aq, "_PURGE_PROBABILITY", 1)
    monkeypatch.setattr(aq, "purge_old_usage", lambda: 1 / 0)
    key, _ = create_api_key(alice, "p")
    aq.consume_api_quota(key)
