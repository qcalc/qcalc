# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import signal
import time
from qutil.timed_thread import QThread
import platform
import threading
from qutil.timed_thread import thread_with_timeout


def run_with_timeout(func_addr, args=(), kwargs=None, timeout=60, pref=None):
    if kwargs is None: kwargs = {}
    if pref is None: pref = {}

    def run_func():
        # | save preferences to main thread local storage to make it available
        # | from within the fn() running in main thread
        QThread.set_pref(pref)
        return func_addr(*args, **kwargs)

    def timeout_handler(signum, frame):
        raise TimeoutError(f"Error (RTO): Function timed out after {timeout} seconds!")

    is_linux = platform.system() == 'Linux'
    is_main_thread = threading.current_thread() is threading.main_thread()

    if is_linux and is_main_thread:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        try:
            result = run_func()
        finally:
            signal.alarm(0)
    elif is_linux:
        # signal-based alarms are unavailable in non-main threads (common in WSGI/threaded servers)
        result = thread_with_timeout(func_addr, args=args, kwargs=kwargs, timeout=timeout, pref=pref)
    else:
        result = run_func()
    return result


if __name__ == '__main__':
    def func(x, y):
        print('Function started')
        sum_ = 0.0
        for i in range(10):
            print(i + x + y)
            sum_ += i + x + y
            time.sleep(1)
        print('Function finished')
        return sum_


    try:
        res = run_with_timeout(func, kwargs={"x": 20, "y": 80}, timeout=5)
        print('End of main program')
        print('Result', res)
    except TimeoutError as e:
        print(str(e))
