# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import openai
from typing import Any
from .mod_qcals import QCals
from qcore import _base_categ_s2d, _base_categories, _unit_info
import inspect
import qconst
from .mod_cache import QMyCal, QPref
from qutil import fid2owner, user_name, md2html, QThread, is_loggedin
from .mod_credentials import get_effective_api_key

DEFAULT_OPENAI_MODEL = 'gpt-5.4-mini'
OPENAI_MODEL_CHOICES = [
    'gpt-4o-mini',  # Coding: Basic–Good | Cost: Very low
    'gpt-4.1-mini',  # Coding: Good | Cost: Low
    'gpt-4.1',  # Coding: Very good | Cost: Medium
    'gpt-4o',  # Coding: Good–Very good | Cost: Medium
    'gpt-5-nano',  # Coding: Basic–Good | Cost: Very low
    'gpt-5-mini',  # Coding: Good–Very good | Cost: Low
    'gpt-5.3-codex',  # Coding: Excellent | Cost: Medium
    'gpt-5.4-nano',  # Coding: Basic–Good | Cost: Very low
    'gpt-5.4-mini',  # Coding: Very good | Cost: Low–Medium
    'gpt-6-luna',  # Coding: Good | Cost: Very low
    'gpt-6-sol',  # Coding: Excellent | Cost: Medium
    'gpt-6.1-sol',  # Coding: Excellent | Cost: Medium–High
    'gpt-6-astra',  # Coding: Excellent | Cost: High
]


def _current_user():
    req = QThread.get_req()
    if req is not None and is_loggedin(req):
        return req.user
    return None


def normalize_openai_model(model):
    return str(model).strip() or DEFAULT_OPENAI_MODEL


def get_openai_model():
    model = QPref.getp1('openai_model', DEFAULT_OPENAI_MODEL)
    return normalize_openai_model(model)


def get_openai_chat_options(temperature=None, max_tokens=None):
    model = get_openai_model()
    options: dict[str, Any] = {'model': model}
    if model.startswith('gpt-5'):
        if max_tokens is not None:
            options['max_completion_tokens'] = max_tokens
    else:
        if temperature is not None:
            options['temperature'] = temperature
        if max_tokens is not None:
            options['max_tokens'] = max_tokens
    return options


def create_openai_chat_completion(messages, temperature=None, max_tokens=None):
    options = get_openai_chat_options(temperature=temperature, max_tokens=max_tokens)
    model = str(options['model'])
    api_key = get_effective_api_key(_current_user(), 'openai')
    client = openai.OpenAI(api_key=api_key)
    try:
        return client.chat.completions.create(**options, messages=messages)
    except openai.NotFoundError as error:
        if getattr(error, 'code', None) == 'model_not_found':
            raise ValueError(
                f'AI model "{model}" was not found or is not available '
                'to your API key. Check the model name in User Preferences.'
            ) from error
        raise


def get_code(func_id: str = 'gold', show_meta=False, as_html=True):
    source_blocks = []
    error = ''
    cal_id, cal_name, owner = fid2owner(func_id=func_id)
    personal = (owner == user_name())
    # print(cal_id, cal_name, owner, user_name(), personal)
    if not personal:
        # func_id = func_name  # for qcalc functions
        if show_meta:
            for meta in qconst.KNOWN_METAS:
                func_meta_id = f'{func_id}{meta}'
                if QCals.func_exists(func_meta_id, scope='q'):
                    fn_info = QCals.addr(func_meta_id, scope='q')
                    source_blocks.append(inspect.getsource(fn_info))
        try:
            fn = QCals.addr(func_id, scope='q')
            if fn:
                source_blocks.append(inspect.getsource(fn))
            else:
                code = QMyCal.getp1_from_owner_public(func_id)
                if code:
                    source_blocks.append(code)
        except Exception as e:
            error = str(e)
    else:
        code = QMyCal.getp1(cal_id)
        if code:
            source_blocks.append(code)
        else:
            error = f'User function {func_id} not found'

    if not as_html:
        return '\n\n'.join(block.strip() for block in source_blocks)
    return ''.join(f'<pre>{block}</pre>' for block in source_blocks) + error


def instruct_ask_gpt(instruction: str = 'please be short and precise',
                     question: str = "What is life", temperature=0.7):  # not used
    # The 'role' can take one of three values: 'system', 'user' or the 'assistant'
    response = create_openai_chat_completion(
        [
            {
                "role": "system",
                "content": instruction,
            },
            {
                "role": "user",
                "content": question,
            },
        ],
        temperature=temperature,
    )
    resp = response.choices[0].message.content
    return resp


def ask_gpt(question: str = "What is qCalc", temperature=0.7):
    # The 'role' can take one of three values: 'system', 'user' or the 'assistant'
    response = create_openai_chat_completion(
        [
            {
                "role": "user",
                "content": question,
            },
        ],
        temperature=temperature,
    )
    resp = response.choices[0].message.content
    return resp


def func_desc(func_id: str = 'gold'):
    prompt = f"""
    Please analyse the following python function. This is a code for a calculator.
    Please describe the purpose of the function to an end user.
    This description will be used in the html meta description tag for the
    respective web page of the calculator for SEO purpose.
    Length of the description should be between 70 to 170 characters.
    For your hint the title of the calculator function is: {QCals.cnode(func_id).title}
    Important:
    a) Do not say that it is a 'Python function'
    b) Do not specify which particular unit of measurement it uses, because it is flexible and can use any units
    """
    prompt += get_code(func_id, show_meta=False)
    desc = ask_gpt(prompt, 0.7)
    return desc


def qty_guide(qty_slug: str = 'length'):
    qty_title = _base_categories[_base_categ_s2d[qty_slug]]
    prompt = f"""
    Please briefly describe physical quantity "{qty_title}",
    Important:
    1) please do not provide any equation or formula or conversions.
    2) Please break down the description into two paragraphs.
    3) Length of the first paragraph of the description should be between 70 to 170 characters.
    4) In 2nd paragraph of the description you can mention some of the common examples of related units of measurements.
    5) description section to be followed by it's application and importance, using bullet points.
    """
    desc = md2html(ask_gpt(prompt, 0.7))
    return desc


def qty_desc(qty_slug: str = 'length'):
    qty_title = _base_categories[_base_categ_s2d[qty_slug]]
    prompt = f"""
    Please briefly describe physical quantity "{qty_title}",
    Length of the description should be less than 170 characters.
    """
    desc = ask_gpt(prompt, 0.7)
    return desc


def unit_desc(unit_name: str = 'ft'):
    uinfo = _unit_info[unit_name]
    prompt = f"""
    please describe physical unit "{unit_name}" within 170 characters.
    In case you need more information about "{unit_name}" please take note of the follwoing:
    Category: {uinfo['category']}, Dimension: {uinfo['dimension']}, Known as: {uinfo['long_name']},
    Remark: {uinfo['comment']}
    """
    # print(prompt)
    desc = ask_gpt(prompt, 0.7)
    return desc
