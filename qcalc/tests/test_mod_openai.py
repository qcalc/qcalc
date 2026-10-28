import qsett

qsett.init()

from types import SimpleNamespace

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


class FakeBadRequest(Exception):
    def __init__(self, param, code='unsupported_parameter'):
        self.param = param
        self.code = code
        self.message = f"Unsupported parameter: '{param}' is not supported with this model."


@pytest.fixture
def fake_openai(monkeypatch):
    state = {'calls': [], 'reject': {}}

    class Responses:
        def create(self, **kwargs):
            state['calls'].append(kwargs)
            for param, code in state['reject'].items():
                if param in kwargs:
                    raise FakeBadRequest(param, code)
            return SimpleNamespace(output_text=state.get('text', 'ok'), incomplete_details=None)

    client = SimpleNamespace(responses=Responses())
    monkeypatch.setattr(mo.openai, 'BadRequestError', FakeBadRequest)
    monkeypatch.setattr(mo.openai, 'OpenAI', lambda **_kwargs: client)
    monkeypatch.setattr(mo, 'get_effective_api_key', lambda _user, _provider: 'key')
    monkeypatch.setattr(mo.QPref, 'getp1', lambda _key, _default: 'any-model')
    return state


def _ask():
    return mo.create_openai_chat_completion(
        [{'role': 'user', 'content': 'Hi'}], max_tokens=300
    )


def test_completion_uses_responses_api_with_output_token_headroom(fake_openai):
    response = _ask()

    assert response.choices[0].message.content == 'ok'
    call = fake_openai['calls'][0]
    assert call['model'] == 'any-model'
    assert call['max_output_tokens'] >= 4000
    assert 'max_tokens' not in call
    assert 'temperature' not in call


def test_completion_drops_parameters_the_model_rejects(fake_openai):
    fake_openai['reject'] = {'reasoning': 'unsupported_parameter'}

    _ask()

    final = fake_openai['calls'][-1]
    assert 'reasoning' not in final
    assert final['max_output_tokens'] >= 4000


def test_completion_drops_parameter_when_error_code_is_missing(fake_openai):
    fake_openai['reject'] = {'reasoning': None}

    _ask()

    assert 'reasoning' not in fake_openai['calls'][-1]


def test_completion_does_not_hide_other_bad_requests(fake_openai):
    fake_openai['reject'] = {'input': 'unsupported_parameter'}

    with pytest.raises(FakeBadRequest):
        _ask()


def test_completion_reports_empty_answer(fake_openai):
    fake_openai['text'] = '  '

    with pytest.raises(ValueError, match='any-model.*empty answer'):
        _ask()


def test_model_not_found_has_actionable_message(monkeypatch):
    class ModelNotFoundError(Exception):
        code = 'model_not_found'

    class Responses:
        def create(self, **_kwargs):
            raise ModelNotFoundError()

    monkeypatch.setattr(mo.openai, 'NotFoundError', ModelNotFoundError)
    monkeypatch.setattr(mo.openai, 'OpenAI', lambda **_kwargs: SimpleNamespace(responses=Responses()))
    monkeypatch.setattr(mo, 'get_effective_api_key', lambda _user, _provider: 'key')
    monkeypatch.setattr(mo.QPref, 'getp1', lambda _key, _default: 'wrong-model')

    with pytest.raises(ValueError, match='wrong-model.*User Preferences'):
        mo.create_openai_chat_completion([{'role': 'user', 'content': 'Hello'}])
