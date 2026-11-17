# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from ..mod_cache import QMeta, QMyCal, QFav, QMem
from .mod_qcals import QCals
from .mod_pubcals import PubCals
from .mod_catalog_build import CatalogBuilder, FOLDER_ID_PREFIX
from ..mod_sandbox import CalcSandbox
from qcore import qinfo, qerror
from qutil.mod_tree import dict_to_tree
from qutil import TreeNode, create_category_node, user_name, get_functions, \
    extract_calculator_name, names2fid, fid2owner, path_title
import fnmatch
import logging
import json
import threading
from collections import OrderedDict
from contextlib import contextmanager

logger = logging.getLogger(__name__)


def get_uc_list():
    return QMeta.getp1('uc_list', [])


@contextmanager
def _edit_tree(meta_key, node_id, title, uname):
    """Load the stored tree (or start a new one), yield its root, then store it back and free it."""
    root = dict_to_tree(QMeta.getp1(meta_key, {})) or create_category_node(node_id, node_id, title, uname)
    try:
        yield root
        root.update_all_descendant_leafs_count()
        root.sort_by()
        QMeta.setp1(meta_key, root.tree_to_dict())
    finally:
        root.delete_tree()


def _remove_cal(kind, cal_id, cal_name, on_remove=None):
    """Remove a calculator from the stored uc (created) or sc (shared) list, dict and tree."""
    cal_list = QMeta.getp1(f'{kind}_list', [])
    if cal_id not in cal_list:
        return qerror(f'{cal_name} not found')
    cal_dict = QMeta.getp1(f'{kind}_dict', {})
    tree = dict_to_tree(QMeta.getp1(f'{kind}_tree', {}))

    try:
        cal_list.remove(cal_id)
        del cal_dict[cal_id]
        node = tree.get_node_by_id(cal_id) if tree else None
        if node:
            CatalogBuilder.remove_leaf(node)
        if on_remove:
            on_remove()
        QMeta.setp1(f'{kind}_list', cal_list)
        QMeta.setp1(f'{kind}_dict', cal_dict)
        if tree:
            QMeta.setp1(f'{kind}_tree', tree.tree_to_dict())
        result = qinfo(f'{cal_name} deleted')
    except Exception as e:
        result = qerror(f'{cal_name} could not be deleted because {str(e)}')

    if tree:
        tree.delete_tree()
    return result


class UCals:
    TreeNode.setup()

    # calc_root: TreeNode('personal', 'personal', 'Personal')

    def __init__(self):
        self.sc_tree = None
        self.sc_list = None
        self.sctg_dict = None
        self.sc_dict = None
        self.sfunc_dict = None

        self.uc_tree = None
        self.uc_list = None
        self.uctg_dict = None
        self.uc_dict = None
        self.ufunc_dict = None

        # self.calc_root = TreeNode('personal', 'personal', 'Personal')
        # # noinspection PyProtectedMember
        # self.calc_root._index_node()
        self.calc_root = create_category_node('personal', 'personal', 'Personal')
        self.cal_owner = user_name()

    def get_code(self, cal_name):
        cal_id = names2fid(self.cal_owner, cal_name)
        code = QMyCal.getp1(cal_id, '')
        if code:
            return code
        else:
            return ''

    def del_tree(self, node_id="personal"):
        utree_node = self.calc_root.get_node_by_id(node_id)
        if utree_node:
            utree_node.delete_tree()
            del utree_node
            self.__init__()

    def ufavs_dict_to_tree(self, fav_dict: dict, parent: TreeNode, id_prefix=''):
        for func_id in fav_dict:
            child = QCals.calc_root.get_node_by_id(func_id)  # | qcalc
            if not child:
                child = PubCals.root.get_node_by_id(func_id)  # | public cal
                if not child:
                    child = self.calc_root.get_node_by_id(func_id)  # | owncal

            if child:
                child = child.clone_detached(f'{id_prefix}{func_id}')
                child.uname = parent.uname
                parent.add_child(child)

    def get_tree(self):
        # create tree for the current user in the current worker process
        self.del_tree("created")  # id = func_id
        self.del_tree("shared")  # id = func_id+variant_info (vowner,varinat_id,token)
        self.del_tree("favorites")  # id = same as above

        uc_tree = QMeta.getp1('uc_tree', {})
        created_node = dict_to_tree(uc_tree)
        if created_node:
            created_node.uname = user_name()
            self.calc_root.add_tree(created_node)

        sc_tree = QMeta.getp1('sc_tree', {})
        shared_node = dict_to_tree(sc_tree)
        if shared_node:
            shared_node.uname = user_name()
            self.calc_root.add_tree(shared_node)  # , allowdups=True)

        ufavs_dict = QFav.getp({})
        if ufavs_dict:
            # favorites_node = TreeNode('favorites', 'favorites', 'My Favorites')
            # favorites_node.data["path"] = "Favorites"
            # favorites_node.uname = user_name()
            favorites_node = create_category_node('favorites', 'favorites',
                                                  'My Favorites', user_name())

            # | add standard calculators found in ufavs_dict to favorites node
            # | add user calculators found in ufavs_dict to favorites node
            self.ufavs_dict_to_tree(ufavs_dict, favorites_node, id_prefix='f:')
            # | add favorites subtree to the main tree
            self.calc_root.add_tree(favorites_node)

        self.calc_root.update_all_descendant_leafs_count()
        return self.calc_root

    def edit_cal(self, cal_name, code):  # , is_public: bool = False
        uc_list: list = QMeta.getp1('uc_list', [])
        uc_dict: dict = QMeta.getp1('uc_dict', {})

        package_name = 'created'
        catalog_name = user_name()
        functions = get_functions(code)
        results = []

        added = False
        cal_name_determind = extract_calculator_name(functions)
        if cal_name_determind == '':
            raise Exception(
                f"Error (SUC): Meta __info() not found. You may click on [Format code] to create one automatically.")
        elif cal_name == '':
            cal_name = cal_name_determind
        elif cal_name != '' and cal_name_determind != cal_name:
            raise Exception(
                f"Error (SUC): Specified name '{cal_name}' mismatches with determind name '{cal_name_determind}'")

        cal_id = names2fid(catalog_name, cal_name)
        update = cal_id in uc_list
        clash = next((i for i in uc_list if i.lower() == cal_id.lower() and i != cal_id), None)
        if clash:  # | search ignores case, so names that differ only by case would hide each other
            raise Exception(f"Error (SUC): '{cal_name}' differs only by case from your calculator '{clash}'")
        CalcSandbox.exec_with_context(
            code,
            scope='edit-mycal',
            username=self.cal_owner,
            item_id=cal_id,
        )

        for ufname in functions:
            # | ufaddr = locals.get(ufname, None)
            # | this dynamic address allocated from within the current worker process and
            # | hence not useful to store and use in future because
            # | successive request can be processed by a different worker process
            # | where this function address may not exist

            results.append(f'{ufname}() is defined')
            if ufname == cal_name:
                uc_dict[cal_id] = package_name
                if not update:
                    added = True
                    uc_list.append(cal_id)

        if added:
            uc_list.sort(key=str.lower)
        results.append(f"Run the calculator using '{cal_name}'")
        QMeta.setp1('uc_list', uc_list)
        QMeta.setp1('uc_dict', uc_dict)
        QMyCal.setp1(cal_id, code)  # QCals.func_title_desc_tags needs it

        ctg_node_id = "created"
        with _edit_tree('uc_tree', ctg_node_id, ctg_node_id, self.cal_owner) as ctg_node:
            try:
                leaf = CatalogBuilder.upsert_leaf(ctg_node, cal_id, QCals.func_title_desc_tags_folder, 'o',
                                                  self.cal_owner, 'e')
                if leaf.parent.id.startswith(FOLDER_ID_PREFIX):
                    results.append(f"Folder: {path_title(leaf.parent.id[len(FOLDER_ID_PREFIX):])}")
            except Exception as e:
                logger.error(f">>> EC: {e}")  # Example: Log the exception

        QMem.clear(cal_id)
        return results

    def del_cal(self, cal_name):
        cal_id = names2fid(self.cal_owner, cal_name)
        return _remove_cal('uc', cal_id, cal_name, on_remove=lambda: QMyCal.delp1(cal_id))

    def package_contents_private(self, request):
        self.ufunc_dict = {}
        self.uc_dict = {}
        self.uctg_dict = {}

        from ..models import MyStuff
        logger.info('Scanning: mycal')
        records = MyStuff.objects.filter(user=request.user, object_id='mycal')
        sources = ((f"ucals.{r.user.username}", r.user.username, r) for r in records)
        CatalogBuilder.scan_cals(sources, 'private-mycal', 'Private',
                                 self.ufunc_dict, self.uc_dict, self.uctg_dict)

        self.uc_list = sorted(self.uc_dict, key=str.lower)

        QMeta.setp1('uc_dict', self.uc_dict)
        QMeta.setp1('uc_list', self.uc_list)

    def create_catalog_calc_private(self, request):
        request.ufunc_dict = {}
        uname = user_name(request)
        created_node = create_category_node("created", "created", "Created by Me", uname)
        self.calc_root.add_child(created_node)
        CatalogBuilder.populate(created_node, self.uctg_dict, self.uc_dict, QCals.func_title_desc_tags_folder, 'o',
                                uname=uname, sub_type='e', flat_ctg=self.cal_owner)

        created_node.update_all_descendant_leafs_count()
        created_node.sort_by()
        self.uc_tree = created_node.tree_to_dict()
        QMeta.setp1('uc_tree', self.uc_tree)

    def package_contents_shared(self, request):
        self.sfunc_dict = {}
        self.sc_dict = {}
        self.sctg_dict = {}

        from ..models import MyStuff
        mystuffs = MyStuff.objects
        logger.info('Scanning: othcal')
        records = mystuffs.filter(user=request.user, object_id='othcal')

        def sources():
            for record in records:
                cal_owner = fid2owner(record.item_id)[2]
                try:
                    oth_record = mystuffs.get(object_id='mycal', item_id=record.item_id)  # get 1 record
                except Exception:
                    oth_record = None
                yield f"scals.{cal_owner}", cal_owner, oth_record

        CatalogBuilder.scan_cals(sources(), 'shared-mycal', 'Shared',
                                 self.sfunc_dict, self.sc_dict, self.sctg_dict)

        self.sc_list = sorted(self.sc_dict, key=str.lower)

        QMeta.setp1('sc_dict', self.sc_dict)
        QMeta.setp1('sc_list', self.sc_list)

    def create_catalog_calc_shared(self, request):
        if len(self.sctg_dict.items()) == 0: return
        request.ufunc_dict = {}
        request.token = ''
        uname = user_name(request)
        shared_node = create_category_node("shared", "shared", "Shared with Me", uname)
        self.calc_root.add_child(shared_node)
        CatalogBuilder.populate(shared_node, self.sctg_dict, self.sc_dict, QCals.func_title_desc_tags, 's',
                                uname=uname, flat_ctg=self.cal_owner)

        shared_node.update_all_descendant_leafs_count()
        shared_node.sort_by()
        self.sc_tree = shared_node.tree_to_dict()
        QMeta.setp1('sc_tree', self.sc_tree)


def register_shared_cal(func_id, token):
    cal_id, cal_name, owner = fid2owner(func_id)
    uname = user_name()
    sc_list: list = QMeta.getp1('sc_list', [])
    sc_dict: dict = QMeta.getp1('sc_dict', {})

    if cal_id not in sc_dict:
        sc_dict[cal_id] = 'shared'
        QMeta.setp1('sc_dict', sc_dict)

    if cal_id not in sc_list:
        sc_list.append(cal_id)
        sc_list.sort(key=str.lower)
        QMeta.setp1('sc_list', sc_list)

    with _edit_tree('sc_tree', 'shared', 'Shared with Me', uname) as ctg_node:
        try:
            # | registering again must not add a duplicate node
            CatalogBuilder.upsert_leaf(ctg_node, cal_id, QCals.func_title_desc_tags, 'qpots', uname)
        except Exception as e:
            logger.error(f">>> RSC: {e}")


def unregister_shared_cal(func_id):  # review tree delete
    cal_id, cal_name, owner = fid2owner(func_id)
    return _remove_cal('sc', cal_id, cal_name)


_PERSONAL_TREES_MAX = 256
_personal_lock = threading.Lock()
_personal_trees = OrderedDict()  # (user, catalog version, stored-data fingerprint) -> read-only root


def _personal_fingerprint():
    # the personal tree is built from these stored values (favorites are cloned from the shared catalogs)
    try:
        return hash(json.dumps([QMeta.getp1('uc_tree', {}), QMeta.getp1('sc_tree', {}), QFav.getp({})],
                               sort_keys=True, default=str))
    except TypeError:
        return None


def search_personal_nodes(pattern):
    """The current user's created and shared calculators whose id matches the wildcard pattern, ignoring case."""
    pattern = pattern.lower()
    return [
        node for node in get_personal_tree().depth_first()
        if node.is_leaf and not node.id.startswith('f:') and fnmatch.fnmatchcase(node.id.lower(), pattern)
    ]


def get_personal_tree():
    """
    The current user's catalog tree, shared across requests while its inputs are unchanged.
    The tree is read-only: callers must not modify it, use UCals().get_tree() for a private copy.
    """
    fingerprint = _personal_fingerprint()
    if fingerprint is None:
        return UCals().get_tree()

    key = (user_name(), QCals.catalog_version, fingerprint)
    with _personal_lock:
        root = _personal_trees.get(key)
        if root is not None:
            _personal_trees.move_to_end(key)
            return root

    root = UCals().get_tree()
    with _personal_lock:
        _personal_trees[key] = root
        while len(_personal_trees) > _PERSONAL_TREES_MAX:
            _personal_trees.popitem(last=False)
    return root
