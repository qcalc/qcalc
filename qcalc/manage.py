#!/usr/bin/env python
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import os
import sys

from django.db import OperationalError

import qenv
print(f"Reading {__file__} ...")

# manage.py
#       │
#       ▼
# Settings loaded
#       │
#       ▼
# INSTALLED_APPS processed
#       │
#       ▼
# AppConfig objects created
#       │
#       ▼
# Models imported
#       │
#       ▼
# AppConfig.ready()
#       │
#       ▼
# Server starts

if __name__ == "__main__":
    # os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    env0 = qenv.read_env()
    settings_module = env0("DJANGO_SETTINGS_MODULE", default=env0.NOTSET)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

    # runserver with autoreload executes manage.py twice (parent watcher + child server).
    is_runserver = len(sys.argv) > 1 and sys.argv[1] == "runserver"
    is_noreload = "--noreload" in sys.argv
    is_reloader_child = os.environ.get("RUN_MAIN") == "true"
    if (not is_runserver) or is_noreload or is_reloader_child:
        print(f"*** Setting up Django environment from [setup.env], [{qenv.env_file()}], and [{settings_module}]")

    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django  # noqa
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )

        raise

    # following code help update existing docker container with new packages installed
    # packages can be specified as a comma separated list of names in setup.env.xxx file
    # assigned to environment variable PIP_INSTALL
    if (not is_runserver) or is_noreload or is_reloader_child:
        from django.conf import settings
        print(f"DEBUG: {settings.DEBUG}")
        print(f"*** Project folder {settings.PROJ_DIR}, Application root {settings.ROOT_DIR}")
        qenv.pip_install_uninstall(settings.PIP_INSTALL, "install")
        qenv.pip_install_uninstall(settings.PIP_UNINSTALL, "uninstall")

    # This allows easy placement of apps within the interior qcalc directory.
    current_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.join(current_path, "qsite"))

    try:
        execute_from_command_line(sys.argv)
    except OperationalError as e:
        print(f"*** Error occurred: {e}")
        sys.exit(1)
    except Exception as error:
        raise
