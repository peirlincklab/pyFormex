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

"""A class for storing and handling adjacency tables.

This module defines a specialized array class for representing adjacency
of items of a single type. This is e.g. used in mesh models, to store
the adjacent elements.
"""

import numpy as np

from pyformex import arraytools as at


############################################################################
##
##   class Adjacency
##
####################
#

# TODO : This could be subclassed from Varray. But our preliminary
#        test show that it is slower and uses more memory. Perhaps
#        because in practical meshes the number of adjacent elements
#        is fairly constant, so using a full array is not much of a loss.
#        Might be different in beam type structures?
#

# TODO: WE SHOULD ADD A CONSISTENCY CHECK THAT WE HAVE BIDIRECTIONAL
#       CONNECTIONS: if row a has a value b, row b should have a value a
#

class Adjacency(np.ndarray):
    #
    # :DEV
    # Because we have a __new__ constructor and no __init__,
    # we have to put the signature of the object creation explicitely
    # in the first line of the docstring.
    #
    """ Adjacency(data=[],dtyp=None,copy=False,normalize=True)

    A class for storing and handling adjacency tables.

    An adjacency table defines a neighbouring relation between elements of
    a single collection. The nature of the relation is not important, but
    should be a binary relation: two elements are either related or they are
    not.

    Typical applications in pyFormex are the adjacency tables for storing
    elements connected by a node, or by an edge, or by a node but not by an
    edge, etcetera.

    Conceptually the adjacency table corresponds with a graph. In graph
    theory however the data are usually stored as a set of tuples `(a,b)`
    indicating a connection between the elements `a` and `b`.
    In pyFormex elements are numbered consecutively from 0 to nelems-1, where
    nelems is the number of elements. If the user wants another numbering,
    he can always keep an array with the actual numbers himself.
    Connections between elements are stored in an efficient two-dimensional
    array, holding a row for each element. This row contains the numbers
    of the connected elements.
    Because the number of connections can be different for each
    element, the rows are padded with an invalid elements number (-1).

    A normalized Adjacency is one where all rows do not contain duplicate
    nonnegative entries and are sorted in ascending order and where no column
    contains only -1 values.
    Also, since the adjacency is defined within a single collection, no row
    should contain a value higher than the maximum row index.

    Parameters
    ----------
    data: int :term:`array_like`
        Data to initialize the Connectivity. The data should be 2-dim with
        shape ``(nelems,ncon)``, where ``nelems`` is the number of elements and
        ``ncon`` is the maximum number of connections per element.
    dtyp: float datatype, optional
        Can be provided to force a specific int data type. If not, the
        datatype of ``data`` is used.
    copy: bool, optional
        If True, the data are copied. The default setting will try to use
        the original data if possible, e.g. if ``data`` is a correctly shaped
        and typed :class:`numpy.ndarray`.
    normalize: bool, optional
        If True (default) the Adjacency will be normalized at creation time.
    allow_self: bool, optional
        If True, connections of elements with itself are allowed. The default
        (False) will remove self-connections when the table is normalized.

    Warning
    -------
    The ``allow_self`` parameter is currently inactive.

    Examples
    --------
    >>> A = Adjacency([[1,2,-1],
    ...                [3,2,0],
    ...                [1,-1,3],
    ...                [1,2,-1],
    ...                [-1,-1,-1]])
    >>> print(A)
    [[-1  1  2]
     [ 0  2  3]
     [-1  1  3]
     [-1  1  2]
     [-1 -1 -1]]
    >>> A.nelems()
    5
    >>> A.maxcon()
    3
    >>> Adjacency([[]])
    Adjacency([], shape=(1, 0))
    """
    def __new__(clas, data=[], dtyp=None, copy=False, normalize=True,
                allow_self=False, bidirectional=False, check_max=True):
        """Create a new Adjacency table."""

        # Turn the data into an array, and copy if requested
        ar = np.array(data, dtype=dtyp, copy=copy)
        if ar.ndim != 2:
            raise ValueError("Expected 2-dim data")

        # Make sure dtype is an int type
        if ar.dtype.kind != 'i':
            ar = ar.astype(at.Int)

        # Check values
        if ar.size > 0:
            maxval = ar.max()
            if check_max and maxval > ar.shape[0]-1:
                raise ValueError(f"Too large element number ({maxval})"
                                 f" for number of rows({ar.shape[0]})")
        else:
            maxval = -1

        if normalize:
            ar = Adjacency._normalize(ar)

        # Transform 'subarr' from an ndarray to our new subclass.
        ar = ar.view(clas)

        return ar


    def nelems(self):
        """Return the number of elements in the Adjacency table.

        """
        return self.shape[0]


    def maxcon(self):
        """Return the maximum number of connections for any element.

        This returns the row width of the Adjacency.
        """
        return self.shape[1]


    ### normalization ###
    # This is a static method because it is called in the __new__ constructor
    @staticmethod
    def _normalize(adj, remove_self=True, remove_dup=True):
        """Reduce an adjacency table.

        An adjacency table is an integer array where each row lists the numbers
        of the items that are connected to the item with number equal to the row
        index. Rows are padded with -1 values to create rows of equal length.

        A reduced adjacency table is one where each row:

        - does not contain the row index itself,
        - does not contain duplicate entries (other than -1),
        - is sorted in ascending order,

        and that has at least one row without -1 value.

        Paramaters
        ----------
        adj: int :term:`array_like`
            A 2-dim integer array with values >=0 or -1
        remove_self: bool
            If True (default), row entries equal to the row index are removed
            (i.e. elements are not considered to be adjacent to themselves).
        remove_dup: bool
            If True (default), duplicate (non-negative) entries on a row are
            removed (i.e. adjacency does not count the number of connections).

        Returns
        -------
        int array
            An integer array with shape (adj.shape[0],maxc) with
            maxc <= adj.shape[1], where row `i` retains the unique non-negative
            numbers of the original array except the value `i`, and is possibly
            padded with -1 values. The actual array class will be the same as
            the input.

        Examples
        --------
        >>> a = np.array([[ 0,  0,  0,  1,  2,  5],
        ...               [-1,  0,  1, -1,  1,  3],
        ...               [-1, -1,  0, -1, -1,  2],
        ...               [-1, -1,  1, -1, -1,  3],
        ...               [-1, -1, -1, -1, -1, -1],
        ...               [-1, -1,  0, -1, -1,  5]])
        >>> Adjacency._normalize(a)
        array([[ 1,  2,  5],
               [-1,  0,  3],
               [-1, -1,  0],
               [-1, -1,  1],
               [-1, -1, -1],
               [-1, -1,  0]])
        >>> Adjacency._normalize(Adjacency(a))
        Adjacency([[ 1,  2,  5],
                   [-1,  0,  3],
                   [-1, -1,  0],
                   [-1, -1,  1],
                   [-1, -1, -1],
                   [-1, -1,  0]])
        """
        adj = at.checkArray(adj, ndim=2, subok=True)
        n = adj.shape[0]
        if n > 0:
            if remove_self:
                # remove the item i from row i
                adj[adj == np.arange(n).reshape(n, -1)] = -1
            adj.sort(axis=1)        # sort the rows
            if remove_dup:
                # remove duplicate items
                adj[np.where(adj[:, :-1] == adj[:, 1:])] = -1
                adj.sort(axis=1)
            maxc = adj.max(axis=0)  # find maximum per column
            adj = adj[:, maxc>=0]   # remove columns with only negative values
        return adj


    def sortRows(self):
        """Sort an adjacency table.

        This sorts the entries in each row of the adjacency table in
        ascending order and removes all columns containing only -1 values.

        Returns
        -------
        Adjacency
            An Adjacency with the same non-negative data but each row
            sorted in ascending order, and no column with only negative
            values. The number of rows is the same as the input, the number
            of columns may be lower.

        See Also
        --------
        normalize: also removes self and duplicate entries

        Examples
        --------
        >>> a = Adjacency([[ 0,  2,  1, -1],
        ...                [-1,  3,  1, -1],
        ...                [ 3, -1,  0,  1],
        ...                [-1, -1, -1, -1]])
        >>> a.sortRows()
        Adjacency([[-1,  1,  2],
                   [-1, -1,  3],
                   [ 0,  1,  3],
                   [-1, -1, -1]])
        >>> a = Adjacency([[ 0,  2,  1, -1],
        ...                [-1,  3,  1, -1],
        ...                [ 3, -1,  0,  1],
        ...                [-1, -1, -1, -1]],normalize=False)
        >>> a.sortRows()
        Adjacency([[ 0,  1,  2],
                   [-1,  1,  3],
                   [ 0,  1,  3],
                   [-1, -1, -1]])
        """
        return Adjacency._normalize(self, remove_self=False, remove_dup=False)


    def normalize(self):
        """Normalize an adjacency table.

        A normalized adjacency table is one where each row:

        - does not contain the row index itself,
        - does not contain duplicates,
        - is sorted in ascending order,

        and that has no columns with all -1 values.

        By default, an Adjacency gets normalized when it is constructed.
        Performing operations on an Adjacency may however leave it in
        a non-normalized state. Calling this method will normalize it again.
        Obviously this can also be obtained by creating a new Adjacency
        with self as data.

        Returns
        -------
        Adjacency
            An Adjacency object with shape (self.shape[0],maxc), with
            ``maxc <= adj.shape[1]``. A row ``i`` of the Adjacency contains
            the unique non-negative numbers except the value ``i`` of the
            same row ``i`` in the original, and is possibly padded with -1
            values.

        Examples
        --------
        >>> a = Adjacency([[ 0,  0,  0,  1,  2,  5],
        ...                [-1,  0,  1, -1,  1,  3],
        ...                [-1, -1,  0, -1, -1,  2],
        ...                [-1, -1,  1, -1, -1,  3],
        ...                [-1, -1, -1, -1, -1, -1],
        ...                [-1, -1,  0, -1, -1,  5]],normalize=False)
        >>> a.normalize()
        Adjacency([[ 1,  2,  5],
                   [-1,  0,  3],
                   [-1, -1,  0],
                   [-1, -1,  1],
                   [-1, -1, -1],
                   [-1, -1,  0]])
        >>> Adjacency(a)
        Adjacency([[ 1,  2,  5],
                   [-1,  0,  3],
                   [-1, -1,  0],
                   [-1, -1,  1],
                   [-1, -1, -1],
                   [-1, -1,  0]])
        """
        return Adjacency._normalize(self)


    ### operations ###


    def pairs(self):
        """Return all pairs of adjacent element.

        Returns
        -------
        int array
            An int array with two columns, where each row contains
            a pair of adjacent elements. The element number in the first column
            is always the smaller of the two element numbers.

        Examples
        --------
        >>> Adjacency([[-1,1],[0,2],[-1,0]]).pairs()
        array([[0, 1],
               [1, 2]])

        """
        p = [[[i, j] for j in k if j >= 0]
             for i, k in enumerate(self[:-1]) if max(k) >= 0]
        p = np.row_stack(p)
        return p[p[:, 1] > p[:, 0]]


    def symdiff(self, adj):
        """Return the symmetric difference of two adjacency tables.

        Parameters
        ----------
        adj: Adjacency
            An Adjacency with the same number of rows as ``self``.

        Returns
        -------
        Adjacency
            An adjacency table of the same length, where each row contains
            all the (nonnegative) numbers of the corresponding rows of ``self``
            and ``adj``, except those that occur in both.

        Examples
        --------
        >>> A = Adjacency([[ 1, 2,-1],
        ...                [ 3, 2, 0],
        ...                [ 1,-1, 3],
        ...                [ 1, 2,-1],
        ...                [-1,-1,-1]])
        >>> B = Adjacency([[ 1, 2, 3],
        ...                [ 3, 4, 1],
        ...                [ 0,-1, 2],
        ...                [ 0, 3, 4],
        ...                [-1, 0,-1]])
        >>> A.symdiff(B)
        Adjacency([[-1, -1, -1,  3],
                   [-1,  0,  2,  4],
                   [-1,  0,  1,  3],
                   [ 0,  1,  2,  4],
                   [-1, -1, -1,  0]])
        """
        if adj.nelems() != self.nelems():
            raise ValueError("`adj` should have same number of rows as `self`")
        adj = np.concatenate([self, adj], axis=-1)
        for i in range(len(adj)):
            row = adj[i]
            mult, uniq = at.multiplicity(row[row>=0])
            r = uniq[mult==1]
            nr = len(r)
            adj[i] = -1
            if nr > 0:
                adj[i, -nr:] = r
        return Adjacency(adj)


    ### frontal methods ###


    def frontGenerator(self, startat=0, frontinc=1, partinc=1):
        """Generator function returning the frontal elements.

        This is a generator function and is normally not used directly,
        but via the :meth:`frontWalk` method.

        Parameters: see :meth:`frontWalk`.

        Returns
        -------
        int array
            Int array with a value for each element. On the initial call,
            all values are -1, except for the elements in the initial front,
            which get a value 0. At each call a new front is created with
            all the elements that are connected to any of the
            current front and which have not yet been visited. The new front
            elements get a value equal to the last front's value plus the
            ``frontinc``. If the front becomes empty and a new starting front is
            created, the front value is extra incremented with ``partinc``.

        Examples
        --------
        >>> A = Adjacency([[ 1, 2,-1],
        ...                [ 3, 2, 0],
        ...                [ 1,-1, 3],
        ...                [ 1, 2,-1],
        ...                [-1,-1,-1]])
        >>> for p in A.frontGenerator(): print(p)
        [ 0 -1 -1 -1 -1]
        [ 0  1  1 -1 -1]
        [ 0  1  1  2 -1]
        [0 1 1 2 4]
        """
        p = -np.ones((self.nelems()), dtype=at.Int)
        if self.nelems() <= 0:
            return

        # Remember current elements front
        elems = np.clip(np.asarray(startat), 0, self.nelems())
        prop = 0
        while elems.size > 0:
            # Store prop value for current elems
            p[elems] = prop
            yield p

            prop += frontinc

            # Determine adjacent elements
            elems = np.unique(np.asarray(self[elems]))
            elems = elems[elems >= 0]
            elems = elems[p[elems] < 0]
            if elems.size > 0:
                continue

            # No more elements in this part: start a new one
            elems = np.where(p<0)[0]
            if elems.size > 0:
                # Start a new part
                elems = elems[[0]]
                prop += partinc


    def frontWalk(self, startat=0, frontinc=1, partinc=1, maxval=-1):
        """Walks through the elements by their node front.

        A frontal walk is executed starting from the given element(s).
        A number of steps is executed, each step advancing the front
        over a given number of single pass increments. The step number at
        which an element is reached is recorded and returned.

        Parameters
        ----------
        startat: int or list of ints
            Initial element number(s) in the front.
        frontinc: int
            Increment for the front number on each frontal step.
        partinc: int
            Increment for the front number when the front gets empty and
            a new part is started.
        maxval: int
            Maximum frontal value. If negative (default) the walk will
            continue until all elements have been reached. If non-negative,
            walking will stop as soon as the frontal value reaches this
            maximum.

        Returns
        -------
        int array
            An array of ints specifying for each element in which step
            the element was reached by the walker.

        Examples
        --------
        >>> A = Adjacency([
        ...       [-1,  1,  2,  3],
        ...       [-1,  0,  2,  3],
        ...       [ 0,  1,  4,  5],
        ...       [-1, -1,  0,  1],
        ...       [-1, -1,  2,  5],
        ...       [-1, -1,  2,  4]])
        >>> print(A.frontWalk())
        [0 1 1 1 2 2]
        """
        for p in self.frontGenerator(startat=startat, frontinc=frontinc, partinc=partinc):
            if maxval >= 0:
                if p.max() >= maxval:
                    break
        return p


    def front(self, startat=0, add=False):
        """Returns the elements of the first node front.

        Parameters
        ----------
        startat: int or list od ints
            Element number(s) or a list of element numbers. The list of
            elements to find the next front for.
        add: bool, optional
            If True, the `startat` elements wil be included in the
            return value. The default (False) will only return the elements
            in the next front line.

        Returns
        -------
        int array
            A list of the elements that are connected to any of the nodes
            that are part of the startat elements.

        Notes
        -----
        This is equivalent to the first step of a :func:`frontWalk`
        with the same startat elements, and could thus also be obtained from
        ``where(self.frontWalk(startat,maxval=1) == 1)[0]``.

        Here however another implementation is used, which is more efficient
        for very large models: it avoids the creation of the large array as
        returned by frontWalk.

        Examples
        --------
        >>> a = Adjacency([[ 0,  0,  0,  1,  2,  5],
        ...                [-1,  0,  1, -1,  1,  3],
        ...                [-1, -1,  0, -1, -1,  2],
        ...                [-1, -1,  1, -1, -1,  3],
        ...                [-1, -1, -1, -1, -1, -1],
        ...                [-1, -1,  0, -1, -1,  5]])
        >>> print(a.front())
        [1 2 5]
        >>> print(a.front([0,1]))
        [2 3 5]
        >>> print(a.front([0,1],add=True))
        [0 1 2 3 5]
        """
        elems = np.unique(np.asarray(self[startat]))
        if not add:
            elems = np.setdiff1d(elems, np.asarray(startat))
        elems = elems[elems >= 0]
        return elems


# End
