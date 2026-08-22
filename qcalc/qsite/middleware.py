# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qutil import create_session_once_per_session, QThread
from calc import w3_initialize_db_catalog_once_per_worker, QPref
import qvars
import threading
from django.core.exceptions import DisallowedHost
from django.http import HttpResponseBadRequest
import logging

logger = logging.getLogger(__name__)


class IgnoreDisallowedHostMiddleware:
    # | middleware/ignore_disallowed_host.py
    # | Add this middleware to MIDDLEWARE settings before Django’s SecurityMiddleware
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except DisallowedHost as e:
            logger.error(f">>> IDH: DisallowedHost exception: {e}")
            return HttpResponseBadRequest("Bad Request: Host not allowed")


class CalcMiddleware:
    _worker_init_lock = threading.Lock()
    _worker_init_done = False

    # Add qcalc middleware after the session and authentication middleware
    def __init__(self, get_response):
        self.get_response = get_response

    def _ensure_worker_init(self):
        if self.__class__._worker_init_done:
            return
        with self.__class__._worker_init_lock:
            if self.__class__._worker_init_done:
                return
            # Run exactly once per process/worker even under concurrent first requests.
            logger.info("CMW: Running one-time per worker db initialization")
            w3_initialize_db_catalog_once_per_worker()
            self.__class__._worker_init_done = True

    def __call__(self, request):  # | run on every request
        QThread.set_req(request)  # for each request, should be before QPref
        try:
            if not request.session.session_key or 'hash' not in request.session:
                # | Run once per user session
                create_session_once_per_session(request)
                QPref.setp(qvars.qc_gpref)  # authentication middleware required

            self._ensure_worker_init()
            response = self.get_response(request)
        except Exception as e:
            logger.error(f">>> CMW: Error in CalcMiddleware after response: {e}")
            raise
        finally:
            QThread.set_req(None)

        return response
