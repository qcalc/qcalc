# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import os
import sys
import qenv

from django.core.asgi import get_asgi_application
print(f"Reading {__file__} ...")
# This allows easy placement of apps within the interior qcalc directory.
app_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
sys.path.append(os.path.join(app_path, "qsite"))

env0 = qenv.read_env()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", env0("DJANGO_SETTINGS_MODULE", default=env0.NOTSET))

application = get_asgi_application()
