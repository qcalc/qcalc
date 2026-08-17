# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from concurrent.futures import ThreadPoolExecutor
# import threading
import time

MAX_THREADS = 10


def run_func(kwargs: dict):
    id_ = kwargs.pop('_id')
    func = kwargs.pop('_func')
    res = func(**kwargs)
    return id_, res
    # QTPool.local.results[id] = res


class QTPool:
    # local = threading.local()

    def __init__(self, func, params: list[{}]):
        self.cnt = len(params)
        # QTPool.local.results = [None for i in range(self.cnt)]
        self.func = func
        self.params = params
        for i in range(self.cnt):
            params[i].update({'_func': func, '_id': i})

    def execute(self):
        thread_count = min(MAX_THREADS, self.cnt)
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            results = executor.map(run_func, self.params)
            return results


if __name__ == '__main__':
    def fsum(n):
        sum_ = 0
        for i in range(n):
            sum_ += i
        return sum_


    def fwait(n):
        time.sleep(n)
        return n


    nvals = [200000, 500000, 10000, 100000000, 3000000, 500]  # CPU bound - multiprocessing better
    nwait = [2, 5, 1, 7, 3, 5]  # I/O bound - thread friendly process
    fn = fsum
    fparams = nvals

    t_start = time.time()
    params = [{'n': v} for v in fparams]
    qt = QTPool(fn, params)
    print(list(qt.execute()))
    print('thread execution time (ms)', (time.time() - t_start) * 1000)

    nt_start = time.time()
    results = []
    for n in fparams:
        results.append(fn(n))
    print(results)
    print('non thread execution time (ms)', (time.time() - nt_start) * 1000)
    # print(QTPool.local.results)
