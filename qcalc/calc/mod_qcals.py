# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import importlib.util
from importlib import import_module
from pathlib import Path
import os
import inspect
import threading
from qutil import variable_to_title, TreeNode, \
    preprocess_expression, QThread, create_category_node, \
    joinx, names2fid, user_name, fid2owner
from qvars import qc_gpref as gs, qfunc_info, qty_info, unit_info
import bisect
from .mod_redis import redis_publish_action
from qcore import _unit_table, Qty, _base_categories, _unit_tree, _unit_info, \
    unit_short_desc, _base_categ_d2s, _qty_tree, _qty_info, lmt_title, dim_to_bname, _base_names
from asteval import make_symbol_table
from .mod_qcals_security import safe_execute
from .mod_cache import QMeta, QMyCal
import qconst
import qcalc_api

import logging

logger = logging.getLogger(__name__)


class QCals:
    qfunc_dict: dict  # dict of qfunction names and addresses
    qc_dict: dict  # dict of qcalc names and packages (calculators)
    qctg_dict: dict  # dict of qcalc package and category names
    qc_list: list  # sorted list of keys from qc_dict (calculators)

    qc_admin_list: list  # sorted list of admin function names, not serach engine indexable
    qc_demo_list: list  # sorted list of demo function names, not serach engine indexable
    qc_user_list: list  # sorted list of user function names, serach engine indexable
    calc_root: TreeNode
    catalog_name: str
    qsymbol_dict: dict  # dict of qfunction names/addresses plus uoms/Qty plus py/asteval syms
    qty_root: TreeNode

    pfunc_dict: dict = {}  # dict of public function names and addresses
    pc_dict: dict = {} # dict of public function names and packages (calculators)
    pctg_dict: dict = {} # dict of public package and category names
    pc_list: list = []  # sorted list of keys from pfunc_dict (calculators)

    pcalc_root: TreeNode
    _registry_lock = threading.RLock()

    @classmethod
    def func_exists(cls, func_id, scope='qpots'):
        request = QThread.get_req()
        if func_id in cls.qfunc_dict and 'q' in scope:
            return True
        elif request and 'o' in scope:  # request is None when creating catalog
            return func_id in request.ufunc_dict
        elif 'p' in scope:
            return func_id in cls.pfunc_dict
        else:
            return False

    @classmethod
    def calc_exists(cls, calc_id, scope='qpots'):
        request = QThread.get_req()
        if calc_id in cls.qc_list and 'q' in scope:
            return True
        elif request and 'o' in scope:  # request is None when creating catalog
            return calc_id in QMeta.getp1('uc_list', [])
        elif 'p' in scope:
            return calc_id in cls.pc_list
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
            cal_id, cal_name, cal_owner = fid2owner(func_id)
            if cal_owner != '':
                with cls._registry_lock:
                    faddr = cls.pfunc_dict.get(func_id, None)
                    cal_loaded = cal_id in cls.pc_list

                if not faddr:
                    _ = cls._load_public_cal(func_id, cal_owner)
                    # logger.debug('~pcl f', f'{func_id} loaded')
                    with cls._registry_lock:
                        faddr = cls.pfunc_dict.get(func_id, None)
                        cal_loaded = cal_id in cls.pc_list

                if faddr and cal_loaded:
                    # logger.debug('~pcl f', f'{func_id} found')
                    if request: request.is_public = True  # | request is None during catalog creation
                    return faddr

        if not faddr and request and 'o' in scope:  # | own functions (o)
            if func_id not in request.ufunc_dict:
                _ = cls._load_user_cal(request, func_id)
                # logger.debug('~user f', f'{func_id} loaded')
            faddr = request.ufunc_dict.get(func_id, None)
            if faddr:
                # logger.debug('~user f', f'{func_id} found')
                request.is_public = False
                return faddr

        if not faddr and request and request.token and 't' in scope:  # | shared functions by others with token (t)
            # logger.debug('~token', request.token)
            if func_id not in request.ufunc_dict:
                _ = cls._load_token_cal(request, func_id, token=request.token)
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
                    _ = cls._load_other_cal(request, func_id, cal_owner, cur_user)
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
            idx = bisect.bisect_left(item_list, part)
            if idx < len(item_list):
                if item_list[idx] == part:
                    return item_list[idx]
                elif item_list[idx].startswith(part):
                    if idx + 1 < len(item_list) and item_list[idx + 1].startswith(part):
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
            result = find_in_list(cls.pc_list, sfname_part)
            if result != 0:
                return None if result == 2 else result

        return None

    @classmethod
    def _load_user_cal(cls, request, func_id, silent=True) -> bool:
        cal_id = func_id.split('__')[0]
        code = QMyCal.getp1(cal_id, '')
        if not code:
            if silent:
                return False
            else:
                raise Exception(f'Error (LUC): Calculator {cal_id} not found')
        local_dict = cls.safe_exec(code)
        catalog = user_name(request)
        package_name = 'created'
        cls.build_func_dict(local_dict.items(), catalog, package_name, request.ufunc_dict, None)
        return True

    @classmethod
    def _load_token_cal(cls, request, func_id, silent=True, token='') -> bool:
        cal_id, cal_name, owner = fid2owner(func_id)
        code = QMyCal.getp1_from_token(cal_id, token)
        if not code:
            if silent:
                return False
            else:
                raise Exception(f'Error (LUC): Calculator {cal_id} not found')
        local_dict = cls.safe_exec(code)
        catalog = owner
        package_name = 'shared'
        cls.build_func_dict(local_dict.items(), catalog, package_name, request.ufunc_dict, None)
        return True

    @classmethod
    def _load_other_cal(cls, request, sfunc_uname, owner, curuser, silent=True) -> bool:
        cal_id = sfunc_uname.split('__')[0]
        code = QMyCal.getp1_from_owner(cal_id, owner, curuser)
        if not code:
            if silent:
                return False
            else:
                raise Exception(f'Error (LUC): Calculator {cal_id} not found')
        local_dict = cls.safe_exec(code)
        catalog = owner
        package_name = 'shared'
        cls.build_func_dict(local_dict.items(), catalog, package_name, request.ufunc_dict, None)
        return True

    @classmethod
    def update_public_cal(cls, cal_id, cal_owner, code) -> bool:
        local_dict = cls.safe_exec(code)
        package_name = f"pcals.{cal_owner}"
        catalog_name = f"{cal_owner}"
        catalog = cal_owner
        updated = False

        with cls._registry_lock:
            if package_name not in cls.pctg_dict:
                updated = True
                cls.pctg_dict[package_name] = catalog_name
                cls.add_catagories_to_node(cls.pcalc_root, catalog_name)

            cls.build_func_dict(local_dict.items(), catalog, 'public', cls.pfunc_dict, None)

            faddr = cls.pfunc_dict.get(cal_id, None)
            if faddr and cal_id not in cls.pc_list:
                updated = True
                cls.pc_list.append(cal_id)
                cls.pc_list.sort()

            node = cls.pcalc_root.get_node_by_id(cal_id)
            if not node:
                updated = True
                cls.add_pub_calc_node(cal_id)

        return updated

    @classmethod
    def delete_public_cal(cls, cal_id) -> bool:
        with cls._registry_lock:
            deleted = cls.delete_pub_calc_node(cal_id)
            if cal_id in cls.pc_list:
                cls.pc_list.remove(cal_id)
                deleted = True

            if cal_id in cls.pfunc_dict:
                _ = cls.pfunc_dict.pop(cal_id, None)
                deleted = True

            keys_to_remove = [key for key in cls.pfunc_dict if key.startswith(f"{cal_id}__")]
            for key in keys_to_remove:
                _ = cls.pfunc_dict.pop(key, None)
                deleted = True

        return deleted

    @classmethod
    def _load_public_cal(cls, sfunc_uname, owner, silent=True) -> bool:
        cal_id = sfunc_uname.split('__')[0]
        code = QMyCal.getp1_from_owner_public(cal_id, owner)
        if not code:
            if silent:
                return False
            else:
                raise Exception(f'Error (LUC): Calculator {cal_id} not found')
        # local_dict = cls.safe_exec(code)
        cls.update_public_cal(cal_id, owner, code)
        redis_publish_action(
            channel="qcalc_channel",
            action="update_public_cal",
            cal_id=cal_id,
            cal_owner=owner,
            code=code
        )
        return True

    @classmethod
    def build_func_dict(cls, func_addr_list, catalog_name, package_name, func_dict, c_dict=None):
        for fname, faddr in func_addr_list:
            if fname.endswith('__info'):
                cal_name = fname.split('__info')[0]
                cal_id = names2fid(catalog_name, cal_name)
                func_dict[f'{cal_id}__info'] = faddr
                if c_dict is not None:
                    c_dict[cal_id] = package_name
            elif '__' in fname:
                splits = fname.split('__')
                cal_id = names2fid(catalog_name, splits[0])
                func_dict[f'{cal_id}__{splits[1]}'] = faddr
            else:
                # print('c', package_name, fname)
                func_id = names2fid(catalog_name, fname)
                func_dict[func_id] = faddr

    @classmethod
    def build_func_dict2(cls, func_addr_list, catalog_name, package_name, func_dict, c_dict=None):  # not used
        for fname, faddr in func_addr_list:
            if '__' in fname:
                cal_id, sub_func = fname.split('__', 1)
                func_dict[f'{names2fid(catalog_name, cal_id)}__{sub_func}'] = faddr
                if sub_func == 'info' and c_dict is not None:
                    c_dict[cal_id] = package_name
            else:
                func_dict[names2fid(catalog_name, fname)] = faddr

    @classmethod
    def cnode(cls, sfunc_id):
        return cls.calc_root.get_node_by_id(sfunc_id)

    @classmethod
    def qnode(cls, sqty):
        return cls.qty_root.get_node_by_id(sqty)  # sqty is unique

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
        host_package_name = package_name

        def searchpath(package_name, catalog_name):
            # logger.info(f'Scanning: {package_name}')
            pkg_cat = package_name.replace(host_package_name, catalog_name)
            cls.qctg_dict[package_name] = pkg_cat

            spec = importlib.util.find_spec(package_name)
            if spec is None:
                return []
            pathname = Path(spec.origin).parent

            with os.scandir(pathname) as entries:
                for entry in entries:
                    if entry.name.startswith('__'):
                        continue
                    current_pkg = '.'.join((package_name, entry.name.partition('.')[0]))
                    if entry.is_dir():
                        searchpath(current_pkg, catalog_name)
                    elif entry.is_file():
                        if not entry.name.endswith('.py'):
                            continue
                        module = import_module(current_pkg)
                        func_address_list = inspect.getmembers(module, inspect.isfunction)
                        cls.build_func_dict(func_address_list, catalog_name, package_name, cls.qfunc_dict, cls.qc_dict)

        searchpath(package_name, catalog_name)
        cls.qc_list[:] = cls.qc_dict.keys()
        cls.qc_list.sort()

    @classmethod
    def create_catalog_calc(cls):
        cls.qc_admin_list = []
        cls.qc_demo_list = []
        cls.qc_user_list = []
        TreeNode.setup(qconst.admin_name, qconst.demo_name, qconst.personal_name)
        # cls.calc_root = TreeNode(nid='calculators', name='calculators', title='Cals', is_leaf=False, node_type='c')
        # cls.calc_root._index_node()
        cls.calc_root = create_category_node('calculators', 'calculators', 'Cals')
        for pkg, ctg in cls.qctg_dict.items():
            cur_node = cls.add_catagories_to_node(cls.calc_root, ctg)

            func_ids = [func_id for func_id, categ in cls.qc_dict.items() if categ == pkg]
            for func_id in func_ids:
                try:
                    title, desc, tags = cls.func_title_desc_tags(func_id, scope='q')
                    func_node = TreeNode(nid=func_id, name=func_id, title=title, desc=desc, tags=tags,
                                         is_leaf=True, node_type='c')
                    cur_node.add_child(func_node)
                    if 'A' in func_node.flags: cls.qc_admin_list.append(func_id)
                    if 'D' in func_node.flags: cls.qc_demo_list.append(func_id)
                    if 'A' not in func_node.flags and 'D' not in func_node.flags:
                        cls.qc_user_list.append(func_id)
                except Exception as _e:
                    # print(str(e))
                    # | func_title_desc_tags will return exception if not in demo mode, and it is a function
                    # | without __info() function
                    pass

        cls.qc_admin_list.sort()
        cls.qc_demo_list.sort()
        cls.qc_user_list.sort()
        cls.calc_root.update_all_descendant_leafs_count()
        cls.calc_root.sort_by()
        # calc_root.save_tree_to_json("all.json")

        # create and validate symbol table for eval()
        assert len(set(cls.qfunc_dict).intersection(_unit_table)) == 0
        qsyms = cls.qfunc_dict.copy()
        # deb@05.09.24 - exclude admin and test calculators from symbol list
        qsyms = {key: qsyms[key] for key in qsyms if key not in cls.qc_admin_list + cls.qc_demo_list}
        qsyms.update({k: Qty(1, v) for k, v in _unit_table.items()})
        qsyms.update({name: getattr(qcalc_api, name) for name in qcalc_api.__evaonly__})

        # | ic(set(cls.qsymbol_dict).intersection(make_symbol_table(use_numpy=False)))  # 'min'
        psyms = make_symbol_table(use_numpy=False)
        assert (len(set(qsyms).intersection(psyms)) <= 1)  # 'min'
        # | py symbols first, then qcalc symbols overriding 1 conflict
        cls.qsymbol_dict = {**psyms, **qsyms}

    @classmethod
    def create_catalog_qty(cls, admin_name='admin', demo_name='demo'):
        TreeNode.setup(admin_name, demo_name)
        cls.qty_root = TreeNode(
            nid='units', name='units', title='UoMs for Quantitites',
            desc='Units of measurement for various physical quantities',
            is_leaf=False, node_type='u'
        )
        cls.qty_root._index_node()
        node_base = TreeNode(
            nid='bases', name='bases', title='Base Quantity UoMs',
            desc='Units of measurement for 7 SI base quantities, 2 derived quantities and currency',
            is_leaf=False, node_type='u'
        )
        node_base.is_leaf = False
        cls.qty_root.add_child(node_base)

        node_comp = TreeNode(
            nid='composites', name='composites', title='Composite Quantity UoMs',
            desc='Units of measurement for physical quantities that are combinations of base quantities',
            is_leaf=False, node_type='u'
        )
        node_comp.is_leaf = False
        cls.qty_root.add_child(node_comp)

        node_obj = TreeNode(
            nid='objects', name='objects', title='Quantities of Typical Objects',
            desc='Magnitudes of the physical quantities of representative physical objects',
            is_leaf=False, node_type='q'
        )
        node_obj.is_leaf = False
        cls.qty_root.add_child(node_obj)

        for dim, categ in _base_categories.items():
            slug = _base_categ_d2s[dim]
            child = TreeNode(nid=slug, name=slug, title=categ, desc=qty_info.get(slug, {}).get('desc', ''),
                             is_leaf=False, node_type='u')
            if dim == 'C':
                cls.qty_root.add_child(child)
            elif len(dim) == 1:
                node_base.add_child(child)
            else:
                node_comp.add_child(child)

            if dim not in _unit_tree:
                _unit_tree[dim] = []

            for uname in _unit_tree[dim]:
                cur_node, flag = cls.qty_root.add_node_if_not_found(parent_id=slug, nid=uname, name=uname)
                if not cur_node:
                    logger.error(f'>>> CCQ: Error processing {uname}')
                if flag == 0:  # newly added node
                    cur_node.title = _unit_info[uname]['long_name']
                    # | unit_short_desc end with a semicolon
                    cur_node.desc = unit_short_desc(uname) + ' ' + unit_info.get(uname, {}).get('desc', '')
                    cur_node.is_leaf = True
                    cur_node.node_type = 'u'

            if len(dim) > 1:  # len(_unit_tree[dim]) == 0:
                name = dim_to_bname(dim, _base_names)
                gchild = TreeNode(nid=name, name=name,
                                  title=f'({slug} base)'.replace('-', ' '),
                                  desc=qty_info.get(slug, {}).get('desc', ''),
                                  is_leaf=True, node_type='u')
                child.add_child(gchild)

        for dim in _qty_tree:
            slug = _base_categ_d2s[dim]
            title = lmt_title(dim)
            name = f"{slug}_objects"
            child = TreeNode(nid=name, name=name, title=title,
                             desc=f"Magnitude of the \"{title}\" of representative physical objects",
                             is_leaf=False, node_type='q')
            parent = node_obj
            parent.add_child(child)

            for qname in _qty_tree[dim]:
                cur_node, flag = cls.qty_root.add_node_if_not_found(parent_id=f"{slug}_objects", nid=qname, name=qname)
                if not cur_node:
                    logger.error(f'>>> CCQ: Error processing {qname}')
                if flag == 0:  # newly added node
                    cur_node.title = _qty_info[qname]['description']
                    cur_node.desc = ''
                    # cur_node.desc = unit_short_desc(uname)+' '+unit_info.get(uname, {}).get('desc','')
                    cur_node.is_leaf = True
                    cur_node.node_type = 'q'
                    cur_node.data = dim

        cls.qty_root.update_all_descendant_leafs_count()
        cls.qty_root.sort_by()

    @classmethod
    def safe_eval(cls, qxpr, gdict=None, ldict=None):
        xpr = preprocess_expression(qxpr)
        if ldict is None:
            ldict = {}
        # | merge dictionaries doesn't involve copying overhead.
        return eval(xpr, {**cls.qsymbol_dict} if gdict is None else {**gdict}, ldict)

    @classmethod
    def safe_exec(cls, code, gdict=None, ldict=None):
        code = preprocess_expression(code)
        if ldict is None:
            ldict = {}
        return safe_execute(code, cls.qsymbol_dict.copy() if gdict is None else gdict, ldict)

    @classmethod
    def func_title_desc_tags(cls, sfunc, __info=None, scope='qpots'):
        func_info = cls.run_func_info(sfunc, __info, scope)
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
    def run_func_info(cls, func_id, __info, scope='qpots'):
        try:
            fninfo = cls.addr(func_id + "__info", scope)
            # Check if fninfo accepts an argument
            args_count = len(inspect.signature(fninfo).parameters)

            if args_count == 0:
                func_info_from_func_def = fninfo()

            elif args_count == 1:
                func_info_from_func_def = fninfo(__info)
            else:
                raise ValueError(f'Error (RFI): {func_id}__info has an invalid number of arguments')

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

    @classmethod
    def package_contents_public(cls):
        from .models import MyStuff
        pfunc_dict = {}
        pc_dict = {}
        pctg_dict = {}
        pc_list = []

        mystuffs = MyStuff.objects
        pubcals = mystuffs.filter(object_id='mycal', is_public=True)
        logger.info(f'Scanning: mycal')

        for record in pubcals:
            package_name = f"pcals.{record.user.username}"
            catalog_name = f"{record.user.username}"

            if package_name not in pctg_dict:
                pctg_dict[package_name] = catalog_name
            code = record.item
            local_dict = cls.safe_exec(code)
            cls.build_func_dict(local_dict.items(), catalog_name, package_name, pfunc_dict, pc_dict)

        pc_list[:] = pc_dict.keys()
        pc_list.sort()

        with cls._registry_lock:
            cls.pfunc_dict = pfunc_dict
            cls.pc_dict = pc_dict
            cls.pctg_dict = pctg_dict
            cls.pc_list = pc_list

    @classmethod
    def add_pub_calc_node(cls, calc_id) -> bool:
        with cls._registry_lock:
            cal_id, cal_name, cal_owner = fid2owner(calc_id)
            owner_node_id = cal_owner
            owner_node, _ = cls.pcalc_root.add_node_if_not_found(cls.pcalc_root.id, owner_node_id, owner_node_id)
            toret = bool(owner_node)
            if not owner_node: return toret
            try:
                title, desc, tags = cls.func_title_desc_tags(calc_id, scope='p')
                func_node = TreeNode(nid=calc_id, name=calc_id, title=title, desc=desc, tags=tags,
                                     is_leaf=True, node_type='c')
                owner_node.add_child(func_node)
                owner_node.count_descendant_leafs()
            except Exception as e:
                logger.error(f'>>> AFP: {calc_id} could not be added, {str(e)}')
                toret = False
            return toret

    @classmethod
    def delete_pub_calc_node(cls, calc_id) -> bool:
        with cls._registry_lock:
            cal_id, cal_name, cal_owner = fid2owner(calc_id)
            owner_node_id = cal_owner
            toret = False
            try:
                owner_node = cls.pcalc_root.get_node_by_id(owner_node_id)
                cur_node = cls.pcalc_root.get_node_by_id(calc_id)
                toret = bool(cur_node)
                if cur_node:
                    cur_node.delete_tree()
                    if owner_node:
                        owner_node.count_descendant_leafs()
            except:
                pass
            return toret

    @classmethod
    def add_catagories_to_node(cls, node, ctg, uname=None):
        cats = ctg.split('.')  # sub categories
        cur_node = node
        par_id = node.id
        cur_node_id = ""
        for cur_node_name in cats:
            cur_node_id = joinx((cur_node_id, cur_node_name), qconst.name_separator)
            cur_node = cur_node.add_category_node(par_id, cur_node_id, cur_node_name, cur_node_name, uname)
            par_id = cur_node_id
        return cur_node  # last sub category added

    @classmethod
    def create_catalog_calc_public(cls):
        TreeNode.setup(qconst.admin_name, qconst.demo_name, qconst.personal_name)
        cls.pcalc_root = create_category_node('pcals', 'pcals', 'Public Cals')
        for pkg, ctg in cls.pctg_dict.items():
            cur_node = cls.add_catagories_to_node(cls.pcalc_root, ctg)

            func_ids = [func_id for func_id, categ in cls.pc_dict.items() if categ == pkg]
            for func_id in func_ids:
                try:
                    title, desc, tags = cls.func_title_desc_tags(func_id, scope='p')
                    func_node = TreeNode(nid=func_id, name=func_id, title=title, desc=desc, tags=tags,
                                         is_leaf=True, node_type='c')
                    cur_node.add_child(func_node)
                except Exception as _e:
                    pass

        cls.pcalc_root.update_all_descendant_leafs_count()
        cls.pcalc_root.sort_by()


if __name__ == "__main__":
    # import sett

    # QCals.package_contents('calc.all')
    QCals.package_contents('calculators.all.fun')
    print(QCals.qfunc_dict)
    print(QCals.qc_dict)
    print(QCals.qctg_dict)
    print(QCals.qc_list)
