# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""
Base settings to build other settings files upon.
"""

import logging

import qenv

NOTE_LEVEL = 35
print(f"Reading {__file__} ...")


def _note(self, message, *args, **kwargs):
    if self.isEnabledFor(NOTE_LEVEL):
        self._log(NOTE_LEVEL, message, args, **kwargs)


def install_note_level():
    # Avoid re-registering during reloads.
    if getattr(logging, "NOTE", None) == NOTE_LEVEL and hasattr(logging.Logger, "note"):
        return

    logging.NOTE = NOTE_LEVEL
    logging.addLevelName(NOTE_LEVEL, "NOTE")
    logging.Logger.note = _note


install_note_level()

ROOT_DIR = qenv.ROOT_DIR
PROJ_DIR = qenv.PROJ_DIR
APP_DIR = qenv.APP_DIR
env = qenv.read_env_file()

# GENERAL
# ------------------------------------------------------------------------------
# Local time zone. Choices are
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# though not all of them may be available with every OS.
# In Windows, this must be set to your system time zone.
TIME_ZONE = "UTC"
# https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = "en-us"
# https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1
# https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True
# https://docs.djangoproject.com/en/dev/ref/settings/#locale-paths
LOCALE_PATHS = [ROOT_DIR.path("locale")]

# URLS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#root-urlconf
ROOT_URLCONF = "config.urls"
# https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
# WSGI_APPLICATION = "config.wsgi.application"

# APPS
# ------------------------------------------------------------------------------
LOCAL_APPS = [
    "qsite.users.apps.UsersConfig",
    # Your stuff: custom apps go here
    "catalog",
    "calc",  # Must come before DJANGO_APPS so custom management commands (runserver) are discovered first
    "qedit.apps.QeditConfig",
]

DJANGO_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    "corsheaders",
    "django.contrib.sitemaps",
]
THIRD_PARTY_APPS = [
    "crispy_forms",  # not used in qcalc but used for user mgmt
    "crispy_bootstrap4",  # not used in qcalc but used for user mgmt
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "rest_framework",
    "django_htmx",
    'django_select2',
]

# https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = LOCAL_APPS + DJANGO_APPS + THIRD_PARTY_APPS

# MIGRATIONS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#migration-modules
MIGRATION_MODULES = {"sites": "qsite.contrib.sites.migrations"}

# AUTHENTICATION
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-user-model
AUTH_USER_MODEL = "users.User"
# https://docs.djangoproject.com/en/dev/ref/settings/#login-redirect-url
LOGIN_REDIRECT_URL = "users:redirect"
# https://docs.djangoproject.com/en/dev/ref/settings/#login-url
LOGIN_URL = "account_login"

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = [
    # https://docs.djangoproject.com/en/dev/topics/auth/passwords/#using-argon2-with-django
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

# MIDDLEWARE
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#middleware
MIDDLEWARE = [
    'qsite.middleware.IgnoreDisallowedHostMiddleware',
    "django.middleware.security.SecurityMiddleware",
    # 'whitenoise.middleware.WhiteNoiseMiddleware',
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.common.BrokenLinkEmailsMiddleware",
    # "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "allauth.account.middleware.AccountMiddleware",  # dj5
    # Add qcalc middleware after the session and authentication middleware
    'qsite.middleware.CalcMiddleware',
]

# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-httponly
# SESSION_COOKIE_HTTPONLY = True # commented deb@07.04.2024, to allow CORS?
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-httponly
# CSRF_COOKIE_HTTPONLY = True # commented deb@07.04.2024, to allow CORS?
CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1']  #
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-browser-xss-filter
# SECURE_BROWSER_XSS_FILTER = True # commented deb@07.04.2024, to allow CORS?
# https://docs.djangoproject.com/en/dev/ref/settings/#x-frame-options
# X_FRAME_OPTIONS = "DENY" # deb@07.04.2024 to allow CORS
# X_FRAME_OPTIONS = "SAMEORIGIN" # deb@07.04.2024 to allow CORS
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CSRF_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_SECURE = True

# STATIC
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = str(ROOT_DIR("staticfiles"))
# https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = "/static/"
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = [
    str(APP_DIR.path("static")),
    str(ROOT_DIR.path("calculators", "static")),
    str(PROJ_DIR.path("qcalc_res")),
]
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# MEDIA
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = str(APP_DIR("media"))
# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "/media/"

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        # https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # "APP_DIRS": True,
        # https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
        "DIRS": [str(APP_DIR.path("templates"))],
        "OPTIONS": {
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
            # https://docs.djangoproject.com/en/dev/ref/templates/api/#loader-types
            # "loaders": [
            #     "django.template.loaders.filesystem.Loader",
            #     "django.template.loaders.app_directories.Loader",
            # ],
            "loaders": [
                (
                    "django.template.loaders.cached.Loader",
                    [
                        "django.template.loaders.filesystem.Loader",
                        "django.template.loaders.app_directories.Loader",
                    ],
                ),
            ],
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "qsite.utils.context_processors.settings_context",
                "qsite.utils.context_processors.allauth_common_context",
            ],
        },
    }
]
# http://django-crispy-forms.readthedocs.io/en/latest/install.html#template-packs
CRISPY_TEMPLATE_PACK = "bootstrap4"

# FIXTURES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#fixture-dirs
# FIXTURE_DIRS = (str(APPS_DIR.path("fixtures")),)  # not used

# EMAIL
# ------------------------------------------------------------------------------
EMAIL_BACKEND = env("DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = env("DJANGO_EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("DJANGO_EMAIL_PORT", default=587)  # Common port for SMTP
EMAIL_USE_TLS = env.bool("DJANGO_EMAIL_USE_TLS", default=True)  # Use TLS
EMAIL_HOST_USER = env("DJANGO_EMAIL_HOST_USER", default='contact@qcalc.org')
EMAIL_HOST_PASSWORD = env("DJANGO_EMAIL_HOST_PASSWORD", default='')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
CONTACT_EMAIL = EMAIL_HOST_USER
# SERVER_EMAIL = env("DJANGO_SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)
# EMAIL_SUBJECT_PREFIX = env("DJANGO_EMAIL_SUBJECT_PREFIX", default="[qCalc]")
# EMAIL_TIMEOUT = 5

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL.
ADMIN_URL = "admin/"
# https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = [("qCalc Admin", CONTACT_EMAIL)]
# https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS

# LOGGING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
# See https://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
# Level 10: DEBUG: Low level system information for debugging purposes
# Level 20: INFO: General system information
# Level 30: WARNING: Information describing a minor problem that has occurred.
# Level 35: NOTE: Information describing a noteworthy event that has occurred. (customized at the start of this file)
# Level 40: ERROR/EXCEPTION: Information describing a major problem that has occurred.
# Level 50: CRITICAL: Information describing a critical problem that has occurred.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        }
    },
    "formatters": {
        "verbose": {
            "format": "{asctime} {levelname} {name}: {message}",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "style": "{",
        }
    },
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "rotating_file": {
            "level": "WARNING",  # "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": env("DJANGO_LOG_FILE", default=str(PROJ_DIR.path(".local/log/qcalc/qcalc.log"))),
            "maxBytes": 2000000,
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "rotating_file"],
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": True,
        },
        "django.security.DisallowedHost": {
            "handlers": [],
            "propagate": False,
        },
    },
}

# django-allauth
# ------------------------------------------------------------------------------
ACCOUNT_ALLOW_REGISTRATION = env.bool("DJANGO_ACCOUNT_ALLOW_REGISTRATION", True)
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_AUTHENTICATION_METHOD = "username"
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_NOTIFICATIONS = True
ACCOUNT_PASSWORD_RESET_ENABLED = env.bool("DJANGO_ACCOUNT_PASSWORD_RESET_ENABLED", True)
ACCOUNT_UNIQUE_EMAIL = True
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_ADAPTER = "qsite.users.adapters.AccountAdapter"
# https://django-allauth.readthedocs.io/en/latest/configuration.html
SOCIALACCOUNT_ADAPTER = "qsite.users.adapters.SocialAccountAdapter"

# Your stuff...
# ------------------------------------------------------------------------------
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000  # deafult is 1000

# HINT: Configure the DEFAULT_AUTO_FIELD setting or
# the CalcConfig.default_auto_field attribute to point to a subclass of AutoField
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'  # for Django v3.2

# files smaller than 2.5MB are handled with MemoryFileUploadHandler by default
# But qcalc only use TemporaryFileUploadHandler for file uploads
# FILE_UPLOAD_HANDLERS = (
#     'django.core.files.uploadhandler.MemoryFileUploadHandler',
#     'django.core.files.uploadhandler.TemporaryFileUploadHandler',
# )

# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env.bool("DJANGO_DEBUG", False)
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env("DJANGO_SECRET_KEY", default=env.NOTSET)

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
DJANGO_EMAIL_BACKEND = env("DJANGO_EMAIL_BACKEND", default=env.NOTSET)

# DATABASES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

DB_ENGINE = env("DB_ENGINE", default=env.NOTSET)
DB_NAME = env("DB_NAME", default=env.NOTSET)
DB_USER = env("DB_USER", default="qcalc")
DB_PASSWORD = env("DB_PASSWORD", default="qcalc")
DB_HOST = env("DB_HOST", default="localhost")
DB_PORT = env("DB_PORT", default="3306")

DATABASES = {
    "default": {
        'ENGINE': DB_ENGINE,
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
    },
}
DATABASES["default"]["ATOMIC_REQUESTS"] = True

FILE_UPLOAD_TEMP_DIR = str(env("FILE_UPLOAD_TEMP_DIR", default=env.NOTSET)).replace("{PROJ_DIR}", str(PROJ_DIR))
JSON_FILES_DIR = str(env("JSON_FILES_DIR", default=env.NOTSET)).replace("{PROJ_DIR}", str(PROJ_DIR))
HELP_FILES_DIR = str(env("HELP_FILES_DIR", default=env.NOTSET)).replace("{PROJ_DIR}", str(PROJ_DIR))
DOCS_FILES_DIR = str(env("DOCS_FILES_DIR", default=env.NOTSET)).replace("{PROJ_DIR}", str(PROJ_DIR))
AI_MODELS_DIR = str(env("AI_MODELS_DIR", default=env.NOTSET)).replace("{PROJ_DIR}", str(PROJ_DIR))
TEMPLATES[0]["DIRS"] += [HELP_FILES_DIR, DOCS_FILES_DIR]

# API keys
FIXER_API_KEY = env("FIXER_API_KEY", default="")
FIXER_API_URL = env("FIXER_API_URL", default="")

OPENAI_API_KEY = env("OPENAI_API_KEY", default="")

OPENW_API_KEY = env("OPENW_API_KEY", default="")
OPENW_API_URL = env("OPENW_API_URL", default="")

PIP_INSTALL = env("PIP_INSTALL", default="")
PIP_UNINSTALL = env("PIP_UNINSTALL", default="")

# deb@23.07.26
MEMCACHE_HOST = env("MEMCACHE_HOST", default="127.0.0.1")
MEMCACHE_PORT = env("MEMCACHE_PORT", default="11211")

# deb@18.11.23
REDIS_HOST = env("REDIS_HOST", default="127.0.0.1")
REDIS_PORT = env("REDIS_PORT", default="6379")
REDIS_DB = int(env("REDIS_DB", default="0"))
REDIS_PUBSUB = env("REDIS_PUBSUB", default="1")

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
CACHES = {
    "locmem": {  # | not tested
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "TIMEOUT": None,  # timeout INFINITE
    },
    "locmem_schema": {  # | not tested
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "TIMEOUT": None,  # timeout INFINITE
    },
    "file": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": str(ROOT_DIR.path("../.cache", "django_sessions")),
        "TIMEOUT": 3600,  # 1-hour session cache
        "OPTIONS": {
            "MAX_ENTRIES": 10000,
            "CULL_FREQUENCY": 3,
        },
    },
    "file_schema": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": str(ROOT_DIR.path("../.cache", "django_schema")),
        "TIMEOUT": None,  # infinite schema cache
        "OPTIONS": {
            "MAX_ENTRIES": 10000,
            "CULL_FREQUENCY": 3,
        },
    },
    "memcached": {
        "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
        "LOCATION": f"{MEMCACHE_HOST}:{MEMCACHE_PORT}",  # '127.0.0.1:11211',
        "TIMEOUT": 3600,  # 1 hour
    },
    "memcached_schema": {
        "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
        "LOCATION": f"{MEMCACHE_HOST}:{MEMCACHE_PORT}",  # '127.0.0.1:11211',
        "TIMEOUT": None,  # timeout INFINITE
        "KEY_PREFIX": 'schema',
    },
    'redis': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}',  # 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            "TIMEOUT": 3600,  # 1 hour
        },
    },
    'redis_schema': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}',  # 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
    },
    # "select2": {
    #     "BACKEND": "django_redis.cache.RedisCache",
    #     "LOCATION": "redis://127.0.0.1:6379/2",
    #     "OPTIONS": {
    #         "CLIENT_CLASS": "django_redis.client.DefaultClient",
    #     }
    # },
}

DEFAULT_CACHE_ALIAS = env("DEFAULT_CACHE_ALIAS", default=env.NOTSET)  # | locmem, memcached, redis
CACHES["default"] = CACHES[DEFAULT_CACHE_ALIAS]

# SERVER OPTION
# SESSION CACHE WITH LIMITED TIMEOUT default 300 sec, specified 3600 sec
SESSION_CACHE_ALIAS = DEFAULT_CACHE_ALIAS
# SCHEMA CACHE with INFINITE TIMEOUT
QSCHEMA_CACHE_ALIAS = f'{DEFAULT_CACHE_ALIAS}_schema'

# Tell select2 which cache configuration to use:
# SELECT2_CACHE_BACKEND = "select2"
SELECT2_CACHE_BACKEND = DEFAULT_CACHE_ALIAS

QCALC_SCHEME = env("QCALC_SCHEME", default='http')
QCALC_DOMAIN = env("QCALC_DOMAIN", default="127.0.0.1:8000")

# Split the domain string at the colon
domain_parts = QCALC_DOMAIN.split(':')
QCALC_PORT = domain_parts[1] if len(domain_parts) > 1 else ""
QCALC_HOST = domain_parts[0].replace("www.", "")

# ==========================================
# Dynamic Host and CSRF Configuration
# ==========================================
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts


ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]
CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1",
    "http://localhost",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]

# 1. Populate ALLOWED_HOSTS (Strictly domain names, NO protocols/ports)
if QCALC_HOST not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(QCALC_HOST)

# Only add www. prefix if it's a domain name (not an IP address like 127.0.0.1)
if not QCALC_HOST.replace('.', '').isdigit():
    www_host = f"www.{QCALC_HOST}"
    if www_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(www_host)

# 2. Populate CSRF_TRUSTED_ORIGINS (Requires protocol + host + port if exists)
if QCALC_PORT:
    base_origin = f"{QCALC_SCHEME}://{QCALC_HOST}:{QCALC_PORT}"
    if base_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(base_origin)
else:
    # Standard production URL (no ports)
    base_origin = f"{QCALC_SCHEME}://{QCALC_HOST}"
    if base_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(base_origin)

    # Add www version for production domains
    if not QCALC_HOST.replace('.', '').isdigit():
        www_origin = f"{QCALC_SCHEME}://www.{QCALC_HOST}"
        if www_origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(www_origin)

# deb@22.08.26
ACCOUNT_FORMS = {
    'signup': 'qsite.users.forms.CustomSignupForm',
}
