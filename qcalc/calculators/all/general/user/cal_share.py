# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import qhtml, qemail, qurl, qtexta
from qutil import qaddr, qdomain
from calc import QCals
from django.template.loader import render_to_string
from calculators.all.admin.cal_email import email_send


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
