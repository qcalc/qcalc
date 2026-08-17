# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

# ref: Astronomical Formulae for Calculators
# by JEEN MEEUS, 1980
# python coding by: DCSaha@26.07.24

from math import sin, cos, tan, asin, atan, pi

# alpha = right_ascension
# delta = declination
# alpha50 = right_ascension_1950
# delta50 = declination_1950
# lambda_ = celestial_longitude
# beta = celestial_latitude
# l = galactic_longitude
# b = galactic_latitude
# h = altitude
# A = azimuth
# epsilon = obliquity_ecliptic
# phi = observer_latitude
# Lo = observer_longitude
# Ha = local_hour_angle
# theta = local_siderial_time
# theta0 = greenwich_siderial_time

# Ha = theta - alpha
# Ha = theta0 - Lo - alpha

# equa = Equatorial Coordinates (alpha=right_ascention, delta=declination)
# eclip = Ecliptical or Celestial Coordinates (lambda_=celestial_longitude, beta=celestial_latitude)
# galac = Galactical Coordinates (l=galactic_longitude, b=galactic_latitude)
# local = Local or Horizontal Coordinates (A=azimuth, h=altitude)

epsilon = 23.4457889 * pi / 180


def sign(val):
    return 1 if val > 1 else -1


def asin_chk(val):
    return sign(val) * pi / 2 if abs(val) > 1.0 else asin(val)


def atan_chk(dividend, divisor):
    return pi / 2 if abs(divisor) < 1e-10 else atan(dividend / divisor)


def equa2eclip(alpha, delta):
    # inputs and outputs are in radian
    divisor = cos(alpha)
    lambda_ = rad2norm(atan_chk((sin(alpha) * cos(epsilon) + tan(delta) * sin(epsilon)), divisor))
    beta = asin_chk(sin(delta) * cos(epsilon) - cos(delta) * sin(epsilon) * sin(alpha))
    return lambda_, beta


def equa2galac(alpha, delta):
    # inputs and outputs are in radian
    a1 = (192 + 25 / 60) * pi / 180 - alpha
    a2 = (27 + 4 / 60) * pi / 180
    x = atan_chk(sin(a1), (cos(a1) * sin(a2) - tan(delta) * cos(a2)))
    l = rad2norm(303 * pi / 180 - x)
    b = asin_chk(sin(delta) * sin(a2) + cos(delta) * cos(a2) * cos(a1))
    return l, b


def equa2local(alpha, delta, phi, theta):
    # inputs and outputs are in radian
    Ha = theta - alpha
    divisor = (cos(Ha) * sin(phi) - tan(delta) * cos(phi))
    A = rad2norm(atan_chk(sin(Ha), divisor))
    h = asin_chk(sin(phi) * sin(delta) + cos(phi) + cos(delta) * cos(Ha))
    return A, h


def eclip2equa(lambda_, beta):
    # inputs and outputs are in radian
    alpha = rad2norm(atan_chk((sin(lambda_) * cos(epsilon) - tan(beta) * sin(epsilon)), cos(lambda_)))
    delta = asin_chk(sin(beta) * cos(epsilon) + cos(beta) * sin(epsilon) * sin(lambda_))
    return alpha, delta


def eclip2galac(lambda_, beta):
    alpha, delta = eclip2equa(lambda_, beta)
    l, b = equa2galac(alpha, delta)
    return l, b


def eclip2local(lambda_, beta, phi, theta):
    alpha, delta = eclip2equa(lambda_, beta)
    A, h = equa2local(alpha, delta, phi, theta)
    return A, h


def galac2equa(l, b):
    # inputs and outputs are in radian
    b1 = l - 123 * pi / 180
    a2 = (27 + 4 / 60) * pi / 180
    y = atan_chk(sin(b1), (cos(b1) * sin(a2) - tan(b) * cos(a2)))
    alpha = rad2norm(y + (12 + 25 / 60) * pi / 180)
    delta = asin_chk(sin(b) * sin(a2) + cos(b) * cos(a2) * cos(b1))
    return alpha, delta


def galac2eclip(l, b):
    alpha, delta = galac2equa(l, b)
    lambda_, beta = equa2eclip(alpha, delta)
    return lambda_, beta


def galac2local(l, b, phi, theta):
    alpha, delta = galac2equa(l, b)
    A, h = equa2local(alpha, delta, phi, theta)
    return A, h


def local2equa(A, h, phi, theta):
    # inputs and outputs are in radian
    delta = asin_chk(sin(h) * sin(phi) + cos(h) * cos(phi) * cos(A))
    divisor = cos(delta)
    if abs(divisor) > 1e-10:
        Ha = asin_chk(sin(A) * cos(h) / divisor)
    else:
        Ha = pi / 2
    alpha = rad2norm(theta - Ha)
    return alpha, delta


def local2eclip(A, h, phi, theta):
    alpha, delta = local2equa(A, h, phi, theta)
    lambda_, beta = equa2eclip(alpha, delta)
    return lambda_, beta


def local2galac(A, h, phi, theta):
    alpha, delta = local2equa(A, h, phi, theta)
    l, b = equa2galac(alpha, delta)
    return l, b


def hms2rad(hours, minute, sec):
    rad = (hours + minute / 60 + sec / 3600) / 12 * pi
    return rad


def dms2rad(deg, minute, sec):
    # degree, minute, seconds to radians
    rad = (deg + minute / 60 + sec / 3600) * pi / 180
    return rad


def rad2deg(rad):
    # radians to degrees
    return rad * 180 / pi


def deg2rad(deg):
    # degrees to radians
    return deg * pi / 180


def rad2dms(rad):
    deg = rad * 180 / pi
    minute = (deg - int(deg)) * 60
    sec = (minute - int(minute)) * 60
    return f"{int(deg)} deg {int(minute)} min {sec} sec"


def rad2ndeg(rad):
    # longitude normalization
    deg = rad * 180 / pi
    return deg2norm(deg)


def rad2norm(rad):
    # longitude normalization
    if rad < 0:
        rad = 2 * pi + rad
    elif rad > 2 * pi:
        rad = rad - 2 * pi
    return rad


def deg2norm(deg):
    # longitude normalization
    if deg < 0:
        deg = 180 + deg
    elif deg > 360:
        deg = deg - 360
    return deg


if __name__ == '__main__':
    print('1', epsilon)
    alpha = pi / 2
    beta = pi / 4
    delta = pi / 8
    print('2', alpha, beta, delta)
    lambda_, beta = equa2eclip(alpha, delta)
    print('3', lambda_, beta)
    alpha2, beta2 = eclip2equa(lambda_, beta)
    print('4', alpha2, beta2)

    pollux_alpha1950 = hms2rad(7, 42, 15.525)
    pollux_delta1950 = dms2rad(28, 8, 55.11)
    lambda_, beta = equa2eclip(pollux_alpha1950, pollux_delta1950)
    print('5', rad2ndeg(lambda_), rad2deg(beta))

    nova_alpha1950 = hms2rad(17, 48, 59.74)
    nova_delta1950 = -dms2rad(14, 43, 8.2)
    l, b = equa2galac(nova_alpha1950, nova_delta1950)
    print('6', rad2ndeg(l), rad2deg(b))
