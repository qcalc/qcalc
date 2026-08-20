# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import json
from django.conf import settings
import redis
import qvars
import time
import logging

logger = logging.getLogger(__name__)

pubsub_client = None
pubsub_actions = {}

if settings.DEFAULT_CACHE_ALIAS == "redis":
    pubsub_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT,
                                db=settings.REDIS_DB)


def redis_pubsub_active():
    return settings.REDIS_PUBSUB == "1" and settings.DEFAULT_CACHE_ALIAS == "redis"


def register_redis_action(func):
    if not redis_pubsub_active(): return
    pubsub_actions[func.__name__] = func


def publish_redis_action(channel, **kwargs):
    # Function to publish notifications to Redis
    if not redis_pubsub_active(): return
    pubsub_client.publish(channel, json.dumps(kwargs))


def publish_redis_check():
    if not redis_pubsub_active(): return
    try:
        # Define action and kwargs
        action = 'qcalc_channel'
        kwargs = {'key': 'value'}

        # Publish message
        if pubsub_client.ping():  # Check connection
            message = json.dumps(kwargs)  # Serialize kwargs
            if action:  # Validate channel name
                pubsub_client.publish(action, message)
                logger.info("Message published successfully to Redis channel.")
            else:
                logger.error(f"PRC: Invalid channel name {action}.")
        else:
            logger.warning("PRC: Redis server is not reachable.")
    except Exception as e:
        logger.exception(f"Exception occurred: {e}")


def handle_qcalc_channel(message):
    if not redis_pubsub_active(): return
    # | Worker function to handle cache invalidation based on Redis messages
    try:
        kwargs = json.loads(message['data'])
        action = kwargs.pop('action', '')
        func = pubsub_actions.get(action, None)
        if not func: return
        if action == "update_public_cal":
            cal_id = kwargs.pop('cal_id', '')
            cal_owner = kwargs.pop('cal_owner', '')
            code = kwargs.pop('code', '')
            # call QCals.update_public_cal(cal_id, cal_owner, code)
            func(cal_id, cal_owner, code)
        elif action == "delete_public_cal":
            # call QCals.delete_public_cal(cal_id)
            cal_id = kwargs.pop('cal_id', '')
            func(cal_id)
        elif action == "update_currency":
            # call update_currency()
            func()
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
    except Exception as e:
        print(f"Error in handle_redis_notification: {e}")


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
            logger.error("LQC: Redis not reachable, retrying in 5 seconds...")
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
        logger.error(f"LQC: Error occurred: {e}")
    finally:
        pubsub.close()  # | Ensure pubsub is closed when listener stops


if __name__ == '__main__':
    publish_redis_check()
