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
"""Some convenient shortcuts for common list operations.

While most of these functions look (and work) like set operations, their
result differs from using Python builtin Sets in that they preserve the
order of the items in the lists.
"""
import functools

def lrange(*args):
    """Return a range as a list."""
    return list(range(*args))


def roll(a, n=1):
    """Roll the elements of a list n positions forward (backward if n < 0)

    >>> roll(lrange(5),2)
    [2, 3, 4, 0, 1]
    """
    return a[n:] + a[:n]


def union(a, b):
    """Return a list with all items in a or in b, in the order of a,b.

    >>> union(lrange(3),lrange(1,4))
    [0, 1, 2, 3]
    """
    return a + [i for i in b if i not in a]


def difference(a, b):
    """Return a list with all items in a but not in b, in the order of a.

    >>> difference(lrange(3),lrange(1,4))
    [0]
    """
    return [i for i in a if i not in b]


def symdifference(a, b):
    """Return a list with all items in a or b but not in both.

    >>> symdifference(lrange(3),lrange(1,4))
    [0, 3]
    """
    return difference(a, b) + difference(b, a)


def intersection(a, b):
    """Return a list with all items in a and in b, in the order of a.

    >>> intersection(lrange(3),lrange(1,4))
    [1, 2]
    """
    return [i for i in a if i in b]


def concatenate(a):
    """Concatenate a list of lists.

    >>> concatenate([lrange(3),lrange(1,4)])
    [0, 1, 2, 1, 2, 3]
    """
    return functools.reduce(list.__add__, a)


def flatten(a, recurse=False):
    """Flatten a nested list.

    By default, lists are flattened one level deep.
    If recurse=True, flattening recurses through all sublists.

    >>> flatten([[[3.,2,],6.5,],[5],6,'hi'])
    [[3.0, 2], 6.5, 5, 6, 'hi']
    >>> flatten([[[3.,2,],6.5,],[5],6,'hi'],True)
    [3.0, 2, 6.5, 5, 6, 'hi']
    """
    r = []
    for i in a:
        if isinstance(i, list):
            if recurse:
                r.extend(flatten(i, True))
            else:
                r.extend(i)
        else:
            r.append(i)
    return r


def group(a, n):
    """Group a list by sequences of maximum n items.

    Parameters:

    - `a`: list
    - `n`: integer

    Returns a list of lists. Each sublist has length n, except for
    the last one, which may be shorter.

    Examples:

      >>> group( [3.0, 2, 6.5, 5, 'hi'],2)
      [[3.0, 2], [6.5, 5], ['hi']]

    """
    return [a[i:i + n] for i in range(0, len(a), n)]


def select(a, b):
    """Return a subset of items from a list.

    Returns a list with the items of a for which the index is in b.

    >>> select(range(2,6),[1,3])
    [3, 5]
    """
    return [a[i] for i in b]


def remove(a, b):
    """Returns the complement of select(a,b).

    >>> remove(range(2,6),[1,3])
    [2, 4]
    """
    return [a[i] for i in range(len(a)) if i not in b]


def toFront(l, i):
    """Add or move i to the front of list l

    l is a list.
    If i is in the list, it is moved to the front of the list.
    Else i is added at the front of the list.

    This changes the list inplace and does not return a value.

    >>> L = lrange(5)
    >>> toFront(L,3)
    >>> L
    [3, 0, 1, 2, 4]
    >>> toFront(L,7)
    >>> L
    [7, 3, 0, 1, 2, 4]
    """
    if i in l:
        l.remove(i)
    l.insert(0, i)


class List(list):
    """A versatile list class.

    This class extends the builtin list type with automatic calling
    of a method for all items in the list.
    Any method other than the ones defined for List will return a new List
    with the method applied to each of the items, using the same arguments.

    As an example, List([a,b]).len() will return List([a.len(),b.len()])

    >>> L = List(['first','second'])
    >>> L.upper()
    ['FIRST', 'SECOND']
    >>> L.startswith('f')
    [True, False]
    """

    def __init__(self, *args):
        list.__init__(self, *args)

    def __getattr__(self, attr):

        def on_all(*args, **kwargs):
            return self.__class__([getattr(obj, attr)(*args, **kwargs)
                                   for obj in self])

        return on_all

    def __getstate__(self):
        """Allow a List to be pickled."""
        return list(self)

    def __setstate__(self, state):
        """Allow a List to be set from pickle"""
        self.__init__(state)


# End
