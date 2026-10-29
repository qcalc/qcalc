# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import qsett

qsett.init()

import pytest
from django.db import connection

import calc.mod_credentials as mc
import calc.mod_cred_quota as mq


class _FakeUser:
    is_authenticated = True

    def __init__(self, pk):
        self.pk = pk


@pytest.fixture(scope="module", autouse=True)
def quota_db():
    old_name = connection.settings_dict["NAME"]
    connection.creation.create_test_db(verbosity=0, autoclobber=True)
    yield
    connection.creation.destroy_test_db(old_name, verbosity=0)


def _set_quota(monkeypatch, text):
    monkeypatch.setattr(mq.settings, "OPENAI_API_KEY_QUOTA", text, raising=False)
    monkeypatch.setitem(mc.PROVIDERS["openai"], "quota", mc.PROVIDERS["openai"].get("quota"))  # restored on undo
    mq.load_provider_quotas()


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    mq._usage().all().delete()
    monkeypatch.setattr(mq, "_PURGE_PROBABILITY", 0)
    _set_quota(monkeypatch, "user_day=2,ip_day=3,global_day=0,global_month=0")


def test_user_limit_blocks_after_quota():
    user = _FakeUser(1)
    mq.consume_system_quota(user, "openai", ip="1.1.1.1")
    mq.consume_system_quota(user, "openai", ip="1.1.1.1")
    with pytest.raises(mq.QuotaExceeded, match="daily limit"):
        mq.consume_system_quota(user, "openai", ip="1.1.1.1")


def test_rejected_call_does_not_consume_other_counters():
    user = _FakeUser(1)
    mq.consume_system_quota(user, "openai", ip="1.1.1.1")
    mq.consume_system_quota(user, "openai", ip="1.1.1.1")
    with pytest.raises(mq.QuotaExceeded):
        mq.consume_system_quota(user, "openai", ip="1.1.1.1")
    assert mq.system_quota_remaining(None, "openai", ip="1.1.1.1") == {"ip": 1}


def test_ip_limit_applies_to_anonymous_and_across_users():
    mq.consume_system_quota(None, "openai", ip="2.2.2.2")
    mq.consume_system_quota(_FakeUser(1), "openai", ip="2.2.2.2")
    mq.consume_system_quota(_FakeUser(2), "openai", ip="2.2.2.2")
    with pytest.raises(mq.QuotaExceeded):
        mq.consume_system_quota(None, "openai", ip="2.2.2.2")


def test_users_and_providers_are_counted_independently():
    mq.consume_system_quota(_FakeUser(1), "openai", ip="3.3.3.3")
    mq.consume_system_quota(_FakeUser(1), "openai", ip="3.3.3.3")
    mq.consume_system_quota(_FakeUser(2), "openai", ip="4.4.4.4")
    mq.consume_system_quota(_FakeUser(1), "openweather", ip="3.3.3.3")


def test_global_monthly_limit(monkeypatch):
    _set_quota(monkeypatch, "user_day=0,ip_day=0,global_day=0,global_month=1")
    mq.consume_system_quota(_FakeUser(1), "openai", ip="5.5.5.5")
    with pytest.raises(mq.QuotaExceeded, match="shared openai key"):
        mq.consume_system_quota(_FakeUser(2), "openai", ip="6.6.6.6")


def test_global_daily_limit_and_rollback(monkeypatch):
    _set_quota(monkeypatch, "user_day=0,ip_day=0,global_month=5,global_day=1")
    mq.consume_system_quota(_FakeUser(1), "openai", ip="5.5.5.5")
    with pytest.raises(mq.QuotaExceeded, match="daily limit"):
        mq.consume_system_quota(_FakeUser(2), "openai", ip="6.6.6.6")
    monthly = mq._usage().get(provider="openai", scope="global", period=mq._period_key("month"))
    assert monthly.count == 1  # rejected call did not consume the monthly counter


def test_counter_resets_on_new_day(monkeypatch):
    user = _FakeUser(1)
    mq.consume_system_quota(user, "openai", ip="7.7.7.7")
    mq.consume_system_quota(user, "openai", ip="7.7.7.7")
    monkeypatch.setattr(mq, "_period_key", lambda kind, now=None: "2099-01-01" if kind == "day" else "2099-01")
    mq.consume_system_quota(user, "openai", ip="7.7.7.7")


def test_unlimited_when_no_limits(monkeypatch):
    _set_quota(monkeypatch, "user_day=0,ip_day=0,global_day=0,global_month=0")
    for _ in range(5):
        mq.consume_system_quota(_FakeUser(1), "openai", ip="8.8.8.8")
    assert mq._usage().count() == 0


def test_parse_quota_ignores_invalid_entries():
    parsed = mq._parse_quota(" user_day = 5 , bogus=3, ip_day=abc, global_day, global_month=10,, ", "X_QUOTA")
    assert parsed == {"user_day": 5, "global_month": 10}


def test_env_quota_overrides_only_named_keys_and_defaults_remain(monkeypatch):
    _set_quota(monkeypatch, "user_day=7")
    limits = mq._provider_limits("openai")
    defaults = mc.PROVIDERS["openai"]["quota_default"]
    assert limits["user_day"] == 7
    assert limits["ip_day"] == defaults["ip_day"]


def test_empty_env_quota_uses_code_defaults(monkeypatch):
    _set_quota(monkeypatch, "")
    assert mq._provider_limits("openai") == mc.PROVIDERS["openai"]["quota_default"]


def test_reload_does_not_keep_stale_overrides(monkeypatch):
    _set_quota(monkeypatch, "user_day=7")
    _set_quota(monkeypatch, "ip_day=9")
    limits = mq._provider_limits("openai")
    assert limits["ip_day"] == 9
    assert limits["user_day"] == mc.PROVIDERS["openai"]["quota_default"]["user_day"]


def test_purge_old_usage():
    mq._usage().create(provider="openai", scope="ip", subject="9.9.9.9", period="2000-01-01", count=1)
    mq.consume_system_quota(None, "openai", ip="9.9.9.9")
    assert mq.purge_old_usage() == 1


def test_ipv6_is_counted_by_64_prefix_and_ipv4_mapped_as_ipv4():
    assert mq._normalize_ip("2001:db8:1:2:aaaa:bbbb:cccc:dddd") == "2001:db8:1:2::/64"
    assert mq._normalize_ip("2001:db8:1:2:1::9") == "2001:db8:1:2::/64"
    assert mq._normalize_ip("::ffff:1.2.3.4") == "1.2.3.4"
    assert mq._normalize_ip("1.2.3.4") == "1.2.3.4"
    assert mq._normalize_ip("not-an-ip") == "not-an-ip"
    for last in ("1", "2", "3"):  # same /64, different addresses share one IP quota
        mq.consume_system_quota(None, "openai", ip=f"2001:db8:1:2::{last}")
    with pytest.raises(mq.QuotaExceeded):
        mq.consume_system_quota(None, "openai", ip="2001:db8:1:2::ffff")
    mq.consume_system_quota(None, "openai", ip="2001:db8:1:3::1")  # different /64


def test_missing_ip_logs_warning_and_skips_ip_limit(caplog):
    with caplog.at_level("WARNING", logger=mq.logger.name):
        mq.consume_system_quota(_FakeUser(1), "openai", ip="")
    assert "ip_day limit" in caplog.text


def test_purge_failure_does_not_break_the_call(monkeypatch):
    monkeypatch.setattr(mq, "_PURGE_PROBABILITY", 1)
    monkeypatch.setattr(mq, "purge_old_usage", lambda: 1 / 0)
    mq.consume_system_quota(_FakeUser(1), "openai", ip="1.1.1.1")
    assert mq.system_quota_remaining(_FakeUser(1), "openai", ip="1.1.1.1")["user"] == 1


def test_user_ip_prefers_configured_header_over_forwarded_for(monkeypatch):
    class Req:
        META = {"HTTP_X_REAL_IP": "10.0.0.5", "HTTP_X_FORWARDED_FOR": "6.6.6.6", "REMOTE_ADDR": "127.0.0.1"}

    monkeypatch.setattr(mq.settings, "CLIENT_IP_HEADER", "HTTP_X_REAL_IP", raising=False)
    assert mq.user_ip(Req) == "10.0.0.5"
    monkeypatch.setattr(mq.settings, "CLIENT_IP_HEADER", "", raising=False)
    assert mq.user_ip(Req) == "127.0.0.1"


def test_get_effective_api_key_consumes_quota_only_for_system_key(monkeypatch):
    calls = []
    monkeypatch.setattr(mc, "consume_system_quota", lambda user, provider: calls.append(provider))
    monkeypatch.setattr(mc, "_personal_api_keys_active", lambda _u: True)
    monkeypatch.setattr(mc.settings, "OPENAI_API_KEY", "SYS", raising=False)

    monkeypatch.setattr(mc, "get_user_api_key", lambda _u, _p: "USER")
    assert mc.get_effective_api_key(_FakeUser(1), "openai") == "USER"
    assert calls == []

    monkeypatch.setattr(mc, "get_user_api_key", lambda _u, _p: "")
    assert mc.get_effective_api_key(_FakeUser(1), "openai") == "SYS"
    assert calls == ["openai"]
