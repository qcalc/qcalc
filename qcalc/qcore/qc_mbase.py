# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qutil import sort_by_val, category_slug
import re

_base_names = ['m', 'kg', 's', 'A', 'K', 'mol', 'cd', 'rad', 'sr', 'USD']  # SI, MKS
_base_dimensions = ['L', 'M', 'T', 'I', 'Θ', 'N', 'J', 'P', 'S', 'C']

_conv_names = ['ft', 'lb', 'min', 'bi', 'K', 'mol', 'cd', 'deg', 'sphere', 'USD']
_unit_operators = ['**', '^', '*', '/', '!', '(', ')']

_fps_names = ['ft', 'lb', 's', 'A', 'K', 'mol', 'cd', 'rad', 'sr', 'USD']
_cgs_names = ['cm', 'g', 's', 'A', 'K', 'mol', 'cd', 'rad', 'sr', 'USD']

_base_categories = {
    "0": "Unitless",
    "I": "Electric current",
    "J": "Luminous intensity",
    "JS": "Luminous flux, Luminous power",
    "LMT-1": "Momentum, Impulse",
    "LMT-2I-2": "Permeability",
    "LMT-2": "Force, Weight",
    "LMT-2P": "Centrifugal force",
    "LMT-3I-1": "Electric field strength",
    "LMT-3Θ-1": "Thermal conductivity",
    "LTI": "Electric dipole moment",
    "LT": "Absement",
    "LΘ": "LΘ",
    "LT-1": "Velocity",
    "LT-2": "Acceleration",
    "LT-3": "Jerk",
    "LT-4": "Jounce, Snap",
    "LT-5": "Crackle",
    "LT-6": "Pop",
    "L": "Length, Wavelength",
    "L-1I": "Magnetic field strength, Magnetization",
    "L-1MT-1": "Dynamic fluid viscosity",
    "L-1MT-2": "Pressure, Stress, Energy density, Spectral exposure (ln)",
    "L-1M": "Linear density",
    "L-1M-1T3Θ": "Thermal resistivity",
    "L-1Θ": "Temperature gradient",
    "L-1": "Optical power, Wavenumber, Wavevector",
    "L-2": "Fuel economy",
    "L-2I": "Current density",
    "L2I": "Magnetic moment, Magnetic dipole moment)",
    "L2T-1": "Viscosity",
    "L-2J": "Luminance",
    "L-2JS": "Illuminance",
    "L-2M-1T3I2": "Electrical conductance",
    "L-2M-1T3J": "Luminous efficacy",
    "L-2M-1T3JS": "Luminous efficacy (sr)",
    "L-2TJ": "Luminous exposure",
    "L-3TJ": "Luminous energy density",
    "L2MT-1": "Angular momentum, Action, Spin",
    "L2MT-2I-1": "Magnetic flux",
    "L2MT-2I-2": "Inductance",
    "L2MT-2N-1": "Chemical potential, Molar energy",
    "L2MT-2Θ-1N-1": "Molar entropy",
    "L2MT-2Θ-1": "Entropy, Heat capacity",
    "L2MT-2": "Energy, Work, Torque, Heat, Spectral flux (fr)",
    "L2MT-2S-1": "Spectral intensity (fr)",
    "LMT-3": "Spectral flux (ln)",
    "LMT-3S-1": "Spectral intensity (ln)",
    "L2MT-3I-1": "Electric potential",
    "L2MT-3I-2": "Impedance, Electrical resistance",
    "L2MT-3Θ-1": "Thermal conductance",
    "L2MT-3": "Power, Radiant flux",
    "L2MT-3S-1": "Radiant intensity",
    "L-2M": "Area density",
    "L-2MT-2": "Pressure gradient",
    "L2M": "Moment of inertia",
    "L-2M-1T2I2": "Reluctance, Electrical conductance",
    "L-2M-1T3Θ": "Thermal resistance",
    "L-2M-1T4I2": "Capacitance",
    "L-2TI": "Electric displacement field",
    "L2T-2Θ-1": "Specific heat capacity",
    "L2T-2": "Specific energy, Radioactive Dose",
    "L2T-3": "Absorbed dose rate",
    "L2": "Area",
    "L3MT-3I-2": "Electrical resistivity",
    "L3MT-4I-2": "L3MT-4I-2",
    "L-3M": "Mass Density, Volume density, Concentration",
    "L-3M-1T3I2": "Electrical conductivity",
    "L-3M-1T4I2": "Permittivity",
    "L3M-1": "Specific volume",
    "L3M-1T-2": "L3M-1T-2",
    "L-3N": "Molar concentration",
    "L-3TI": "Electric charge density",
    "L-3T-1N": "Catalytic activity concentration, Reaction rate",
    "L3T-1": "Volume flow rate",
    "L3": "Volume",
    "L3T-2": "Gravitational Parameter",
    "L3N-1": "Molar volume",
    "L4MT-3": "L4MT-3",
    "L4MT-3S-1": "L4MT-3S-1",
    "M": "Mass",
    "MT-1": "Mass flow rate, Spectral exposure (fr)",
    "MT-2I-1": "Magnetic flux density",
    "MT-2": "Surface tension, Spectral irradiance (fr)",
    "MT-2S-1": "Specific intensity (fr)",
    "L-1MT-3S-1": "Specific intensity (ln)",
    "L-1MT-3": "Spectral irradiance (ln)",
    "MT-3S-1": "Radiance",
    "MT-3": "Irradiance, Heat flux density, Radiosity",
    "MN-1": "Molar mass",
    "M-1T3Θ": "Thermal resistance coefficient",
    "MT-3Θ-4": "MT-3Θ-4",
    "M-1TI": "M-1TI",
    "N": "Amount of substance",
    "N-1": "N-1",
    "P": "Plane angle",
    "S": "Solid angle",
    "TI": "Electric charge",
    "TIN-1": "TIN-1",
    "TJ": "Luminous energy",
    "T": "Time, Half-life, Labour",
    "T-1": "Periodic Rate, Frequency, Heart Rate",
    "T-1Θ-1": "T-1Θ-1",
    "T-1P": "Angular velocity, Radioactive activity",
    "T-2P": "Angular acceleration",
    "Θ": "Temperature",
    "C": "Currency",
}

_base_categories = sort_by_val(_base_categories)  # dict {dim: desc}
_base_categ_list = list(zip(_base_categories.keys(), _base_categories.values()))  # list (dim, desc)
_base_slugs = [category_slug(v) for v in _base_categories.values()]
assert len(_base_slugs) == len(set(_base_slugs))
_base_categ_d2s = dict(zip(_base_categories.keys(), _base_slugs))  # dict {dim: slug}
_base_categ_s2d = dict(zip(_base_slugs, _base_categories.keys()))  # dict {slug: dim}
_base_categ_list2 = list(zip(_base_slugs, _base_categories.values()))  # list (slug, desc)


def lmt_title(dim):
    return _base_categories[dim]


def dim_to_bname(dim, unames):  # unames can be either _base_names or _conv_names
    # dim = 'L-1MT-2SP2'
    lmt = re.split(r'([LMTIΘNJPSC])', dim)[1:]
    powers = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    for i in range(0, len(lmt) - 1, 2):
        if lmt[i + 1] == '':
            lmt[i + 1] = 1
        else:
            lmt[i + 1] = int(lmt[i + 1])

        for j, bdim in enumerate(_base_dimensions):
            if lmt[i] == bdim:
                powers[j] = lmt[i + 1]
                break
    uname, cdim = powers_to_bname_lmt(powers, unames)
    return uname


def powers_to_bname_lmt(powers, unames):  # unames can be either _base_names or _conv_names
    p1 = ''
    p2 = ''
    lmt = ''
    for i, p in enumerate(powers):
        if p == 0:
            continue
        elif p == 1:
            p1 += '*' + unames[i]
            lmt += _base_dimensions[i]
        elif p == -1:
            p2 += '/' + unames[i]
            lmt += _base_dimensions[i] + '-1'
        elif p > 1:
            p1 += '*' + unames[i] + '^' + str(p)
            lmt += _base_dimensions[i] + str(p)
        elif p < -1:
            p2 += '/' + unames[i] + '^' + str(abs(p))
            lmt += _base_dimensions[i] + str(p)

    # strip off the trailing blank if any
    lmt = lmt.strip()
    if lmt == '': lmt = '0'
    if p1 != '':
        p1 = p1[1:]  # remove the . from the start
    if p1 == '' and p2 == '':
        bn = ''
    elif p2 == '':
        bn = p1
    elif p1 == '':
        bn = '1' + p2
    else:
        bn = p1 + p2
    return bn, lmt


_prefixes = [
    ('quetta', 1.e30, 'quetta'),
    ('ronna', 1.e27, 'ronna'),
    ('yotta', 1.e24, 'yotta'),
    ('zetta', 1.e21, 'zetta'),
    ('exa', 1.e18, 'exa'),
    ('peta', 1.e15, 'peta'),
    ('tera', 1.e12, 'tera'),
    ('giga', 1.e9, 'giga'),
    ('mega', 1.e6, 'mega'),
    ('kilo', 1.e3, 'kilo'),
    ('hecto', 1.e2, 'hecto'),
    ('deca', 1.e1, 'deca'),
    ('deci', 1.e-1, 'deci'),
    ('centi', 1.e-2, 'centi'),
    ('milli', 1.e-3, 'milli'),
    ('micro', 1.e-6, 'micro'),
    ('nano', 1.e-9, 'nano'),
    ('pico', 1.e-12, 'pico'),
    ('femto', 1.e-15, 'femto'),
    ('atto', 1.e-18, 'atto'),
    ('zepto', 1.e-21, 'zepto'),
    ('yocto', 1.e-24, 'yocto'),
    ('ronto', 1.e-27, 'ronto'),
    ('quecto', 1.e-30, 'quecto'),
    ('th', 1.e3, 'Thousand'),
    ('lac', 1.e5, 'Lac'),
    ('mn', 1.e6, 'Million'),
    ('cr', 1.e7, 'Crore'),
    ('bn', 1.e9, 'Billion'),
    ('tn', 1.e12, 'Trillion'),
]


def base_dims():
    return _base_dimensions

_prefix_list = [pf[0] for pf in _prefixes]

def prefixes():
    return _prefix_list
