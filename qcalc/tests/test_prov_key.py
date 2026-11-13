# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import qsett

qsett.init()

import pytest

import calc.quota.mod_prov_key as mc


class _FakeUser:
    is_authenticated = True


class _FakeManager:
    def __init__(self):
        self.calls = []

    def update_or_create(self, **kwargs):
        self.calls.append(kwargs)
        return None, True


@pytest.fixture(autouse=True)
def no_quota(monkeypatch):
    monkeypatch.setattr(mc.ProviderApiQuota, "consume", lambda *_a, **_k: None)


@pytest.fixture
def fake_user():
    return _FakeUser()


def test_effective_prefers_user_key_when_active(monkeypatch, fake_user):
    monkeypatch.setattr(mc.ProviderApiKey, "personal_active", lambda _self: True)
    monkeypatch.setattr(mc.ProviderApiKey, "get", lambda _self: "USER_KEY")
    monkeypatch.setattr(mc.settings, "OPENAI_API_KEY", "SYS_KEY", raising=False)

    assert mc.ProviderApiKey(fake_user, "openai").effective() == "USER_KEY"


def test_effective_uses_system_when_inactive(monkeypatch, fake_user):
    monkeypatch.setattr(mc.ProviderApiKey, "personal_active", lambda _self: False)
    monkeypatch.setattr(mc.ProviderApiKey, "get", lambda _self: "USER_KEY")
    monkeypatch.setattr(mc.settings, "OPENAI_API_KEY", "SYS_KEY", raising=False)

    assert mc.ProviderApiKey(fake_user, "openai").effective() == "SYS_KEY"


def test_effective_falls_back_to_system_when_user_key_missing(monkeypatch, fake_user):
    monkeypatch.setattr(mc.ProviderApiKey, "personal_active", lambda _self: True)
    monkeypatch.setattr(mc.ProviderApiKey, "get", lambda _self: "")
    monkeypatch.setattr(mc.settings, "OPENAI_API_KEY", "SYS_KEY", raising=False)

    assert mc.ProviderApiKey(fake_user, "openai").effective() == "SYS_KEY"


def test_effective_raises_when_both_user_and_system_keys_missing(monkeypatch, fake_user):
    monkeypatch.setattr(mc.ProviderApiKey, "personal_active", lambda _self: True)
    monkeypatch.setattr(mc.ProviderApiKey, "get", lambda _self: "")
    monkeypatch.setattr(mc.settings, "OPENAI_API_KEY", "", raising=False)

    with pytest.raises(Exception, match="OPENAI_API_KEY"):
        mc.ProviderApiKey(fake_user, "openai").effective()


def test_unsupported_provider_is_rejected(fake_user):
    with pytest.raises(Exception, match="Unsupported provider"):
        mc.ProviderApiKey(fake_user, "nope")


def test_set_stores_encrypted_secret_and_suffix4(monkeypatch, fake_user):
    manager = _FakeManager()
    monkeypatch.setattr(mc.ProviderApiKey, "rows", staticmethod(lambda: manager))
    monkeypatch.setattr(mc.ProviderApiKey, "encrypt", classmethod(lambda _cls, s: {"ct": f"enc:{s}"}))

    mc.ProviderApiKey(fake_user, "openai").set("  abcd1234  ")

    assert len(manager.calls) == 1
    call = manager.calls[0]
    assert call["user"] is fake_user
    assert call["provider"] == "openai"
    assert call["defaults"]["secret"] == {"ct": "enc:abcd1234"}
    assert call["defaults"]["suffix4"] == "1234"
