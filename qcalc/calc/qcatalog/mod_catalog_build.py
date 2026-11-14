# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import importlib.util
import inspect
import logging
import os
import traceback
from importlib import import_module
from pathlib import Path

import qconst
from django.conf import settings
from qutil import TreeNode, joinx, names2fid
from qvars import qfunc_categ_info
from ..mod_sandbox import CalcSandbox

logger = logging.getLogger(__name__)


class CatalogBuilder:
    """Scans calculator sources into function dictionaries and grows calculator catalog trees."""

    @staticmethod
    def build_func_dict(func_addr_list, catalog_name, package_name, func_dict, c_dict=None):
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
                func_dict[names2fid(catalog_name, fname)] = faddr

    @classmethod
    def scan_package(cls, package_name, catalog_name, func_dict, c_dict, ctg_dict):
        host_package_name = package_name

        def searchpath(package_name):
            ctg_dict[package_name] = package_name.replace(host_package_name, catalog_name)

            spec = importlib.util.find_spec(package_name)
            if spec is None:
                return
            with os.scandir(Path(spec.origin).parent) as entries:
                for entry in entries:
                    if entry.name.startswith('__'):
                        continue
                    current_pkg = '.'.join((package_name, entry.name.partition('.')[0]))
                    if entry.is_dir():
                        searchpath(current_pkg)
                    elif entry.is_file() and entry.name.endswith('.py'):
                        module = import_module(current_pkg)
                        func_address_list = inspect.getmembers(module, inspect.isfunction)
                        cls.build_func_dict(func_address_list, catalog_name, package_name, func_dict, c_dict)

        searchpath(package_name)

    @classmethod
    def scan_cals(cls, sources, scope, label, func_dict, c_dict, ctg_dict):
        """Run user calculator code from MyStuff records and collect its functions.

        sources yields (package_name, catalog_name, record); record may be None when the code is missing.
        """
        for package_name, catalog_name, record in sources:
            ctg_dict.setdefault(package_name, catalog_name)
            if record is None:
                continue
            try:
                local_dict = CalcSandbox.exec_with_context(
                    record.item,
                    scope=scope,
                    username=record.user.username,
                    item_id=record.item_id,
                )
            except Exception as e:
                logger.error(
                    "%s calculator scan skipped | user=%s item_id=%s error=%s",
                    label,
                    record.user.username,
                    record.item_id,
                    str(e),
                )
                if getattr(settings, 'DEBUG', False):
                    traceback.print_exc()
                continue
            cls.build_func_dict(local_dict.items(), catalog_name, package_name, func_dict, c_dict)

    @staticmethod
    def add_categories(node, ctg, uname=None):
        cats = ctg.split('.')  # sub categories
        cur_node = node
        par_id = node.id
        cur_node_id = ""
        for cur_node_name in cats:
            cur_node_id = joinx((cur_node_id, cur_node_name), qconst.name_separator)
            cur_node = cur_node.add_category_node(par_id, cur_node_id, cur_node_name, cur_node_name, uname)
            cur_node_path_dot = cur_node_id.replace(qconst.name_separator, '.')
            cur_node.desc = (
                qfunc_categ_info.get(cur_node_id, {}).get('desc')
                or qfunc_categ_info.get(cur_node_path_dot, {}).get('desc')
                or qfunc_categ_info.get(cur_node_name, {}).get('desc')
                or cur_node.title
            )
            par_id = cur_node_id
        return cur_node  # last sub category added

    @staticmethod
    def upsert_leaf(root, func_id, title_fn, scope, uname='', sub_type=''):
        """Add the calculator leaf under root, or refresh its title, desc and tags if root's tree already has it.

        Raises whatever title_fn raises, so the caller decides how to log it.
        """
        title, desc, tags = title_fn(func_id, scope=scope)
        func_node = root.get_node_by_id(func_id)
        if func_node is None:
            func_node = TreeNode(nid=func_id, name=func_id, title=title, desc=desc, tags=tags,
                                 is_leaf=True, node_type='c', sub_type=sub_type)
            func_node.uname = uname
            root.add_child(func_node)
        else:
            func_node.title = title
            func_node.desc = desc
            func_node.tags = tags
        return func_node

    @classmethod
    def populate(cls, root, ctg_dict, c_dict, title_fn, scope, uname=None, sub_type='', flat_ctg=None, on_leaf=None):
        """Add category and calculator leaf nodes under root.

        title_fn(func_id, scope=) returns (title, desc, tags); a calculator for which it raises is left out.
        Calculators of the category flat_ctg are added directly under root. on_leaf(func_node) is called per leaf.
        """
        func_ids_by_pkg = {}
        for func_id, pkg in c_dict.items():
            func_ids_by_pkg.setdefault(pkg, []).append(func_id)

        for pkg, ctg in ctg_dict.items():
            cur_node = root if ctg == flat_ctg else cls.add_categories(root, ctg, uname)
            for func_id in func_ids_by_pkg.get(pkg, ()):
                try:
                    title, desc, tags = title_fn(func_id, scope=scope)
                    func_node = TreeNode(nid=func_id, name=func_id, title=title, desc=desc, tags=tags,
                                         is_leaf=True, node_type='c', sub_type=sub_type)
                    func_node.uname = uname or ''
                    cur_node.add_child(func_node)
                    if on_leaf:
                        on_leaf(func_node)
                except Exception:
                    # | title_fn raises if not in demo mode and the function has no __info()
                    pass
