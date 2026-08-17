# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from django.conf import settings


def settings_context(_request):
    return {"settings": settings}


def allauth_common_context(request):
    part = request.GET.get('part', '0')
    context = {
        'page_base': 'insert-page.html' if part == '1' else 'gen-base.html'
    }
    # print('c', context)
    return context
