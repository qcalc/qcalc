# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import random
from django_htmx.middleware import HtmxDetails
from django.http import HttpRequest
from django.shortcuts import render

import qvars
from .mod_basic import nzs, iif
from django.http import Http404
import hashlib
import logging

logger = logging.getLogger(__name__)


class HtmxHttpRequest(HttpRequest):
    def __init__(self):
        super().__init__()
        self.session = None
        self.user = None

    htmx: HtmxDetails
    pref: dict
    context: dict
    json_schema: list[dict]
    json_data: dict  # data for schema e.g.  'gold':10, 'gold_part_uom': 'vori',
    # 'gold_2_part': 8, 'gold_2_part_uom': 'anna'
    json_doc: dict
    json_s2f: dict  # schema to form (e.g. gold, gold_part_uom, gold_2_part, gold_2_part_uom)
    json_d4f: dict  # data for function (e.g. '10 vori, 8 anna')
    json_c4f: dict  # count of fields per function argument, used for layout purpose

    ojson_schema: list
    ojson_data: dict
    ojson_data_type: list
    ojson_doc: dict

    ojson_d4f: dict
    ojson_keep_dumps: str

    sfunc: str
    cid: str
    is_public: bool
    input_id: int
    var_owner: int
    var_title: str
    variant: int
    token: str
    token_state: bool
    remember: bool
    recall: bool
    success: bool
    cmd: str = ''
    extra: dict = {}
    times = []
    ufunc_dict: dict = {}


def not_found(_request: HtmxHttpRequest, **kwargs):
    raise Http404(f"Page {kwargs.get('pname', 'was')} not found")


def create_session_once_per_session(request):
    def new_session(request):
        request.session.save()
        assert request.session.session_key is not None
        request.session['hash'] = session_id_hash(request.session.session_key)
        logger.info(f'CRS: New session key created | user={request.session['hash']}')

    if not request.session.session_key or 'hash' not in request.session:
        # logger.info('Session key not found')
        # if session key exists or the old session is lost and a new session is created
        # e.g. when server restarts
        new_session(request)

    # print('session key', request.session.session_key, request.session['hash'])


def q1139_request_init(request: HtmxHttpRequest):
    request.pref = {}
    # request.dec = ''
    request.context = {}
    request.json_schema = []
    request.json_data = {}
    request.json_doc = {}
    request.json_s2f = []
    request.json_c4f = {}
    request.json_d4f = {}

    request.ojson_schema = []
    request.ojson_data = {}
    request.ojson_data_type = []
    request.ojson_doc = {}

    request.ojson_d4f = {}
    request.ojson_keep_dumps = '{}'

    request.sfunc = ''
    request.cid = ''
    request.is_public = True
    request.input_id = 0
    request.variant = 0
    request.var_owner = qvars.super_user.username
    request.var_title = ''
    request.token = ''
    request.token_state = False  # | not saved
    # | follwoing two variables are defined even before calling this request_init()
    # | request.remember = True  # remember input
    # | request.recall = True  # recall input
    request.success = True

    request.json_doc['fxpr'] = ''
    request.json_doc['furl'] = ''
    request.json_doc['floop'] = ''
    request.cmd = ''
    request.extra = {}
    request.times = {}
    request.ufunc_dict = {}


def request_dump(request: HtmxHttpRequest):
    return {
        'sfunc': request.sfunc,
        'cid': request.cid,
        'variant': request.variant,
        'remember': request.remember,
        'recall': request.recall,
        'success': request.success,
        'pref': request.session.get("pref", None),
        'mem': request.session.get("mem", None),
        'json_schema': request.json_schema,
        'json_data': request.json_data,
        'json_doc': request.json_doc,
        'json_s2f': request.json_s2f,
        'json_c4f': request.json_c4f,
        'json_d4f': request.json_d4f,
        'ojson_data': request.ojson_data,
        'ojson_data_type': request.ojson_data_type,
        'ojson_doc': request.ojson_doc,
        'ojson_d4f': request.ojson_d4f,
        'ojson_keep_dumps': request.ojson_keep_dumps,
        'extra': request.extra,
        'times': request.times,
        'ufunc_dict': request.ufunc_dict,
        # 'qc_cache': QCache.root(),  # some type is not serializable
    }


def show_modal(request: HtmxHttpRequest, title, body, part='1'):
    context = get_page_context('dialog')
    context['data'] = {"title": title, "body": body}
    template = iif(part == '0', "modal-full.html", "modal-part.html", )
    res = render(request, template, context)  #
    return res


def makeid():
    # ref: https://stackoverflow.com/questions/48095737/django-new-session-for-each-browser-tab
    text = ""
    possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    for i in range(8):
        text += random.choice(possible)
    return text


def get_page_context(page='card') -> dict:
    cid = f"{page}__page"  # __{makeid()}"
    return {"input": {"cid": cid, "doc": {"name": page}}}


def get_page(request: HtmxHttpRequest, template='', context=None, page='', as_card=False):
    if context is None:
        context = {}
    part = request.GET.get("part", '0').strip() if request.method == 'GET' else '1'
    try:
        if nzs(page) != '':
            template = f'pages/{page}.html' if template == '' else template
            # | check if ctx_id is already supplied or not
            ctx_input = context.get('input', {})
            ctx_id = ctx_input.get('cid', None) if ctx_input != {} else None
            if not ctx_id: context.update(get_page_context(page))

            page_or_card = 'insert-card.html' if as_card else 'insert-page.html'
            context['base'] = page_or_card if part != '0' else 'gen-base.html'
            return render(request, template, context)
        else:
            return show_modal(request, "Get Page", 'Page name empty', part)
    except Exception as e:
        return show_modal(request, "Get Page", f'Error (GP): {e}, not found', part)


def session_id_hash(session_id):
    # session_id = request_sesn(request, True).session_key
    # Custom alphabets for consonants and vowels
    consonants = 'bcdfghjklmnpqrstvwxz'
    vowels = 'aeiouy'

    # Create an SHA-256 hash of the session ID
    hash_object = hashlib.sha256(session_id.encode())

    # Get the hexadecimal representation of the hash
    hex_dig = hash_object.hexdigest()

    # Initialize an empty hash code
    pronounceable_hash = ''

    # Generate the hash with vowels at positions 2 and 5
    for i in range(0, 6):
        if i in [1, 4]:  # 2nd and 5th positions (index 1 and 4) should be vowels
            index = int(hex_dig[i * 2:i * 2 + 2], 16) % len(vowels)
            pronounceable_hash += vowels[index]
        else:  # Other positions should be consonants
            index = int(hex_dig[i * 2:i * 2 + 2], 16) % len(consonants)
            pronounceable_hash += consonants[index]

    return pronounceable_hash.lower()
