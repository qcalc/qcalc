# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import qvars


def get_super_user():
    from qsite.users.models import User  # | import after initialization
    qvars.super_user = User.objects.get(username='super')


def get_user(uname):
    from qsite.users.models import User  # | import after initialization
    return User.objects.get(username=uname)
