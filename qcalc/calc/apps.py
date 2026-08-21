# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from django.apps import AppConfig
from calc import StdList, listen_to_qcalc_channel, w2_initialize_py_catalog_once_per_worker, \
    redis_publish_check, redis_pubsub_active
import os
import sys
import threading
import atexit
import qenv
import qvars
import logging

logger = logging.getLogger(__name__)
print(f"Reading {__file__} ...")

class CalcConfig(AppConfig):
    name = 'calc'
    _shutdown_hook_registered = False

    @classmethod
    def _request_stop(cls):
        qvars.stop_redis_listener = True
        logger.note('SVR: Stopping qCalc server')

    def ready(self):
        """Initialize application state for serving processes."""

        if self._is_serving_process():
            self._initialize_worker()

    def _is_serving_process(self):
        """Return True only for an actual Django serving process."""

        # Django development server
        is_runserver = len(sys.argv) > 1 and sys.argv[1] == "runserver"
        if is_runserver:
            # Skip the parent autoreloader process when --noreload is absent
            return "--noreload" in sys.argv or os.environ.get("RUN_MAIN") == "true"

        # Gunicorn does not normally put "runserver" in sys.argv,
        # so detect Gunicorn separately by environment variable in YML
        if os.environ.get("GUNICORN_INSTANCE_ID"):
            logger.info(f"GUNICORN_INSTANCE_ID={os.environ.get('GUNICORN_INSTANCE_ID')}")
            return True

        # Management commands such as: migrate, collectstatic, check, shell, etc.
        return False

    def _initialize_worker(self):
        """Initialization performed independently by every serving worker."""

        # Per-instance initialization
        qenv.run_once_per_instance()

        # Shutdown handling
        if not self.__class__._shutdown_hook_registered:
            atexit.register(self.__class__._request_stop)
            self.__class__._shutdown_hook_registered = True

        # Redis pub/sub listener for this worker
        if redis_pubsub_active():
            redis_publish_check()
            logger.info("*** STAGE W.0.1: redis_publish_check() completed")

            listener_thread = threading.Thread(
                target=listen_to_qcalc_channel,
                daemon=True,
            )
            listener_thread.start()
            logger.info("*** STAGE W.0.2: listen_to_qcalc_channel() started")

        # Application data loaded into this worker's memory
        StdList.w1_prepare_lists_once_per_worker()

        # Worker-local catalog
        w2_initialize_py_catalog_once_per_worker()

        logger.info("*** Initialization code per worker completed")

