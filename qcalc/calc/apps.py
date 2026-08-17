# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from django.apps import AppConfig
from calc import StdList, listen_to_qcalc_channel, initialize_py_catalog_once_per_worker, publish_redis_check
import os
import sys
import threading
import atexit
from django.conf import settings
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

    def ready(self):  # | run once for every worker
        # Skip heavy startup in Django autoreload parent process (dev/runserver).
        # RUN_MAIN is "true" only in the serving child process.
        is_runserver = len(sys.argv) > 1 and sys.argv[1] == "runserver"
        is_noreload = "--noreload" in sys.argv
        is_reloader_child = os.environ.get("RUN_MAIN") == "true"
        # if (not is_runserver) or is_noreload or is_reloader_child:
        if is_runserver and not is_reloader_child and not is_noreload:  # settings.DEBUG and
            # logger.info('SVR: Skipping worker init in autoreload parent process')
            return
        if not is_runserver: # return for other commands like collectstatic, check, migrate, etc.
            return
        # | Worker level application initialization code here
        # | Previous stages per instance in qenv.py
        qenv.run_once_per_instance()

        if not self.__class__._shutdown_hook_registered:
            atexit.register(self.__class__._request_stop)
            self.__class__._shutdown_hook_registered = True

        # upr = user_process()
        StdList.prepare_lists()
        logger.info(f'--- STAGE W.1: prepare_lists() completed')
        if settings.REDIS_PUBSUB == "1" and settings.DEFAULT_CACHE_ALIAS == "redis":
            # Initialize Redis client
            publish_redis_check()
            logger.info(f'--- STAGE W.1.1: publish_redis_check() completed')
            # | daemon = True is required to work inside docker
            listener_thread = threading.Thread(target=listen_to_qcalc_channel, daemon=True)
            listener_thread.start()
            logger.info(f'--- STAGE W.1.2: listen_to_qcalc_channel() completed')

        initialize_py_catalog_once_per_worker()
        logger.info("*** Initialization code per worker completed")
        # | Next stages per request in qsite/middleware.py
