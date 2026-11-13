# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import qsett

qsett.init()

import pytest
from django.db import connection

import calc.quota.mod_prov_key as mc
import calc.quota.mod_prov_quota as mq

Q = mq.ProviderApiQuota


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
    connection.close()  # sqlite keeps the in-memory test db open until closed with the restored name


def _set_quota(monkeypatch, text):
    monkeypatch.setattr(mq.settings, "OPENAI_API_KEY_QUOTA", text, raising=False)
    monkeypatch.setitem(mc.PROVIDERS["openai"], "quota", mc.PROVIDERS["openai"].get("quota"))  # restored on undo
    Q.load()


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    Q.rows().all().delete()
    monkeypatch.setattr(Q, "PURGE_PROBABILITY", 0)
    _set_quota(monkeypatch, "user_day=2,ip_day=3,global_day=0,global_month=0")


def test_user_limit_blocks_after_quota():
    user = _FakeUser(1)
    Q.consume(user, "openai", ip="1.1.1.1")
    Q.consume(user, "openai", ip="1.1.1.1")
    with pytest.raises(mq.QuotaExceeded, match="daily limit"):
        Q.consume(user, "openai", ip="1.1.1.1")


def test_rejected_call_does_not_consume_other_counters():
    user = _FakeUser(1)
    Q.consume(user, "openai", ip="1.1.1.1")
    Q.consume(user, "openai", ip="1.1.1.1")
    with pytest.raises(mq.QuotaExceeded):
        Q.consume(user, "openai", ip="1.1.1.1")
    assert Q.remaining(None, "openai", ip="1.1.1.1") == {"ip": 1}


def test_ip_limit_applies_to_anonymous_and_across_users():
    Q.consume(None, "openai", ip="2.2.2.2")
    Q.consume(_FakeUser(1), "openai", ip="2.2.2.2")
    Q.consume(_FakeUser(2), "openai", ip="2.2.2.2")
    with pytest.raises(mq.QuotaExceeded):
        Q.consume(None, "openai", ip="2.2.2.2")


def test_users_and_providers_are_counted_independently():
    Q.consume(_FakeUser(1), "openai", ip="3.3.3.3")
    Q.consume(_FakeUser(1), "openai", ip="3.3.3.3")
    Q.consume(_FakeUser(2), "openai", ip="4.4.4.4")
    Q.consume(_FakeUser(1), "openweather", ip="3.3.3.3")


def test_global_monthly_limit(monkeypatch):
    _set_quota(monkeypatch, "user_day=0,ip_day=0,global_day=0,global_month=1")
    Q.consume(_FakeUser(1), "openai", ip="5.5.5.5")
    with pytest.raises(mq.QuotaExceeded, match="shared openai key"):
        Q.consume(_FakeUser(2), "openai", ip="6.6.6.6")


def test_global_daily_limit_and_rollback(monkeypatch):
    _set_quota(monkeypatch, "user_day=0,ip_day=0,global_month=5,global_day=1")
    Q.consume(_FakeUser(1), "openai", ip="5.5.5.5")
    with pytest.raises(mq.QuotaExceeded, match="daily limit"):
        Q.consume(_FakeUser(2), "openai", ip="6.6.6.6")
    monthly = Q.rows().get(provider="openai", scope="global", period=Q.period_key("month"))
    assert monthly.count == 1  # rejected call did not consume the monthly counter


def test_counter_resets_on_new_day(monkeypatch):
    user = _FakeUser(1)
    Q.consume(user, "openai", ip="7.7.7.7")
    Q.consume(user, "openai", ip="7.7.7.7")
    monkeypatch.setattr(Q, "period_key", staticmethod(lambda kind, now=None: "2099-01-01" if kind == "day" else "2099-01"))
    Q.consume(user, "openai", ip="7.7.7.7")


def test_unlimited_when_no_limits(monkeypatch):
    _set_quota(monkeypatch, "user_day=0,ip_day=0,global_day=0,global_month=0")
    for _ in range(5):
        Q.consume(_FakeUser(1), "openai", ip="8.8.8.8")
    assert Q.rows().count() == 0


def test_parse_limits_ignores_invalid_entries():
    parsed = Q.parse_limits(" user_day = 5 , bogus=3, ip_day=abc, global_day, global_month=10,, ", "X_QUOTA")
    assert parsed == {"user_day": 5, "global_month": 10}


def test_env_quota_overrides_only_named_keys_and_defaults_remain(monkeypatch):
    _set_quota(monkeypatch, "user_day=7")
    limits = Q.limits("openai")
    defaults = mc.PROVIDERS["openai"]["quota_default"]
    assert limits["user_day"] == 7
    assert limits["ip_day"] == defaults["ip_day"]


def test_empty_env_quota_uses_code_defaults(monkeypatch):
    _set_quota(monkeypatch, "")
    assert Q.limits("openai") == mc.PROVIDERS["openai"]["quota_default"]


def test_reload_does_not_keep_stale_overrides(monkeypatch):
    _set_quota(monkeypatch, "user_day=7")
    _set_quota(monkeypatch, "ip_day=9")
    limits = Q.limits("openai")
    assert limits["ip_day"] == 9
    assert limits["user_day"] == mc.PROVIDERS["openai"]["quota_default"]["user_day"]


def test_purge_old_usage():
    Q.rows().create(provider="openai", scope="ip", subject="9.9.9.9", period="2000-01-01", count=1)
    Q.consume(None, "openai", ip="9.9.9.9")
    assert Q.purge() == 1


def test_ipv6_is_counted_by_64_prefix_and_ipv4_mapped_as_ipv4():
    assert Q.normalize_ip("2001:db8:1:2:aaaa:bbbb:cccc:dddd") == "2001:db8:1:2::/64"
    assert Q.normalize_ip("2001:db8:1:2:1::9") == "2001:db8:1:2::/64"
    assert Q.normalize_ip("::ffff:1.2.3.4") == "1.2.3.4"
    assert Q.normalize_ip("1.2.3.4") == "1.2.3.4"
    assert Q.normalize_ip("not-an-ip") == "not-an-ip"
    for last in ("1", "2", "3"):  # same /64, different addresses share one IP quota
        Q.consume(None, "openai", ip=f"2001:db8:1:2::{last}")
    with pytest.raises(mq.QuotaExceeded):
        Q.consume(None, "openai", ip="2001:db8:1:2::ffff")
    Q.consume(None, "openai", ip="2001:db8:1:3::1")  # different /64


def test_missing_ip_logs_warning_and_skips_ip_limit(caplog):
    with caplog.at_level("WARNING", logger=mq.logger.name):
        Q.consume(_FakeUser(1), "openai", ip="")
    assert "ip_day limit" in caplog.text


def test_purge_failure_does_not_break_the_call(monkeypatch):
    monkeypatch.setattr(Q, "PURGE_PROBABILITY", 1)
    monkeypatch.setattr(Q, "purge", staticmethod(lambda: 1 / 0))
    Q.consume(_FakeUser(1), "openai", ip="1.1.1.1")
    assert Q.remaining(_FakeUser(1), "openai", ip="1.1.1.1")["user"] == 1


def test_user_ip_prefers_configured_header_over_forwarded_for(monkeypatch):
    class Req:
        META = {"HTTP_X_REAL_IP": "10.0.0.5", "HTTP_X_FORWARDED_FOR": "6.6.6.6", "REMOTE_ADDR": "127.0.0.1"}

    monkeypatch.setattr(mq.settings, "CLIENT_IP_HEADER", "HTTP_X_REAL_IP", raising=False)
    assert mq.user_ip(Req) == "10.0.0.5"
    monkeypatch.setattr(mq.settings, "CLIENT_IP_HEADER", "", raising=False)
    assert mq.user_ip(Req) == "127.0.0.1"


def test_effective_consumes_quota_only_for_system_key(monkeypatch):
    calls = []
    monkeypatch.setattr(mc.ProviderApiQuota, "consume", lambda user, provider: calls.append(provider))
    monkeypatch.setattr(mc.ProviderApiKey, "personal_active", lambda _self: True)
    monkeypatch.setattr(mc.settings, "OPENAI_API_KEY", "SYS", raising=False)

    monkeypatch.setattr(mc.ProviderApiKey, "get", lambda _self: "USER")
    assert mc.ProviderApiKey(_FakeUser(1), "openai").effective() == "USER"
    assert calls == []

    monkeypatch.setattr(mc.ProviderApiKey, "get", lambda _self: "")
    assert mc.ProviderApiKey(_FakeUser(1), "openai").effective() == "SYS"
    assert calls == ["openai"]
