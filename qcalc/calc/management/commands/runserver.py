# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import os
import socket
from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.management.commands.runserver import Command as StaticfilesRunserverCommand
import logging

logger = logging.getLogger(__name__)
print(f"Reading {__file__} ...")

class Command(StaticfilesRunserverCommand):
    """Custom runserver command that validates prerequisites before starting the server."""

    def handle(self, *args, **options):
        """Validate database, superuser, and cache before delegating to runserver."""
        # With autoreload enabled, runserver starts a parent watcher and a serving child.
        # Run prechecks only in the child process to avoid duplicate startup work/logging.
        if options.get("use_reloader") and os.environ.get("RUN_MAIN") != "true":
            return super().handle(*args, **options)
        print("")
        logger.info("SVR: Checking database service availability...")
        self._check_database_service_is_reachable()
        logger.info("SVR: Checking required superuser...")
        self._validate_required_superuser()
        logger.info("SVR: Checking static files...")
        self._validate_static_probe()
        logger.info("SVR: Checking if caching is active...")
        self._validate_cache_is_active()
        print("")
        logger.note("SVR: Starting qCalc server")
        return super().handle(*args, **options)

    @staticmethod
    def _check_database_service_is_reachable():
        """Verify database host is reachable via socket before attempting connection."""
        # Skip check for SQLite (file-based database).
        logger.info(f"- Database service is [{settings.DB_ENGINE}]")
        if "sqlite" in settings.DB_ENGINE.lower():
            return

        db_host = settings.DB_HOST
        if not db_host:
            return

        db_port_raw = settings.DB_PORT
        try:
            db_port = int(str(db_port_raw))
        except (TypeError, ValueError):
            return

        try:
            with socket.create_connection((db_host, db_port), timeout=2):
                return
        except OSError:
            logger.error(">>> CDS: Database server is not available. Start the database service, then run runserver again.")
            os._exit(1)

    @staticmethod
    def _validate_required_superuser():
        """Check superuser exists; terminate process immediately if not."""
        logger.info(f"- Required super user account name is [super]")
        try:
            user_model = get_user_model()
            if user_model.objects.filter(username='super').exists():
                return
        except Exception as e:
            logger.error(f">>> VRS: {e}. If required database or table doesn't exist, Run >> python manage.py migrate")
            os._exit(1)
        logger.error(">>> VRS: Super user has not been created yet. Run >> python manage.py createsuperuser")
        # Force immediate process termination before server loop starts.
        os._exit(1)

    @staticmethod
    def _validate_static_probe():
        """Ensure a known static asset can be resolved by staticfiles finders."""
        logger.info(f"- Configured static URL is [{settings.STATIC_URL}]")
        static_probe = 'qsite/js/qcalc.js'
        if finders.find(static_probe):
            return

        logger.error(
            f">>> VSP: Static probe failed: cannot resolve {settings.STATIC_URL}{static_probe}. "
            "Check STATICFILES_DIRS / app static folders / collectstatic setup."
        )
        os._exit(1)

    @staticmethod
    def _validate_cache_is_active():
        """Verify cache is properly configured and active."""
        from calc import QCache
        from qutil import check_setting
        logger.info(f"- Configured cache is [{settings.DEFAULT_CACHE_ALIAS}]")
        if QCache.isactive():
            return

        logger.error(
            f">>> VCA: Cache [{check_setting(settings.QSCHEMA_CACHE_ALIAS, "QSCHEMA_CACHE_ALIAS")}] is not active. "
            "Use either locmem, file, memcached, or redis (configured in base.py settings) as the DEFAULT_CACHE_ALIAS."
            "If memcached or redis, then start the corresponding service."
        )
        os._exit(1)
