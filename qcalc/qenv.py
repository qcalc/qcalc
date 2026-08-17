# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import environ
import subprocess
import sys
import platform
import os
import threading
import shlex
import logging
logger = logging.getLogger(__name__)

ROOT_DIR = (environ.Path(__file__) - 1)  # (qcalc/qenv.py - 1 = qcalc/)
PROJ_DIR = ROOT_DIR.path("..") # qcalc/.. i.e. qcalc_dock/
APP_DIR = ROOT_DIR.path("qsite")  # qcalc/qsite/

def _download_nltk_resources():
    """Download required NLTK corpora only when missing."""
    import nltk

    not_found_downloaded = False
    try:
        nltk.data.find('corpora/wordnet.zip')
    except LookupError:
        not_found_downloaded = True
        nltk.download('wordnet')

    try:
        nltk.data.find('corpora/sentiwordnet.zip')
    except LookupError:
        not_found_downloaded = True
        nltk.download('sentiwordnet')

    return not_found_downloaded


def run_once_per_instance():  # | run once for every instance
    if _download_nltk_resources():
        logger.info(f'--- STAGE I.1: download_nltk_resources() completed')
        logger.info("*** Initialization code per instance completed")
        # | Next stages per worker in calc/app.py


def read_env(dotenv='setup.env'):
    env = environ.Env()
    env.read_env(str(ROOT_DIR.path(dotenv)))
    return env


def env_file():
    env0 = read_env()
    return env0("QCALC_ENV_FILE", default=env0.NOTSET)


def read_env_file():
    return read_env(env_file())


def pip_install_uninstall(css_packages, cmd='install'):  # cmd='uninstall'
    if css_packages == '':
        return
    list_of_packages = [x.strip() for x in css_packages.split(',')]
    for package in list_of_packages:
        try:
            __import__(package)
        # except: @15.09.24
        #     subprocess.call([sys.executable, "-m", "pip", cmd, "--no-input", package])
        except ImportError:
            subprocess.run([sys.executable, "-m", "pip", cmd, "--no-input", package])


def get_worker_info():
    # Get the instance information from the environment variable
    instance_id = os.getenv('GUNICORN_INSTANCE_ID', 'Unnamed')

    # Get the worker PID
    worker_pid = os.getpid()

    # Get the current thread name
    thread_name = threading.current_thread().name
    return {
        'instance_id': instance_id,
        'worker_pid': worker_pid,
        'thread_name': thread_name,
    }


def _parse_workers_from_gunicorn_args(cmd_args):
    if not cmd_args:
        return None
    try:
        tokens = shlex.split(cmd_args)
    except ValueError:
        return None

    for idx, token in enumerate(tokens):
        if token in ('--workers', '-w') and idx + 1 < len(tokens):
            nxt = tokens[idx + 1].strip()
            if nxt.isdigit() and int(nxt) > 0:
                return int(nxt)
        elif token.startswith('--workers='):
            val = token.split('=', 1)[1].strip()
            if val.isdigit() and int(val) > 0:
                return int(val)
        elif token.startswith('-w') and len(token) > 2:
            val = token[2:].strip()
            if val.isdigit() and int(val) > 0:
                return int(val)
    return None


def get_worker_count():
    # Prefer explicit environment variables when set by deployment scripts.
    for env_name in ('GUNICORN_WORKERS', 'WEB_CONCURRENCY', 'WORKERS'):
        val = os.getenv(env_name, '').strip()
        if val.isdigit() and int(val) > 0:
            return int(val)

    # Fallback to parsing gunicorn command arguments if present.
    parsed = _parse_workers_from_gunicorn_args(os.getenv('GUNICORN_CMD_ARGS', ''))
    if parsed:
        return parsed

    # Django runserver/dev environments are effectively single-worker processes.
    return 1


def get_platform_info():
    processor = (platform.processor() or '').strip()
    if not processor:
        # Windows may return an empty processor string; fall back to machine/architecture.
        processor = platform.machine() or 'Unknown'
    return {
        'system': platform.system(),
        'processor': processor,
    }
