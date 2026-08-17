# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""
WSGI config for qCalc project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.

"""
import os
import sys
import qenv

from django.core.wsgi import get_wsgi_application
print(f"Reading {__file__} ...")
# This allows easy placement of apps within the interior qcalc directory.
app_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
sys.path.append(os.path.join(app_path, "qsite"))

# Code to run once per instance
# qenv.run_once_per_instance()

# We defer to a DJANGO_SETTINGS_MODULE already in the environment. This breaks
# if running multiple sites in the same mod_wsgi process. To fix this, use
# mod_wsgi daemon mode with each site in its own daemon process, or use
# os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.production"
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
env0 = qenv.read_env()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", env0("DJANGO_SETTINGS_MODULE", default=env0.NOTSET))

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
application = get_wsgi_application()
# Apply WSGI middleware here.
