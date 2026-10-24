# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
import socket

import qenv
from .timed_thread import QThread


def requires_login(func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionError("Login required")
        return func(request, *args, **kwargs)

    return wrapper


def user_name(request=None):
    """Return current user identity for calculator runtime context.

    Falls back to thread-bound request and returns:
    - authenticated username,
    - session hash for anonymous users,
    - ``'none'`` when no request is available.
    """
    request = request or QThread.get_req()
    if not request:
        return 'none'
    elif request.user.is_authenticated:
        return request.user.username  # name
    else:
        return request.session['hash']


def user_ip(request=None):
    """Return client IP address from request metadata.

    Uses the META key named by ``settings.CLIENT_IP_HEADER`` (e.g. ``HTTP_X_REAL_IP``, set by a trusted proxy)
    if configured, otherwise ``REMOTE_ADDR``. ``X-Forwarded-For`` is not used because a client can forge it.
    Returns ``''`` when no request is available.
    """
    from django.conf import settings
    request = request or QThread.get_req()
    if request is None:
        return ''
    header = getattr(settings, 'CLIENT_IP_HEADER', '') or ''
    ip = (request.META.get(header) if header else '') or request.META.get('REMOTE_ADDR') or ''
    return ip.strip()


def local_ip():
    """Return host machine IP resolved from hostname."""
    return socket.gethostbyname(socket.gethostname())


def is_loggedin(request):
    if request:
        return request.user.is_authenticated
    else:
        return False


def is_staff(request):
    return is_loggedin(request) and request.user.is_staff


def user_process():
    """Return a compact process label for logs/debug output."""
    info = qenv.get_worker_info()
    instance_id = info.get('instance_id')
    worker_pid = info.get('worker_pid')
    return f'User: {user_name()}, Instance: {instance_id}, PID: {worker_pid}'
