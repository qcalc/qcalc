# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import re
from urllib.parse import quote
from django.utils.html import format_html
from qcore import qhtml, qemail, qurl, qpage
from qutil import qaddr, qdomain
from qutil.mod_md import code2html, md2html
from calc import QCals
from django.template.loader import render_to_string
from calculators.all.admin import email_send


def share_by_email__info():
    return {
        'title': 'Share by Email',
        'schema': {
            'recipient_emails': {
                'help_text': 'Enter semicolon (;) separated list of recipient email addresses',
                # 'required': True,
            },
        },
        'calculate': 'Share',
    }


def share_by_email(func_id='bmi', url: qurl = '', recipient_emails: str = '', your_email: qemail = ''):
    message = ''
    if not func_id:
        return 'Calculator id is misiing'
    title, desc, tags = QCals.func_title_desc_tags(func_id)
    url = f'{qaddr()}/calc/{func_id}/' if url == '' else url
    if f'/{func_id}/' not in url:
        result = f'Function {func_id} and URL is inconsistent. Please note URL is optional.'
    else:
        subject = f'Sharing - {title}'
        message = render_to_string('share_by_email.html', {
            'sender': your_email,
            'qaddr': qaddr(),
            'domain': qdomain(),
            'func_id': func_id,
            'title': title,
            'desc': desc,
            'url': url,
        })
        if recipient_emails and your_email:
            result = email_send(subject, recipient_emails, '', message, your_email, html_message=True)
        else:
            result = ("Error (SBM): Your link has not been shared yet. Please enter a) recipient email(s). "
                      "You can enter one or more emails separated by a semicolon (;), also b) enter your_email.")

    return {
        'Result': result,
        'Message': qhtml(message)
    }


def embed_code__info():
    return {
        'title': 'Embed on Your Website',
        'schema': {
            'height': {'help_text': 'Height of the no-JavaScript iframe: pixels (e.g. 600) or 100% to fill a container '
                                    'that has its own height. It scrolls if the content is taller. '
                                    'The script version ignores it and auto-fits its content.'},
            'run': {'help_text': 'Show results as soon as the widget loads'},
        },
        'calculate': 'Get Code',
    }


def embed_code__help():
    return md2html(
        'Generates code to show this calculator on your own website. Two versions are offered:\n\n'
        '- **Script version** auto-fits its content: it grows or shrinks as results appear, so there is no '
        'inner scrollbar. It needs `<script>` to be allowed on the host page. `height` is ignored.\n'
        '- **No-JavaScript version** is a plain `<iframe>` for sites that strip scripts (e.g. many CMS and forum '
        'editors). It does not follow the content: it scrolls inside the frame when the content is taller than '
        '`height`.\n\n'
        '`height` for the iframe is either pixels (e.g. `600`) or `100%`. `100%` fills the parent element, so it '
        'only works when the parent has its own height (e.g. a container with a fixed height or `100vh`). '
        'Otherwise it collapses to about 150px.\n\n'
        '`run` shows the results as soon as the calculator loads. Both versions hide the share and favorite '
        'buttons. Use *Preview* to check the result before pasting.'
    )


def embed_code(func_id='bmi', height: str = '100%', run: bool = True):
    if not func_id:
        return 'Calculator id is missing'
    height = height.strip().lower()
    if not re.fullmatch(r'\d+(px|%)?', height):
        return 'Height must be a number of pixels (e.g. 600) or a percentage (e.g. 100%)'
    run_attr = '' if run else ' data-run="false"'
    snippet = (f'<div data-qcalc="{func_id}"{run_attr}></div>\n'
               f'<script src="{qaddr()}/static/qsite/js/qembed.js" async></script>')
    preview = f'{qaddr()}/calc/core/{quote(func_id)}/?embed=1{"&run" if run else ""}'
    iframe = (f'<iframe src="{preview}" title="{func_id} calculator" '
              f'width="100%" height="{height}" style="border:0"></iframe>')
    note = format_html(
        'Paste this where the calculator should appear. The script version auto-fits its content. '
        'The no-JavaScript version scrolls if the content is taller than its height. '
        '<a href="{}" target="_blank">Preview</a>',
        preview,
    )
    return {
        'Embed code': qhtml(code2html(snippet, 'html', pre_wrap=True)),
        'Embed code (no JavaScript)': qhtml(code2html(iframe, 'html', pre_wrap=True)),
        'Note': qhtml(str(note)),
    }
