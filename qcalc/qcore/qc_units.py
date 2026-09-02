# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore.qc_mbase import _base_names, _conv_names, lmt_title, dim_to_bname, _prefix_list,_prefixes
from qcore.qc_munit import MeasureUnit, isMeasureUnit
from qutil import iif, preprocess_expression
import numpy as np

_base_units = [
    ('m', MeasureUnit('m', 1., [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'meter'),
    ('g', MeasureUnit('g', 0.001, [0, 1, 0, 0, 0, 0, 0, 0, 0, 0]), 'gram'),
    ('s', MeasureUnit('s', 1., [0, 0, 1, 0, 0, 0, 0, 0, 0, 0]), 'second'),
    ('A', MeasureUnit('A', 1., [0, 0, 0, 1, 0, 0, 0, 0, 0, 0]), 'ampere'),
    ('K', MeasureUnit('K', 1., [0, 0, 0, 0, 1, 0, 0, 0, 0, 0]), 'Kelvin'),
    ('mol', MeasureUnit('mol', 1., [0, 0, 0, 0, 0, 1, 0, 0, 0, 0]), 'mole'),
    ('cd', MeasureUnit('cd', 1., [0, 0, 0, 0, 0, 0, 1, 0, 0, 0]), 'candela'),
    ('rad', MeasureUnit('rad', 1., [0, 0, 0, 0, 0, 0, 0, 1, 0, 0]), 'radian'),
    ('sr', MeasureUnit('sr', 1., [0, 0, 0, 0, 0, 0, 0, 0, 1, 0]), 'steradian'),
    ('USD', MeasureUnit('USD', 1., [0, 0, 0, 0, 0, 0, 0, 0, 0, 1]), 'US dollar'),
]

_unitless = [
    ('bit', 1, 'bit'),
    ('byte', 8, 'Byte'),
    ('px', 1, 'pixel'),
    ('pixel', 1, 'pixel'),
    ('rem16', '16*pixel', 'rootem'),
    ('KB', 8 * 2 ** 10, 'Kilobyte'),
    ('MB', 8 * 2 ** 20, 'Megabyte'),
    ('GB', 8 * 2 ** 30, 'Gigabyte'),
    ('TB', 8 * 2 ** 40, 'Terabyte'),
    ('PB', 8 * 2 ** 50, 'Petabyte'),
    ('EB', 8 * 2 ** 60, 'Exabyte'),
    ('ZB', 8 * 2 ** 70, 'Zettabyte'),
    ('YB', 8 * 2 ** 80, 'Yottabyte'),
    ('kbit', 1.e3, 'kilobit'),
    ('mbit', 1.e6, 'megabit'),
    ('gbit', 1.e9, 'gigabit'),
    ('tbit', 1.e12, 'terabit'),
    ('pbit', 1.e15, 'petabit'),
    ('ebit', 1.e18, 'exabit'),
    ('zbit', 1.e21, 'zettabit'),
    ('ybit', 1.e24, 'yottabit'),
]


def _add_unitless():
    for unitless in _prefixes + _unitless:
        _add_unit(
            unitless[0], MeasureUnit(unitless[0], unitless[1],
                                     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]), unitless[2], '', 'Unitless')


def _add_all_units():
    # Unitless

    _add_unit('unit', MeasureUnit('unit', 1, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'single unit')
    _add_unit('beat', '1*unit', 'heart beat')
    _add_unit('bag', '1*unit', '')
    _add_unit('bale', '5000*unit', '')
    _add_unit('bundle', '1000*unit', '')
    _add_unit('dozen', '12*unit', '')
    _add_unit('ea', '1*unit', 'each')
    _add_unit('gross', '144*unit', '')
    _add_unit('hali', '4*unit', 'four piece')
    _add_unit('hd', '100*unit', 'hundred')
    _add_unit('myria', '10000*unit', '')
    _add_unit('person', '1*unit', '')
    _add_unit('nos', '1*unit', 'numbers')
    _add_unit('pair', '2*unit', '')
    _add_unit('pct', '0.01*unit', 'percent')
    _add_unit('ppm', '0.000001*unit', 'parts per million')
    _add_unit('quire', '25*unit', '')
    _add_unit('ream', '500*unit', '')
    # _add_unit('e', MeasureUnit('e', 2.30258509299404, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]), '')  # e is a value

    # _add_unit( 1. unit name, 2. physical unit object / conversion string 3. long name 4. comment )

    _add_unit('kg', MeasureUnit('kg', 1, [0, 1, 0, 0, 0, 0, 0, 0, 0, 0]), 'kilogram')
    _add_unit('Hz', '1/s', 'hertz')
    _add_unit('bpm', MeasureUnit('bpm', 1, [0, 0, -1, 0, 0, 0, 0, 0, 0, 0]), 'beats per minute')
    _add_unit('bph', 'bpm/60', 'beats per hour')
    _add_unit('N', 'm*kg/s**2', 'newton')
    _add_unit('Pa', 'N/m**2', 'pascal')
    _add_unit('J', 'N*m', 'joule')
    _add_unit('W', 'J/s', 'watt')
    _add_unit('kW', '1000*W', 'kilowatt')
    _add_unit('MW', '1000*kW', 'megawatt')
    _add_unit('Clm', 's*A', 'coulomb')
    # dup_add_unit('C', 's*A', 'coulomb')
    _add_unit('V', 'W/A', 'volt')
    # dup_add_unit('F', 'C/V', 'farad')
    _add_unit('F', 'Clm/V', 'farad')
    _add_unit('ohm', 'V/A', 'ohm')
    # dup_add_unit('S', 'A/V', 'siemens')
    _add_unit('Si', 'A/V', 'siemens')
    _add_unit('Wb', 'V*s', 'weber')
    # _add_unit('T', 'Wb/m**2', 'tesla')
    _add_unit('Ts', 'Wb/m**2', 'tesla')
    _add_unit('tesla', '1*Ts', 'tesla')
    # dup_add_unit('H', 'Wb/A', 'henry')
    _add_unit('Hn', 'Wb/A', 'henry')
    _add_unit('lm', 'cd*sr', 'lumen')
    _add_unit('lx', 'lm/m**2', 'lux')
    _add_unit('Bq', '1/s', 'becquerel')
    _add_unit('Gy', 'J/kg', 'gray')
    _add_unit('Sv', 'J/kg', 'sievert')

    # Fundamental constants
    # https://en.wikipedia.org/wiki/List_of_physical_constants#Table_of_physical_constants
    # https://www.bipm.org/en/measurement-units/si-defining-constants
    _add_unit('hfCs', '9192631770/s', 'caesium hyperfine frequency',
              '#1 of 7 SI Defining constants', "universal physical constant")
    _add_unit('c', '299792458*m/s', 'speed of light in vacuum',
              '#2 of 7 SI Defining constants', "universal physical constant")
    _add_unit('hplanck', '6.62607015e-34*J*s', 'planck constant',
              '#3 of 7 SI Defining constants', "universal physical constant")
    _add_unit('hbar', 'hplanck/(2*pi)', 'reduced planck constant',
              'also called Dirac constant', "physical constant")
    _add_unit('ec', '1.602176634e-19*Clm', 'electron charge',
              '#4 of 7 SI Defining constants', "universal physical constant")
    _add_unit('k_B', '1.380649e-23*J/K', 'boltzmann constant',
              '#5 of 7 SI Defining constants', "universal physical constant")
    _add_unit('Nav', '6.02214076e23/mol', 'avogadro constant',
              '#6 of 7 SI Defining constants', "universal physical constant")
    _add_unit('Kcd', '683.002*lm/W', 'luminous efficacy of a defined visible radiation',
              '#7 of 7 SI Defining constants', "universal physical constant")
    _add_unit('mu0', '4.e-7*pi*N/A**2', 'permeability of vacuum',
              '', "physical constant")
    _add_unit('eps0', '1/mu0/c**2', 'permittivity of vacuum',
              '', "physical constant")
    # dup_add_unit('G', '6.67259e-11*m**3/kg/s**2', 'gravitational constant')
    _add_unit('Gv', '6.6743015e-11*m**3/kg/s**2', 'gravitational constant',
              '', "physical constant")
    _add_unit('k_e', '1/4/pi/eps0', 'coulomb constant',
              '', "physical constant")
    _add_unit('cosmo', '1.0829e-52/m**2', 'cosmological constant',
              '', "physical constant")
    _add_unit('sigma_sb', '5.670374419e-8*W/K**4/m**2', 'stefan boltzman constant',
              '', 'physical constant')
    _add_unit('c1', '2*pi*hplanck*c**2', 'first radiation constant',
              '', 'physical constant')
    _add_unit('c1L', '2*hplanck*c**2/sr', 'first radiation constant for spectral radiance',
              '', 'physical constant')
    _add_unit('c2', 'hplanck*c/k_B', 'second radiation constant',
              '', 'physical constant')
    _add_unit('bw_wien', '2.897771955e-3*m*K', 'wien wavelength displacement law constant',
              '', 'physical constant')
    _add_unit('bf_wien', '5.878925757e10/s/K', 'wien frequency displacement law constant',
              '', 'physical constant')
    _add_unit('be_wien', '3.002916077e-3*m*K', 'wien entropy displacement law constant',
              '', 'physical constant')

    _add_unit('lplanck', '(hbar*Gv/c**3)**0.5', 'planck length',
              'approx. 1.61625518e-35*m', "physical constant")
    _add_unit('mplanck', '(hbar*c/Gv)**0.5', 'planck mass',
              'approx. 2.17643424e-8*kg', "physical constant")
    _add_unit('tplanck', 'lplanck/c', 'planck time',
              'approx. 5.39124760e-44*s', "physical constant")
    _add_unit('kplanck', '1.41678416e32*K', 'planck temperature',
              '', "physical constant")

    # to avoid name conflict with math.e, electron charge 'e' renamed to 'ec'
    _add_unit('m_e', '9.109383713928e-31*kg', 'electron mass',
              '', "physical constant")
    _add_unit('m_mu', '1.88353162742e-28*kg', 'muon mass',
              '', "physical constant")
    _add_unit('m_tau', '3.1675421e-27*kg', 'tau mass',
              '', "physical constant")
    _add_unit('m_p', '1.6726219259552e-27*kg', 'proton mass',
              '', "physical constant")
    _add_unit('m_n', '1.6749275005685e-27*kg', 'neutron mass',
              '', "physical constant")
    _add_unit('m_tq', '3.078453e-25*kg', 'top quark mass',
              '', "physical constant")
    _add_unit('mr_pe', 'm_p/m_e', 'proton to electron mass ratio',
              'approx. 1836.15267342', "physical constant")

    _add_unit('mu_B', '9.274010065729e-24*J/Ts', 'bohr magneton',
              '', 'physical constant')
    _add_unit('Ryd', '10973731.56815712/m', 'rydberg constant',
              '', "physical constant")
    _add_unit('Rg', '8.31446261815324*J/mol/K', 'molar gas constant',
              '', "physical constant")
    _add_unit('m_a', '1.6605390689252e-27*kg', 'atomic mass constant',
              '', "physical constant")
    _add_unit('m_m', '1.0000000010531e-3*kg/mol', 'molar mass constant',
              '', "physical constant")
    _add_unit('Fd', '96485.3321233100184*Clm/mol', 'faraday constant',
              '', "physical constant")

    _add_unit('L_sun', '3.828E+26*W', 'nominal solar luminosity',
              '', 'physical constant')
    _add_unit('sigma_T', '6.65245873E-29*m**2', 'thomson scattering',
              '', 'physical constant')
    _add_unit('L_bol0', '3.0128E+28*W', 'luminosity for absolute bolometric magnitude',
              '', 'physical constant')

    # Time units

    _add_unit('min', '60*s', 'minute')
    # did not rename 'min' to 'mnt' to avoid conflict with min(), rewrite min() as minimum()
    _add_unit('minute', '60*s', 'minute')
    _add_unit('h', '60*min', 'hour')
    _add_unit('hr', '1*h', 'hour')
    _add_unit('d', '24*h', 'day')
    _add_unit('day', '1*d', 'day')
    _add_unit('sec', '1*s', 'second')
    _add_unit('ss2', '1/2*s', 'half-second')
    _add_unit('ss4', '1/4*s', 'one-fourth second')
    _add_unit('ss8', '1/8*s', 'one-eighth second')
    _add_unit('ss15', '1/15*s', 'one-fifteenth second')
    _add_unit('ss30', '1/30*s', 'one-thirtieth second')
    _add_unit('ss60', '1/60*s', 'one-sixtieth second')
    _add_unit('ss125', '1/125*s', '0.008 second')
    _add_unit('ss250', '1/250*s', '0.004 second')
    _add_unit('ss500', '1/500*s', '0.002 second')
    _add_unit('ss1000', '1/1000*s', '0.001 second')
    _add_unit('ms', '0.001*s', 'millisecond')
    _add_unit('mics', '1e-6*s', 'microsecond')
    _add_unit('ns', '1e-9*s', 'nanosecond')
    _add_unit('wk', '7*d', 'week')
    _add_unit('fortnight', '14*d', '')
    _add_unit('yr', '365.25*d', 'year')
    _add_unit('mo', 'yr/12', 'month')
    _add_unit('bimo', '2*mo', 'bi-month')
    _add_unit('qrtr', '3*mo', 'quarter')
    _add_unit('halfyr', '6*mo', 'half-year')

    # periodic rate
    _add_unit('peryr', '1/yr', 'per year')
    _add_unit('permo', '1/mo', 'per month')
    _add_unit('perday', '1/day', 'per day')
    _add_unit('perhr', '1/hr', 'per hour')
    _add_unit('persec', '1/s', 'per second')
    _add_unit('permin', '1/min', 'per minute')

    _add_unit('dsr', MeasureUnit('dsr', 86164.09, [0, 0, 1, 0, 0, 0, 0, 0, 0, 0]), 'sidereal day')
    _add_unit('hsr', MeasureUnit('hsr', 3590.17, [0, 0, 1, 0, 0, 0, 0, 0, 0, 0]), 'sidereal hour')
    _add_unit('minsr', MeasureUnit('minsr', 59.83617, [0, 0, 1, 0, 0, 0, 0, 0, 0, 0]), 'sidereal minute')
    _add_unit('prahar', MeasureUnit('prahar', 10800, [0, 0, 1, 0, 0, 0, 0, 0, 0, 0]), 'three hour')
    _add_unit('shake', MeasureUnit('shake', 0.00000001, [0, 0, 1, 0, 0, 0, 0, 0, 0, 0]), 'ten nanosecond')
    _add_unit('ssr', MeasureUnit('ssr', 0.9972696, [0, 0, 1, 0, 0, 0, 0, 0, 0, 0]), 'sidereal second')
    _add_unit('yrsr', MeasureUnit('yrsr', 31558150, [0, 0, 1, 0, 0, 0, 0, 0, 0, 0]), 'sidereal year')
    _add_unit('yrtp', MeasureUnit('yrtp', 31556927, [0, 0, 1, 0, 0, 0, 0, 0, 0, 0]), 'tropical year')
    _add_unit('thyr', '1e3*yr', 'thousand year')
    _add_unit('lcyr', '1e5*yr', 'lac year')
    _add_unit('mnyr', '1e6*yr', 'million year')
    _add_unit('cryr', '1e7*yr', 'crore year')
    _add_unit('bnyr', '1e9*yr', 'billion year')

    _add_unit('quectosec', '1.e-30*s', 'quectosecond')
    _add_unit('rontosec', '1.e-27*s', 'rontosecond')
    _add_unit('yottasec', '1.e24*s', 'yottasecond')
    _add_unit('zettasec', '1.e21*s', 'zettasecond')
    _add_unit('exasec', '1.e18*s', 'exasecond')
    _add_unit('petasec', '1.e15*s', 'petasecond')
    _add_unit('terasec', '1.e12*s', 'terasecond')
    _add_unit('gigasec', '1.e9*s', 'gigasecond')
    _add_unit('megasec', '1.e6*s', 'megasecond')
    _add_unit('kilosec', '1.e3*s', 'kilosecond')
    _add_unit('hectosec', '1.e2*s', 'hectosecond')
    _add_unit('decasec', '1.e1*s', 'decasecond')
    _add_unit('decisec', '1.e-1*s', 'decisecond')
    _add_unit('centisec', '1.e-2*s', 'centisecond')
    _add_unit('millisec', '1.e-3*s', 'millisecond')
    _add_unit('microsec', '1.e-6*s', 'microsecond')
    _add_unit('nanosec', '1.e-9*s', 'nanosecond')
    _add_unit('picosec', '1.e-12*s', 'picosecond')
    _add_unit('femtosec', '1.e-15*s', 'femtosecond')
    _add_unit('attosec', '1.e-18*s', 'attosecond')
    _add_unit('zeptosec', '1.e-21*s', 'zeptosecond')
    _add_unit('yoctosec', '1.e-24*s', 'yoctosecond')
    _add_unit('ronaatosec', '1.e27*s', 'roanatosecond')
    _add_unit('quettasec', '1.e30*s', 'quettasecond')

    # Labour units
    _add_unit('manhr', '1*h', 'man hour')
    _add_unit('manday', '8*h', 'man day')
    _add_unit('manmo', '30*manday', 'man month')
    _add_unit('manyr', '365*manday', 'man year')

    # Length units

    _add_unit('cm', MeasureUnit('cm', 0.01, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'centimeter')
    _add_unit('inch', '2.54*cm', 'inch')
    _add_unit('ft', '12*inch', 'foot', 'us_ft')
    _add_unit('yd', '3*ft', 'yard')
    _add_unit('mi', '5280.*ft', 'british mile')
    _add_unit('mile', '5280.*ft', 'british mile')
    _add_unit('nmi', '1852.*m', 'nautical mile')
    _add_unit('Angs', '1.e-10*m', 'angstrom')
    _add_unit('lyr', 'c*yr', 'light year')
    _add_unit('lhr', 'c*hr', 'light hour')
    _add_unit('lmin', 'c*s*60', 'light minute')
    _add_unit('lsec', 'c*s', 'light second')
    _add_unit('a0', '4*pi*eps0*hbar**2/m_e/ec**2', 'bohr radius')

    _add_unit('chain', '66*ft', 'chain')
    _add_unit('ch', '66*ft', 'chain')
    _add_unit('link', '0.66*ft', 'link')
    _add_unit('fur', '660*ft', 'furlong')
    _add_unit('angstrom', MeasureUnit('angstrom', 0.0000000001, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]), '', '')
    _add_unit('au', MeasureUnit('au', 149597900000, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'astronomical unit', '')
    _add_unit('che', '100*ft', 'hundred feet')
    _add_unit('chg', '66*ft', 'chain')
    _add_unit('em', '6378000*m', 'earth radius')
    _add_unit('fath', MeasureUnit('fath', 1.828804, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'fathom', '')
    # _add_unit('fm', MeasureUnit('fm', 1, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]), '', '')
    _add_unit('hat', MeasureUnit('hat', 0.4572, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]), '', '')
    _add_unit('km', MeasureUnit('km', 1000, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'kilometer', '')
    _add_unit('lie', MeasureUnit('lie', 0.3048, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'linear inch', '')
    _add_unit('lig', MeasureUnit('lig', 0.201168, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'gunter link', '')
    _add_unit('microinch', MeasureUnit('microinch', 0.0000000254, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]), '', '')
    _add_unit('micron', MeasureUnit('micron', 0.000001, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'micrometer', '')
    _add_unit('mil', MeasureUnit('mil', 0.0000254, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'milli-inch', '')
    _add_unit('us_mi', MeasureUnit('us_mi', 1609.347, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'us survey mile', '')
    _add_unit('mm', MeasureUnit('mm', 0.001, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'millimeter', '')
    _add_unit('pc', MeasureUnit('pc', 30856780000000000, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'parsec', '')
    _add_unit('kpc', '1000*pc', 'kiloparsec', '')
    _add_unit('pica', MeasureUnit('pica', 0.00423333333333333, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'postscript pica', '')
    _add_unit('picaprn', MeasureUnit('picaprn', 0.004217518, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'printer pica', '')
    _add_unit('pt', MeasureUnit('pt', 0.0003527778, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'point of meter', '')
    _add_unit('ptprn', MeasureUnit('ptprn', 0.0003514598, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]), '', '')
    _add_unit('rod', MeasureUnit('rod', 5.02921, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'rod', '')
    _add_unit('sm', MeasureUnit('sm', 696000000, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'solar radius', '')
    _add_unit('sut', MeasureUnit('sut', 0.003175, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'sute', '')
    _add_unit('xu', MeasureUnit('xu', 0.0000000000001002, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'x unit', '')
    _add_unit('nam', '1e-9*m', 'nanometer')

    _add_unit('quettam', '1.e30*m', 'quettameter')
    _add_unit('ronaatom', '1.e27*m', 'roanatometer')
    _add_unit('yottam', '1.e24*m', 'yottameter')
    _add_unit('zettam', '1.e21*m', 'zettameter')
    _add_unit('exam', '1.e18*m', 'exameter')
    _add_unit('petam', '1.e15*m', 'petameter')
    _add_unit('teram', '1.e12*m', 'terameter')
    _add_unit('gigam', '1.e9*m', 'gigameter')
    _add_unit('megam', '1.e6*m', 'megameter')
    _add_unit('kilom', '1.e3*m', 'kilometer')
    _add_unit('hectom', '1.e2*m', 'hectometer')
    _add_unit('decam', '1.e1*m', 'decameter')
    _add_unit('decim', '1.e-1*m', 'decimeter')
    _add_unit('centim', '1.e-2*m', 'centimeter')
    _add_unit('millim', '1.e-3*m', 'millimeter')
    _add_unit('microm', '1.e-6*m', 'micrometer')
    _add_unit('nanom', '1.e-9*m', 'nanometer')
    _add_unit('picom', '1.e-12*m', 'picometer')
    _add_unit('femtom', '1.e-15*m', 'femtometer')
    _add_unit('attom', '1.e-18*m', 'attometer')
    _add_unit('zeptom', '1.e-21*m', 'zeptometer')
    _add_unit('yoctom', '1.e-24*m', 'yoctometer')
    _add_unit('rontom', '1.e-27*m', 'rontometer')
    _add_unit('quectom', '1.e-30*m', 'quectometer')

    _add_unit('fermi', '1.e-15*m', 'femtometer')

    # Area units

    _add_unit('ha', '10000*m**2', 'hectare')
    _add_unit('b', '1.e-28*m**2', 'barn')

    _add_unit('us_acre', MeasureUnit('us_acre', 4046.8726098, [2, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'us acre')
    _add_unit('are', MeasureUnit('are', 100, [2, 0, 0, 0, 0, 0, 0, 0, 0, 0]), '')
    _add_unit('cunit', MeasureUnit('cunit', 2.8316846592, [2, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'cue nit', 'wood volume')
    _add_unit('darcy', MeasureUnit('darcy', 9.869233E-13, [2, 0, 0, 0, 0, 0, 0, 0, 0, 0]), '')
    _add_unit('sqm', '1*m*m', 'square meter')
    _add_unit('sft', '1*ft*ft', 'square foot')
    _add_unit('sqft', '1*sft', 'square foot')
    _add_unit('sqyd', '9*sft', 'square yard')
    _add_unit('sqlink', '1*link*link', 'square link')
    _add_unit('chhotak', '45*sft', 'chhotak', 'Land area unit, India')
    _add_unit('katha', '720*sft', '', 'Land area unit, India')
    _add_unit('bigha', '20*katha', '', 'Land area unit, India')
    _add_unit('acre', '4840*sqyd', '', 'Land area unit, India')
    _add_unit('decimal', '48.40*sqyd', '', 'Land area unit, India')
    _add_unit('shotok', '1*decimal', 'shotangsho', 'Land area unit, India')
    _add_unit('til', '3.6*sft', '', 'Land area unit, India')
    _add_unit('kranti', '20*til', '', 'kontho or kranti, Land area unit, India')
    _add_unit('donto', '12*sft', '', 'Land area unit, India')
    _add_unit('renu', '12/210*sft', '', 'Land area unit, India')
    _add_unit('dhul', '30*renu', '', 'Land area unit, India')
    _add_unit('kora', '3*kranti', '', 'Land area unit, India')
    _add_unit('gonda', '4*kora', '', 'Land area unit, India')
    _add_unit('kani', '20*gonda', '', 'Land area unit, India')
    _add_unit('milc', MeasureUnit('milc', 0.0000000005067075, [2, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'circular mil')
    _add_unit('rood', MeasureUnit('rood', 1011.7141056, [2, 0, 0, 0, 0, 0, 0, 0, 0, 0]), '')
    _add_unit('sqkm', '1*km*km', 'square kilometer')
    _add_unit('sqmi', '1*mi*mi', 'square mile')
    _add_unit('m2', '1*sqm', 'square meter')
    _add_unit('ft2', '1*sqft', 'square foot')
    _add_unit('yd2', '1*sqyd', 'square yard')
    _add_unit('link2', '1*sqlink', 'square link')
    _add_unit('km2', '1*sqkm', 'square kilometer')
    _add_unit('mi2', '1*sqmi', 'square mile')

    # Volume units

    _add_unit('L', '0.001*m**3', 'liter')
    _add_unit('dL', '0.1*l', 'deciliter')
    _add_unit('cL', '0.01*l', 'centiliter')
    _add_unit('ml', '0.001*l', 'milliliter')
    _add_unit('teasp', '4.92892159375*ml', 'teaspoon', 'aliases: t or tsp')
    _add_unit('tblsp', '3*teasp', 'tablespoon', 'aliases: T, TB or tbsp')
    _add_unit('floz', '2*tblsp', 'fluid ounce')
    _add_unit('cup', '8*floz', 'cup', 'aliases: C or c')
    _add_unit('pint', '16*floz', 'pint', '')
    _add_unit('qt', '2*pint', 'quart')
    _add_unit('us_gal', '4*qt', 'us gallon')
    _add_unit('gal', '1*us_gal', 'us gallon')
    _add_unit('uk_gal', '4.54609*l', 'british gallon')

    _add_unit('cft', '1*ft**3', 'cubic foot', 'ft3 or ft^3')
    _add_unit('cum', '1*m**3', 'cubic meter', 'm3 or m^3')
    _add_unit('cucm', '1*cm**3', 'cubic centimeter', 'cm3 or cm^3')
    _add_unit('cm3', '1*cm**3', 'cubic centimeter')
    _add_unit('m3', '1*m**3', 'cubic meter')
    _add_unit('ft3', '1*ft**3', 'cubic foot')

    _add_unit('bbl', MeasureUnit('bbl', 0.1589873, [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'standrad barrel') # 42 us gallon
    _add_unit('bbl_oil', MeasureUnit('bbl_oil', 0.15899040557, [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'oil barrel')
    _add_unit('bu', MeasureUnit('bu', 0.03523907, [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'bushel')
    _add_unit('bushel', '1*bu', 'bushel')
    _add_unit('cc', MeasureUnit('cc', 0.000001, [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'cubic centimeter')
    _add_unit('cord', MeasureUnit('cord', 3.624556, [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]), '')
    _add_unit('cu', MeasureUnit('cu', 0.0002365882, [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'us cup')
    _add_unit('drygal', 'bu/8', 'dry gallons')
    _add_unit('peck', 'bu/4', 'peck')
    _add_unit('drypt', MeasureUnit('drypt', 0.0005506105, [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'dry pint')
    _add_unit('dryqt', MeasureUnit('dryqt', 0.001101221, [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'dry quart')
    _add_unit('fbm', MeasureUnit('fbm', 0.002359737216, [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'foot board measure')
    _add_unit('flozv', MeasureUnit('flozv', 0.00002957353, [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'us fluid ounce volume')
    _add_unit('gil', MeasureUnit('gil', 0.0001420653, [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'imperial gill')
    _add_unit('us_gil', MeasureUnit('us_gil', 0.0001182941, [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'us gill')
    _add_unit('lamv', MeasureUnit('lamv', 0.000000001, [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'lambda volume')
    _add_unit('liqpt', MeasureUnit('liqpt', 0.0004731765, [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'us liquid pint')
    _add_unit('liqqt', MeasureUnit('liqqt', 0.9463529, [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'us liquid quart')
    _add_unit('pk', MeasureUnit('pk', 0.008809768, [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'us dry peck')
    _add_unit('stere', MeasureUnit('stere', 1, [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]), '')
    # 'str' renamed to 'stere' which is the full form, to avoid conflict with str() function deb@04.04.24
    _add_unit('tr', MeasureUnit('tr', 2.831685, [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'ton of registry')

    # Mass units

    _add_unit('amu', '1.6605402e-27*kg', 'atomic mass unit')
    _add_unit('oz', '28.349523125*g', 'ounce')
    _add_unit('lb', '16*oz', 'pound')
    _add_unit('us_ton', '2000*lb', 'us ton', '2000 lb')
    _add_unit('ton', '2240*lb', 'uk ton', '2240 lb')
    _add_unit('uk_ton', '2240*lb', 'uk ton', '2240 lb')
    _add_unit('tonne', '1000*kg', 'metric tonne', '1000 kg')
    _add_unit('t', '1*tonne', 'metric tonne', '1000kg')
    _add_unit('pdl', '0.138254954376*N', 'poundal', '')  # 14.0867195652*g
    # https://en.wikipedia.org/wiki/Poundal # 0.138254954376*N 14.09808185*g

    _add_unit('us_bale_cotton', '480*lb', '')
    _add_unit('bale_jute', '180*kg', '')
    _add_unit('ct', '0.0002*kg', 'carat us')
    _add_unit('ctus', '0.0002*kg', 'carat us')
    _add_unit('cwt', '50.80235*kg', 'hundredweight')
    _add_unit('us_cwt', '45.35924*kg', 'us hundredweight')
    _add_unit('dram', '1.771845*g', 'avoirdupois dram')
    _add_unit('dwt', '1.555174*g', 'pennyweight')
    _add_unit('gmass', MeasureUnit('gmass', 0.000000001, [0, 1, 0, 0, 0, 0, 0, 0, 0, 0]), 'gamma mass')
    _add_unit('grain', '0.00006479891*kg', '')
    _add_unit('gm', '1*g', 'gram')
    _add_unit('lbt', MeasureUnit('lbt', 0.3732417, [0, 1, 0, 0, 0, 0, 0, 0, 0, 0]), 'troy pound')
    _add_unit('mg', '0.001*g', 'milligram')
    _add_unit('us_ozfl', '0.02957353*kg', '')
    _add_unit('oz_troy', '0.03110348*kg', '')
    _add_unit('oz_imp', '1*oz', 'oz imperial')
    _add_unit('pood', '16.3806872*kg', '')
    _add_unit('qter', '12.70059*kg', 'quarter')
    _add_unit('slug', '14.5939*kg', '')
    _add_unit('stone', '6.35029*kg', '')
    _add_unit('tas', MeasureUnit('tas', 0.02916667, [0, 1, 0, 0, 0, 0, 0, 0, 0, 0]), 'assay ton')
    _add_unit('vori', '11.6638125*g', 'gold vori', 'bhori, India')
    _add_unit('bhori', '1*vori', 'gold vori', 'bhori, India')
    _add_unit('anna', '1/16*vori', 'gold anna', 'ana, India')
    _add_unit('ana', '1*anna', 'gold anna', 'India')
    _add_unit('roti', '1/6*anna', 'gold roti', 'India')
    _add_unit('point', '1/10*roti', 'gold point', 'India, 10 point = 1 roti')
    _add_unit('tola', '1*vori', '', 'India')
    _add_unit('seer', '80*tola', '-', 'India')
    _add_unit('poa', '20*tola', '-', 'India')
    _add_unit('chtk', '5*tola', 'chhotak', 'India')
    _add_unit('maund', '40*seer', '-', 'India')

    _add_unit('quettagm', '1.e30*g', 'quettagram')
    _add_unit('ronaatogm', '1.e27*g', 'roanatogram')
    _add_unit('yottagm', '1.e24*g', 'yottagram')
    _add_unit('zettagm', '1.e21*g', 'zettagram')
    _add_unit('exagm', '1.e18*g', 'exagram')
    _add_unit('petagm', '1.e15*g', 'petagram')
    _add_unit('teragm', '1.e12*g', 'teragram')
    _add_unit('gigagm', '1.e9*g', 'gigagram')
    _add_unit('megagm', '1.e6*g', 'megagram')
    _add_unit('kilogm', '1.e3*g', 'kilogram')
    _add_unit('hectogm', '1.e2*g', 'hectogram')
    _add_unit('decagm', '1.e1*g', 'decagram')
    _add_unit('decigm', '1.e-1*g', 'decigram')
    _add_unit('centigm', '1.e-2*g', 'centigram')
    _add_unit('milligm', '1.e-3*g', 'milligram')
    _add_unit('microgm', '1.e-6*g', 'microgram')
    _add_unit('mcg', '1.e-6*g', 'microgram')
    _add_unit('nanogm', '1.e-9*g', 'nanogram')
    _add_unit('picogm', '1.e-12*g', 'picogram')
    _add_unit('femtogm', '1.e-15*g', 'femtogram')
    _add_unit('attogm', '1.e-18*g', 'attogram')
    _add_unit('zeptogm', '1.e-21*g', 'zeptogram')
    _add_unit('yoctogm', '1.e-24*g', 'yoctogram')
    _add_unit('rontogm', '1.e-27*g', 'rontogram')
    _add_unit('quectogm', '1.e-30*g', 'quectogram')

    # Concentration
    _add_unit('gpL', 'g/l', 'gram per deciliter')
    _add_unit('mgpdL', 'mg/dl', 'mg per deciliter')
    _add_unit('mmol_GCpL', '18.015588*mg/dl', 'mmol Glucose per liter')

    # Substance
    _add_unit('mmol', 'mol/1000', 'millimole')

    # Flow rate

    _add_unit('cumec', MeasureUnit('cumec', 1, [3, 0, -1, 0, 0, 0, 0, 0, 0, 0]), 'cubic_meter_per_second')
    _add_unit('cusec', '1*ft**3/s', 'cubic foot per second')
    _add_unit('cfs', '1*cusec', 'cubic foot per second')
    _add_unit('cfm', '60*cusec', 'cubic foot per minute')
    _add_unit('gpm', '1*us_gal/min', 'us gallon per minute')
    _add_unit('lpm', '1*l/min', 'liter per minute')
    _add_unit('mlpm', '1*ml/min', 'milliliter per minute')

    # Velocity

    _add_unit('knot', MeasureUnit('knot', 0.514444444444444, [1, 0, -1, 0, 0, 0, 0, 0, 0, 0]), '')
    _add_unit('kph', '1*km/h', 'kilometer per hour', 'aliases: kmph')
    _add_unit('mph', '1*mi/h', 'mile per hour', 'aliases: miph')

    # Acceleration unit

    _add_unit('g0', MeasureUnit('g0', 9.80665, [1, 0, -2, 0, 0, 0, 0, 0, 0, 0]), 'nominal earth gravity')
    # dup_add_unit('Gal', MeasureUnit('Gal', 0.01, [1, 0, -2, 0, 0, 0, 0, 0, 0, 0]), 'galileo')
    _add_unit('Ga', MeasureUnit('Ga', 0.01, [1, 0, -2, 0, 0, 0, 0, 0, 0, 0]), 'galileo')
    _add_unit('fps2', '1*ft/s**2', 'foot per square second', '')
    _add_unit('mps2', '1*m/s**2', 'meter per square second', '')

    # Force units

    _add_unit('kN', '1000*N', 'kilo newton')
    _add_unit('dyn', '1.e-5*N', 'dyne', 'CGS unit of force')
    _add_unit('gf', '1*g*g0', 'gram force')
    _add_unit('kgf', '1*kg*g0', 'kilogram force')
    _add_unit('kp', '1000*gf', 'kilopond', '1 kilopond = 1000 gram force')
    _add_unit('lbf', '1*lb*g0', 'pound force')
    _add_unit('kip', '1000*lbf', 'kilopound force')
    _add_unit('ozf', '1*oz*g0', 'ounce force')
    _add_unit('pdlf', 'pdl', 'poundal force')
    _add_unit('tf', 't*g0', 'tonne force')

    # Energy units

    _add_unit('erg', '1.e-7*J', '', 'CGS unit of energy')
    _add_unit('eV', 'ec*V', 'electron volt')
    _add_unit('Hartree', 'm_e*ec**4/16/pi**2/eps0**2/hbar**2', '', 'Wavenumbers/inverse cm')
    _add_unit('Ken', 'k_B*K', 'kelvin as energy')
    _add_unit('cal', '4.184*J', 'thermochemical calorie')
    _add_unit('kcal', '1000*cal', 'thermochemical kilocalorie')
    _add_unit('kJ', '1000*J', 'kilojule')
    _add_unit('Calorie', '1*kcal', 'nutrition calorie', 'Energy in nutrition and exercise, 1 Calorie = 1000 cal')
    _add_unit('calInt', '4.1868*J', 'international calorie')
    _add_unit('kcalInt', '1000*calInt', 'international kilocalorie')
    _add_unit('Btu', '1055.05585262*J', 'british thermal unit')

    _add_unit('Btu39F', MeasureUnit('Btu39F', 1059.67, [2, 1, -2, 0, 0, 0, 0, 0, 0, 0]), '')
    _add_unit('Btu59F', MeasureUnit('Btu59F', 1054.8, [2, 1, -2, 0, 0, 0, 0, 0, 0, 0]), '')
    _add_unit('Btu60F', MeasureUnit('Btu60F', 1054.68, [2, 1, -2, 0, 0, 0, 0, 0, 0, 0]), '')
    _add_unit('BtuTH', MeasureUnit('BtuTH', 1055.87, [2, 1, -2, 0, 0, 0, 0, 0, 0, 0]), '')
    _add_unit('cal15C', MeasureUnit('cal15C', 4.1858, [2, 1, -2, 0, 0, 0, 0, 0, 0, 0]), '')
    _add_unit('cal20C', MeasureUnit('cal20C', 4.1819, [2, 1, -2, 0, 0, 0, 0, 0, 0, 0]), '')
    _add_unit('calMean', MeasureUnit('calMean', 4.19002, [2, 1, -2, 0, 0, 0, 0, 0, 0, 0]), '')
    _add_unit('kcalMean', MeasureUnit('kcalMean', 4190.02, [2, 1, -2, 0, 0, 0, 0, 0, 0, 0]), '')
    _add_unit('kWh', MeasureUnit('kWh', 3600000, [2, 1, -2, 0, 0, 0, 0, 0, 0, 0]), 'kilowatt hour')
    _add_unit('unitpower', '1*kWh', 'unit electricity')
    _add_unit('Wh', 'kWh/1000', 'watt hour')
    _add_unit('MWh', '1000*kWh', 'megawatt hour')
    _add_unit('GWh', '1e6*kWh', 'gigawatt hour')
    _add_unit('mJ', MeasureUnit('mJ', 1000000, [2, 1, -2, 0, 0, 0, 0, 0, 0, 0]), 'megajule')
    _add_unit('quad', MeasureUnit('quad', 1055056000000000000, [2, 1, -2, 0, 0, 0, 0, 0, 0, 0]), 'quadrillion btu')
    _add_unit('therm', MeasureUnit('therm', 105506000, [2, 1, -2, 0, 0, 0, 0, 0, 0, 0]), '')
    _add_unit('us_therm', MeasureUnit('us_therm', 105480400, [2, 1, -2, 0, 0, 0, 0, 0, 0, 0]), '')
    _add_unit('tonTNT', MeasureUnit('tonTNT', 4184000000, [2, 1, -2, 0, 0, 0, 0, 0, 0, 0]), 'ton of tnt')
    _add_unit('kilotonTNT', '1000*tonTNT', 'kiloton of TNT')
    _add_unit('megatonTNT', '1e6*tonTNT', 'megaton of TNT')
    # dup_add_unit('wb', MeasureUnit('wb', 1, [2, 1, -2, -1, 0, 0, 0, 0, 0, 0]), '')
    _add_unit('ws', MeasureUnit('ws', 100000, [2, 1, -2, 0, 0, 0, 0, 0, 0, 0]), 'watt-second')

    # Power units

    _add_unit('hp', MeasureUnit('hp', 745.6999, [2, 1, -3, 0, 0, 0, 0, 0, 0, 0]), 'mechanical horsepower')
    _add_unit('hpb', MeasureUnit('hpb', 9809.5, [2, 1, -3, 0, 0, 0, 0, 0, 0, 0]), 'boiler horsepower')
    _add_unit('hpe', MeasureUnit('hpe', 746, [2, 1, -3, 0, 0, 0, 0, 0, 0, 0]), 'electrical horsepower')
    _add_unit('hpw', MeasureUnit('hpw', 746.043, [2, 1, -3, 0, 0, 0, 0, 0, 0, 0]), 'water Horsepower')
    _add_unit('uk_hp', MeasureUnit('uk_hp', 745.7, [2, 1, -3, 0, 0, 0, 0, 0, 0, 0]), 'uk horsepower')
    _add_unit('us_hp', MeasureUnit('us_hp', 735.4988, [2, 1, -3, 0, 0, 0, 0, 0, 0, 0]), 'us horsepower')
    _add_unit('sw', MeasureUnit('sw', 3.9E+26, [2, 1, -3, 0, 0, 0, 0, 0, 0, 0]), 'solar watt')
    # dup_add_unit('w', MeasureUnit('w', 1, [2, 1, -3, 0, 0, 0, 0, 0, 0, 0]), '')

    # Area density
    _add_unit('GSM', '1.0*g/m**2', 'gram per square meter')

    # Pressure units

    _add_unit('hPa', '100.0*Pa', 'hecto pascal')
    _add_unit('kPa', '1000.0*Pa', 'kilo pascal')
    _add_unit('MPa', '1e6*Pa', 'mega pascal')
    _add_unit('bar', '1.e5*Pa', 'bar')
    _add_unit('atm', '101325.*Pa', 'standard atmosphere')
    _add_unit('torr', 'atm/760', 'mm of mercury')
    _add_unit('mmHg', '1.0*torr', 'mm of mercury')
    _add_unit('psi', '6894.75729317*Pa', 'poundf per square inch')
    _add_unit('psf', '1/144*psi', 'poundf per square foot')
    _add_unit('atmtech', MeasureUnit('atmtech', 98066.5, [-1, 1, -2, 0, 0, 0, 0, 0, 0, 0]), 'technical atmosphere')
    _add_unit('cmH2O', MeasureUnit('cmH2O', 98.0665, [-1, 1, -2, 0, 0, 0, 0, 0, 0, 0]), 'cm water')
    _add_unit('cmH2O4C', MeasureUnit('cmH2O4C', 98.0638, [-1, 1, -2, 0, 0, 0, 0, 0, 0, 0]), 'cm water at 4 degC')
    _add_unit('cmHg', MeasureUnit('cmHg', 1333.224, [-1, 1, -2, 0, 0, 0, 0, 0, 0, 0]), 'cm mercury')
    _add_unit('cmHg0C', MeasureUnit('cmHg0C', 1333.22, [-1, 1, -2, 0, 0, 0, 0, 0, 0, 0]), 'cm mercury at 0 degC')
    _add_unit('ftH2O', MeasureUnit('ftH2O', 2989.067, [-1, 1, -2, 0, 0, 0, 0, 0, 0, 0]), 'feet water')
    _add_unit('ftH2O39F', MeasureUnit('ftH2O39F', 2988.98, [-1, 1, -2, 0, 0, 0, 0, 0, 0, 0]), 'feet water at 39 degF')
    _add_unit('ftHg', MeasureUnit('ftHg', 40636.66, [-1, 1, -2, 0, 0, 0, 0, 0, 0, 0]), 'feet mercury')
    _add_unit('inH2O', MeasureUnit('inH2O', 249.0889, [-1, 1, -2, 0, 0, 0, 0, 0, 0, 0]), 'inch water')
    _add_unit('inH2O39F', MeasureUnit('inH2O39F', 249.082, [-1, 1, -2, 0, 0, 0, 0, 0, 0, 0]), 'inch water at 39 degF')
    _add_unit('inH2O60F', MeasureUnit('inH2O60F', 248.84, [-1, 1, -2, 0, 0, 0, 0, 0, 0, 0]), 'inch water at 60 degF')
    _add_unit('inHg', MeasureUnit('inHg', 3386.389, [-1, 1, -2, 0, 0, 0, 0, 0, 0, 0]), 'inch mercury')
    _add_unit('inHg32F', MeasureUnit('inHg32F', 3386.38, [-1, 1, -2, 0, 0, 0, 0, 0, 0, 0]), 'inch mercury at 32 degF')
    _add_unit('inHg60F', MeasureUnit('inHg60F', 3376.85, [-1, 1, -2, 0, 0, 0, 0, 0, 0, 0]), 'inch mercury at 60 degF')
    _add_unit('ksi', MeasureUnit('ksi', 6894757, [-1, 1, -2, 0, 0, 0, 0, 0, 0, 0]), 'kips per square inch')
    _add_unit('mbar', MeasureUnit('mbar', 100, [-1, 1, -2, 0, 0, 0, 0, 0, 0, 0]), 'millibar')
    _add_unit('mmH2O', MeasureUnit('mmH2O', 9.80665, [-1, 1, -2, 0, 0, 0, 0, 0, 0, 0]), 'millimeter water')

    # Electricity units

    # dup_add_unit('a', MeasureUnit('a', 1, [0, 0, 0, 1, 0, 0, 0, 0, 0, 0]), 'ampere')
    _add_unit('amp', '1*A', 'ampere')
    _add_unit('abampere', MeasureUnit('abampere', 10, [0, 0, 0, 1, 0, 0, 0, 0, 0, 0]), '')
    _add_unit('bi', MeasureUnit('bi', 10, [0, 0, 0, 1, 0, 0, 0, 0, 0, 0]), 'biot')
    _add_unit('gi', MeasureUnit('gi', 0.7957747, [0, 0, 0, 1, 0, 0, 0, 0, 0, 0]), 'gillbert')
    _add_unit('statampere', MeasureUnit('statampere', 0.0000000003335641, [0, 0, 0, 1, 0, 0, 0, 0, 0, 0]), '')

    # Angle units

    _add_unit('deg', MeasureUnit('deg', 0.0174532925199432, [0, 0, 0, 0, 0, 0, 0, 1, 0, 0]), 'angle degree')
    _add_unit('gon', MeasureUnit('gon', 0.01570796, [0, 0, 0, 0, 0, 0, 0, 1, 0, 0]), 'gradian')
    _add_unit('grade', MeasureUnit('grade', 0.01570796, [0, 0, 0, 0, 0, 0, 0, 1, 0, 0]), 'gradian',
              'one hundreadth of the right angle')
    _add_unit('milA', MeasureUnit('milA', 0.0009817477, [0, 0, 0, 0, 0, 0, 0, 1, 0, 0]), 'milliradian')
    _add_unit('minA', MeasureUnit('minA', 0.000290888208665721, [0, 0, 0, 0, 0, 0, 0, 1, 0, 0]), 'angle minute')
    _add_unit('rev', MeasureUnit('rev', 6.283185, [0, 0, 0, 0, 0, 0, 0, 1, 0, 0]), 'revolution')
    _add_unit('rot', '1*rev', 'rotation')
    _add_unit('secA', MeasureUnit('secA', 4.84813681109535E-06, [0, 0, 0, 0, 0, 0, 0, 1, 0, 0]), 'angle second')

    # Temperature units
    # -- can't use the 'eval' trick that _add_unit provides
    # for degC and degF because you can't add units
    kelvin = find_unit('K')
    _add_unit('degK', '1*K', 'degree kelvin')
    _add_unit('degR', '(5./9.)*K', 'degree rankine')
    _add_unit('degC', MeasureUnit(None, 1.0, kelvin.powers, 273.15), 'degree celcius')
    _add_unit('degF', MeasureUnit(None, 5. / 9., kelvin.powers, 459.67), 'degree fahrenheit')
    del kelvin


def _add_all_extra_units():
    _add_unit('abcoulomb', MeasureUnit('abcoulomb', 10, [0, 0, 1, 1, 0, 0, 0, 0, 0, 0]), '')
    _add_unit('coulomb', MeasureUnit('coulomb', 1, [0, 0, 1, 1, 0, 0, 0, 0, 0, 0]), 'coulomb')
    _add_unit('fdy', MeasureUnit('fdy', 96485.31, [0, 0, 1, 1, 0, 0, 0, 0, 0, 0]), 'faraday')
    _add_unit('fr', MeasureUnit('fr', 0.0000000003335641, [0, 0, 1, 1, 0, 0, 0, 0, 0, 0]), 'franklin')

    _add_unit('abfarad', MeasureUnit('abfarad', 1000000000, [-2, -1, 4, 2, 0, 0, 0, 0, 0, 0]), '')
    # dup_add_unit('f', MeasureUnit('f', 1, [-2, -1, 4, 2, 0, 0, 0, 0, 0, 0]), '')
    _add_unit('statfarad', MeasureUnit('statfarad', 0.00000000000111265, [-2, -1, 4, 2, 0, 0, 0, 0, 0, 0]), '')

    _add_unit('abhenry', MeasureUnit('abhenry', 0.000000001, [2, 1, -2, -2, 0, 0, 0, 0, 0, 0]), '')
    _add_unit('hy', MeasureUnit('hy', 1, [2, 1, -2, -2, 0, 0, 0, 0, 0, 0]), 'henry')
    _add_unit('stathenry', MeasureUnit('stathenry', 898755200000, [2, 1, -2, -2, 0, 0, 0, 0, 0, 0]), '')

    _add_unit('abmho', MeasureUnit('abmho', 1000000000, [-2, -1, 3, 2, 0, 0, 0, 0, 0, 0]), '')
    _add_unit('mho', MeasureUnit('mho', 1, [-2, -1, 3, 2, 0, 0, 0, 0, 0, 0]), 'siemens')
    # dup_add_unit('si', MeasureUnit('si', 1, [-2, -1, 3, 2, 0, 0, 0, 0, 0, 0]), '')
    _add_unit('statmho', MeasureUnit('statmho', 0.00000000000111265, [-2, -1, 3, 2, 0, 0, 0, 0, 0, 0]), '')

    _add_unit('abohm', MeasureUnit('abohm', 0.000000001, [2, 1, -3, -2, 0, 0, 0, 0, 0, 0]), '')
    _add_unit('statohm', MeasureUnit('statohm', 898755200000, [2, 1, -3, -2, 0, 0, 0, 0, 0, 0]), '')

    _add_unit('abvolt', MeasureUnit('abvolt', 0.00000001, [2, 1, -3, -1, 0, 0, 0, 0, 0, 0]), '')
    _add_unit('statvolt', MeasureUnit('statvolt', 299.7925, [2, 1, -3, -1, 0, 0, 0, 0, 0, 0]), '')
    # dup_add_unit('v', MeasureUnit('v', 1, [2, 1, -3, -1, 0, 0, 0, 0, 0, 0]), '')

    # dup_add_unit('bq', MeasureUnit('bq', 1, [0, 0, -1, 0, 0, 0, 0, 0, 0, 0]), '')
    _add_unit('ci', MeasureUnit('ci', 37000000000, [0, 0, -1, 0, 0, 0, 0, 0, 0, 0]), 'curie')
    # dup_add_unit('hz', MeasureUnit('hz', 1, [0, 0, -1, 0, 0, 0, 0, 0, 0, 0]), 'hertz')
    _add_unit('rpm', MeasureUnit('rpm', 0.104719755119659, [0, 0, -1, 0, 0, 0, 0, 1, 0, 0]), 'rotation per minute')

    _add_unit('clo', MeasureUnit('clo', 1.55, [0, -1, 3, 0, 1, 0, 0, 0, 0, 0]), 'clos')

    _add_unit('cp', MeasureUnit('cp', 0.001, [-1, 1, -1, 0, 0, 0, 0, 0, 0, 0]), 'centipoise')
    _add_unit('p', MeasureUnit('p', 0.1, [-1, 1, -1, 0, 0, 0, 0, 0, 0, 0]), 'poise')

    _add_unit('cst', MeasureUnit('cst', 0.000001, [2, 0, -1, 0, 0, 0, 0, 0, 0, 0]), 'centistokes')
    _add_unit('stk', MeasureUnit('stk', 0.0001, [2, 0, -1, 0, 0, 0, 0, 0, 0, 0]), 'stokes')

    _add_unit('fc', MeasureUnit('fc', 10.76391, [-2, 0, 0, 0, 0, 0, 1, 0, 1, 0]), 'foot-candle')
    _add_unit('ph', MeasureUnit('ph', 10000, [-2, 0, 0, 0, 0, 0, 1, 0, 1, 0]), 'phot')

    _add_unit('flam', MeasureUnit('flam', 3.426259, [-2, 0, 0, 0, 0, 0, 1, 0, 0, 0]), 'foot-lambert')
    _add_unit('gama', MeasureUnit('gama', 0.000000001, [0, 1, -2, -1, 0, 0, 0, 0, 0, 0]), 'gamma')
    # to avoid name conflict with math.gamma(), magnetic flux density gamma renamed to gama
    _add_unit('gs', MeasureUnit('gs', 0.0001, [0, 1, -2, -1, 0, 0, 0, 0, 0, 0]), 'gauss')
    _add_unit('ky', MeasureUnit('ky', 100, [-1, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'kayser')
    _add_unit('lambert', MeasureUnit('lambert', 3183.099, [-2, 0, 0, 0, 0, 0, 1, 0, 0, 0]), '')
    _add_unit('langley', MeasureUnit('langley', 41840, [0, 1, -2, 0, 0, 0, 0, 0, 0, 0]), '')
    _add_unit('mpg', MeasureUnit('mpg', 425143.7, [-2, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 'mile per gallon')
    _add_unit('mx', MeasureUnit('mx', 0.00000001, [2, 1, -2, -1, 0, 0, 0, 0, 0, 0]), 'maxwell')
    _add_unit('oe', MeasureUnit('oe', 79.5774715459476, [-1, 0, 0, 1, 0, 0, 0, 0, 0, 0]), 'oersted')
    _add_unit('r', MeasureUnit('r', 0.000258, [0, -1, 1, 1, 0, 0, 0, 0, 0, 0]), 'roentgen')
    _add_unit('radu', MeasureUnit('radu', 0.01, [2, 0, -2, 0, 0, 0, 0, 0, 0, 0]), 'radiation unit')
    _add_unit('rem', MeasureUnit('rem', 0.01, [2, 0, -2, 0, 0, 0, 0, 0, 0, 0]), 'roentgen equivalent man')
    _add_unit('sb', MeasureUnit('sb', 10000, [-2, 0, 0, 0, 0, 0, 1, 0, 0, 0]), 'stilb')
    _add_unit('sphere', MeasureUnit('sphere', 12.56637061, [0, 0, 0, 0, 0, 0, 0, 0, 1, 0]), 'sphere')
    _add_unit('st', MeasureUnit('st', 1, [0, 0, 0, 0, 0, 0, 0, 0, 1, 0]), 'steradian')
    _add_unit('te', MeasureUnit('te', 1, [0, 1, -2, -1, 0, 0, 0, 0, 0, 0]), 'tesla')
    _add_unit('UNC', MeasureUnit('UNC', 1, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1]), 'unit currency')
    _add_unit('upole', MeasureUnit('upole', 0.0000001256637, [2, 1, -2, -1, 0, 0, 0, 0, 0, 0]), 'unit pole')


_units_loaded = False


def add_measurement_units():
    global _units_loaded
    if _units_loaded:
        return
    _add_all_extra_units()
    _add_all_units()
    _add_unitless()
    _units_loaded = True
    # add_currencies(curlist)  # cannot call it here as curlist is required


# _unit_table Example: {'m': MeasureUnit(1.0,'m'), ...}
_unit_table = {}

# _unit_info Example: {'m': {'proper_name': 'm', 'long_name': 'meter', 'base_qty': '1.0 m',
# 'comment': 'Base Unit', 'category': 'Length, Wavelength', 'dimension': 'L'},...}
_unit_info = {}

# _unit_tree Example: 'LMT-2': ['dyn', 'gf', 'kgf', 'kip', 'kn', 'kp', 'lbf', 'n', 'ozf', 'pdl', 'tf'],
_unit_tree = {}


def _add_unit(name, unit_or_str, long_name='', comment='', category=''):
    proper_name = name
    name = name.lower()  # dup check

    if name in _unit_table:
        error = False
        if category != 'C':
            # category 'C' will be replaced with unit category name
            error = True
        elif _unit_table[name].dimension != 'C':
            error = True

        if error:
            raise KeyError(f'Error (PQ): Unit {name} already defined')

    if isinstance(unit_or_str, str):  # it is a string e.g. '3*ft'
        unit_or_str = unit_or_str.lower()  # dup check
        unit = eval(unit_or_str, _unit_table, {'pi': np.pi})  # safe
        for cruft in ['__builtins__', '__args__']:
            try:
                del _unit_table[cruft]
            except:
                pass
    else:  # it is a MeasureUnit(...)
        unit = unit_or_str

    # dup unit.set_name(name)
    unit.set_name(proper_name)
    _unit_table[name] = unit
    if long_name == '':
        long_name = proper_name
    # _unit_info.append((name, long_name, unit.bname, comment))
    if unit.dimension == '':
        unit.category = category
    _unit_info[name] = {
        "proper_name": proper_name,
        "long_name": long_name,
        "base_qty": unit.base_qty,
        "comment": comment,
        "category": unit.category,
        "dimension": unit.dimension
    }
    id_ = unit.dimension  # unit.dimension will be assigned to '0' for unitless entity
    if id_ not in _unit_tree:
        _unit_tree[id_] = []
    _unit_tree[id_].append(name)


def _add_base_units():
    for unit in _base_units:
        # _unit_table[unit[0]] = unit[1]
        _add_unit(unit[0], unit[1], unit[2], 'Base Unit')


# runs unconditionally at module level, but only on first import.
_add_base_units()


def unit_desc(sname):  # deb@19.08.23
    if sname in _unit_info:
        pname = _unit_info[sname]['proper_name']
        long_name = _unit_info[sname]['long_name']
        bqty = _unit_info[sname]['base_qty']
        comment = _unit_info[sname]['comment']
        comment = iif(comment != '', f' ({comment});', ';')
        category = _unit_info[sname]['category']
        lmt = '[' + _unit_info[sname]['dimension'] + ']'  # [] to enable exact search

        lname = long_name if long_name != sname else ''
        lname_categ = ', '.join(filter(None, [lname, category, lmt]))
        lname_categ = '(' + lname_categ + ')' if lname_categ != '' else ''
        unitdesc = '%s %s: 1 %s = %s%s' % (pname, lname_categ, pname, bqty, comment)
    else:
        unitdesc = f'unit {sname}: not found'
    return unitdesc


def unit_short_desc(sname):  # deb@29.06.24
    if sname in _unit_info:
        pname = _unit_info[sname]['proper_name']
        bqty = _unit_info[sname]['base_qty']
        comment = _unit_info[sname]['comment']
        comment = iif(comment != '', f' ({comment});', ';')
        unitdesc = '1 %s = %s%s' % (pname, bqty, comment)
    else:
        unitdesc = f'unit {sname}: not found'
    return unitdesc


def find_unit(unit) -> MeasureUnit:
    if isinstance(unit, str):
        unit = unit.lower()  # lowercase
        # .# name = string.strip(unit)
        name = preprocess_expression(unit.strip())

        unit = eval(name, _unit_table)  # safe
        for cruft in ['__builtins__', '__args__']:  # deb@13.08.23 required
            # print(cruft)
            try:
                del _unit_table[cruft]
            except:
                pass

    if not isMeasureUnit(unit):
        raise TypeError(f'Error (PQ): {str(unit)} is not an unit')
    return unit


# Initialize the registry once the helper functions are available.
# runs at module level on first import, but has an additional internal guard (_units_loaded)
# that prevents re-execution even if some code calls it again explicitly later.
add_measurement_units()


def lmt2catalog(dim):
    dim_title = lmt_title(dim)
    categ_items = []
    bname = dim_to_bname(dim, _base_names)
    bname_url = bname.replace('/', '!')
    cname = dim_to_bname(dim, _conv_names)
    cname_url = cname.replace('/', '!')
    if dim in _unit_tree:
        for name in _unit_tree[dim]:
            categ_items.append((_unit_info[name]['proper_name'], cname_url, unit_desc(name)))
    categ_items.sort()
    categ_items.insert(0, (bname_url, cname_url, dim_title +
                           ': Base Uom: ' + bname + ' [' + dim + ']'))
    return categ_items


altcur = {'TRY': 'TRL', 'CUP': 'CPS', 'ALL': 'LEK'}


# Turkish Lira, Cuban Peso, Albanian Lek

def add_currencies(rates, base, curdesc):
    _usd = rates["USD"]
    factr = 1.0
    if base != _usd:
        factr = _usd
    for key, val in rates.items():
        if key != 'USD':
            if key in altcur:  # rename turkish lira, as eval('try') will raise exception deb@23.11.23
                key = altcur[key]
            _add_unit(key, MeasureUnit(key, factr / val, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1]),
                      curdesc.get(key, ''), '', 'C')
            # Category 'C' will help update the rates on subsequent run while qCalc is running
        # print(key)
    # currencies are added after units are added, sort qtree[lmt]'s
    for lmt in _unit_tree.keys():
        _unit_tree[lmt].sort()
    assert (len(_unit_table) == len(set(_unit_table.keys())))


def base_units():
    return [bu[0] for bu in _base_units]


if __name__ == '__main__':
    _add_all_units()
