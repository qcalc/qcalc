from .conflicts import *
from .mod_cache import QMem, QPref, QCache, QTemp, QKeep, QSave, QIO, QData, QRam, QMeta, QFav
from .mod_cutil import valid_numq, ancestors, get_help_path, get_fhelp
from .mod_db import QInput
from .mod_fchart import *
from .mod_head import *
from .mod_init import *
# mfunc
from .mod_openai import *
from .mod_qcals import QCals
# mod_qcals_security
from .mod_qlist import *
from .mod_redis import *
from .mod_redis_act import *
from .mod_result import result_values
from .mod_ucals import UCals
from .mod_whoosh import QSearch, print_search_result, search_result_nodes

import os
import signal
import logging
from qcalc_api import pylib_dict

logger = logging.getLogger(__name__)


def _shutdown_current_process(exit_code=1):
    """Request a process-level shutdown even when called from a worker thread."""
    try:
        os.kill(os.getpid(), signal.SIGTERM)
    except Exception:
        # Hard fallback when signal delivery is unavailable.
        os._exit(exit_code)


def create_standard_cataog_from_packages():
    # UCals.initialize()
    QCals.package_contents('calculators.all', 'all', extend=False)
    # | use extend=false only once
    # QCals.qfunc_dict.update(dict(inspect.getmembers(math, inspect.isbuiltin)))  # ok but covered by asteval
    QCals.qfunc_dict.update(pylib_dict)  # ok

    # | Extend Ctalog : Add Pacakge
    QCals.package_contents('calculators.ext', 'ext', extend=True)
    # | use extend=false only once, admin_name = catalg_name+name_separator+admin_folder, demo_name=<same rule>
    QCals.create_catalog_calc()

    QCals.create_catalog_qty()
    logger.info(f'*** Standard Catalog Created')


def create_public_catalog_from_db():
    QCals.package_contents_public()
    QCals.create_catalog_calc_public()
    logger.info(f'*** Public Catalog Created')


def build_search_index():
    QSearch('m', True)


def w2_initialize_py_catalog_once_per_worker():
    create_standard_cataog_from_packages()  # | Read python modules
    logger.info(f'*** STAGE W.2: w2_initialize_py_catalog_once_per_worker() completed')


def w3_initialize_db_catalog_once_per_worker():
    # accessing the database during app initialization is discouraged
    # avoid executing queries in AppConfig.ready()
    if not StdList.initialized:
        StdList.w1_prepare_lists_once_per_worker()
    if not hasattr(QCals, 'calc_root'):
        w2_initialize_py_catalog_once_per_worker()
    create_public_catalog_from_db()  # | Accessing the database
    build_search_index()  # | based on both pacakage based and db based catalog
    get_super_user()  # | Accessing the database
    logger.info(f'*** STAGE W.3: w3_initialize_db_catalog_once_per_worker() completed')
