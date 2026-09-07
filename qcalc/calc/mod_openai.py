# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import openai
from django.conf import settings
from .mod_qcals import QCals
from qcore import _base_categ_s2d, _base_categories, _unit_info
import inspect
import markdown
import qconst
from .mod_cache import QMyCal
from qutil import fid2owner, user_name, check_setting


def get_code(func_id: str = 'gold', show_meta=False):
    html = ''
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
                    html += f'<pre>{inspect.getsource(fn_info)}</pre>'
        try:
            fn = QCals.addr(func_id, scope='q')
            if fn:
                html += f'<pre>{inspect.getsource(fn)}</pre>'
            else:
                code = QMyCal.getp1_from_owner_public(func_id)
                if code: html += f'<pre>{code}</pre>'
        except Exception as e:
            html += f'{str(e)}'
    else:
        code = QMyCal.getp1(cal_id)
        if code:
            html += f'<pre>{code}</pre>'
        else:
            html += f'User function {func_id} not found'

    return html


def instruct_ask_gpt(instruction: str = 'please be short and precise',
                     question: str = "What is life", temperature=0.7):  # not used
    # The 'role' can take one of three values: 'system', 'user' or the 'assistant'
    api_key = check_setting(settings.OPENAI_API_KEY, "OPENAI_API_KEY", optional=False)
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
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
    api_key = check_setting(settings.OPENAI_API_KEY, "OPENAI_API_KEY", optional=False)
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "user",
                "content": question,
            },
        ],
        temperature=temperature,
    )
    resp = response.choices[0].message.content
    return resp


def format_markdown(content):
    return markdown.markdown(content, extensions=qconst.MARKDOWN_EXTENSIONS, output_format="html")


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
    desc = format_markdown(ask_gpt(prompt, 0.7))
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
