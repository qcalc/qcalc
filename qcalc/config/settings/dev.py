# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from .base import *  # noqa
from .base import env
print(f"Reading {__file__} ...")

ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_PASSWORD_RESET_ENABLED = False

QCALC_PROFILING = env("QCALC_PROFILING", default='none')  # silk
if QCALC_PROFILING == 'toolbar':
    # pip install django-debug-toolbar==4.2.0
    INSTALLED_APPS += ["debug_toolbar"]  # noqa F405
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa F405
    # https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
    DEBUG_TOOLBAR_CONFIG = {
        "DISABLE_PANELS": ["debug_toolbar.panels.redirects.RedirectsPanel"],
        "SHOW_TEMPLATE_CONTEXT": True,
    }
    # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips
    INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]
elif QCALC_PROFILING == 'pyinst':
    # pip install pyinstrument==4.6.2
    MIDDLEWARE += ["pyinstrument.middleware.ProfilerMiddleware"]  # noqa F405
elif QCALC_PROFILING == 'cprofile':
    # pip install django-cprofile-middleware==1.0.5
    MIDDLEWARE += ["django_cprofile_middleware.middleware.ProfilerMiddleware"]  # noqa F405
    DJANGO_CPROFILE_MIDDLEWARE_REQUIRE_STAFF = False
elif QCALC_PROFILING == 'silk':
    #pip install django-silk==5.1.0
    INSTALLED_APPS += ["silk"]  # noqa F405
    MIDDLEWARE += ["silk.middleware.SilkyMiddleware"]
    SILKY_PYTHON_PROFILER = True
    # SILKY_PYTHON_PROFILER_BINARY = True
    SILKY_META = True
    SILKY_DYNAMIC_PROFILING = [
        # {'module': 'calc.view_form_data', 'function': 'q11421_get_extra_form_data_posted'},
        # {'module': 'calc.view_form_data', 'function': 'q11422_form_data_modify_after_post'},
        # {'module': 'calc.view_form_data', 'function': 'q11429_func_to_form_schema'},
        # {'module': 'calc.view_form_data', 'function': 'q11440b_get_saved_io'},
        # {'module': 'calc.view_form_data', 'function': 'q11441_data_for_function'},
        # {'module': 'calc.view_form_data', 'function': 'q11442_func_call_by_name'},
        # {'module': 'calc.view_form_data', 'function': 'q11449_form_data_postprocess_and_run'},
        # {'module': 'calc.view_form_data', 'function': 'q11461_create_dynaform_class'},
        # {'module': 'calc.view_form_data', 'function': 'q11469_form_data_create_dynaform_and_fill'},
        # {'module': 'calc.view_form_data', 'function': 'schema_type_initial_class'},
        # {'module': 'calc.views2', 'function': 'q1_add_func'},
        # {'module': 'calc.views2', 'function': 'q1_add_func_help'},
        # {'module': 'calc.views2', 'function': 'q1_add_func_qhelp'},
        # {'module': 'calc.views2', 'function': 'q1_create_func_help'},
        # {'module': 'calc.views2', 'function': 'q1_func_to_form_core'},
        # {'module': 'calc.views2', 'function': 'q1_open_func'},
        # {'module': 'calc.views2', 'function': 'q1_render'},
        # {'module': 'calc.views2', 'function': 'q1_run_func'},
        # {'module': 'calc.views2', 'function': 'q1_step2'},
        # {'module': 'calc.views2', 'function': 'q1119_urlpath_to_func_args'},
        # {'module': 'calc.views2', 'function': 'q1129_is_func_authorised'},
        # {'module': 'calc.views2', 'function': 'q1141_read_func_meta'},
        # {'module': 'calc.views2', 'function': 'q1143_create_form_layout'},
        # {'module': 'calc.views2', 'function': 'q1145_result_to_form_schema'},
        # {'module': 'calc.views2', 'function': 'q1146_result_transfer'},
        # {'module': 'calc.views2', 'function': 'q1149_func_to_form_context'},
        # {'module': 'calc.views2', 'function': 'q1199_func_to_form_common'},
        # {'module': 'calc.views2', 'function': 'q1199_func_to_form_part'},
        # {'module': 'calc.views2', 'function': 'q1999_func_to_form'},
        {'module': 'qcore.PhysicalQuantities', 'function': 'MeasureQuantity.__init__'},
        {'module': 'qcore.PhysicalQuantities', 'function': 'MeasureUnit.__init__'},
    ]

# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [
    "localhost",
    "0.0.0.0",
    "127.0.0.1",
    "testserver",
]

host = QCALC_HOST
if host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(host)
