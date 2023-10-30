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

"""Working with variable width tables.

Mesh type geometries use tables of integer data to store the connectivity
between different geometric entities. The basic connectivity table in a
Mesh with elements of the same type is a table of constant width: the
number of nodes connected to each element is constant.
However, the inverse table (the elements connected to each node) does not
have a constant width.

Tables of constant width can conveniently be stored as a 2D array, allowing
fast indexing by row and/or column number. A variable width table can be
stored (using arrays) in two ways:

- as a 2D array, with a width equal to the maximal row length.
  Unused positions in the row are then filled with an invalid value (-1).
- as a 1D array, storing a simple concatenation of the rows.
  An additional array then stores the position in that array of the first
  element of each row.

In pyFormex, variable width tables were initially stored as 2D arrays:
a remnant of the author's past FORTRAN experience. With a growing
professional use of pyFormex involving ever larger models, it became clear
that there was a large memory (and thus also speed) penalty related to the
use of 2D arrays with lots of unused entries.

The Varray class can offer important memory and speed gains for large models.
With many algorithms we even found that a 2D array result could be achieved
faster by first constructing a Varray and then converting that to a 2D array.
Not sorting the entries in the Varray provides a further gain.
The Varray class defined below therefore does not sort the rows
by default, but provides methods to sort them when needed.
"""

import numpy as np

from pyformex import arraytools as at


class Varray():
    """A variable width 2D integer array.

    This class provides an efficient way to store tables of
    nonnegative integers when the rows of the table may have
    different length.

    For large tables this may allow an important memory saving
    compared to a rectangular array where the non-existent entries
    are filled by some special value.
    Data in the Varray are stored as a single 1D array,
    containing the concatenation of all rows.
    An index is kept with the start position of each row in the 1D array.

    Parameters
    ----------
    data:
        Data to initialize to a new Varray object. This can either of:

        - another Varray instance: a shallow copy of the Varray is created.

        - a list of lists of integers. Each item in the list contains
          one row of the table.

        - a 2D ndarray of integer type. The nonnegative numbers on each row
          constitute the data for that row.

        - a 1D array or list of integers, containing the concatenation of
          the rows. The second argument `ind` specifies the indices of the
          first element of each row.

        - a 1D array or list of integers, containing the concatenation of
          the rows obtained by prepending each row with the row length.
          The caller should make sure these 1D data are consistent.

    ind: 1-dim int :term:`array_like`, optional
        This is only used when `data` is a pure concatenation of all rows.
        It holds the position in `data` of the first element of each row.
        Its length is equal to the number of rows (`nrows`) or `nrows+1`.
        It is a non-decreasing series of integer values, starting with 0.
        If it has ``nrows+1`` entries, the last value is equal to the total
        number of elements in `data`. This last value may be omitted,
        and will then be added automatically.
        Note that two subsequent elements may be equal, corresponding with
        an empty row.

    Examples
    --------
    Create a Varray from a nested list:

    >>> Va = Varray([[0],[1,2],[0,2,4],[0,2]])
    >>> Va
    Varray([[0], [1, 2], [0, 2, 4], [0, 2]])

    The Varray prints in a user-friendly format:

    >>> print(Va)
    Varray (nrows=4, width=1..3)
      [0]
      [1 2]
      [0 2 4]
      [0 2]
    <BLANKLINE>

    The internal data are 1-D arrays:

    >>> print(Va.data)
    [0 1 2 0 2 4 0 2]
    >>> print(Va.ind)
    [0 1 3 6 8]

    Other initialization methods resulting in the same Varray:

    >>> Vb = Varray(Va)
    >>> print(str(Vb) == str(Va))
    True
    >>> Vb = Varray(np.array([[-1,-1,0],[-1,1,2],[0,2,4],[-1,0,2]]))
    >>> print(str(Vb) == str(Va))
    True
    >>> Vc = Varray([0,1,2,0,2,4,0,2], at.cumsum0([1,2,3,2]))
    >>> print(str(Vc) == str(Va))
    True
    >>> Vd = Varray([1,0, 2,1,2, 3,0,2,4, 2,0,2])
    >>> print(str(Vd) == str(Va))
    True

    Show info about the Varray

    >>> print(Va.nrows, Va.width, Va.shape)
    4 (1, 3) (4, 3)
    >>> print(Va.size, Va.lengths)
    8 [1 2 3 2]

    Indexing: The data for any row can be obtained by simple indexing:

    >>> print(Va[1])
    [1 2]

    This is equivalent with

    >>> print(Va.row(1))
    [1 2]

    >>> print(Va.row(-1))
    [0 2]

    Change elements:

    >>> Va[1][0] = 3
    >>> print(Va[1])
    [3 2]

    Full row can be changed with matching length:

    >>> Va[1] = [1, 2]
    >>> print(Va[1])
    [1 2]

    Negative indices are allowed:

    Extracted columns are filled with -1 values where needed

    >>> print(Va.col(1))
    [-1  2  2  2]

    Select takes multiple rows using indices or bool:

    >>> print(Va.select([1,3]))
    Varray (nrows=2, width=2..2)
      [1 2]
      [0 2]
    <BLANKLINE>
    >>> print(Va.select(Va.lengths==2))
    Varray (nrows=2, width=2..2)
      [1 2]
      [0 2]
    <BLANKLINE>

    Iterator: A Varray provides its own iterator:

    >>> for row in Va:
    ...     print(row)
    [0]
    [1 2]
    [0 2 4]
    [0 2]

    >>> print(Varray())
    Varray (nrows=0, width=0..0)
    <BLANKLINE>

    """
    def __init__(self, data=[], ind=None):
        """Initialize the Varray. See the class docstring."""
        self._row = 0   # current row, for use iterators

        # If data is a Varray, just use its data
        if isinstance(data, Varray):
            self.data = data.data
            self.ind = data.ind
            return

        # Allow for empty Varray
        if len(data) <= 0:
            data = []

        try:
            data = np.array(data, dtype=at.Int)
        except ValueError:
            data = np.array(data, dtype=object)

        if data.dtype.kind == 'i' and data.ndim == 1:
            # data is a 1-dim int array
            if ind is None:
                # It is a 1-d array with embedded length
                # extract row lengths from data
                i = 0
                size = len(data)
                rowlen = []
                while i < size:
                    rowlen.append(data[i])
                    i += data[i] + 1
                # create indices and remove row lengths from data
                ind = at.cumsum0(rowlen)
                if size > 0:
                    data = np.delete(data, ind[:-1] + np.arange(len(rowlen)))
            else:
                # ind holds the indices of the row starts
                ind = at.checkArray(ind, kind='i', ndim=1)
                if ind[0] != 0 or ind[-1] > len(data):
                    raise ValueError(
                        f"Invalid ind: should start with 0; end with len(data)"
                        f"\nGot: {ind}")
                if np.any(ind[:-1] > ind[1:]):
                    raise ValueError(
                        f"Invalid ind: should be a no-decreasing sequence"
                        f"\nGot: {ind}")
        else:
            # A 2-d int array or a nested list was specified
            # remove the negative elements
            data = [np.array(row) for row in data]
            data = [row[row >= 0] for row in data]
            rowlen = [len(row) for row in data]
            ind = at.cumsum0(rowlen)
            data = np.concatenate(data).astype(at.Int)

        # Make sure we have the last row
        if ind[-1] != len(data):
            ind = np.concatenate([ind, [len(data)]])

        # Store the data
        self.data = data.astype(at.Int)
        self.ind = ind.astype(at.Int)


    # Attributes computed ad hoc, because cheap(er)

    @property
    def nrows(self):
        """The number of rows in the Varray"""
        return len(self.ind) - 1

    @property
    def lengths(self):
        """An array with the row lengths"""
        return self.ind[1:] - self.ind[:-1]

    @property
    def minwidth(self):
        """The length of the shortest row"""
        l = self.lengths
        return l.min() if len(l) > 0 else 0

    @property
    def maxwidth(self):
        """The length of the longest row"""
        l = self.lengths
        return l.max() if len(l) > 0 else 0

    @property
    def width(self):
        """A tuple with the minimum and maximum width"""
        return self.minwidth, self.maxwidth

    @property
    def strwidth(self):
        """A string with the mainimum and maximum row length"""
        return f"{self.minwidth}..{self.maxwidth}"

    @property
    def size(self):
        """The total number of elements in the Varray"""
        return self.ind[-1]

    @property
    def shape(self):
        """A tuple with the number of rows and the maximum row length"""
        return (self.nrows, self.maxwidth)

    @property
    def dtype(self):
        """Return the data type of the elements in the Varray"""
        return self.data.dtype


    def __len__(self):
        """Return the number of rows in the Varray"""
        return len(self.ind) - 1


    def copy(self):
        """Return a deep copy of the Varray"""
        return Varray(self.data.copy(), self.ind.copy())


    def length(self, i):
        """Return the length of row i"""
        return self.ind[i + 1] - self.ind[i]


    def row(self, i):
        """Return the data for the row i.

        Parameters
        ----------
        i: int
            The index of the row to return.

        Returns
        -------
        1-dim int array
            An array with the values of row i

        Notes
        -----
        The same is obtained by simple indexing. See the examples.

        Examples
        --------
        >>> Va = Varray([[0],[1,2],[0,2,4],[0,2]])
        >>> print(Va.row(1))
        [1 2]
        >>> print(Va[1])
        [1 2]

        """
        if not at.isInt(i):
            raise ValueError("Varray index should be an single int")
        if i < 0:
            i += self.nrows
        return self.data[self.ind[i]:self.ind[i + 1]]


    __getitem__ = row


    def rowslice(self, i):
        """Return a slice object for the row i.

        Parameters
        ----------
        i: int
            The index of the row to return.

        Returns
        -------
        slice
            A slice object representing the set of indices for row i

        Examples
        --------
        >>> Va = Varray([[0],[1,2],[0,2,4],[0,2]])
        >>> print(Va.rowslice(2))
        slice(3, 6, None)
        >>> print(Va.data[Va.rowslice(2)])
        [0 2 4]
        """
        return slice(self.ind[i], self.ind[i+1])


    def rowlimits(self):
        """Generator for row slice limits

        Examples
        --------
        >>> Va = Varray([[0],[1,2],[0,2,4],[0,2]])
        >>> for row in Va.rowlimits():
        ...     print(row)
        (0, 1)
        (1, 3)
        (3, 6)
        (6, 8)
        """
        i = 0
        while i < self.nrows:
            yield self.ind[i], self.ind[i+1]
            i += 1


    def index1d(self, i, j):
        """Return the sequential index for the element with 2D index i,j

        Parameters
        ----------
        i: int
            The row index
        j: int
            The column index

        Returns
        -------
        int
            The sequential index corresponding with position (i,j).

        Examples
        --------
        >>> Va = Varray([[0],[1,2],[0,2,4],[0,2]])
        >>> print(Va.index1d(2,2))
        5
        """
        if j >= 0 and j < self.length(i):
            return self.ind[i] + j
        else:
            raise IndexError("Index out of bounds")


    def index2d(self, k):
        """Return the 2D index for the element with sequential index k

        Parameters
        ----------
        k: int
            The sequential index in the flat array

        Returns
        -------
        i: int
            The row index of the element with sequential index k
        j: int
            The column index of the element with sequential index k

        Examples
        --------
        >>> Va = Varray([[0],[1,2],[0,2,4],[0,2]])
        >>> print(Va.index2d(5))
        (2, 2)
        """
        if k < 0 or k >= self.ind[-1]:
            raise IndexError(
                f"Varray: index {k} out of bounds [0, {self.ind[-1]})")
        i = self.ind.searchsorted(k, side='right') - 1
        j = k - self.ind[i]
        return i, j


    def __setitem__(self, i, data):
        """Set the data for the row i.

        Parameters
        ----------
        i: int
            The index of the row to change.
        data: int or int :term:`array_like`
            Data to replace the row i.
            If a single int, all items in the row are set to this value.
            If an array, it should match the row length.

        Examples
        --------
        >>> Va = Varray([[0],[1,2],[0,2,4],[0,2]])
        >>> Va[1] = 0
        >>> Va[2] = [1,3,5]
        >>> Va[3][1] = 1
        >>> print(Va)
        Varray (nrows=4, width=1..3)
          [0]
          [0 0]
          [1 3 5]
          [0 1]
        <BLANKLINE>

        """
        if not at.isInt(i):
            raise ValueError("Varray index should be an single int")
        if i < 0:
            i += self.nrows
        self.data[self.ind[i]:self.ind[i + 1]] = data


    def setRow(self, i, data):
        """Replace the data of row i

        This is equivalent to self[i] = data.
        """
        self[i] = data


    def col(self, i):
        """Return the data for column i

        This always returns a list of length nrows.
        For rows where the column index i is missing, a value -1 is returned.
        """
        return np.array([r[i] if i in range(-len(r), len(r)) else -1
                         for r in self])


    def select(self, sel):
        """Select some rows from the Varray.

        Parameters
        ----------
        sel: iterable of ints or bools
            Specifies the row(s) to be selected.
            If type is int, the values are the row numbers.
            If type is bool, the length of the iterable should be
            exactly ``self.nrows``; the positions where the value is True are
            the rows to be returned.

        Returns
        -------
        Varray object
            A Varray with only the selected rows.

        Examples
        --------
        >>> Va = Varray([[0],[1,2],[0,2,4],[0,2]])
        >>> Va.select((1,3))
        Varray([[1, 2], [0, 2]])
        >>> Va.select((False,True,False,True))
        Varray([[1, 2], [0, 2]])

        """
        sel = np.asarray(sel)   # this is important, because Python bool isInt
        if len(sel) > 0 and not at.isInt(sel[0]):
            sel = np.where(sel)[0]
        return Varray([self[j] for j in sel])


    # TODO: These could be removed and replaced with index2d()[0/1]
    # and put sel = self.index(sel) in index2d
    def rowindex(self, sel):
        """Return the rowindex for the elements flagged by selector sel.

        sel is either a list of element numbers or a bool array with
        length self.size
        """
        sel = self.index(sel)
        return self.ind.searchsorted(sel, side='right') - 1


    def colindex(self, sel):
        """Return the column index for the elements flagged by selector sel.

        sel is either a list of element numbers or a bool array with
        length self.size
        """
        sel = self.index(sel)
        ri = self.rowindex(sel)
        return sel - self.ind[ri]


    def __iter__(self):
        """Return an iterator for the Varray"""
        self._row = 0
        return self


    def __next__(self):
        """Return the next row of the Varray"""
        if self._row >= self.nrows:
            raise StopIteration
        row = self[self._row]
        self._row += 1
        return row


    def index(self, sel):
        """Convert a selector to an index.

        Parameters
        ----------
        sel: iterable of ints or bools
            Specifies the elements of the Varray to be selected.
            If type is int, the values are the index numbers in the
            flat array. If type is bool, the length of the iterable
            should be exactly ``self.size``; the positions where the
            value is True will be returned.

        Returns
        -------
        int array
            The selected element numbers.

        Examples
        --------
        >>> Va = Varray([[0],[1,2],[0,2,4],[0,2]])
        >>> Va.index((1,3,5,7))
        array([1, 3, 5, 7])
        >>> Va.index((False,True,False,True,False,True,False,True))
        array([1, 3, 5, 7])

        """
        try:
            sel = at.checkArray(sel, shape=(self.size,), kind='b')
            sel = np.where(sel)[0]
        except ValueError:
            sel = at.checkArray(sel, kind='i')
        return sel


    def where(self, sel):
        """Return row and column index of the selected elements

        sel is either a list of element numbers or a bool array with
        length self.size

        Returns a 2D array where the first column is the row index
        and the second column the corresponding column index of an
        element selected by sel

        Examples
        --------
        >>> Va = Varray([[0],[1,2],[0,2,4],[0,2]])
        >>> Va.where([1,3,5,7])
        array([[1, 0],
               [2, 0],
               [2, 2],
               [3, 1]])
        """
        return np.row_stack([self.index2d(i) for i in self.index(sel)])


    def sorted(self):
        """Returns a sorted Varray.

        Returns a Varray with the same entries but where each
        row is sorted.

        This returns a copy of the data, and leaves the original
        unchanged.

        See also :meth:`sort` for sorting the rows inplace.
        """
        return Varray([sorted(row) for row in self])


    def roll(self, shift):
        """Roll the elements row by row.

        Parameters
        ----------
        shift: int
            The number of places by which elements are shifted. Positive
            values shift to the right.

        Returns
        -------
        Varray
            A Varray containing on each row the entries from the input
            Varray shifted ofter the specified number of places.

        Examples
        --------
        >>> Varray([[0], [0, 1, 2, 3], [0, 2, 4]]).roll(1)
        Varray([[0], [3, 0, 1, 2], [4, 0, 2]])
        """
        return Varray([np.roll(row, shift) for row in self])


    def removeFlat(self, ind):
        """Remove the element with flat index i

        Parameters
        ----------
        ind: int or int :term:`array_like`
            Index in the flat data of the element(s) to remove.

        Returns
        -------
        Varray
            A Varray with the element(s) ind removed.

        Examples
        --------
        >>> Va = Varray([[0],[1,2],[0,2,4],[0,2]])
        >>> Va.removeFlat(3)
        Varray([[0], [1, 2], [2, 4], [0, 2]])
        >>> Va.removeFlat([0,2,7])
        Varray([[], [1], [0, 2, 4], [0]])
        """
        srt = np.unique(ind)
        data = self.data[at.complement(srt, len(self.data))]
        ind = self.ind.copy()
        for i in srt[::-1]:
            ind[ind>i] -= 1
        return Varray(data, ind)


    def sort(self):
        """Sort the Varray inplace.

        Sorting a Varray sorts the elements in each row.
        The sorting is done inplace.

        See also :meth:`sorted` for sorting the rows without
        changing the original.

        Examples
        --------
        >>> va = Varray([[0],[2,1],[4,0,2],[0,2]])
        >>> va.sort()
        >>> print(va)
        Varray (nrows=4, width=1..3)
          [0]
          [1 2]
          [0 2 4]
          [0 2]
        <BLANKLINE>
        """
        for row in self:
            row.sort()


    def toArray(self):
        """Convert the Varray to a 2D array.

        Returns a 2D array with shape (self.nrows,self.maxwidth), containing
        the row data of the Varray.
        Rows which are shorter than width are padded at the start with
        values -1.

        Examples
        --------
        >>> Varray([[0],[2,1],[4,0,2],[0,2]]).toArray()
        array([[-1, -1,  0],
               [-1,  2,  1],
               [ 4,  0,  2],
               [-1,  0,  2]])
        >>> Varray([[0,3],[2,1],[4,0],[0,2]]).toArray()
        array([[0, 3],
               [2, 1],
               [4, 0],
               [0, 2]])
        """
        if self.minwidth == self.maxwidth:
            a = self.data.reshape(self.nrows, self.maxwidth)
        else:
            a = -np.ones((self.nrows, self.maxwidth), dtype=at.Int)
            for i, r in enumerate(self):
                if len(r) > 0:
                    a[i, -len(r):] = r
        return a


    def sameLength(self):
        """Groups the rows according to their length.

        Returns
        -------
        lengths: list
            the sorted unique row lengths
        rows: list
            the indices of the rows having the corresponding length.

        Examples
        --------
        >>> Va = Varray([[0],[1,2],[0,2,4],[0,2]])
        >>> L,R = Va.sameLength()
        >>> print(L)
        [1 2 3]
        >>> print(R)
        [array([0]), array([1, 3]), array([2])]
        """
        lens = self.lengths
        ulens = np.unique(lens)
        return ulens, [np.where(lens == l)[0] for l in ulens]


    def split(self):
        """Split the Varray into 2D arrays.

        Returns
        -------
        list
            A list of 2D arrays where all the rows of VA with the same number
        of columns are collected. The list is sorted in order of increasing
        number of columns.

        Examples
        --------
        >>> Va = Varray([[0],[1,2],[0,2,4],[0,2]])
        >>> for a in Va.split():
        ...     print(a)
        [[0]]
        [[1 2]
         [0 2]]
        [[0 2 4]]
        """
        return [self.select(ind).toArray() for ind in self.sameLength()[1]]


    def toList(self):
        """Convert the Varray to a nested list.

        Returns a list of lists of integers.
        """
        return [r.tolist() for r in self]


    def inverse(self, sort=True, expand=False):
        """Return the inverse of a Varray.

        The inverse of a Varray is again a Varray. Values k on a row i will
        become values i on row k. The number of data in both Varrays is thus
        the same.

        The inverse of the inverse is equal to the original. Two Varrays are
        equal if they have the same number of rows and all rows contain the
        same numbers, independent of their order.

        Parameters
        ----------
        sort: bool
            If True (default), the values on each row of the returned index
            are sorted.
            The default (False) will leave the values in the order obtained
            by the algorithm, which depends on Python/numpy sorting, and
            usually turns out to be sorted as well.

        Returns
        -------
        :class:`Varray`
        The inverse index, as a Varray (default).
        Each row ``i`` of the inverse contains the numbers of the rows of the
        input in which a value ``i`` appeared. The rows are sorted by default.

        Examples
        --------
        >>> a = Varray([[0,1],[2,0],[1,2],[4]])
        >>> b = a.inverse()
        >>> c = b.inverse()
        >>> print(a,b,c)
        Varray (nrows=4, width=1..2)
          [0 1]
          [2 0]
          [1 2]
          [4]
         Varray (nrows=5, width=0..2)
          [0 1]
          [0 2]
          [1 2]
          []
          [3]
         Varray (nrows=4, width=1..2)
          [0 1]
          [0 2]
          [1 2]
          [4]
        <BLANKLINE>
        >>> a = Varray([[-1,0,1],[0,2,-1],[2,1,1],[3,-2,0]])
        >>> print(a.inverse())
        Varray (nrows=4, width=1..3)
          [0 1 3]
          [0 2 2]
          [1 2]
          [3]
        <BLANKLINE>
        """
        nrows, ncols = self.shape
        if nrows <= 0:
            # allow inverse of empty Varray
            va = Varray()
        else:
            # Create a row index for each value of the data
            row = np.arange(nrows).repeat(self.lengths)
            s = self.data.argsort()
            t = self.data[s]
            u = row[s]
            # Now search for the start of every row number
            v = t.searchsorted(np.arange(t.max() + 1))
            if v[0] > 0:
                # There were negative numbers: remove them
                u = u[v[0]:]
                v -= v[0]
            va = Varray(u, v)
            if sort:
                # TODO: this could be avoided by using a stable
                # sort algorithm above
                va.sort()
        if expand:
            va = va.toArray()
        return va


    def __repr__(self):
        """String representation of the Varray"""
        return f"{self.__class__.__name__}({self.toList()})"


    def __str__(self):
        """Nicely print the Varray"""
        s = [f"{self.__class__.__name__} "
             f"(nrows={self.nrows}, width={self.strwidth})"]
        s.extend([str(row) for row in self])
        return '\n  '.join(s) + '\n'


    @classmethod
    def concatenate(clas, varrays):
        """Concatenate a list of Varrays to a single Varray.

        Parameters
        ----------
        varrays: list of Varray
            The list of Varrays to concatenate.

        Returns
        -------
        Varray
            The concatenated Varrays.

        Examples
        --------
        >>> VA0 = Varray([[0,1],[2,3,4]])
        >>> VA1 = Varray([[5,6]])
        >>> VA2 = Varray([[7,8],[9]])
        >>> VA = Varray.concatenate([VA0,VA1,VA2])
        >>> print(VA)
        Varray (nrows=5, width=1..3)
          [0 1]
          [2 3 4]
          [5 6]
          [7 8]
          [9]
        """
        data = np.concatenate([va.data for va in varrays])
        ind = at.cumsum0(np.concatenate([va.lengths for va in varrays]))
        return Varray(data, ind=ind)


    @classmethod
    def fromArrays(clas, arrays):
        """Concatenate a list of 2D int arrays into a Varray

        Examples
        --------
        >>> VA = Varray.fromArrays([
        ...     [[1,1], [2,2]],
        ...     [[3,3,3], [4,4,4]],
        ...     [[5,5], [6,6], [7,7]],
        ... ])
        >>> print(VA)
        Varray (nrows=7, width=2..3)
          [1 1]
          [2 2]
          [3 3 3]
          [4 4 4]
          [5 5]
          [6 6]
          [7 7]
        """
        arrays = [at.checkArray(a, ndim=2, kind='i') for a in arrays]
        indices = [np.arange(a.shape[0]) * a.shape[1] for a in arrays]
        lengths = [a.size for a in arrays]
        offsets = at.cumsum0(lengths)
        data = np.concatenate([a.flat for a in arrays])
        indices = np.concatenate([i + o for i, o in zip(indices, offsets)])
        return Varray(data, indices)


def graphColors(adj):
    """Colorizes all nodes of a graph using Welsh-Powell algorithm.

    The algorithm determines a color scheme thus that no two connected
    nodes of a graph have the same color. While not guaranteeing to be
    the optimal solution, it usually is a very close. This function can
    for example be used to determine a color scheme for different areas
    on a planar map, such that no two touching regions will have the same
    color.

    Parameters
    ----------
    adj: :term:`varray_like`
        An adjacency array where each row `i` lists the nodes connected
        to node `i`. It can be a Varray or a regular 2d array padded with
        -1 entries to have constant row length.

    Returns
    -------
    int array:
        An 1-d int array with the color palette numbers for the nodes.

    Examples
    --------
    """
    adj = Varray(adj)
    nnodes = len(adj)
    order = np.argsort(-adj.lengths)
    colors = np.full((nnodes,), -1, dtype=at.Int)
    for i in order:
        for color in range(nnodes):
            for j in adj[i]:
                if colors[j] == color:
                    break
            else:  # no break
                colors[i] = color
                break
    return colors

# End
