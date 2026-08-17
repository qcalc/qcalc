# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

# ---------------------------------------------------------------------
# KThread.py: A killable Thread implementation.
# http://mail.python.org/pipermail/python-list/2004-May/281943.html
# Connelly Barnes
# https://web.archive.org/web/20130503082442/http://mail.python.org/pipermail/python-list/2004-May/281943.html
# ---------------------------------------------------------------------

import sys
import time
import threading
from qvars import qc_gpref as gs


class QThread(threading.Thread):
    """A subclass of threading.Thread, with a kill()
  method."""

    local = threading.local()

    def __init__(self, *args, **kwargs):
        # threading.Thread.__init__(self, *args, **keywords)
        super().__init__(*args, **kwargs)
        self.killed = False

    def start(self):
        """Start the thread."""
        self.__run_backup = self.run
        self.run = self.__run  # Force the Thread to install our trace.
        # threading.Thread.start(self)
        super().start()

    def __run(self):
        """Hacked run function, which installs the trace."""
        sys.settrace(self.globaltrace)
        self.__run_backup()
        self.run = self.__run_backup

    def globaltrace(self, frame, why, arg):
        if why == 'call':
            return self.localtrace
        return None

    def localtrace(self, frame, why, arg):
        if self.killed and why == 'line':
            raise SystemExit()
        return self.localtrace

    def kill(self):
        self.killed = True

    # -----------------------
    # Function that uses preferences without explicitly taking request as an argument
    @classmethod
    def set_pref(cls, pref):
        # Set the preference in thread-local storage
        cls.local.user_pref = pref
        # cls.local.user_req = request

    @classmethod
    def get_prefs(cls):
        # Access the preference from thread-local storage
        return getattr(cls.local, 'user_pref', gs)

    @classmethod
    def get_pref(cls, pref: str, defa=None):
        # Access the preference from thread-local storage
        return getattr(cls.local, 'user_pref', gs).get(pref, defa)

    @classmethod
    def set_req(cls, request):
        cls.local.request = request

    @classmethod
    def get_req(cls):
        return getattr(cls.local, 'request', None)


def thread_with_timeout(func_addr, args=(), kwargs=None, timeout=60, pref=None):
    if kwargs is None:
        kwargs = {}
    if pref is None:
        pref = {}
    parent_req = QThread.get_req()

    state = {
        "value": None,
        "error": None,
    }

    # Define a function to run the target function and store the result
    def run_func():
        # | save preferences to child thread local storage to make it available
        # | from within the fn() running in child thread
        QThread.set_pref(pref)
        QThread.set_req(parent_req)
        try:
            state["value"] = func_addr(*args, **kwargs)
        except BaseException as exc:
            state["error"] = exc
        finally:
            QThread.set_req(None)

    th = QThread(target=run_func, daemon=True)
    th.start()
    join_timeout = None if timeout is None or timeout <= 0 else timeout
    th.join(join_timeout)
    if th.is_alive():
        th.kill()
        th.join(1.0)
        raise TimeoutError(f"Error (XTO): Execution timed out after {timeout} seconds.")

    if state["error"] is not None:
        raise state["error"]

    return state["value"]


if __name__ == '__main__':
    # from KThread import *

    def func(x, y):
        print('Function started')
        sum_ = 0.0
        for i in range(30):
            print(i + x + y)
            sum_ += i + x + y
            time.sleep(1)
        print('Function finished')
        return sum_


    try:
        res = thread_with_timeout(func, kwargs={"x": 20, "y": 80}, timeout=5)
        print('End of main program')
        print('Result', res)
    except TimeoutError as e:
        print(str(e))
