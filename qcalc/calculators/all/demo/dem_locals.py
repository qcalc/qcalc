# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

def demo_try2__info():
    return {}


def demo_try2(p=2, x=3, y=23):
    z_ = (x + y) / p
    t_ = (x + y) * p
    note_ = 'Calculations: z = (x + y) / p, t = (x + y) * p'
    another_ = z_ / t_
    return z_


def demo_try__info():
    return {}


def demo_try(x=3, y=23):
    a = 5
    b = 6
    c = a * b + x + y
    d = a + b + c
    return a, b, c


if __name__ == '__main__':
    print(demo_try())
    print(demo_try2())
