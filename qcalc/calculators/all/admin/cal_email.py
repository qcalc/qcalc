# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from django.core.mail import EmailMessage  # | send_mail doesn't have cc
from django.conf import settings
from qcore import qtexta, qemail
from qutil import css2strs


def email_send__info():
    return {
        'title': 'Send Email',
        'schema': {
            'recipient_emails': {
                'help_text': 'Enter semicolon (;) separated list of recipient email addresses',
            },
            'cc_emails': {
                'help_text': 'Enter semicolon (;) separated list of copy to email addresses',
            }
        },
        'calculate': 'Send',
    }


def email_send(subject: str, recipient_emails: str, cc_emails: str,
               message: qtexta, sender_email:qemail='', html_message=False):
    """Function to send an email"""
    recipient_emails = css2strs(recipient_emails, ';')
    cc_emails = css2strs(cc_emails, ';')
    cc = list(dict.fromkeys(cc_emails + [sender_email]))
    try:
        if subject and message and recipient_emails and sender_email:
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,  # Sender email address (configured in settings)
                to=recipient_emails,  # List of recipient email addresses
                cc=cc,
                reply_to=[sender_email]
            )
        else:
            return 'Recipient emails, subject, message and sender email are required'
        # Add HTML message if provided
        if html_message:
            email.content_subtype = 'html'  # Set the email type to HTML
        else:
            email.content_subtype = 'plain'  # Default to plain text

        email.send(fail_silently=False)  # Set to True to silently ignore errors
        return "Email sent successfully"
    except Exception as e:
        return f"Error sending email: {e}"
