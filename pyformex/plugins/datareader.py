#
##
##  SPDX-FileCopyrightText: © 2007-2023 Benedict Verhegghe <bverheg@gmail.com>
##  SPDX-License-Identifier: GPL-3.0-or-later
##
##  This file is part of pyFormex 3.3  (Sun Mar 26 20:16:15 CEST 2023)
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: https://pyformex.org
##  Project page: https://savannah.nongnu.org/projects/pyformex/
##  Development: https://gitlab.com/bverheg/pyformex
##  Distributed under the GNU General Public License version 3 or later.
##
##  This program is free software: you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation, either version 3 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program.  If not, see http://www.gnu.org/licenses/.
##
#
"""Numerical data reader

"""

__all__ = ['splitFloat', 'readData']

import re

_re_float = re.compile(r'[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?')
_re_float_string = re.compile(r'(?P<float>[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)(?P<string>.*)')


def splitFloat(s):
    """Match a floating point number at the beginning of a string.

    Parameters
    ----------
    s: str
        A string that starts with a numerical part (float).

    Returns
    -------
    tuple (float, str) | None:
        If the beginning of the string matches a floating point number,
        returns a tuple with the float and the remainder of the string.
        Else, return None

    Examples
    --------
    >>> splitFloat('123e4rt345e6')
    [1230000.0, 'rt345e6']
    """
    m = _re_float_string.match(s)
    if m:
        return [float(m.group('float')), m.group('string')]
    return None


def convertData(s, to):
    """Convert numerical data to a requested type or units.

    Converts a string including a numerical value and optional units
    to the requested type or units.

    Parameters
    ----------
    s: str
        A string containing a numerical value and an optional units string,
        optionally separated by whitespace. E.g. '10 kg'.
    to: str
        The units or type to which the value from the string ``s`` is to be
        converted. If ``s`` contains units, the specified ``to`` units should
        be compatible (i.e. for the same physical quantity).
        If a field has no units, the target ``to`` value can also be
        'int' or 'float'.

    Returns
    -------
    int | float
        The numerical value read from the string ``s``, converted to the
        specified units or type ``to``.

    Examples
    --------
    >>> convertData('1 inch', 'mm')
    25.4
    >>> convertData('1', 'mm')
    1.0
    >>> convertData('14.5e3', 'kg')
    14500.0
    >>> convertData('12 inch', 'float')
    12.0
    >>> convertData('17.5', 'int')
    17

    Warning
    -------
    You need to have the GNU ``units`` command installed for the unit
    conversion to work.
    """
    # IMPORT HERE: LATE IMPORT
    from pyformex.plugins import units
    s = s.strip()
    m = _re_float.match(s)
    if not m:
        raise ValueError(f"No value found in '{s}'")
    if m.end() == len(s) or to in ['int', 'float']:
        # no units or no units conversion: handle ourself
        val = float(s[:m.end()])
        if to == 'int':
            val = int(val)
    else:
        # let 'units' do the conversion
        val = float(units.convertUnits(s, to))
    return val


def readData(s, to, strict=False):
    """Read values from a string matching the units/type specifications.

    This is a powerful function for reading, interpreting and converting
    numerical data from a string.

    Parameters
    ----------
    s: str
        A string containing comma-separated fields. Each field is either
        a numerical value, or a numerical value followed by a units string.
        The value and the units can optionally be separated by whitespace.
    to: list of str
        A list of units to which the fields in the string ``s`` should be
        converted. The length of the list is usually equal to the number
        of fields in the string ``s``.
        If a field has units, the corresponding ``to`` should be a compatible
        unit (i.e. for the same physical quantity). If a field has no units,
        the target ``to`` value can also be 'int' or 'float'.
    strict: bool
        If True, the length of the ``to`` list should exactly match the
        number of fields in ``s``. The default (False) allows unequal lengths
        and will only proceed until the shortest is exhausted.

    Returns
    -------
    list
        A list of int/float values read from the string s.
        With ``strict=True`` the list will have the same length as the
        number of fields in ``s`` and the number of items in ``to``.
        Else, it will have the shortest length of the two.
        Where the field contains a units designator, the value is converted
        to the requested ``to`` units.
        designator.Fields in the string s are separated by

    Examples
    --------
    >>> readData('1 inch', ['mm'])
    [25.4]
    >>> readData('12, 13s, 14.5e3, 12 inch, 1hr, 31kg, 5MPa',
    ...     ['int','float','kg','cm','s','g','kN/m**2'])
    [12, 13.0, 14500.0, 30.48, 3600.0, 31000.0, 5000.0]

    Warning
    -------
    You need to have the GNU ``units`` command installed for the unit
    conversion to work.
    """
    data = s.split(',')
    if strict and len(data) != len(to):
        raise ValueError(f"'{s} does not match {to}")
    return [convertData(si, ti) for ti, si in zip(to, data)]


# End
