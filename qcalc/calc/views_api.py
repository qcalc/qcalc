# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""JSON HTTP layer for /calc/api/v1/. Bearer-key auth only (no cookies, so no CSRF surface)."""

import functools
import json
import logging

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import qutil as ut
from .mod_api_core import ApiError, list_calculators, get_schema, run_calculator, enforce_quota
from .mod_api_keys import authenticate_api_key

logger = logging.getLogger(__name__)


def _json(data, status=200, headers=None):
    response = JsonResponse(data, status=status, json_dumps_params={'allow_nan': False})
    response['Cache-Control'] = 'no-store'
    for key, value in (headers or {}).items():
        response[key] = value
    return response


def _error_response(err: ApiError):
    headers = dict(err.headers)
    if err.status == 401:
        headers['WWW-Authenticate'] = 'Bearer'
    return _json({'error': err.to_dict()}, err.status, headers)


def _bearer_token(request):
    header = request.META.get('HTTP_AUTHORIZATION', '')
    scheme, _, token = header.partition(' ')
    if scheme.lower() == 'bearer' and token.strip():
        return token.strip()
    # | dev convenience for browser testing only: keys in URLs leak into history and logs
    if settings.DEBUG and request.method == 'GET':
        return request.GET.get('api_key', '').strip()
    return ''


def api_view(*methods):
    """Authenticate with a bearer key, restrict HTTP methods and render every failure as JSON."""

    def decorator(view):
        @csrf_exempt
        @functools.wraps(view)
        def wrapper(request, *args, **kwargs):
            try:
                if request.method not in methods:
                    raise ApiError('method_not_allowed', f"Use {' or '.join(methods)}", 405,
                                   headers={'Allow': ', '.join(methods)})

                key = authenticate_api_key(_bearer_token(request))
                if key is None:
                    raise ApiError('unauthorized', 'A valid API key is required (Authorization: Bearer <key>)', 401)

                # | calculators read the user and per-request state through the thread-bound request
                request.user = key.user
                request.api_key = key
                ut.q1139_request_init(request)
                return view(request, *args, **kwargs)
            except ApiError as e:
                return _error_response(e)
            except Exception as e:
                logger.exception('API: unexpected error: %s', e)
                return _error_response(ApiError('server_error', 'Unexpected server error', 500))

        return wrapper

    return decorator


def _int_param(request, name, default):
    try:
        return int(request.GET.get(name, default))
    except ValueError:
        raise ApiError('bad_request', f"'{name}' must be an integer", 400, name)


@api_view('GET')
def api_index(request):
    return _json(list_calculators(
        query=request.GET.get('q', ''),
        limit=_int_param(request, 'limit', 50),
        offset=_int_param(request, 'offset', 0),
    ))


@api_view('GET')
def api_schema(request, fid):
    return _json(get_schema(fid))


_RESERVED_QUERY_PARAMS = {'api_key', 'mode'}


def _query_inputs(request):
    """GET (DEBUG only): every query parameter except ``mode`` and ``api_key`` is an input. A value that starts
    with ``{`` or ``[`` is read as JSON, so a table can be passed as ``{"columns": [...], "data": [[...]]}``."""
    inputs = {}
    for name in request.GET:
        if name in _RESERVED_QUERY_PARAMS:
            continue
        value = request.GET.get(name, '')
        if value.lstrip()[:1] in ('{', '['):
            try:
                value = json.loads(value)
            except ValueError:
                raise ApiError('bad_request', f"'{name}' looks like JSON but is not valid JSON", 400, name)
        inputs[name] = value
    return inputs, request.GET.get('mode', 'full')


@api_view('GET', 'POST')
def api_run(request, fid):
    if request.method == 'GET':
        # | dev convenience for browser testing: a run is not a safe read (it costs quota and CPU), so production
        # | accepts POST only. Query parameters carry plain values and small JSON, and appear in logs and history.
        if not settings.DEBUG:
            raise ApiError('method_not_allowed', 'Use POST', 405, headers={'Allow': 'POST'})
        inputs, mode = _query_inputs(request)
    else:
        try:
            body = json.loads(request.body or b'{}')
        except ValueError:
            raise ApiError('bad_request', 'Request body must be valid JSON', 400)
        if not isinstance(body, dict):
            raise ApiError('bad_request', 'Request body must be a JSON object', 400)
        inputs, mode = body.get('inputs'), body.get('mode', 'full')

    enforce_quota(request.api_key)  # only runs are limited; list and schema calls are not counted
    return _json(run_calculator(fid, inputs, mode, request=request))
