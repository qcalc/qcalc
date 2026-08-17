# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import qvars
from qutil import css2strs, nzs, HtmxHttpRequest, check_setting, QThread, fid2owner, get_object, is_loggedin
from django.core.cache import caches
from django.conf import settings
from qcore import QFile
# | from .models import MyStuff
# | lazily imported within myobjects() to avoid application initialization issue
from typing import Optional, Any
from django.utils.functional import cached_property
from .mod_db import QInput
import logging

logger = logging.getLogger(__name__)


class QCacheGen:

    def __init__(self, alias):  # prefix,
        self.cache = caches[alias]
        self.alias = alias
        self._health_key = f"{self.alias}:healthcheck"
        self.active = self.isactive()

    def isactive(self):
        try:
            self.cache.set(self._health_key, 'ok', timeout=10)
            return self.cache.get(self._health_key) == 'ok'
        except Exception:
            return False

    def clear(self):
        self.cache.clear()
        self.cache.set(self._health_key, 'ok', timeout=10)

    def set_data(self, key, data):  # data e.g schema_def or temp_file
        if self.active:
            self.cache.set(key, data)

    def get_data(self, key):
        if self.active:
            return self.cache.get(key)
        else:
            return None

    def remove(self, key):
        self.cache.delete(key)


class QSession:
    def __init__(self, prefix, volatile=False, defa=None):  # 'qc_pref'
        self.prefix = prefix
        self.volatile = volatile
        if defa is not None and isinstance(defa, dict):
            self.defa = defa.copy()
        else:
            self.defa = defa or {}

    def clear(self):
        request = QThread.get_req()
        rqsn = request.session
        rqsn[self.prefix] = {}

    def setp(self, pref: dict):
        request = QThread.get_req()
        cur_pref = self.getp()
        cur_pref.update(pref.copy())  # | .copy() important
        rqsn = request.session
        rqsn[self.prefix] = cur_pref
        if QCache.active and not self.volatile:
            rqsn.modified = True
        else:
            logger.error('QSP: Session not saved')

    def getp(self, defa: None | dict = None) -> dict:
        # | get dict. If it doesn't exist return {}, never returns None
        request = QThread.get_req()
        # Check if request exists and has a session attribute
        if request is None or not hasattr(request, 'session'):
            return defa  # Return default if no session is available
        rqsn = request.session
        saved_pref: dict = rqsn.get(self.prefix, defa or self.defa)
        return saved_pref.copy()  # | .copy() important

    def getp_temp(self, defa: Optional[dict] = None) -> dict:
        request = QThread.get_req()
        auth_user = self.get_authenticated_user(request)
        if not auth_user:
            return self.getp(defa)
        return {}

    def setp1(self, spref, data):
        request = QThread.get_req()
        rqsn = request.session
        if self.prefix not in rqsn:
            rqsn[self.prefix] = {}
        rqsn[self.prefix][spref] = data
        if QCache.active and not self.volatile:
            rqsn.modified = True

    def delp1(self, spref):
        request = QThread.get_req()
        rqsn = request.session
        if self.prefix in rqsn and spref in rqsn[self.prefix]:
            del rqsn[self.prefix][spref]
            if QCache.active and not self.volatile:
                rqsn.modified = True
            return True
        else:
            return False

    def getp1(self, spref, defa=None):
        # | get value. if it doesn't exist return specified defa
        request = QThread.get_req()
        # Check if request exists and has a session attribute
        if request is None or not hasattr(request, 'session'):
            return defa  # Return default if no session is available
        rqsn = request.session
        saved_pref: dict = rqsn.get(self.prefix, self.defa)
        return saved_pref.get(spref, defa)

    @classmethod
    def get_authenticated_user(cls, request: HtmxHttpRequest):  # -> Optional[User]:
        return request.user if is_loggedin(request) else None

    def clear_temp(self):
        request = QThread.get_req()
        auth_user = self.get_authenticated_user(request)
        if not auth_user:
            self.clear()

class QDBSession(QSession):
    def __init__(self, prefix, volatile=False, defa=None):
        super().__init__(prefix, volatile, defa)

    @cached_property
    def mystuffs(self):
        # | lazily imported within mystuffs() to avoid application initialization issue
        from .models import MyStuff
        return MyStuff.objects

    def clear(self):
        request = QThread.get_req()
        auth_user = self.get_authenticated_user(request)
        if auth_user:
            self.mystuffs.filter(user=auth_user, object_id=self.prefix).delete()
        else:
            super().clear()

    def clear_temp(self):
        super().clear()

    def _save_preferences(self, user, pref: dict):
        for item_id, data in pref.items():
            self.mystuffs.update_or_create(
                user=user,
                object_id=self.prefix,
                item_id=item_id,
                defaults={'item': data}
            )

    def setp(self, pref: dict):
        request = QThread.get_req()
        user = self.get_authenticated_user(request)
        if user:
            self._save_preferences(user, pref)
        else:
            super().setp(pref)

    def getp(self, defa: Optional[dict] = None) -> dict:
        request = QThread.get_req()
        user = self.get_authenticated_user(request)
        if user:
            prefs = self.mystuffs.filter(user=user, object_id=self.prefix)
            data = {pref.item_id: pref.item for pref in prefs}
            return data or (defa or self.defa)
        return super().getp(defa)

    def getp_temp(self, defa: Optional[dict] = None) -> dict:
        return super().getp(defa)

    def setp1(self, spref: str, data: Any):
        self.setp({spref: data})

    def delp1(self, spref: str) -> bool:
        request = QThread.get_req()
        user = self.get_authenticated_user(request)
        if user:
            count, _ = self.mystuffs.filter(user=user, object_id=self.prefix, item_id=spref).delete()
            return count > 0
        return super().delp1(spref)

    def getp1(self, spref: str, defa: Optional[Any] = None) -> Any:
        request = QThread.get_req()
        user = self.get_authenticated_user(request)
        if user:
            try:
                record = self.mystuffs.get(user=user, object_id=self.prefix, item_id=spref)
                return record.item
            except self.mystuffs.model.DoesNotExist:
                return defa
        return super().getp1(spref, defa)

    def getp1_from_token(self, func_id: str, token: str) -> Any:
        cal_id, cal_name, owner = fid2owner(func_id)
        record = QInput.get_variant_from_token(func_id, token)
        if record is None:
            return None
        from qsite.users.models import User  # | import after initialization
        owner_user = User.objects.get(username=owner)
        if owner_user:
            try:
                record = self.mystuffs.get(user=owner_user, object_id=self.prefix, item_id=func_id)
                return record.item
            except self.mystuffs.model.DoesNotExist:
                return None
        return None

    def getp1_from_owner(self, sfunc_uname: str, owner, curuser) -> Any:
        # sfunc, owner = sfunc_uname.split('-')
        from qsite.users.models import User  # | import after initialization
        # owner_user = User.objects.get(username=owner)
        owner_user = get_object(User, username=owner)
        # cur_user = User.objects.get(username=curuser)
        cur_user = get_object(User, username=curuser)
        if owner_user and cur_user:
            try:
                # | first check if cur_user is authorized to run the function
                _ = self.mystuffs.get(user=cur_user, object_id='othcal', item_id=sfunc_uname)
                # | if there is no exception then return with code obtained from the owner
                record = self.mystuffs.get(user=owner_user, object_id=self.prefix, item_id=sfunc_uname)
                return record.item
            except self.mystuffs.model.DoesNotExist:
                return None
        return None

    def getp1_from_owner_nocheck(self, sfunc_uname: str, owner) -> Any:
        from qsite.users.models import User  # | import after initialization
        owner_user = get_object(User, username=owner)
        if owner_user:
            try:
                record = self.mystuffs.get(user=owner_user, object_id=self.prefix, item_id=sfunc_uname)
                return record.item
            except self.mystuffs.model.DoesNotExist:
                return None
        return None

    def getp1_from_owner_public(self, sfunc_uname: str, owner='') -> Any:
        from qsite.users.models import User  # | import after initialization
        if owner == '':
            cal_id, cal_name, owner = fid2owner(sfunc_uname)
        owner_user = get_object(User, username=owner)
        if owner_user:
            try:
                record = self.mystuffs.get(user=owner_user, object_id=self.prefix, item_id=sfunc_uname, is_public=True)
                return record.item
            except self.mystuffs.model.DoesNotExist:
                return None
        return None


class QMem:
    xlist = {'mem', 'pref', 'qcache', 'temp', 'gpref', 'collect'}
    prefix = 'mem'

    @classmethod
    def clear(cls, functions=''):
        request = QThread.get_req()
        rqsn = request.session
        qc_mem = rqsn.get(cls.prefix, {})
        if not nzs(functions):
            qc_mem = {}
        else:
            keylist = css2strs(functions)
            for sfunc in keylist:
                qc_mem.pop(sfunc, None)

        rqsn[cls.prefix] = qc_mem
        if QCache.active:
            rqsn.modified = True

    @classmethod
    def clearf(cls, sfunc):
        request = QThread.get_req()
        rqsn = request.session
        qc_mem = rqsn.get(cls.prefix, {})
        if sfunc not in cls.xlist and sfunc not in qc_mem:
            ln = len(qc_mem)
            mem_max = QPref.getp1('memory')
            if ln >= mem_max:
                n2del = ln - mem_max + 1
                for k in range(n2del):
                    k2del = list(qc_mem.keys())[0]
                    del qc_mem[k2del]

        qc_mem[sfunc] = {}
        rqsn[cls.prefix] = qc_mem
        if QCache.active:
            rqsn.modified = True

    @classmethod
    def setf(cls, sfunc, mem_dict):
        request = QThread.get_req()
        if sfunc in cls.xlist:
            return
        for key, val in mem_dict.items():
            if isinstance(val, QFile):
                # | do not cache the file if more than 300 KB
                # | by default memcached item size is 1 MB
                if len(val.file_bytes) > 307200:  # 300KB
                    mem_dict[key] = ''

        rqsn = request.session
        qc_mem = rqsn.get(cls.prefix, {})
        if sfunc not in qc_mem:
            cls.clearf(sfunc)
            qc_mem = rqsn.get(cls.prefix, {})

        try:
            qc_mem[sfunc].update(mem_dict)
            rqsn[cls.prefix] = qc_mem
            if QCache.active:
                rqsn.modified = True
        except:
            pass

    @classmethod
    def getf(cls, sfunc):
        return cls._getf(QThread.get_req(), sfunc)

    @classmethod
    def _getf(cls, request: HtmxHttpRequest, sfunc):
        rqsn = request.session
        qc_mem = rqsn.get(cls.prefix, {})
        return qc_mem.get(sfunc)

    @classmethod
    def getp(cls):
        return cls._getp(QThread.get_req())

    @classmethod
    def _getp(cls, request: HtmxHttpRequest):
        rqsn = request.session
        qc_mem = rqsn.get(cls.prefix, {})
        return qc_mem


# | global, prefix='schema:'
# These are module-level global object creation, so they run on import, once per Python process.
# from django.utils.functional import SimpleLazyObject
# QCache = SimpleLazyObject(lambda: QCacheGen(alias=check_setting(settings.QSCHEMA_CACHE_ALIAS)))
# QPref = SimpleLazyObject(lambda: QDBSession(prefix='pref', volatile=False, defa=qvars.qc_gpref))

QCache = QCacheGen(alias=check_setting(settings.QSCHEMA_CACHE_ALIAS, "QSCHEMA_CACHE_ALIAS"))
# QCache.active will be false if cache is not configured properly; runserver checks this at startup.
# | session specific user preferences and data - stay alive throughout the session
# QPref = QSession(prefix='pref', volatile=False, defa=qvars.qc_gpref)  # User Preferences
QPref = QDBSession(prefix='pref', volatile=False, defa=qvars.qc_gpref)  # User Preferences
QData = QSession(prefix='data', volatile=False)  # User Data e.g. rates etc.
# | session_specific users temporary storage for uploaded files - can be cleared from temp()
QTemp = QSession(prefix='temp', volatile=False)  # User Temporary files
# | session_specific users collected results - cleared when?
QKeep = QSession(prefix='keep', volatile=False)  # User Collected data for aggregation
# | session_specific users last io stored for immediate saving to file - cleared before save/saveio command
QSave = QSession(prefix='save', volatile=False)  # User saved last input/output for saving
# | session_and_cid_specific users IO stored for reuse in step2, cleared when card is closed?
QIO = QSession(prefix='io', volatile=False)  # User input/output saved for reuse in step2
# | session_specific users console variables
QRam = QSession(prefix='ram', volatile=False)  # User console variables
# | session_specific users own calculators
QMeta = QSession(prefix='meta', volatile=False)  # User meta
# | QMy = QSession(prefix='mycal', volatile=False)  # User calculators
QMyCal = QDBSession(prefix='mycal', volatile=False)  # User calculators
# | session_specific user favorites
# | QFavs = QSession(prefix='fav', volatile=False)  # User favorites
QFav = QDBSession(prefix='fav', volatile=False)  # User favorites

# if __name__ == '__main__':
#     import os
#
#     os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
#     print(qcache())
