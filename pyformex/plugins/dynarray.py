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
  element of each row. It is very efficient if the data (or at least the
  row lengths) do not change during the lifetime of the table (see Varray).
- as a 1D array where the actual rows do not have to be contiguous. A start
  and stop marker is held for each row, and the unused element between
  subsequent rows can be used to efficiently grow the rows at their ends.
  This is the current Dynarray implementation. It could be a welcome
  replacement for a Varray or an array with -1 fill values, but a real
  use case has not yet been found.

"""

import numpy as np

from pyformex import arraytools as at


class Dynarray():
    """A variable width 2D integer array

    This class provides an efficient way to store tables of
    nonnegative integers when the rows of the table may have
    different length.

    For large tables this may allow an important memory saving
    compared to a rectangular array where the non-existent entries
    are filled by some special value.
    Data in the Dynarray are stored as a single 1D array,
    containing the concatenation of all rows.
    An index is kept with the start position of each row in the 1D array.

    Parameters
    ----------
    data:
        Data to initialize to a new Dynarray object. This can either of:

        data is anything that

        - has a length: nrows
        - has an iterator
        - each item has a length
        - each item contains a sequence of ints

        - another Dynarray instance: a shallow copy of the Dynarray is created.

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


    **Attributes**

    Attributes
    ----------
    nrows: int
        The number of rows in the table
    width: int
        The length of the longest row in the table
    size: int
        The total number of entries in the table
    shape: tuple of two ints
        The combined (``nrows``,``width``) values.

    Examples
    --------
    Create a Dynarray is by default printed in user-friendly format:

    >>> Da = Dynarray([[0],[1,2],[0,2,4],[0,2]])
    >>> Da
    Dynarray([[0], [1, 2], [0, 2, 4], [0, 2]])

    The Dynarray prints in a user-friendly format:

    >>> print(Da)
    Dynarray (4,3)
      [0]
      [1 2]
      [0 2 4]
      [0 2]
    <BLANKLINE>

    Show info about the Dynarray

    >>> print(Da.nrows, Da.width, Da.shape)
    4 3 (4, 3)
    >>> print(Da.size, Da.lengths)
    8 [1 2 3 2]

    Initialize from another Dynarray return a deep copy

    >>> Db = Dynarray(Da)
    >>> str(Db) == str(Da)
    True

    Indexing: The data for any row can be obtained by simple indexing:

    >>> print(Da[1])
    [1 2]

    This is equivalent with

    >>> print(Da.row(1))
    [1 2]

    Change elements:

    >>> Da[1][0] = 3
    >>> print(Da[1])
    [3 2]
    >>> str(Db) == str(Da)
    False

    Full row can be changed with matching length:

    >>> Da[1] = [1, 2]
    >>> print(Da[1])
    [1 2]

    Negative indices are allowed:

    >>> print(Da.row(-1))
    [0 2]

    Extracted columns are filled with -1 values where needed

    >>> print(Da.col(1))
    [-1  2  2  2]

    Select takes multiple rows using indices or bool:

    >>> print(Da.select([1,3]))
    Dynarray (2,2)
      [1 2]
      [0 2]
    <BLANKLINE>
    >>> print(Da.select(Da.lengths==2))
    Dynarray (2,2)
      [1 2]
      [0 2]
    <BLANKLINE>

    Iterator: A Dynarray provides its own iterator:

    >>> for row in Da:
    ...     print(row)
    [0]
    [1 2]
    [0 2 4]
    [0 2]

    >>> print(Da.flat)
    [0 1 2 0 2 4 0 2]
    >>> print(list(Da))
    [array([0]), array([1, 2]), array([0, 2, 4]), array([0, 2])]

    >>> print(Dynarray())
    Dynarray (0,0)
    <BLANKLINE>

    >>> L,R = Da.sameLength()
    >>> print(L)
    [1 2 3]
    >>> print(R)
    [array([0]), array([1, 3]), array([2])]
    >>> for a in Da.split():
    ...     print(a)
    [[0]]
    [[1 2]
     [0 2]]
    [[0 2 4]]

    """

    def __init__(self, data=None, shape=(0, 0), fill=-1, dtype=np.int32):
        """Initialize the Dynarray. See the class docstring."""
        a = np.full(shape=shape, fill_value=fill, dtype=dtype)
        start = np.zeros(shape=shape[:1], dtype=dtype)
        stop = np.zeros(shape=shape[:1], dtype=dtype)

        # Store the data
        self._data = a
        self._start = start
        self._stop = stop
        self._fill = fill

        if data is not None:
            self.data = data


    @property
    def data(self):
        """Return the data array"""
        return self._data

    @data.setter
    def data(self, data):
        """Replace the data array with new data"""
        nrows = len(data)
        maxwidth = max([len(row) for row in data])
        self.__init__(shape=(nrows, maxwidth), fill=self._fill)
        for i, r in enumerate(data):
            self[i] = r

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, start):
        self._start = start

    @property
    def stop(self):
        return self._stop

    @stop.setter
    def stop(self, stop):
        self._start = stop

    def __getitem__(self, i):
        """Return the data of row i"""
        if not at.isInt(i):
            raise ValueError("Requires an int argument")
        return self._data[i][self._start[i]:self._stop[i]]

    def __setitem__(self, i, rowdata):
        """Set the data of row i"""
        if not at.isInt(i):
            raise ValueError("Requires an int argument")
        if at.isInt(rowdata):
            # Set all items of row i to this value
            self._data[i] = rowdata
        else:
            # Set row i to the contents of rowdata
            rowlen = len(rowdata)
            self.resize(rowlen)
            self._data[i][:rowlen] = rowdata
            self._data[i][rowlen:] = self._fill
            self._start[i] = 0
            self._stop[i] = len(rowdata)

    @property
    def lengths(self):
        """Return the length of all rows of the Dynarray"""
        return self._stop - self._start

    @property
    def nrows(self):
        """Return the number of rows in the Dynarray"""
        return self._data.shape[0]

    @property
    def width(self):
        """Return the max length the rows of the Dynarray can have"""
        return self._data.shape[1]

    @property
    def size(self):
        """Return the total number of elements in the Dynarray"""
        return self.lengths.sum()

    @property
    def shape(self):
        """Return a tuple with the number of rows and maximum row length"""
        return self._data.shape

    @property
    def flat(self):
        """Return all sequential row data as a flat array."""
        return np.concatenate([r for r in self])

    def resize(self, width):
        """Change the maxwidth of the table"""
        maxwidth = self._data.shape[1]
        if width > maxwidth:
            self._data = at.growAxis(self._data, width-maxwidth, fill=self._fill)

    def __len__(self):
        """Allow len(Dynarray)"""
        return self.nrows

    def length(self, i):
        """Return the length of row i"""
        return self._stop[i] - self._start[i]

    def row(self, i):
        """Return the data for row i

        This returns self[i].
        """
        return self[i]

    def setRow(self, i, data):
        """Replace the data of row i

        This is equivalent to self[i] = data.
        """
        self[i] = data

    def col(self, i):
        """Return the data for column i

        This always returns a list of length nrows.
        For rows where the column index i is missing, a value self._fill is returned.
        """
        return np.array([r[i] if i in range(-len(r), len(r)) else self._fill
                         for r in self])

    def select(self, sel):
        """Select some rows from the Dynarray.

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
        Dynarray object
            A Dynarray with only the selected rows.

        Examples
        --------
        >>> Da = Dynarray([[0],[1,2],[0,2,4],[0,2]])
        >>> Da.select((1,3))
        Dynarray([[1, 2], [0, 2]])
        >>> Da.select((False,True,False,True))
        Dynarray([[1, 2], [0, 2]])

        """
        sel = np.asarray(sel)   # this is important, because Python bool isInt
        if len(sel) > 0 and not at.isInt(sel[0]):
            sel = np.where(sel)[0]
        return Dynarray([self[j] for j in sel])

    def __iter__(self):
        """Return an iterator for the Dynarray"""
        self._row = 0
        return self

    def __next__(self):
        """Return the next row of the Dynarray"""
        if self._row >= self.nrows:
            raise StopIteration
        row = self[self._row]
        self._row += 1
        return row

    def sort(self):
        """Sort the rows of the Dynarray.

        Sorting a Dynarray sorts the elements in each row.
        The sorting is done inplace.

        In most applications, two Dynarrays are considered equal if they
        have the same number of rows and all rows contain the same values,
        independent of their order. Rows can be sorted to create
        a unique representation.

        Examples
        --------
        >>> Da = Dynarray([[0],[2,1],[4,0,2],[0,2]])
        >>> Da.sort()
        >>> print(Da)
        Dynarray (4,3)
          [0]
          [1 2]
          [0 2 4]
          [0 2]
        <BLANKLINE>
        """
        for i in range(self.nrows):
            self[i] = sorted(self[i])

    def pop(self, i, j=-1):
        """Pop a value from row i at index j

        Parameters
        ----------
        i: int
            Index of the row from which to pop the value.
        j: int, optional
            Index of the element to pop. Default is the last element.

        Returns
        -------
        int:
            The value popped from the row i.

        Examples
        --------
        >>> Da = Dynarray([[0],[1,2],[0,2,4],[0,2]])
        >>> print(Da.pop(1))
        2
        >>> print(Da.pop(0,0))
        0
        >>> print(Da.pop(2,1))
        2
        >>> print(Da)
        Dynarray (4,3)
          []
          [1]
          [0 4]
          [0 2]
        <BLANKLINE>
        """
        val = self[i][j]
        if j == 0:
            self._start[i] += 1
        elif j == -1:
            self._stop[i] -= 1
        else:
            if j < 0:
                j += self._stop[i]
            if j < 0 or j >= self._stop[i]:
                raise ValueError("IndexError: index out of range")
            self._data[i][j:self._stop[i]-1] = self._data[i][j+1:self._stop[i]]
            self._stop[i] -= 1
        return val

    def insert(self, i, j, val):
        """Insert a value at position j of row i

        Parameters
        ----------
        i: int
            Index of the row from which to pop the value.
        j: int, optional
            Position in row i where to insert the value. If negative, this
            is counted from the end of the row. A value -1 will insert before
            the last position. Values exceeding the end (or start) of the row,
            will insert at end (or start).
        val: int
            The value to insert in row ``i``.

        See also
        --------
        append: insert a value at the end of a row.

        Examples
        --------
        >>> Da = Dynarray([[0],[1,2],[0,2,4],[0,2]])
        >>> Da.insert(1,1,3)
        >>> Da.insert(0,0,1)
        >>> Da.insert(2,-1,5)
        >>> print(Da)
        Dynarray (4,4)
          [1 0]
          [1 3 2]
          [0 2 5 4]
          [0 2]
        <BLANKLINE>
        """
        if j == -1 and self._stop[i] < self._data.shape[1]:
            self._data[i][self._stop[i]] = val
            self._stop[i] += 1
        elif j == 0 and self._start[i] > 0:
            self._data[i][self._start[i]-1] = val
            self._start[i] -= 1
        else:
            # This handles all cases, but less effective than
            # special cases above
            rowlen = self.length(i)
            if j < 0:
                j += rowlen
            # Index beyond ends: insert at end
            if j < 0:
                j = 0
            elif j > rowlen:
                j = rowlen
            # Now j is positive valid index
            if rowlen >= self.width:
                # need to enlarge data array
                self._data = at.growAxis(self._data, 1, fill=self._fill)
            # Now we certainly have space to insert
            if j < rowlen // 2:
                # roll forward if we can:
                forward = self._start[i] > 0
            else:
                # roll forward if we should:
                forward = self._stop[i] >= self._data.shape[1]
            # shift data if needed and insert value
            k = self._start[i]
            if forward:
                if j > 0:
                    self._data[i][k-1:k-1+j] = self._data[i][k:k+j]
                self._data[i][k-1+j] = val
                self._start[i] -= 1
            else:
                if j < rowlen:
                    self._data[i][k+j+1:k+rowlen+1] = self._data[i][k+j:k+rowlen]
                self._data[i][k+j] = val
                self._stop[i] += 1

    def append(self, i, val):
        """Append a value at the end of a given row.

        Parameters
        ----------
        i: int
            Index of the row to which to append the value.
        val: int
            The value to append to row ``i``.

        Examples
        --------
        >>> Da = Dynarray([[0],[1,2],[0,2,4],[0,2]])
        >>> Da.append(1,3)
        >>> print(Da.width)
        3
        >>> Da.append(2,5)
        >>> print(Da.width)
        4
        >>> print(Da)
        Dynarray (4,4)
          [0]
          [1 2 3]
          [0 2 4 5]
          [0 2]
        <BLANKLINE>
        """
        while self._stop[i] >= self._data.shape[1]:
            if self._start[i] > 0:
                self._data[i] = np.roll(self._data[i], -1)
                self._start[i] -= 1
                self._stop[i] -= 1
            else:
                self._data = at.growAxis(self._data, 1, fill=self._fill)
        self._data[i][self._stop[i]] = val
        self._stop[i] += 1

    def remove(self, i, val):
        """Remove a value from a given row

        Parameters
        ----------
        i: int
            Index of the row from which to remove the given value.
        val: int
            The value to remove from row ``i``. All occurrences of this
            value in row ``i`` are removed.

        Examples
        --------
        >>> Da = Dynarray([[0],[1,2],[0,2,4,0],[0,2]])
        >>> Da.remove(2,0)
        >>> print(Da)
        Dynarray (4,4)
          [0]
          [1 2]
          [2 4]
          [0 2]
        <BLANKLINE>
        """
        rem = self[i] == val
        nrem = rem.sum()
        if nrem > 0:
            self[i] = self[i][~rem]

    def sameLength(self):
        """Groups the rows according to their length.

        Returns a tuple of two lists (lengths,rows):

        - lengths: the sorted unique row lengths,
        - rows: the indices of the rows having the corresponding length.
        """
        lens = self.lengths
        ulens = np.unique(lens)
        return ulens, [np.where(lens == l)[0] for l in ulens]

    def split(self):
        """Split the Dynarray into 2D arrays.

        Returns
        -------
        list of arrays
            A list of 2-dim arrays with the same number
            of columns and the indices in the original Dynarray.
        """
        return [np.asarray(self.select(ind)) for ind in self.sameLength()[1]]

    def inverse(self, sort=False, ignore_neg=False):
        """Create the inverse of a Dynarray.

        The inverse of a Dynarray is again a Dynarray. Values k on a row i will
        become values i on row k. The number of data in both Dynarrays is thus
        the same. Since values become row indices, this operation only makes
        sense if there are no negative values in the Dynarray (except for the
        fill value).

        The inverse of the inverse is equal to the original.

        Parameters
        ----------
        sort: bool
            If True, rows are sorted.
        ignore_neg: bool
            If True, negative values are silently ignored (and thrown away).
            This will result in an inverse with less element that the original.
            The default (False) will raise an error if negative values exist.

        Returns
        -------
        Dynarray
            The inverse Dynarray. If sort is True, rows are sorted.

        Examples
        --------
        >>> a = Dynarray([[0,1],[2,0],[1,2],[4]])
        >>> b = a.inverse()
        >>> c = b.inverse()
        >>> print(a,b,c)
        Dynarray (4,2)
          [0 1]
          [2 0]
          [1 2]
          [4]
         Dynarray (5,2)
          [0 1]
          [0 2]
          [1 2]
          []
          [3]
         Dynarray (4,2)
          [0 1]
          [0 2]
          [1 2]
          [4]
        <BLANKLINE>
         """
        a = Dynarray(self)
        for i in range(a.nrows):
            a[i] = i
        c = np.row_stack([self.flat, a.flat])
        neg = c[0] < 0
        if neg.any():
            if ignore_neg:
                c = c[:, ~neg]
        s = c[0].argsort()
        t = c[0][s]
        u = c[1][s]
        v = t.searchsorted(np.arange(t.max() + 1))
        v = np.append(v, len(u))
        a = Dynarray([u[v[i]:v[i+1]] for i in range(len(v)-1)])
        if sort:
            a.sort()
        return a

    def tolist(self):
        """Convert the Dynarray to a nested list.

        Returns
        -------
        list of lists
            A list of all the rows as list.

        Examples
        --------
        >>> Dynarray([[0], [1, 2], [0, 2, 4], [0, 2]]).tolist()
        [[0], [1, 2], [0, 2, 4], [0, 2]]
        """
        return [r.tolist() for r in self]

    def __repr__(self):
        """String representation of the Dynarray

        Examples
        --------
        >>> Dynarray([[0], [1, 2], [0, 2, 4], [0, 2]])
        Dynarray([[0], [1, 2], [0, 2, 4], [0, 2]])
        """
        return "%s(%s)" % (self.__class__.__name__, self.tolist())

    def __str__(self):
        """Nicely print the Dynarray

        Examples
        --------
        >>> Da = Dynarray([[0], [1, 2], [0, 2, 4], [0, 2]])
        >>> print(Da)
        Dynarray (4,3)
          [0]
          [1 2]
          [0 2 4]
          [0 2]
        <BLANKLINE>
        """
        s = "%s (%s,%s)\n" % (self.__class__.__name__, self.nrows, self.width)
        for row in self:
            s += '  ' + row.__str__() + '\n'
        return s


if __name__ == "__main__":

    # This allows running the doctests with a command

    import doctest
    doctest.testmod()

# End
