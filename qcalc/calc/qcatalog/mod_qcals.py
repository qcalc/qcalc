# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qutil import variable_to_title, TreeNode, \
    QThread, create_category_node, user_name, fid2owner, fid_separator
from qvars import qc_gpref as gs, qfunc_info
import bisect
from ..mod_cache import QMeta, QMyCal
from ..mod_sandbox import CalcSandbox
from .mod_catalog_build import CatalogBuilder
from .mod_pubcals import PubCals
import qconst

import logging

logger = logging.getLogger(__name__)


class QCals:
    catalog_name: str

    qfunc_dict: dict  # dict of qfunction names and addresses
    qc_dict: dict  # dict of qcalc names and packages (calculators)
    qctg_dict: dict  # dict of qcalc package and category names
    qc_list: list  # sorted list of keys from qc_dict (calculators)
    calc_root: TreeNode

    qc_admin_list: list  # sorted list of admin function names, not serach engine indexable
    qc_demo_list: list  # sorted list of demo function names, not serach engine indexable
    qc_user_list: list  # sorted list of user function names, serach engine indexable

    catalog_version: int = 0  # bumped whenever a catalog tree changes, invalidates rendered catalog fragments

    @classmethod
    def bump_catalog_version(cls):
        cls.catalog_version += 1

    @classmethod
    def func_exists(cls, func_id, scope='qpots'):
        request = QThread.get_req()
        if func_id in cls.qfunc_dict and 'q' in scope:
            return True
        elif request and 'o' in scope:  # request is None when creating catalog
            return func_id in request.ufunc_dict
        elif 'p' in scope:
            return func_id in PubCals.func_dict
        else:
            return False

    @classmethod
    def addr(cls, func_id, scope='qpots'):
        # q=qcalc, p=public, o=owncal, t=token, s=shared (qpots)
        request = QThread.get_req()  # request is None when creating catalog
        faddr = None
        if request: request.is_public = True

        if 'q' in scope:  # | qcalc standard functions (q)
            faddr = cls.qfunc_dict.get(func_id, None)
            if faddr:
                return faddr

        if not faddr and 'p' in scope:  # | public functions by self and others (p)
            faddr = PubCals.addr(func_id)
            if faddr:
                return faddr

        if not faddr and request and 'o' in scope:  # | own functions (o)
            if func_id not in request.ufunc_dict:
                cal_id = func_id.split('__')[0]
                _ = cls._load_cal(request, cal_id, QMyCal.getp1(cal_id, ''),
                                  'load-user-cal', user_name(request), 'created')
                # logger.debug('~user f', f'{func_id} loaded')
            faddr = request.ufunc_dict.get(func_id, None)
            if faddr:
                # logger.debug('~user f', f'{func_id} found')
                request.is_public = False
                return faddr

        if not faddr and request and request.token and 't' in scope:  # | shared functions by others with token (t)
            # logger.debug('~token', request.token)
            if func_id not in request.ufunc_dict:
                cal_id, cal_name, owner = fid2owner(func_id)
                _ = cls._load_cal(request, cal_id, QMyCal.getp1_from_token(cal_id, request.token),
                                  'load-token-cal', owner, 'shared')
                # logger.debug('~token f', f'{func_id} loaded')
            faddr = request.ufunc_dict.get(func_id, None)
            if faddr:
                # logger.debug('~token f', f'{func_id} found')
                request.is_public = False
                return faddr

        if not faddr and request and 's' in scope:  # | shared functions by others (s)
            cal_id, cal_name, cal_owner = fid2owner(func_id)
            cur_user = user_name(request)
            if cal_owner != '':  # and request.variant >= 0:  # | shared functions 0=w/o token, >0=curuser's variant
                if func_id not in request.ufunc_dict:
                    _ = cls._load_cal(request, cal_id, QMyCal.getp1_from_owner(cal_id, cal_owner, cur_user),
                                      'load-other-cal', cal_owner, 'shared')
                    # logger.debug('~oth f', f'{func_id} loaded')
                faddr = request.ufunc_dict.get(func_id, None)
                if faddr:
                    # logger.debug('~oth f', f'{func_id} found')
                    request.is_public = False
                    return faddr

        return faddr

    @classmethod
    def quick_find_func(cls, sfname_part, scope='qpots'):
        request = QThread.get_req()

        def find_in_list(item_list, part):
            # | lists are sorted by str.lower, so the search ignores case and returns the id as stored
            part = part.lower()
            idx = bisect.bisect_left(item_list, part, key=str.lower)
            if idx < len(item_list):
                item = item_list[idx].lower()
                if item == part:
                    return item_list[idx]
                elif item.startswith(part):
                    nxt = item_list[idx + 1].lower() if idx + 1 < len(item_list) else ''
                    # | a user calculator id is <name>-<owner>, so its name alone is an exact match
                    # | unless the next id has the same name (e.g. shared by two owners)
                    if item.partition(fid_separator)[0] == part and nxt.partition(fid_separator)[0] != part:
                        return item_list[idx]
                    if nxt.startswith(part):
                        return 2  # Multiple matches
                    return item_list[idx]
            return 0

        if sfname_part.endswith('.'):
            sfname_part = sfname_part[:-1]
        elif 'q' in scope:
            result = find_in_list(cls.qc_list, sfname_part)
            if result != 0:
                return None if result == 2 else result

        # not found in qcalc list, so search ucal list
        if request and 'o' in scope:
            uc_list = QMeta.getp1('uc_list', [])
            result = find_in_list(uc_list, sfname_part)
            if result != 0:
                return None if result == 2 else result

        # not found in qcalc and ucal list, so search scal list
        if request:
            sc_list = QMeta.getp1('sc_list', [])
            result = find_in_list(sc_list, sfname_part)
            if result != 0:
                return None if result == 2 else result

        if request:
            result = find_in_list(PubCals.cal_list, sfname_part)
            if result != 0:
                return None if result == 2 else result

        return None

    @classmethod
    def _load_cal(cls, request, cal_id, code, scope, owner, package_name) -> bool:
        if not code:
            return False
        local_dict = CalcSandbox.exec_with_context(code, scope=scope, username=owner, item_id=cal_id)
        CatalogBuilder.build_func_dict(local_dict.items(), owner, package_name, request.ufunc_dict)
        return True

    @classmethod
    def cnode(cls, sfunc_id):
        return cls.calc_root.get_node_by_id(sfunc_id)

    @classmethod
    def internals(cls):  # internal functions to support calculators
        return [x for x in cls.qfunc_dict if x not in cls.qc_list and '__' not in x]

    @classmethod
    def package_contents(cls, package_name, catalog_name='', extend=False):
        if not extend:
            cls.qfunc_dict = {}  # dict of qfunction names and addresses (functions)
            cls.qc_dict = {}  # dict of qcalc names and packages (calculators)
            cls.qctg_dict = {}  # dict of qcalc package and category names
            cls.qc_list = []  # sorted list of keys from qc_dict (calculators)

        catalog_name = package_name.split('.')[-1] if catalog_name == '' else catalog_name
        CatalogBuilder.scan_package(package_name, catalog_name, cls.qfunc_dict, cls.qc_dict, cls.qctg_dict)
        cls.qc_list[:] = cls.qc_dict.keys()
        cls.qc_list.sort(key=str.lower)

    @classmethod
    def create_catalog_calc(cls):
        cls.qc_admin_list = []
        cls.qc_demo_list = []
        cls.qc_user_list = []
        TreeNode.setup(qconst.admin_name, qconst.demo_name, qconst.personal_name)
        cls.calc_root = create_category_node('calculators', 'calculators', 'Cals')

        def classify(func_node):
            if 'A' in func_node.flags: cls.qc_admin_list.append(func_node.id)
            if 'D' in func_node.flags: cls.qc_demo_list.append(func_node.id)
            if 'A' not in func_node.flags and 'D' not in func_node.flags:
                cls.qc_user_list.append(func_node.id)

        CatalogBuilder.populate(cls.calc_root, cls.qctg_dict, cls.qc_dict, cls.func_title_desc_tags, 'q',
                                on_leaf=classify)
        cls.qc_admin_list.sort()
        cls.qc_demo_list.sort()
        cls.qc_user_list.sort()
        cls.calc_root.update_all_descendant_leafs_count()
        cls.calc_root.sort_by()
        cls.bump_catalog_version()
        # calc_root.save_tree_to_json("all.json")

        # | symbols exclude admin and test calculators (deb@05.09.24)
        CalcSandbox.build_symbols(cls.qfunc_dict, set(cls.qc_admin_list).union(cls.qc_demo_list))

    @classmethod
    def func_title_desc_tags(cls, sfunc, scope='qpots'):
        func_info = cls.run_func_info(sfunc, scope)
        if 'title' in func_info:
            title = func_info['title']
        else:
            title = 'Calculate ' + variable_to_title(sfunc)

        if 'desc' in func_info:
            desc = func_info['desc']
        else:
            desc = title

        tags = func_info.get('tags', '')
        return title, desc, tags

    @classmethod
    def run_func_info(cls, func_id, scope='qpots'):
        try:
            fninfo = cls.addr(func_id + "__info", scope)
            func_info_from_func_def = fninfo()
            func_info_from_jsonfile = qfunc_info.get(func_id, {})
            func_info_from_func_def.update(func_info_from_jsonfile)
        except Exception as e:
            if gs['demo_mode']:
                func_info_from_func_def = {
                    'title': f'Calculate {variable_to_title(func_id)} - Demo',
                    'desc': str(e)  # e is an error object
                }
            else:
                e.args = (f'Error (RFI): {func_id} may not be compatible',)
                raise e

        return func_info_from_func_def


if __name__ == "__main__":
    import qsett

    # QCals.package_contents('calc.all')
    QCals.package_contents('calculators.all.fun')
    print(QCals.qfunc_dict)
    print(QCals.qc_dict)
    print(QCals.qctg_dict)
    print(QCals.qc_list)
