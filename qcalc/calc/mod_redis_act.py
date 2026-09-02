# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import json
from django.conf import settings
import redis
import qvars
import time
from .mod_redis import redis_pubsub_active
from .mod_qcals import QCals
from .mod_qlist import cur_loader
from qvars import qc_gpref
import logging

logger = logging.getLogger(__name__)


def handle_qcalc_channel(message):
    if not redis_pubsub_active(): return
    # | Worker function to handle cache invalidation based on Redis messages
    try:
        kwargs = json.loads(message['data'])
        action = kwargs.pop('action', '')
        if action == "update_public_cal":
            cal_id = kwargs.pop('cal_id', '')
            cal_owner = kwargs.pop('cal_owner', '')
            code = kwargs.pop('code', '')
            QCals.update_public_cal(cal_id, cal_owner, code)
        elif action == "delete_public_cal":
            cal_id = kwargs.pop('cal_id', '')
            QCals.delete_public_cal(cal_id)
        elif action == "update_currency":
            update_now = kwargs.pop('update_now', False)
            cur_loader.update_currency(update_now)  # update_now False=already downloaded, upload only
        elif action == "update_gpref":
            up_gpref = kwargs.pop('up_gpref', qc_gpref)
            qc_gpref.update(up_gpref)
            logger.note(f"HQC: Updated gpref")
    except json.JSONDecodeError as e:
        logger.error(f">>> HQC: JSON decoding error: {e}")
    except Exception as e:
        logger.error(f">>> HQC: {e}")


def listen_to_qcalc_channel():
    if not redis_pubsub_active(): return

    # | Retry connecting to Redis until it's available
    pubsub = None
    while not qvars.stop_redis_listener:
        try:
            pubsub_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
            pubsub = pubsub_client.pubsub()
            pubsub.subscribe("qcalc_channel")
            break  # | Exit the loop once connection and subscription succeed
        except redis.exceptions.ConnectionError:
            if qvars.stop_redis_listener:
                return
            logger.error(">>> LQC: Redis not reachable, retrying in 5 seconds...")
            time.sleep(5)

    if qvars.stop_redis_listener: return
    if not pubsub: return

    # | Begin listening for messages
    try:
        while not qvars.stop_redis_listener:
            message = pubsub.get_message(timeout=5)  # | Check for messages every 5 seconds
            if message and message['type'] == 'message':
                handle_qcalc_channel(message)
            else:
                time.sleep(0.1)  # | Add a small sleep to prevent high CPU usage
    except Exception as e:
        logger.error(f">>> LQC: Error occurred: {e}")
    finally:
        pubsub.close()  # | Ensure pubsub is closed when listener stops
