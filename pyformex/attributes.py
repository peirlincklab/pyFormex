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

"""Attributes

This module defines a general class for adding extra attributes to
other objects without cluttering the name space.
"""

from pyformex.mydict import Dict


class Attributes(Dict):

    """A general class for holding attributes.

    This class is a versatile :term:`mapping` class for objects that need
    a customizable set of attributes, while avoiding a wildly expanding
    name space.

    The class derives from :class:`Dict` and therefore has key lookup
    via normal dict key mechanism or via attribute syntax or via
    function call. It also provides a default_factory to lookup missing
    keys.

    The difference with the :class:`Dict` class are:

    - The function call can also be used to populate or update the
      contents of the Mapping.
    - By default, a default_factory is set returning None for any
      missing key.
    - Giving an attribute the value None removes it from the Mapping.

    Parameters
    ----------
    default_factory: callable, optional
        If provided, missing keys will be looked up by a call to the
        default_factory.
    args, kargs: other positional and keyword arguments
        Any other arguments are passed to the dict initialization.

    Notes
    -----
    While setting a single item to None will remove the item from the
    Attributes, None values can be entered using the update() method.

    The parameter order is different from previous implementation of
    this class. This was done for consistency with the Dict and CDict
    classes.

    Examples
    --------
    >>> A = Attributes()
    >>> A
    Attributes({})
    >>> A(color='red',alpha=0.7,ontop=True)
    >>> A
    Attributes({'color': 'red', 'alpha': 0.7, 'ontop': True})
    >>> A['alpha'] = 0.8
    >>> A.color = 'blue'
    >>> A.ontop = None       # remove 'ontop'
    >>> A
    Attributes({'color': 'blue', 'alpha': 0.8})
    >>> A = Attributes({'alpha': 0.8, 'color': 'blue'})
    >>> A.ontop is None
    True

    Create another Attributes with A as default, override color:

    >>> B = Attributes(default_factory=A, color='green')
    >>> B
    Attributes({'color': 'green'})
    >>> B.color, B.alpha      # alpha found in A
    ('green', 0.8)
    >>> A.clear()
    >>> A
    Attributes({})
    >>> A['alpha'], A.alpha, A('alpha')     # all mechanisms still working
    (None, None, None)
    >>> B['alpha'], B.alpha, B('alpha')
    (None, None, None)
    >>> B(color=None,alpha=1.0)            # remove and change in 1 operation
    >>> B
    Attributes({'alpha': 1.0})
    >>> B.update(color=None)     # update can be used to enter None values.
    >>> B
    Attributes({'alpha': 1.0, 'color': None})
    >>> B['alpha'] = None
    >>> B
    Attributes({'color': None})
    """

    def __init__(self, default_factory=Dict.returnNone, *args, **kargs):
        if default_factory is None or callable(default_factory):
            pass
        elif len(args) == 0:
            args = [default_factory]
            default_factory = Dict.returnNone
        Dict.__init__(self, default_factory, *args, **kargs)

    # with args: key lookup
    # with kargs: set values
    def __call__(self, *args, **kargs):
        if len(args) > 0:
            # This is required to make the default_factory work
            return self[args[0]]
        else:
            for k in kargs:
                setattr(self, k, kargs[k])

    # Remove items when value is set to None
    def __setitem__(self, key, value):
        if value is None:
            if key in self:
                del self[key]
        else:
            Dict.__setitem__(self, key, value)

    __setattr__ = __setitem__


# End
