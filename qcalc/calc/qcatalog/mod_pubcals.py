# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import logging
import threading

import qconst
from qutil import TreeNode, create_category_node, fid2owner
from ..mod_cache import QMyCal
from .mod_catalog_build import CatalogBuilder
from ..mod_redis import redis_publish_action
from ..mod_sandbox import CalcSandbox

logger = logging.getLogger(__name__)


def _qcals():
    from .mod_qcals import QCals  # QCals imports PubCals, so import it lazily
    return QCals


class PubCals:
    """Registry and catalog tree of public calculators published by users."""

    func_dict: dict = {}  # public function names and addresses
    cal_dict: dict = {}  # public calculator names and packages
    ctg_dict: dict = {}  # public package and category names
    cal_list: list = []  # sorted keys of cal_dict
    root: TreeNode = create_category_node('pcals', 'pcals', 'Public Cals')

    _lock = threading.RLock()

    @classmethod
    def addr(cls, func_id):
        cal_id, cal_name, cal_owner = fid2owner(func_id)
        if cal_owner == '':
            return None
        with cls._lock:
            faddr = cls.func_dict.get(func_id, None)
        if not faddr:
            cls.load(func_id, cal_owner)
            with cls._lock:
                faddr = cls.func_dict.get(func_id, None)
        return faddr

    @classmethod
    def load(cls, sfunc_uname, owner) -> bool:
        cal_id = sfunc_uname.split('__')[0]
        code = QMyCal.getp1_from_owner_public(cal_id, owner)
        if not code:
            return False
        cls.update_cal(cal_id, owner, code)
        redis_publish_action(
            channel="qcalc_channel",
            action="update_public_cal",
            cal_id=cal_id,
            cal_owner=owner,
            code=code
        )
        return True

    @classmethod
    def update_cal(cls, cal_id, cal_owner, code) -> bool:
        local_dict = CalcSandbox.exec_with_context(
            code,
            scope='update-public-cal',
            username=cal_owner,
            item_id=cal_id,
        )
        package_name = f"pcals.{cal_owner}"
        updated = False

        with cls._lock:
            if package_name not in cls.ctg_dict:
                updated = True
                cls.ctg_dict[package_name] = cal_owner
                CatalogBuilder.add_categories(cls.root, cal_owner)

            CatalogBuilder.build_func_dict(local_dict.items(), cal_owner, 'public', cls.func_dict)

            faddr = cls.func_dict.get(cal_id, None)
            if faddr and cal_id not in cls.cal_list:
                updated = True
                cls.cal_list.append(cal_id)
                cls.cal_list.sort(key=str.lower)

            node = cls.root.get_node_by_id(cal_id)
            if not node:
                updated = True
                cls.add_node(cal_id)

        return updated

    @classmethod
    def delete_cal(cls, cal_id) -> bool:
        with cls._lock:
            deleted = cls.delete_node(cal_id)
            if cal_id in cls.cal_list:
                cls.cal_list.remove(cal_id)
                deleted = True

            if cal_id in cls.func_dict:
                _ = cls.func_dict.pop(cal_id, None)
                deleted = True

            keys_to_remove = [key for key in cls.func_dict if key.startswith(f"{cal_id}__")]
            for key in keys_to_remove:
                _ = cls.func_dict.pop(key, None)
                deleted = True

        return deleted

    @classmethod
    def scan(cls):
        from ..models import MyStuff
        func_dict = {}
        cal_dict = {}
        ctg_dict = {}

        logger.info('Scanning: mycal')
        records = MyStuff.objects.filter(object_id='mycal', is_public=True)
        sources = ((f"pcals.{r.user.username}", r.user.username, r) for r in records)
        CatalogBuilder.scan_cals(sources, 'public-mycal', 'Public', func_dict, cal_dict, ctg_dict)

        with cls._lock:
            cls.func_dict = func_dict
            cls.cal_dict = cal_dict
            cls.ctg_dict = ctg_dict
            cls.cal_list = sorted(cal_dict, key=str.lower)

    @classmethod
    def build_catalog(cls):
        TreeNode.setup(qconst.admin_name, qconst.demo_name, qconst.personal_name)
        CatalogBuilder.populate(cls.root, cls.ctg_dict, cls.cal_dict, _qcals().func_title_desc_tags, 'p')
        cls.root.update_all_descendant_leafs_count()
        cls.root.sort_by()
        _qcals().bump_catalog_version()

    @classmethod
    def add_node(cls, calc_id) -> bool:
        with cls._lock:
            cal_id, cal_name, cal_owner = fid2owner(calc_id)
            owner_node, _ = cls.root.add_node_if_not_found(cls.root.id, cal_owner, cal_owner)
            toret = bool(owner_node)
            if not owner_node: return toret
            try:
                CatalogBuilder.upsert_leaf(owner_node, calc_id, _qcals().func_title_desc_tags, 'p')
                owner_node.count_descendant_leafs()
            except Exception as e:
                logger.error(f'>>> AFP: {calc_id} could not be added, {str(e)}')
                toret = False
            _qcals().bump_catalog_version()
            return toret

    @classmethod
    def delete_node(cls, calc_id) -> bool:
        with cls._lock:
            cal_id, cal_name, cal_owner = fid2owner(calc_id)
            toret = False
            try:
                owner_node = cls.root.get_node_by_id(cal_owner)
                cur_node = cls.root.get_node_by_id(calc_id)
                toret = bool(cur_node)
                if cur_node:
                    cur_node.delete_tree()
                    if owner_node:
                        owner_node.count_descendant_leafs()
            except Exception:
                pass
            _qcals().bump_catalog_version()
            return toret
