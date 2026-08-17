# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import molmass
from molmass import ELEMENTS


def molecule__info():
    return {
        'title': 'Calculate molecular mass and composition of an element',
        'schema': {'molecule': {'type': 'textarea'}}
    }


def molecule(molecule='H2O'):
    """Calculate molecular mass and composition of an element

    Calculate the molecular mass (average, nominal, and isotopic pure), and the elemental composition,
    of a molecule given by its chemical formula. Calculations are based on the isotopic
    composition of the elements. Mass deficiency due to chemical bonding is not taken into account.

    Based on the work of: Christoph Gohlke
    """
    molecule = molecule.upper()
    f = molmass.Formula(molecule)
    return {
        'Hill Notation': f.formula,
        'Empirical Notation': f.empirical,
        'Average Mass': f.mass,
        'Nominal Mass': f.nominal_mass,
        'Isotopic Mass': f.monoisotopic_mass,
        'Atoms': f.atoms,
        'Charge': f.charge,
        'Composition': f.composition().dataframe(),
        # 'Spectrum': f.spectrum(min_intensity=0.01).dataframe()
    }


def element_choice():
    # atomic symbol, atomic name, atomic number
    return {ele.symbol: f'{ele.symbol} ({ele.name}, {ele.number})' for ele in ELEMENTS}


def element__info():
    return {
        'title': 'Periodic Element Information',
        'schema': {
            'symbol': {'type': 'choice', 'choices': element_choice()}
        }
    }


def element(symbol='H'):
    ele = ELEMENTS[symbol]
    return {
        'Name': ele.name,
        'Atomic Number': ele.number,
        'Symbol': ele.symbol,
        'Description': ele.description,
        'Atomic Mass': ele.mass,
        'Boiling Temperature': ele.tboil,
        'Melting temperature': ele.tmelt,
        'Density': ele.density,
        'Electron Configuration': ele.eleconfig,
        'Group': ele.group,
        'Period':ele.period,
        'Block':ele.block
    }
