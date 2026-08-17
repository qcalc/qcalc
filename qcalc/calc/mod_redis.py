# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import json
from django.conf import settings
import redis

import logging

logger = logging.getLogger(__name__)

pubsub_client = None

if settings.DEFAULT_CACHE_ALIAS == "redis":
    # pubsub_client = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
    pubsub_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT,
                                db=settings.REDIS_DB)


def publish_redis_action(channel, **kwargs):
    # Function to publish notifications to Redis
    if settings.REDIS_PUBSUB != "1" or settings.DEFAULT_CACHE_ALIAS != "redis": return
    pubsub_client.publish(channel, json.dumps(kwargs))


def publish_redis_check():
    if settings.REDIS_PUBSUB != "1" or settings.DEFAULT_CACHE_ALIAS != "redis": return
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


if __name__ == '__main__':
    publish_redis_check()
