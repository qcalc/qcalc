import json

import pytest
import qsett

qsett.init()

import qvars
from django.test import RequestFactory

from calc import views_api
from calc.mod_api_keys import authenticate_api_key
from qutil.timed_thread import QThread


class _FakeUser:
    username = 'apiuser'
    is_authenticated = True


@pytest.fixture(autouse=True)
def _api_env(monkeypatch):
    monkeypatch.setattr(qvars, 'super_user', type('_FakeUser', (), {'username': 'super'})())
    monkeypatch.setattr(
        views_api, 'authenticate_api_key',
        lambda raw: type('_Key', (), {'user': _FakeUser()})() if raw == 'good-key' else None,
    )
    QThread.set_req(None)
    yield
    QThread.set_req(None)


def _call(view, method='get', path='/calc/api/v1/', key='good-key', body=None, **kwargs):
    rf = RequestFactory()
    headers = {'HTTP_AUTHORIZATION': f'Bearer {key}'} if key else {}
    if method == 'post':
        request = rf.post(path, data=body if isinstance(body, (str, bytes)) else json.dumps(body or {}),
                          content_type='application/json', **headers)
    else:
        request = rf.get(path, **headers)
    response = view(request, **kwargs)
    return response, json.loads(response.content)


def test_missing_or_wrong_key_is_401_json():
    for key in (None, 'bad-key'):
        response, data = _call(views_api.api_index, key=key)
        assert response.status_code == 401
        assert data['error']['code'] == 'unauthorized'
        assert response['WWW-Authenticate'] == 'Bearer'


def test_api_key_query_param_works_for_get_only_in_debug(monkeypatch):
    request = RequestFactory().get('/calc/api/v1/?api_key=good-key')

    monkeypatch.setattr(views_api.settings, 'DEBUG', True)
    assert views_api.api_index(request).status_code == 200

    monkeypatch.setattr(views_api.settings, 'DEBUG', False)
    assert views_api.api_index(request).status_code == 401


def test_api_key_query_param_is_ignored_for_post_even_in_debug(monkeypatch):
    monkeypatch.setattr(views_api.settings, 'DEBUG', True)
    request = RequestFactory().post('/calc/api/v1/bmi/run/?api_key=good-key', data='{}',
                                    content_type='application/json')
    assert views_api.api_run(request, fid='bmi').status_code == 401


def test_bearer_header_wins_over_query_param(monkeypatch):
    monkeypatch.setattr(views_api.settings, 'DEBUG', True)
    request = RequestFactory().get('/calc/api/v1/?api_key=good-key', HTTP_AUTHORIZATION='Bearer bad-key')
    assert views_api.api_index(request).status_code == 401


def test_index_lists_opted_in_calculators():
    response, data = _call(views_api.api_index, path='/calc/api/v1/?q=bmi')
    assert response.status_code == 200
    assert [c['id'] for c in data['calculators']] == ['bmi']
    assert response['Cache-Control'] == 'no-store'


def test_bad_integer_param_is_400():
    response, data = _call(views_api.api_index, path='/calc/api/v1/?limit=abc')
    assert response.status_code == 400 and data['error']['field'] == 'limit'


def test_schema_view_and_unknown_calculator():
    response, data = _call(views_api.api_schema, fid='bmi')
    assert response.status_code == 200 and data['id'] == 'bmi'

    response, data = _call(views_api.api_schema, fid='redo')
    assert response.status_code == 404 and data['error']['code'] == 'not_found'


def test_run_view_returns_result():
    response, data = _call(views_api.api_run, 'post', body={'inputs': {'weight': '70 kg', 'height': '1.75 m'}},
                           fid='bmi')
    assert response.status_code == 200
    assert data['result']['BMI']['unit']


def test_run_view_errors_are_json_with_status_codes():
    response, data = _call(views_api.api_run, 'post', body={'inputs': {'x': 1}}, fid='bmi')
    assert response.status_code == 422 and data['error']['code'] == 'unknown_argument'

    response, data = _call(views_api.api_run, 'post', body='{not json', fid='bmi')
    assert response.status_code == 400 and data['error']['code'] == 'bad_request'

    response, data = _call(views_api.api_run, 'post', body=[1, 2], fid='bmi')
    assert response.status_code == 400

    response, data = _call(views_api.api_run, 'post', body={'mode': 'tiny'}, fid='bmi')
    assert response.status_code == 400


def test_wrong_method_is_405():
    response, data = _call(views_api.api_run, 'get', fid='bmi')
    assert response.status_code == 405 and data['error']['code'] == 'method_not_allowed'


def test_malformed_keys_are_rejected_without_a_database_lookup():
    for raw in ('', 'abc', 'qck_only', 'other_prefix_secret'):
        assert authenticate_api_key(raw) is None


def test_routes_are_registered_ahead_of_catch_all():
    from django.urls import resolve

    assert resolve('/calc/api/v1/').url_name == 'calc-api-index'
    assert resolve('/calc/api/v1/bmi/schema/').url_name == 'calc-api-schema'
    assert resolve('/calc/api/v1/bmi/run/').url_name == 'calc-api-run'
