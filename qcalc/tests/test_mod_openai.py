import qsett

qsett.init()

import pytest

import calc.mod_openai as mo


def test_get_openai_model_uses_user_preference(monkeypatch):
    monkeypatch.setattr(mo.QPref, 'getp1', lambda _key, _default: 'gpt-4o-mini')

    assert mo.get_openai_model() == 'gpt-4o-mini'


def test_get_openai_model_falls_back_for_empty_preference(monkeypatch):
    monkeypatch.setattr(mo.QPref, 'getp1', lambda _key, _default: '  ')

    assert mo.get_openai_model() == mo.DEFAULT_OPENAI_MODEL


def test_get_openai_model_accepts_unlisted_model(monkeypatch):
    monkeypatch.setattr(mo.QPref, 'getp1', lambda _key, _default: ' custom-model ')

    assert mo.get_openai_model() == 'custom-model'


def test_gpt5_chat_options_use_completion_token_limit(monkeypatch):
    monkeypatch.setattr(mo.QPref, 'getp1', lambda _key, _default: 'gpt-5-mini')

    assert mo.get_openai_chat_options(temperature=0.7, max_tokens=50) == {
        'model': 'gpt-5-mini',
        'max_completion_tokens': 50,
    }


def test_legacy_chat_options_include_temperature(monkeypatch):
    monkeypatch.setattr(mo.QPref, 'getp1', lambda _key, _default: 'gpt-4.1-mini')

    assert mo.get_openai_chat_options(temperature=0.7, max_tokens=50) == {
        'model': 'gpt-4.1-mini',
        'temperature': 0.7,
        'max_tokens': 50,
    }


def test_model_not_found_has_actionable_message(monkeypatch):
    class ModelNotFoundError(Exception):
        code = 'model_not_found'

    class Completions:
        def create(self, **_kwargs):
            raise ModelNotFoundError()

    class Client:
        chat = type('Chat', (), {'completions': Completions()})()

    monkeypatch.setattr(mo.openai, 'NotFoundError', ModelNotFoundError)
    monkeypatch.setattr(mo.openai, 'OpenAI', lambda **_kwargs: Client())
    monkeypatch.setattr(mo, 'get_effective_api_key', lambda _user, _provider: 'key')
    monkeypatch.setattr(mo.QPref, 'getp1', lambda _key, _default: 'wrong-model')

    with pytest.raises(ValueError, match='wrong-model.*User Preferences'):
        mo.create_openai_chat_completion([{'role': 'user', 'content': 'Hello'}])
