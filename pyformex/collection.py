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

"""Tools for handling collections of elements belonging to multiple parts.

This module defines the Collection class.
"""
from copy import deepcopy
import numpy as np
import pyformex as pf

################# Collection of Actors or Actor Elements ###############


def uniq(data, keep_order):
    """Uniqify data, keeping order if needed"""
    if keep_order:
        return np.asarray(list(dict.fromkeys(data)))
    else:
        return np.unique(data)

def uniq_add(a, b, keep_order):
    """Add to a uniq array. a is supposed to be uniq, not checked!"""
    if keep_order:
        return np.concatenate([a, [i for i in b if i not in a]])
    else:
        return np.union1d(a,b)

def uniq_remove(a, b, keep_order):
    """Remove from a uniq array. a is supposed to be uniq, not checked!"""
    if keep_order:
        return np.asarray([i for i in a if i not in b])
    else:
        return np.setdiff1d(a, b)


class Collection:

    """A collection  is a set of (int,int) tuples.

    The first part of the tuple has a limited number of values and are used
    as the keys in a dict.
    The second part can have a lot of different values and is implemented
    as an integer array with unique values.
    This is e.g. used to identify a set of individual parts of one or more
    OpenGL actors.

    Examples
    --------
    >>> a = Collection()
    >>> a.add(range(7),3)
    >>> a.add(range(4))
    >>> a.remove([2,4],3)
    >>> print(a)
    -1 [0 1 2 3]; 3 [0 1 3 5 6];
    >>> a.add([[2,0],[2,3],[-1,7],[3,88]])
    >>> print(a)
    -1 [0 1 2 3 7]; 2 [0 3]; 3 [ 0  1  3  5  6 88];
    >>> print(a.total())
    13
    >>> a[2] = [1,2,3]
    >>> print(a)
    -1 [0 1 2 3 7]; 2 [1 2 3]; 3 [ 0  1  3  5  6 88];
    >>> a[2] = []
    >>> print(a)
    -1 [0 1 2 3 7]; 3 [ 0  1  3  5  6 88];
    >>> a.set([[2,0],[2,3],[-1,7],[3,88]])
    >>> print(a)
    -1 [7]; 2 [0 3]; 3 [88];
    >>> print(a.keys())
    [-1  2  3]
    >>> for k, i in a.singles(): print(k,i)
    -1 7
    2 0
    2 3
    3 88
    >>> print([k for k in a])
    [-1, 2, 3]
    >>> 2 in a
    True
    >>> del a[2]
    >>> 2 in a
    False

    """
    def __init__(self, obj_type=None, keep_order=False):
        self.d = {}
        self.obj_type = obj_type
        self.keep_order = keep_order

    def copy(self):
        return deepcopy(self)

    def __len__(self):
        return len(self.d)

    def total(self):
        return sum([len(v) for v in self.d.values()])

    def clear(self, keys=[]):
        if keys:
            for k in keys:
                k = int(k)
                if k in self.d:
                    del self.d[k]
        else:
            self.d = {}

    def add(self, data, key=-1):
        """Add new data to a Collection.

        Parameters
        ----------
        data: :term:`array_like` | Collection
            An int array with shape (ndata, 2) or (ndata,), or another
            Collection with the same obj_type as self. If an array
            with shape (ndata, 2), each row has a key value in column 0
            and a data value in column 1. If an (ndata,) shaped array,
            all items have the same key and it has to be specified separately.
        key: int
            The key value if data is an (ndata,) shaped array. Else ignored.
        keep_order
        separately, or a default value will be used.

        data can also be another Collection, if it has the same object
        type.
        """
        if len(data) == 0:
            return
        if isinstance(data, Collection):
            if data.obj_type == self.obj_type:
                for k in data.d:
                    self.add(data.d[k], k)
                return
            else:
                raise ValueError(
                    "Cannot add Collections with different object type")
        data = np.asarray(data)
        if data.ndim == 2:
            for key in np.unique(data[:, 0]):
                self.add(data[data[:, 0] == key, 1], key)
        else:
            if key in self.d:
                self.d[key] = uniq_add(self.d[key], data, self.keep_order)
            elif data.size > 0:
                self.d[key] = uniq(data, self.keep_order)

    def set(self, data, key=-1):
        """Set the collection to the specified data.

        This is equivalent to clearing the corresponding keys
        before adding.
        """
        self.clear()
        self.add(data, key)

    def remove(self, data, key=-1):
        """Remove data from the collection."""
        if isinstance(data, Collection):
            if data.obj_type == self.obj_type:
                for k in data.d:
                    self.remove(data.d[k], k)
                return
            else:
                raise ValueError(
                    "Cannot remove Collections with different object type")
        data = np.asarray(data)
        if data.ndim == 2:
            for key in np.unique(data[:, 0]):
                self.remove(data[data[:, 0] == key, 1], key)
        else:
            key = int(key)
            if key in self.d:
                data = uniq_remove(self.d[key], data, self.keep_order)
                if data.size > 0:
                    self.d[key] = data
                else:
                    del self.d[key]
            else:
                pf.debug(f"Not removing from non-existing selection "
                         f"for actor {key}", pf.DEBUG.DRAW)

    def __contains__(self, key):
        """Check whether the collection has an entry for the key.

         This inplements the 'in' operator for a Collection.
         """
        return key in self.d

    def __setitem__(self, key, data):
        """Set new values for the given key. This does not force uniqueness"""
        key = int(key)
        data = np.asarray(data)
        if data.size > 0:
            self.d[key] = data
        else:
            del self.d[key]

    def __iter__(self):
        """Return an iterator for the Collection

        The iterator loops over the sorted keys.
        """
        return iter(self.keys())

    def __getitem__(self, key):
        """Return item with given key."""
        return self.d[key]

    def __delitem__(self, key):
        """Delete an item with given key"""
        del self.d[key]

    def get(self, key, default=[]):
        """Return item with given key or default."""
        key = int(key)
        return self.d.get(key, default)

    def keys(self):
        """Return a sorted array with the keys"""
        return np.asarray(sorted(self.d.keys()))

    def items(self):
        """Return an iterator over (key,value) pairs."""
        return self.d.items()

    def singles(self):
        """Return an iterator over the single instances

        Returns next (k, i) pair from the collection.
        """
        for k in self:
            for v in self.d[k]:
                yield k, v

    def __str__(self):
        if len(self) == 0:
            s = 'Empty Collection'
        else:
            s = ''
            for k in self.keys():
                s += f"{k} {self.d[k]}; "
            s = s.rstrip()
        return s

# End
