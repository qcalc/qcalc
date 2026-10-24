import qsett

qsett.init()

import pytest

import calc.mod_credentials as mc


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
    monkeypatch.setattr(mc, "consume_system_quota", lambda *_a, **_k: None)


@pytest.fixture
def fake_user():
    return _FakeUser()


def test_get_effective_api_key_prefers_user_key_when_active(monkeypatch, fake_user):
    monkeypatch.setattr(mc, "_personal_api_keys_active", lambda _u: True)
    monkeypatch.setattr(mc, "get_user_api_key", lambda _u, _p: "USER_KEY")
    monkeypatch.setattr(mc.settings, "OPENAI_API_KEY", "SYS_KEY", raising=False)

    assert mc.get_effective_api_key(fake_user, "openai") == "USER_KEY"


def test_get_effective_api_key_uses_system_when_inactive(monkeypatch, fake_user):
    monkeypatch.setattr(mc, "_personal_api_keys_active", lambda _u: False)
    monkeypatch.setattr(mc, "get_user_api_key", lambda _u, _p: "USER_KEY")
    monkeypatch.setattr(mc.settings, "OPENAI_API_KEY", "SYS_KEY", raising=False)

    assert mc.get_effective_api_key(fake_user, "openai") == "SYS_KEY"


def test_get_effective_api_key_falls_back_to_system_when_user_key_missing(monkeypatch, fake_user):
    monkeypatch.setattr(mc, "_personal_api_keys_active", lambda _u: True)
    monkeypatch.setattr(mc, "get_user_api_key", lambda _u, _p: "")
    monkeypatch.setattr(mc.settings, "OPENAI_API_KEY", "SYS_KEY", raising=False)

    assert mc.get_effective_api_key(fake_user, "openai") == "SYS_KEY"


def test_get_effective_api_key_raises_when_both_user_and_system_keys_missing(monkeypatch, fake_user):
    monkeypatch.setattr(mc, "_personal_api_keys_active", lambda _u: True)
    monkeypatch.setattr(mc, "get_user_api_key", lambda _u, _p: "")
    monkeypatch.setattr(mc.settings, "OPENAI_API_KEY", "", raising=False)

    with pytest.raises(Exception, match="OPENAI_API_KEY"):
        mc.get_effective_api_key(fake_user, "openai")


def test_set_user_api_key_stores_encrypted_secret_and_suffix4(monkeypatch, fake_user):
    manager = _FakeManager()
    monkeypatch.setattr(mc, "_mycredentials", lambda: manager)
    monkeypatch.setattr(mc, "_encrypt_secret", lambda s: {"ct": f"enc:{s}"})

    mc.set_user_api_key(fake_user, "openai", "  abcd1234  ")

    assert len(manager.calls) == 1
    call = manager.calls[0]
    assert call["user"] is fake_user
    assert call["provider"] == "openai"
    assert call["defaults"]["secret"] == {"ct": "enc:abcd1234"}
    assert call["defaults"]["suffix4"] == "1234"
