# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from django.conf import settings
from urllib.parse import urljoin


def is_debug():
    """Return whether DEBUG mode is enabled."""
    return settings.DEBUG


def qdomain():
    return settings.QCALC_DOMAIN


def setting(name:str):
    return getattr(settings, name)


def qaddr():
    return f'{settings.QCALC_SCHEME}://{settings.QCALC_DOMAIN}'


def check_setting(setting, name:str = "", optional:bool = False):
    if setting == '':
        if optional:
            return ''
        else:
            raise Exception(f'Related setting {name} is missing')
    return setting


def abs_url(relative_url):
    """
    Converts a relative URL to an absolute URL based on the given base URL.

    :param relative_url: The relative URL e.g., '/path/to/resource/'
    :return: Absolute URL e.g., 'https://qcalc.org/path/to/resource/'
    """
    return urljoin(qaddr(), relative_url)


def demo_url(file):
    """Return absolute URL for a file under the ``static/demo`` path."""
    from django.templatetags.static import static

    return abs_url(static(f'demo/{file}'))
