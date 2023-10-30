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

"""Extensions to Python's built-in dict class.

Dict is a dictionary with default values and alternate attribute syntax.
CDict is a Dict with lookup cascading into the next level Dict's
if the key is not found in the CDict itself.

The classes have been largely reimplemented in 2019, because many of the
reasons for choosing the old implementation are not valid anymore because
of improved features of Python. And the migration to Python3 showed the
shortcomings of an implementation that was too hackishly meddling with
Python internals. Now we have a much cleaner and simpler implementation
while still preserving the intended functionality.

(C) 2005,2008,2019 Benedict Verhegghe
Distributed under the GNU GPL version 3 or later
"""

from collections import defaultdict
from collections.abc import Mapping


def formatDict(d, indent=4):
    """Format a dict in nicely formatted Python source representation.

    Each (key,value) pair is formatted on a line of the form::

       key = value

    If all the keys are strings containing only characters that are
    allowed in Python variable names, the resulting text is a legal
    Python script to define the items in the dict. It can be stored
    on a file and executed.

    >>> d = {'y':'s', 'x':'t'}
    >>> D = {'a':0, 'd':d, 'b':1}
    >>> print(formatDict(D))
    {
        'a': 0,
        'd': {'y': 's', 'x': 't'},
        'b': 1,
        }
    >>> D = {'a':0, 'd':Dict(d), 'b':1}
    >>> print(formatDict(D))
    {
        'a': 0,
        'd': {
            'y': 's',
            'x': 't',
        },
        'b': 1,
    }
    """
    global default_indent
    s = "{\n"
    for k, v in d.items():
        s += ' ' * indent + f"'{k}': "
        if isinstance(v, Dict):
            s += formatDict(v, indent + 4)
        else:
            s += f"{v!r}"
        s += ",\n"
    s += ' ' * (indent-4) + '}'
    return s


class Dict(defaultdict):

    """A dictionary with default lookup and attribute and call syntax.

    :class:`Dict` is a dictionary class providing extended functionality
    over the builtin Python :class:`dict` class:

    - Items can not only be accessed with dictionary key syntax, but also
      with attribute and call syntax. Thus, if ``C`` is a :class:`Dict`,
      an item with key 'foo' can be obtained in any of the following
      equivalent ``C['foo']``, ``C.foo``, ``C('foo')``. The attribute syntax
      can of course only be used if the key is a string that is valid as
      Python variable.
      The first two can also be used to set the value in the Dict:
      ``C['foo'] = bar``, ``C.foo = bar``. The call syntax does not
      allow setting a value. See however the :class:`Attributes` subclass
      for a dict that does allow ``C(foo=bar)`` to set values.

    - A default_factory function can be provided to handle missing keys.
      The function is then passed the missing key and whatever it returns
      is returned as the value for that key. Note that this is different
      from Python's :class:`defaultdict`, where the default_factory does
      not take an argument and can only return a constant value.
      Without default_factory, the Dict will still produce a KeyError on
      missing keys.

    - Because the Dict accepts call syntax to lookup keys, another Dict
      instance can perfectly well be used as default_factory. You can even
      create a chain of Dict's to lookup missing keys.

    - An example default_factory is provided which returns None for any
      key. Using this default_factory will make the Dict accept any key
      and just return None for the nonexistent keys.

    Parameters
    ----------
    default_factory: callable, optional
        If provided, missing keys will be looked up by a call to the
        default_factory.
    args, kargs: other arguments
        Any other arguments are passed to the dict initialization.

    Notes
    -----
    Watch for this syntax quirks when initializing a Dict:

    - ``Dict()``: an empty Dict without default_factory
    - ``Dict(callable)``: an empty Dict with callable as default_factory
    - ``Dict(noncallable)``: a Dict without default_factory initialized with
      data fron noncallable (e.g. a dict or a sequence of tuples)
    - ``Dict(callable, noncallable)``: a Dict with callable as default_factory
      and initialized with data from noncallable.

    And since a Dict is callable, but a dict is not, Dict(some_dict) will
    initialize the data in the Dict, while Dict(some_Dict) will use
    ``some_dict`` as defaults, but stay empty itself.

    If a default_factory is provided, all lookup mechanisms (key, attribute,
    call) will use it for missing keys. The proper way to test whether a key
    actually exists in the Dict (and not in the default_factory) is using the
    'key in Dict' operation.


    Examples
    --------
    >>> A = Dict()
    >>> A
    Dict({})
    >>> A['a'] = 0
    >>> A.b = 1
    >>> # A(c=2) # not allowed
    >>> A
    Dict({'a': 0, 'b': 1})
    >>> sorted(A.keys())
    ['a', 'b']
    >>> 'c' in A
    False
    >>> A.default_factory is None   # A does have a default_factory attribute
    True

    Now a Dict with a default_factory.

    >>> B = Dict(Dict.returnNone,A)   # The dict is initialized with the values of A
    >>> B
    Dict({'a': 0, 'b': 1})
    >>> sorted(B.keys())
    ['a', 'b']
    >>> 'c' in B
    False
    >>> B['c'] is None   # lookup nonexistent key returns None
    True
    >>> B.c is None
    True
    >>> B('c') is None
    True
    >>> B.get('c','Surprise?')  # get() does not use default_factory!
    'Surprise?'

    Using another Dict as default_factory

    >>> C = Dict(A,{'b':5, 'c':6})   # Now A is used for missing keys
    >>> C
    Dict({'b': 5, 'c': 6})
    >>> sorted(C.keys())
    ['b', 'c']
    >>> 'a' in C, 'b' in C, 'c' in C        # 'a' is not in C
    (False, True, True)
    >>> C['a'], C['b'], C['c']         # but still returns a value
    (0, 5, 6)
    >>> C('a'), C('b'), C('c')         # also with call syntax
    (0, 5, 6)
    >>> C.a, C.b, C.c                  # or as attributes
    (0, 5, 6)
    >>> hasattr(C,'a')           # hasattr uses default_factory
    True
    >>> getattr(C,'a',None)      # getattr too
    0
    >>> 'a' in C                 # the proper way to test if key exists in C
    False
    >>> C['b'], C.__missing__('b')  # masked entries of A can also be accessed
    (5, 1)

    """

    @staticmethod
    def returnNone(*args, **kargs):
        """Always returns None."""
        return None

    def __init__(self, default_factory=None, *args, **kargs):
        """Create a new Dict instance.
        """
        if default_factory is None or callable(default_factory):
            pass
        elif len(args) == 0:
            args = [default_factory]
            default_factory = None
        defaultdict.__init__(self, default_factory, *args, **kargs)

    def __missing__(self, key):
        """What to do on a missing key

        If the Dict has a default_factory, that is called with the key
        as argument and the result returned.
        Else, a KeyError for the given key is raised.
        """
        if self.default_factory is None:
            raise KeyError(key)
        else:
            return self.default_factory(key)

    def __repr__(self):
        """Format the Dict as a string.

        We use the format Dict({}), so that the string is a valid Python
        representation of the Dict.
        """
        return f"{self.__class__.__name__}({dict.__repr__(self)})"

    def __str__(self):
        """Nicely format the Dict as a string.

        Formats the dict in a human readable way.
        """
        return formatDict(self)

    def __call__(self, key):
        """Make the dict callable

        This makes a Dict usable as default_factory in another Dict.
        """
        return self[key]

    def __getattr__(self, key):
        """Allows items to be addressed as self.key.

        This makes self.key equivalent to self['key'], except if key
        is an attribute of the builtin type 'dict': then we return that
        attribute instead, so that the 'dict' methods keep their binding.
        """
        try:
            return dict.__getattribute__(self, key)
        except AttributeError as e:
            try:
                return self.__getitem__(key)
            except Exception:
                raise e

    def __setattr__(self, key, value=None):
        """Allows items to be set as self.key=value.

        >>> D = Dict()
        >>> D.a = 5
        >>> D
        Dict({'a': 5})
        """
        self[key] = value

    def __delattr__(self, key):
        """Allow items to be deleted using del self.key.

        >>> D = Dict(a=5)
        >>> del D.a
        >>> D
        Dict({})
        """
        if key in self:
            del self[key]

    def update(self, data={}, **kargs):
        """Add a dictionary to the Dict object.

        The data can be a dict or Dict type object.
        """
        dict.update(self, data)
        dict.update(self, kargs)


class CDict(Dict):

    """A cascading Dict: missing keys are looked up in all dict values.

    This is a :class:`Dict` subclass with an extra lookup mechanism for
    missing keys: any value in the Dict that implements the Mapping
    mechanism (such as dict, Dict and their subclasses) will be tested
    for the missing key, and the first one found will be returned.
    If there is no Mapping value providing the key, and a default_factory
    exists, the key will finally be looked up in the default_factory
    as well.

    Parameters
    ----------
    default_factory: callable, optional
        If provided, missing keys will be looked up by a call to the
        default_factory.
    args, kargs: other arguments
        Any other arguments are passed to the dict initialization.

    Notes
    -----
    If there are multiple Mapping values in the CDict containing the
    missing key, it is undefined which one will be used to return a
    value. CDict's are therefore usually used where the Mapping values
    have themselves separate sets of keys.

    If any of the values in the CDict is also a CDict, the lookup of missing
    keys will continue in the Mapping values of that CDict. This results
    in a cascading lookup as long as the Mapping types in the values as
    CDict (and not Dict or dict). This is another way of creating chained
    lookup mechanisms (besides using a Dict as default_factory).

    Examples
    --------
    >>> C = CDict(a=0, d={'a':1, 'b':2})
    >>> C
    CDict({'a': 0, 'd': {'a': 1, 'b': 2}})
    >>> C['a']
    0
    >>> C['d']
    {'a': 1, 'b': 2}
    >>> C['b']           # looked up in C['d']
    2
    >>> 'b' in C
    False

    Now a CDict with a default_factory.

    >>> C = CDict(CDict.returnNone,a=0, d={'a':1, 'b':2})
    >>> C
    CDict({'a': 0, 'd': {'a': 1, 'b': 2}})
    >>> 'c' in C, C['c']      # No 'c', but returns None
    (False, None)

    """

    def __init__(self, default_factory=Dict.returnNone, *args, **kargs):
        if default_factory is None or callable(default_factory):
            pass
        elif len(args) == 0:
            args = [default_factory]
            default_factory = Dict.returnNone
        Dict.__init__(self, default_factory, *args, **kargs)

    def __missing__(self, key):
        # First try to cascade
        for k in self:
            if isinstance(self[k], CDict):
                # Cascade through by just trying to lookup and accept if not None
                try:
                    res = self[k][key]
                    if res:
                        return res
                except Exception:
                    continue
            elif isinstance(self[k], Mapping):
                # Any other mapping: accept if it has the key itself
                if key in self[k]:
                    return self[k][key]
        # Then try the default_factory
        if self.default_factory is not None:
            res = self.default_factory(key)
            return res
        # Out of options
        raise KeyError(key)

    def __repr__(self):
        """Format the CDict as a string.

        We use the format Dict({}), so that the string is a valid Python
        representation of the Dict.
        """
        return f"CDict({dict.__repr__(self)})"


# for compatibility (reading .pyf files)

returnNone = Dict.returnNone

# def __newobj__(cls, *args):
#     return cls.__new__(cls, *args)


if __name__ == "__main__":
    import doctest
    doctest.testmod()

# End
