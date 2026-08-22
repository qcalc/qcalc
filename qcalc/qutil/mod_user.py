# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import qenv
from .timed_thread import QThread


def requires_login(func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionError("Login required")
        return func(request, *args, **kwargs)

    return wrapper


def user_name(request=None):
    request = request or QThread.get_req()
    if not request:
        return 'none'
    elif request.user.is_authenticated:
        return request.user.username  # name
    else:
        return request.session['hash']


def is_loggedin(request):
    if request:
        return request.user.is_authenticated
    else:
        return False


def is_staff(request):
    return is_loggedin(request) and request.user.is_staff


def user_process():
    info = qenv.get_worker_info()
    instance_id = info.get('instance_id')
    worker_pid = info.get('worker_pid')
    return f'User: {user_name()}, Instance: {instance_id}, PID: {worker_pid}'
