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

"""A class and functions for handling nodal connectivity.

This module defines a specialized array class for representing nodal
connectivity. This is e.g. used in mesh models, where geometry is
represented by a set of numbered points (nodes) and the geometric elements
are described by refering to the node numbers.
In a mesh model, points common to adjacent elements are unique, and
adjacency of elements can easily be detected from common node numbers.
"""

from itertools import combinations
import numpy as np

from pyformex import utils
from pyformex import arraytools as at
from pyformex.varray import Varray
from pyformex.adjacency import Adjacency


############################################################################
##
##   class Connectivity
##
#########################


class Connectivity(np.ndarray):
    #
    # :DEV
    # Because we have a __new__ constructor and no __init__,
    # we have to put the signature of the object creation explicitely
    # in the first line of the docstring.
    #
    """Connectivity(data=[],dtyp=None,copy=False,nplex=0,eltype=None)

    A class for handling element to node connectivity.

    A connectivity object is a 2-dimensional integer array with all
    non-negative values. Each row of the array defines an element by listing
    the numbers of its lower entity types.
    A typical use is a :class:`~mesh.Mesh` object, where each element
    is defined in function of its nodes.
    While in a Mesh the word 'node' will normally refer to a geometrical
    point, here we will use 'node' for the lower entity whatever its nature
    is. It doesn't even have to be a geometrical entity.

    Note
    ----
    The current implementation limits a Connectivity object to numbers that
    are smaller than 2**31. That is however largely sufficient for all
    practical cases.

    In a row (element), the same node number may occur more than once, though
    usually all numbers in a row are different. Rows containing duplicate
    numbers are called `degenerate` elements.
    Rows containing the same node sets, albeit different permutations thereof,
    are called duplicates.

    Parameters
    ----------
    data: int :term:`array_like`
        Data to initialize the Connectivity. The data should be 2-dim with
        shape ``(nelems,nplex)``, where ``nelems`` is the number of elements and
        ``nplex`` is the plexitude of the elements.
    dtyp: float datatype, optional
        It not provided, the datatype of ``data`` is used.
    copy: bool, optional
        If True, the data are copied. The default setting will try to use
        the original data if possible, e.g. if ``data`` is a correctly shaped
        and typed :class:`numpy.ndarray`.
    nplex: int, optional
        The plexitude of the data. This can be specified to force a check on
        the plexitude of the data, or to set the plexitude for an empty
        Connectivity.
        If an ``eltype`` is specified, the plexitude of the element type
        will override this value.
    eltype: str or :class:`elements.ElementType` subclass, optional
        The element type associated with the Connectivity. It can be either
        a subclass of:class:`elements.ElementType` or the ``name`` of such
        a subclass.
        If not provided, a non-typed Connectivity will result.

    Raises
    ------
    ValueError
        If ``nplex`` is provided and the specified ``data`` do not match the
        specified plexitude.

    Notes
    -----
    The Connectivity class has no knowledge about the geometrical meaning
    of the element types. In most cases the use of its subclass
    :class:`~elements.Elems` is therefore more appropriate.

    Empty Connectivities with ``nelems==0`` and ``nplex > 0`` can be useful,
    but a Connectivity with ``nplex==0`` generally is not.

    See Also
    --------
    :class:`~elements.Elems`: a subclass that holds geometrical information
        about the element types and is used to create :class:`Mesh` geometries.

    Examples
    --------
    >>> Connectivity([[0,1,2],[0,1,3],[0,3,2],[0,5,3]])
    Connectivity([[0, 1, 2],
                  [0, 1, 3],
                  [0, 3, 2],
                  [0, 5, 3]])

    >>> Connectivity(np.array([],dtype=at.Int).reshape(0,3))
    Connectivity([], shape=(0, 3))

    """

    _exclude_members_ = ['reorderNodes']

    def __new__(self, data=[], dtyp=None, copy=False, nplex=0, eltype=None):
        """Create a new Connectivity object."""
        if isinstance(data, Connectivity):
            if nplex == 0:
                nplex = data.nplex()
            if eltype is None:
                eltype = data.eltype

        if eltype is None:
            try:
                eltype = data.eltype
            except Exception:
                eltype = None

        # Turn the data into an array, and copy if requested
        ar = np.array(data, dtype=dtyp, copy=copy)
        if ar.ndim < 2:
            if nplex > 0:
                ar = ar.reshape(-1, nplex)
            else:
                ar = ar.reshape(-1, 1)

        elif ar.ndim > 2:
            raise ValueError("Expected 2-dim data")

        # Check values
        if ar.size > 0:
            if ar.max() >= 2**31 or (ar.min() < 0):
                raise ValueError("Negative or too large positive value in data")
            if nplex > 0 and ar.shape[1] != nplex:
                raise ValueError(f"Expected data of plexitude {nplex}")
        else:
            if nplex > 0:
                ar = ar.reshape(0, nplex)

        # Make sure dtype is an ar.Int type
        ar = ar.astype(at.Int)

        # Transform 'subarr' from an ndarray to our new subclass.
        ar = ar.view(self)

        ## # Other data
        ar.eltype = eltype  # ! this may be a string!!!!!!!!!!!
        ar.inv = None   # inverse index
        ar.eadj = None  # element adjacency
        ar.nadj = None  # node adjacency
        return ar


    def __array_finalize__(self, obj):
        # reset the attributes from passed original object
        # all extra attributes added in __new__ should be reset here
        if obj is None:
            return
        self.eltype = getattr(obj, 'eltype', None)
        self.inv = getattr(obj, 'inv', None)
        self.eadj = getattr(obj, 'eadj', None)
        self.nadj = getattr(obj, 'nadj', None)


    def __reduce__(self):
        """Reduce the object to a pickled state"""
        # Get the pickled ndarray state (as a list, so we can change it)
        object_state = list(np.ndarray.__reduce__(self))
        # Define our own state with the extra attributes we added
        extra_state = str(self.eltype) if self.eltype is not None else None
        # Store both in place of the original ndarray state
        object_state[2] = (object_state[2], extra_state)
        return tuple(object_state)


    def __setstate__(self, state):
        """Restore from pickled state"""
        # In __reduce__, we replaced ndarray's state with a tuple
        # of itself and our own state
        nd_state, extra_state = state
        np.ndarray.__setstate__(self, nd_state)
        if isinstance(extra_state, tuple):
            extra_state = extra_state[0]  # legacy version stored (eltype,inv)
        self.eltype = extra_state
        self.__array_finalize__(self)


    def __repr__(self):
        """String representation of a Connectivity

        Examples
        --------
        >>> Connectivity([[0,1,2],[0,1,3]],eltype='line3')
        Connectivity([[0, 1, 2],
                      [0, 1, 3]], eltype='line3')

        """
        res = np.ndarray.__repr__(self)
        # This is not needed for doctests, but is needed for
        # normal output
        if self.dtype == at.Int:
            res = res.replace(', dtype=int32', '')
        if self.eltype is not None:
            res = res.replace(')', f", eltype='{self.eltype}')")
        return res


    def nelems(self):
        """Return the number of elements in the Connectivity table.

        Returns
        -------
        int
            The number of rows in the table.

        Examples
        --------
        >>> Connectivity([[0,1,2],[0,1,3],[0,3,2],[0,5,3]]).nelems()
        4
        """
        return self.shape[0]


    def maxnodes(self):
        """Return an upper limit for number of nodes in the Connectivity.

        Returns
        -------
        int
            The highest node number plus one.

        See Also
        --------
        nnodes: the actual number of nodes in the table

        Examples
        --------
        >>> Connectivity([[0,1,2],[0,1,3],[0,3,2],[0,5,3]]).maxnodes()
        6

        """
        return int(self.max() + 1)


    def nnodes(self):
        """Return the actual number of nodes in the Connectivity.

        This returns the count of the unique node numbers.

        See Also
        --------
        maxnodes: the highest node number + 1

        Examples
        --------
        >>> Connectivity([[0,1,2],[0,1,3],[0,3,2],[0,5,3]]).nnodes()
        5
        """
        return np.unique(self).shape[0]


    def nplex(self):
        """Return the plexitude of the elements in the Connectivity table.

        Examples
        --------
        >>> Connectivity([[0,1,2],[0,1,3],[0,3,2],[0,5,3]]).nplex()
        3
        """
        return self.shape[1]


    def report(self):
        """Format a Connectivity table"""
        s = f"Connectivity {self.shape}, eltype={self/eltype}"
        return s + '\n' + np.ndarray.__str__(self)


    ############### Detecting degenerates and duplicates ##############


    def testDegenerate(self):
        """Flag the degenerate elements (rows).

        A degenerate element is a row which contains at least two
        equal values.

        Returns
        -------
        bool array
             A 1-dim bool array with length ``self.nelems()``, holding
             True values for the degenerate rows.

        Examples
        --------
        >>> Connectivity([[0,1,2],[0,1,1],[0,3,2]]).testDegenerate()
        array([False,  True, False])

        """
        srt = np.asarray(self.copy())
        srt.sort(axis=1)
        return (srt[:, :-1] == srt[:, 1:]).any(axis=1)


    def listDegenerate(self):
        """Return a list with the numbers of the degenerate elements.

        Returns
        -------
        int array
            A 1-dim int array holding the row indices of the
            degenerate elements.

        Examples
        --------
        >>> Connectivity([[0,1,2],[0,1,1],[0,3,2]]).listDegenerate()
        array([1])

        """
        return np.arange(self.nelems())[self.testDegenerate()]


    def listNonDegenerate(self):
        """Return a list with the numbers of the non-degenerate elements.

        Returns
        -------
        int array
            A 1-dim int array holding the row indices of the
            non-degenerate elements.

        Examples
        --------
        >>> Connectivity([[0,1,2],[0,1,1],[0,3,2]]).listNonDegenerate()
        array([0, 2])

        """
        return np.arange(self.nelems())[~self.testDegenerate()]


    def removeDegenerate(self):
        """Remove the degenerate elements from a Connectivity table.

        Returns
        -------
        Connectivity
            A Connectivity object with the degenerate elements removed.

        Examples
        --------
        >>> Connectivity([[0,1,2],[0,1,1],[0,3,2]]).removeDegenerate()
        Connectivity([[0, 1, 2],
                      [0, 3, 2]])

        """
        return self[~self.testDegenerate()]


    def findDuplicate(self, permutations='all'):
        """Find duplicate rows in the Connectivity.

        Parameters
        ----------
        permutations: str
            Defines which permutations of the row data are allowed while still
            considering the rows equal. Possible values are:

            - 'none': no permutations are allowed: rows must match the same date
              at the same positions.
            - 'roll': rolling is allowed. Rows that can be transformed into
              each other by rolling are considered equal;
            - 'all': any permutation of the same data will be considered an
              equal row. This is the default.

        Returns
        -------
        V: :class:`~varray.Varray`
            A Varray where each row contains a list of the row numbers
            from a that are considered equal. The entries in each row are
            sorted and the rows are sorted according to their first element.

        Notes
        -----
        This is like :func:`arraytools.equalRows` but has a different
        default value for ``permutations``.

        Examples
        --------
        >>> C = Connectivity([[0,1,2],[0,1,3],[0,1,2],[2,0,1],[2,1,0]])
        >>> C.findDuplicate()
        Varray([[0, 2, 3, 4], [1]])
        >>> C.findDuplicate(permutations='roll')
        Varray([[0, 2, 3], [1], [4]])
        >>> C.findDuplicate(permutations='none')
        Varray([[0, 2], [1], [3], [4]])

        """
        return at.equalRows(self, permutations=permutations)


    def listDuplicate(self, permutations='all'):
        """Return a list with the numbers of the duplicate elements.

        Returns
        -------
        1-dim int array
            The indices of the unique rows in the Connectivity array.

        Examples
        --------
        >>> C = Connectivity([[0,1,2],[0,1,3],[0,1,2],[2,0,1],[2,1,0]])
        >>> C.listDuplicate()
        array([2, 3, 4])
        >>> C.listDuplicate(permutations='roll')
        array([2, 3])
        >>> C.listDuplicate(permutations='none')
        array([2])

        """
        ind, ok = at.findEqualRows(self, permutations=permutations)
        return np.sort(ind[~ok])


    def listUnique(self, permutations='all'):
        """Return a list with the numbers of the unique elements.

        Returns
        -------
        1-dim int array
            The indices of the unique rows in the Connectivity array.

        See Also
        --------
        findDuplicate: find duplicate rows
        listDuplicate: list duplicate rows
        removeDuplicate: remove duplicate rows

        Examples
        --------
        >>> C = Connectivity([[0,1,2],[0,1,3],[0,1,2],[2,0,1],[2,1,0]])
        >>> C.listUnique()
        array([0, 1])
        >>> C.listUnique(permutations='roll')
        array([0, 1, 4])
        >>> C.listUnique(permutations='none')
        array([0, 1, 3, 4])

        """
        return at.uniqueRows(self, permutations=permutations)


    def removeDuplicate(self, permutations='all'):
        """Remove duplicate elements from a Connectivity list.

        By default, duplicates are elements that consist of the same set of
        nodes, in any particular order. Setting permutations to 'none'
        will only remove the duplicate rows that have matching values at
        matching positions.

        Returns
        -------
        Connectivity
            A new Connectivity with the duplicate elements removed.

        Examples
        --------
        >>> C = Connectivity([[0,1,2],[0,1,3],[0,1,2],[2,0,1],[2,1,0]])
        >>> C.removeDuplicate()
        Connectivity([[0, 1, 2],
                      [0, 1, 3]])
        >>> C.removeDuplicate(permutations='roll')
        Connectivity([[0, 1, 2],
                      [0, 1, 3],
                      [2, 1, 0]])
        >>> C.removeDuplicate(permutations='none')
        Connectivity([[0, 1, 2],
                      [0, 1, 3],
                      [2, 0, 1],
                      [2, 1, 0]])

        """
        return self[self.listUnique(permutations)]


    def reorder(self, order='nodes'):
        """Reorder the elements of a Connectivity in a specified order.

        This does not actually reorder the elements itself, but returns
        an index with the order of the rows (elements) in the Connectivity
        table that meets the specified ordering requirements.

        Parameters
        ----------
        order: str or list of ints
            Specifies how to reorder the elements. It is either one
            of the special string values defined below, or else it is an index
            with length equal to the number of elements. The index should be
            a permutation of the numbers in ``range(self.nelems()``. Each value
            gives the number of the old element that should be placed at
            this position. Thus, the order values are the old element numbers
            on the position of the new element number.

            ``order`` can also take one of the following predefined values,
            resulting in the corresponding renumbering scheme being generated:

            - 'nodes': the elements are renumbered in order of their appearance
              in the inverse index, i.e. first are the elements connected to
              node 0, then the as yet unlisted elements connected to node 1, etc.
            - 'random': the elements are randomly renumbered.
            - 'reverse': the elements are renumbered in reverse order.

        Returns
        -------
        1-dim int array
            Int array with a permutation of ``arange(self.nelems()``, such that
            taking the elements in this order will produce a Connectivity
            reordered as requested.
            In case an explicit order was specified as input, this order is
            returned after checking that it is indeed a permutation of
            ``range(self.nelems()``.

        Examples
        --------
        >>> A = Connectivity([[1,2],[2,3],[3,0],[0,1]])
        >>> A[A.reorder('reverse')]
        Connectivity([[0, 1],
                      [3, 0],
                      [2, 3],
                      [1, 2]])
        >>> A[A.reorder('nodes')]
        Connectivity([[0, 1],
                      [3, 0],
                      [1, 2],
                      [2, 3]])
        >>> A[A.reorder([2,3,0,1])]
        Connectivity([[3, 0],
                      [0, 1],
                      [1, 2],
                      [2, 3]])

        """
        if order == 'nodes':
            a = np.sort(self, axis=-1)  # first sort rows
            order = at.sortByColumns(a)
        elif order == 'reverse':
            order = np.arange(self.nelems()-1, -1, -1)
        elif order == 'random':
            order = np.random.permutation(self.nelems())
        else:
            order = np.asarray(order)
            if not (order.dtype.kind == 'i'
                    and (np.sort(order) == np.arange(order.size)).all()):
                raise ValueError(
                    f"order should be a permutation of range({self.nelems()})")
        return order


    def renumber(self, start=0):
        """Renumber the nodes to a consecutive integer range.

        The node numbers in the table are changed thus that they
        form a consecutive integer range starting from the specified
        value.

        Parameters
        ----------
        start: int
            Lowest node number to be used in the renumbered Connectivity.

        Returns
        -------
        elems: Connectivity
            The renumbered Connectivity
        oldnrs: 1-dim int array
            The sorted list of unique (old) node numbers. The new
            node numbers are assigned in order of increasing old node numbers,
            thus the old node number for new node number ``i`` can be found
            at position ``i - start``.

        Examples
        --------
        >>> e,n = Connectivity([[0,2],[1,4],[4,2]]).renumber(7)
        >>> print(e)
        [[ 7  9]
         [ 8 10]
         [10  9]]
        >>> print(n)
        [0 1 2 4]

        Find the old node number of new node 10
        >>> n[10-7]
        4
        """
        nodes = np.asarray(np.unique(self))
        if nodes.size == 0:
            elems = self

        else:
            old = np.arange(nodes.max()+1)
            if nodes.shape[0] == old.shape[0]:
                # we have a consecutive range
                if nodes[0] == start:
                    # numbering is ok, keep
                    elems = self
                else:
                    # add the correct offset
                    elems = self + (start-nodes[0])
            else:
                # need to renumber
                elems = at.inverseUniqueIndex(nodes)[self] + start
                elems = Connectivity(elems, eltype=self.eltype)

        return elems, nodes


    def inverse(self, expand=None):
        """Return the inverse index of a Connectivity table.

        Returns
        -------
        int array
            The inverse index of the Connectivity, as computed
            by :func:`arraytools.inverseIndex`.

        Examples
        --------
        >>> Connectivity([[0,1,2],[0,1,4],[0,4,2]]).inverse(expand=True)
        array([[ 0,  1,  2],
               [-1,  0,  1],
               [-1,  0,  2],
               [-1, -1, -1],
               [-1,  1,  2]])
        >>> Connectivity([[0,1,2],[0,1,4],[0,4,2]]).inverse(expand=False)
        Varray([[0, 1, 2], [0, 1], [0, 2], [], [1, 2]])
        >>> Connectivity().inverse()
        Varray([])
        """
        if expand is None:
            utils.warn("warn_Connectivity_inverse", uplevel=1)
            expand = False

        if self.inv is None or self.flags.writeable:
            self.inv = Varray(self).inverse()
            self.flags.writeable = False

        if expand:
            return self.inv.toArray()
        else:
            return self.inv


    def nParents(self):
        """Return the number of elements connected to each node.

        Returns
        -------
        1-dim int array
            The number of elements connected to each node. The length of
            the array is equal to the highest node number + 1.
            Unused node numbers will have a count of zero.

        Examples
        --------
        >>> Connectivity([[0,1,2],[0,1,4],[0,4,2]]).nParents()
        array([3, 2, 2, 0, 2])
        """
        return self.inverse(expand=False).lengths


    def connectedTo(self, nodes, return_ncon=False):
        """Check if the elements are connected to the specified nodes.

        Parameters
        ----------
        nodes: int or int :term:`array_like`
            One or more node numbers to check for connections in the table.
        return_ncon: bool, optional
            If True, also return the number of connections for each element.

        Returns
        -------
        connections: int array
            The numbers of the elements that contain at least one of the
            specified nodes.
        ncon: int array, optional
            The number of connections for each connected element.
            This is only provided if ``return_ncon`` is True.

        Examples
        --------
        >>> A = Connectivity([[0,1,2],[0,1,3],[0,3,2],[1,2,3]])
        >>> print(A.connectedTo(2))
        [0 2 3]
        >>> A.connectedTo([0,1,3],True)
        (array([0, 1, 2, 3]), array([2, 3, 2, 2]))

        """
        nodes = at.checkArray1D(nodes, kind='i')
        nodes = np.intersect1d(nodes, self)  # remove unconnected nodes
        inv = self.inverse(expand=True)
        ad = inv[nodes]
        ad = ad[ad>=0]
        # We now have a list of all individual attachements to any of the nodes,
        # identified by the element number. We count them per element.
        m, u = at.multiplicity(ad)
        if return_ncon:
            return u, m
        else:
            return u


    def hits(self, nodes):
        """Count the nodes from a list connected to the elements.

        Parameters
        ----------
        nodes: int or list of ints
            One or more node numbers.

        Returns
        -------
        int array (nelems,)
            An int array holding the number of nodes from the specified
            input that are contained in each of the elements.

        Notes
        -----
        This information can also be got from meth:`connectedTo`.
        This method however expands the results to the full element set,
        making it apt for use in selector expressions like
        ``self[self.hits(nodes) >= 2]``.

        Examples
        --------
        >>> A = Connectivity([[0,1,2],[0,1,3],[0,3,2],[1,2,3]])
        >>> A.hits(2)
        array([1, 0, 1, 1])
        >>> A.hits([0,1,3])
        array([2, 3, 2, 2])
        """
        u, m = self.connectedTo(nodes, True)
        res = np.zeros(self.shape[0], dtype=m.dtype)
        res[u] = m
        return res


    def adjacency(self, kind='e', *, exclude=None, mask=None):
        """Create a table of adjacent items.

        This creates an element adjacency table or node adjacency table
        An element `i` is said to be adjacent to element `j`, if the two
        elements have at least one common node.
        A node `i` is said to be adjacent to node `j`, if there is at least
        one element containing both nodes.

        Parameters
        ----------
        kind: 'e' or 'n'
            Select element ('e') or node (n') adjacency table. Default is
            element adjacency.
        exclude: bool array or int index, optional
            Node selector. If provided (with ``kind=='e'``) this defines
            by a bool flag array or int index numbers a list of nodes
            that are not to be considered connectors between elements.

            This option is only useful in the case `kind` == 'e'. If you want to
            exclude elements for the 'n' case, remove those elements from
            the Connectivity before calling adjacency().
        mask: bool array or int index, optional
            This is like exclude, but specifies the nodes that should be
            considered connectors instead of the ones that should be excluded.

            This argument can not be used together with ``exclude``.
            Its use is deprecated.

        Returns
        -------
        :class:`~adjacency.Adjacency` object
            An Adjacency array with shape (nr,nc), where row `i` holds
            a sorted list of all the items that are adjacent to item `i`,
            padded with -1 values to create an equal list length for all items.

        Examples
        --------
        >>> Connectivity([[0,1],[0,2],[1,3],[0,5]]).adjacency('e')
        Adjacency([[ 1,  2,  3],
                   [-1,  0,  3],
                   [-1, -1,  0],
                   [-1,  0,  1]])
        >>> Connectivity([[0,1],[0,2],[1,3],[0,5]]).adjacency('e',exclude=[0,4])
        Adjacency([[ 2],
                   [-1],
                   [ 0],
                   [-1]])
        >>> Connectivity([[0,1],[0,2],[1,3],[0,5]]).adjacency('e',mask=[1,2,3,5])
        Adjacency([[ 2],
                   [-1],
                   [ 0],
                   [-1]])
        >>> Connectivity([[0,1],[0,2],[1,3],[0,5]]).adjacency(
        ...     'e',mask=[False,True,True,True,False,True])
        Adjacency([[ 2],
                   [-1],
                   [ 0],
                   [-1]])
        >>> Connectivity([[0,1],[0,2],[1,3],[0,5]]).adjacency('n')
        Adjacency([[ 1,  2,  5],
                   [-1,  0,  3],
                   [-1, -1,  0],
                   [-1, -1,  1],
                   [-1, -1, -1],
                   [-1, -1,  0]])
        >>> Connectivity([[0,1,2],[0,1,3],[2,4,5]]).adjacency('n')
        Adjacency([[-1,  1,  2,  3],
                   [-1,  0,  2,  3],
                   [ 0,  1,  4,  5],
                   [-1, -1,  0,  1],
                   [-1, -1,  2,  5],
                   [-1, -1,  2,  4]])
        >>> Connectivity([[0,1,2],[0,1,3],[2,4,5]])[[0,2]].adjacency('n')
        Adjacency([[-1, -1,  1,  2],
                   [-1, -1,  0,  2],
                   [ 0,  1,  4,  5],
                   [-1, -1, -1, -1],
                   [-1, -1,  2,  5],
                   [-1, -1,  2,  4]])
        >>> Connectivity([[0,1,],[2,3]]).adjacency('e')
        Adjacency([], shape=(2, 0))
        """
        adj = getattr(self, kind+'adj')
        if adj is not None:
            # We already computed it
            return adj

        # We need the expanded inverse
        inv = self.inverse(expand=True)
        if kind == 'e':
            if mask is not None:
                if exclude is not None:
                    raise ValueError("exclude and mask can not be used together")
                exclude = at.complement(mask, inv.shape[0])
            if exclude is not None:
                inv[exclude] = -1
            if self.size <= 4000000:
                # do in one step
                adj = _elem_adj(inv, self, True)
            else:
                # use multiprocessing
                adj = _elem_adj_multi(inv, self, nproc=4)
                maxcols = max([a.shape[1] for a in adj])
                adj = [at.growAxis(a, maxcols-a.shape[1], axis=1, fill=-1)
                       for a in adj]
                adj = np.concatenate(adj, axis=0)

        elif kind == 'n':
            adj = np.concatenate([np.where(inv>=0, self[:, i][inv], inv)
                                  for i in range(self.nplex())], axis=1)
        else:
            raise ValueError(f"kind should be 'e' or 'n', got {kind}")

        adj = Adjacency(adj)
        # Store the adjacency, because it is expensive to compute
        # True for eadj, don'tknow for nadj
        self.flags.writeable = True
        setattr(self, kind+'adj', adj)
        self.flags.writeable = False
        return adj


    def adjacentElements(self, els, mask=None):
        """Compute adjacent elements.

        This creates an element adjacency table or node adjacency table.
        An element `i` is said to be adjacent to element `j`, if the two
        elements have at least one common node.
        A node `i` is said to be adjacent to node `j`, if there is at least
        one element containing both nodes.

        Parameters
        ----------
        else: int or list of ints
            The element number(s) for which to compute the adjacent elements
        mask: bool array or int index, optional
            Node selector. If provided (with ``kind=='e'``) this defines
            by a bool flag array or int index numbers the list of nodes
            that are to be considered connectors between elements. The default
            is to consider all nodes as connectors.

            This option is only useful in the case `kind` == 'e'. If you want to
            use an element mask for the 'n' case, just apply the (element) mask
            beforehand by using ``self[mask].adjacency('n')``.

        Returns
        -------
        :class:`~adjacency.Adjacency` object
            An Adjacency array with shape (nr,nc), where row `i` holds
            a sorted list of all the items that are adjacent to item `i`,
            padded with -1 values to create an equal list length for all items.

        Examples
        --------
        >>> Connectivity([[0,1],[0,2],[1,3],[0,5]]).adjacentElements([0,1,2,3])
        array([[ 1,  2,  3],
               [-1,  0,  3],
               [-1, -1,  0],
               [-1,  0,  1]])
        >>> Connectivity([[0,1],[0,2],[1,3],[0,5]]).adjacentElements([0,1,2])
        array([[ 1,  2,  3],
               [-1,  0,  3],
               [-1, -1,  0]])
        >>> Connectivity([[0,1],[0,2],[1,3],[0,5]]).adjacentElements([1,2,3])
        array([[ 0,  3],
               [-1,  0],
               [ 0,  1]])
        >>> Connectivity([[0,1],[0,2],[1,3],[0,5]]).adjacentElements([0,2])
        array([[ 1,  2,  3],
               [-1, -1,  0]])
        >>> Connectivity([[0,1],[0,2],[1,3],[0,5]]).adjacentElements([2])
        array([[0]])
        >>> Connectivity([[0,1],[0,2],[1,3],[0,5]]).adjacentElements(1)
        array([[0, 3]])
        """
        els = at.checkArray1D(els, kind='i')
        nels = els.shape[0]
        if nels <= 0:
            return np.array([], dtype=at.Int)
        inv = self.inverse(expand=True)
        # print(inv)
        if mask is not None:
            mask = at.complement(mask, inv.shape[0])
            inv[mask] = -1
        # print(inv[self[els]])
        adj = inv[self[els]].reshape((nels, -1))
        adj[adj == els.reshape(nels, -1)] = -1  # remove the element itself
        adj.sort(axis=1)
        adj[np.where(adj[:, :-1] == adj[:, 1:])] = -1  # remove duplicate items
        adj.sort(axis=1)
        maxc = adj.max(axis=0)  # find maximum per column
        adj = adj[:, maxc>=0]   # retain columns with non-negative maximum
        return adj


    ### frontal methods ###


    def frontGenerator(self, startat=0, frontinc=1, partinc=1):
        # TODO: This is still much slower than Adjacency.frontwalk
        #   Maybe we should just remove this (or else implement in C)
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
        >>> C = Connectivity([[2,8,7],[2,3,8],[3,9,8],[4,10,9],[5,6,11],
        ...                   [6,12,11]])
        >>> for p in C.frontGenerator(): print(p)
        [ 0 -1 -1 -1 -1 -1]
        [ 0  1  1 -1 -1 -1]
        [ 0  1  1  2 -1 -1]
        [ 0  1  1  2  4 -1]
        [0 1 1 2 4 5]
        >>> A = C.adjacency()
        >>> for p in A.frontGenerator(): print(p)
        [ 0 -1 -1 -1 -1 -1]
        [ 0  1  1 -1 -1 -1]
        [ 0  1  1  2 -1 -1]
        [ 0  1  1  2  4 -1]
        [0 1 1 2 4 5]
        """
        if self.nelems() <= 0:
            return

        # Initialize result
        p = -np.ones((self.nelems()), dtype=at.Int)

        # Compute inverse once, then lock array
        self.inverse(expand=True)

        # Remember current elements front
        elems = np.clip(np.asarray(startat), 0, self.nelems())
        prop = 0
        while elems.size > 0:
            # Store prop value for current elems
            # at.printar("Elems ",elems)
            p[elems] = prop
            yield p

            prop += frontinc

            # Determine adjacent elements
            # nodes = np.unique(np.asarray(self[elems]))
            # elems = self.connectedTo(nodes)
            elems = np.unique(self.adjacentElements(elems))
            while elems[0] < 0:  # There should only be one -1
                elems = elems[1:]
            # Remove already done
            elems = np.setdiff1d(elems, np.where(p>=0)[0])
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
        >>> C = Connectivity([[2,8,7],[2,3,8],[3,9,8],[4,10,9],[5,6,11],
        ...                   [6,12,11]])
        >>> print(C.frontWalk())
        [0 1 1 2 4 5]
        """
        for p in self.frontGenerator(
                startat=startat, frontinc=frontinc, partinc=partinc):
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
        >>> C = Connectivity([[2,8,7],[2,3,8],[3,9,8],[4,10,9],[5,6,11],
        ...                   [6,12,11]])
        >>> print(C.front([2]))
        [0 1 3]
        """
        nodes = np.unique(np.asarray(self[startat]))
        front = self.connectedTo(nodes)
        if not add:
            front = np.setdiff1d(front, startat)
        return front


    ##### Creating intermediate levels ###################


    def selectNodes(self, selector):
        """Return a :class:`Connectivity` containing subsets of the nodes.

        Parameters
        ----------
        selector: int :term:`array_like`
            An object that can be converted to a 1-dim or 2-dim
            int array. Examples are a tuple of local node numbers, or a list
            of such tuples all having the same length.
            Each row of `selector` holds a list of the local node numbers that
            should be retained in the new Connectivity table. As an example,
            if the Connectivity is plex-3 representing triangles, a selector
            [[0,1],[1,2],[2,0]] would extract the edges of the triangle.

        Returns
        -------
        :class:`Connectivity`
            A new Connectivity object with shape
            ``(self.nelems*selector.nelems,selector.nplex)``.
            Duplicate elements created by the selector are retained.
            If the selector has an eltype (for example if it is a
            Connectivity itself), the returned Connectivity will have
            the same eltype.

        Examples
        --------
        >>> Connectivity([[0,1,2],[0,2,1],[0,3,2]]).selectNodes([[0,1],[0,2]])
        Connectivity([[0, 1],
                      [0, 2],
                      [0, 2],
                      [0, 1],
                      [0, 3],
                      [0, 2]])
        """
        sel = Connectivity(selector)
        if sel.size > 0:
            lo = Connectivity(self[:, sel].reshape(-1, sel.nplex()))
            lo.eltype = sel.eltype
        else:
            lo = Connectivity(eltype=sel.eltype)
        return lo


    def insertLevel(self, selector, permutations='all'):
        """Insert an extra hierarchical level in a Connectivity table.

        A Connectivity table identifies higher hierarchical entities in
        function of lower ones. This method inserts an extra level in the
        hierarchy.
        For example, if you have volumes defined in function of points,
        you can insert an intermediate level of edges, or faces.
        Each element may generate multiple instances of the intermediate level.

        Parameters
        ----------
        selector: int :term:`array_like`
            An object that can be converted to a 1-dim or 2-dim
            int array. Examples are a tuple of local node numbers, or a list
            of such tuples all having the same length.
            Each row of `selector` holds a list of the local node numbers that
            should be retained in the new Connectivity table.
        permutations: str or None
            Defines which permutations of the row data are allowed while still
            considering the rows equal. Equal rows in the intermediate level
            are collapsed into single items. Possible values are:

            - 'none': no permutations are allowed: rows must match the same date
              at the same positions.
            - 'roll': rolling is allowed. Rows that can be transformed into
              each other by rolling are considered equal;
            - 'all': any permutation of the same data will be considered an
              equal row. This is the default.

        Returns
        -------
        hi: :class:`Connectivity`
            A Connecivity defining the original elements
            in function of the intermediate level ones.
        lo: :class:`Connectivity`
            A Connectivity defining the intermediate level
            items in function of the lowest level ones (the original nodes).
            If the ``selector`` has an ``eltype`` attribute, then ``lo`` will
            inherit the same ``eltype`` value.

        The resulting node numbering of the created intermediate entities
        (the `lo` return value) respects the numbering order of the original
        elements and the applied selector, but in case of collapsing
        duplicate rows, it is undefined which of the collapsed sequences is
        returned.
        Because the precise order of the data in the collapsed rows is lost,
        it is in general not possible to restore the exact original table
        from the two resulting tables.
        See however :meth:`mesh.Mesh.getBorder` for an application where an
        inverse operation is possible, because the border only contains
        unique rows.

        See also :meth:`mesh.Mesh.combine`, which is an almost inverse operation
        for the general case, if the selector is complete.
        The resulting rows may however be permutations of the original.

        Examples
        --------
        >>> Connectivity([[0,1,2],[0,2,1],[0,3,2]]).\
        insertLevel([[0,1],[1,2],[2,0]])
        (Connectivity([[0, 3, 1],
                  [1, 3, 0],
                  [2, 4, 1]]), Connectivity([[0, 1],
                  [2, 0],
                  [0, 3],
                  [1, 2],
                  [3, 2]]))
        >>> Connectivity([[0,1,2,3]]).insertLevel(
        ...     [[0,1,2],[1,2,3],[0,1,1],[0,0,1],[1,0,0]])
        (Connectivity([[1, 2, 0, 0, 0]]), Connectivity([[0, 1, 1],
                  [0, 1, 2],
                  [1, 2, 3]]))
        """
        selector = Connectivity(selector)
        lo = self.selectNodes(selector)
        if lo.size > 0:
            # change the double entries to -1
            LO = lo.copy()
            LO[np.where(LO[:, :-1] == LO[:, 1:])] = -1
            uniq, uniqid = at.uniqueRowsIndex(LO, permutations=permutations)
            hi = Connectivity(uniqid.reshape(-1, selector.nelems()))
            lo = lo[uniq]
        else:
            hi = lo = Connectivity()
        if hasattr(selector, 'eltype') and selector.eltype is not None:
            lo.eltype = selector.eltype
        return hi, lo


    def combine(self, lo):
        # TODO: This is currently far from general!!!
        # should probably be moved to Mesh/TriSurface if needed there
        """Combine two hierarchical Connectivity levels to a single one.

        self and lo are two hierarchical Connectivity tables, representing
        higher and lower level respectively. This means that the elements
        of self hold numbers which point into lo to obtain the lowest level
        items.

        *In the current implementation, the plexitude of lo should be 2!*

        As an example, in a structure of triangles, hi could represent
        triangles defined by 3 edges and lo could represent edges defined
        by 2 vertices. This method will then result in a table
        with plexitude 3 defining the triangles in function of the vertices.

        This is the inverse operation of :meth:`insertLevel` with a selector
        which is complete.
        The algorithm only works if all node numbers of an element are
        unique.

        Examples
        --------
        >>> hi,lo = Connectivity([[0,1,2],[0,2,1],[0,3,2]]).\
        insertLevel([[0,1],[1,2],[2,0]])
        >>> hi.combine(lo)
        Connectivity([[0, 1, 2],
                      [0, 2, 1],
                      [0, 3, 2]])

        """
        lo = Connectivity(lo)
        if self.shape[1] < 2 or lo.shape[1] != 2:
            raise ValueError("Can only combine plex>=2 with plex==2")
        elems = lo[self]
        elems1 = np.roll(elems, -1, axis=1)
        for i in range(elems.shape[1]):
            flags = (elems[:, i, 1] != elems1[:, i, 0]) * (
                elems[:, i, 1] != elems1[:, i, 1])
            elems[flags, i] = np.roll(elems[flags, i], 1, axis=1)
        return Connectivity(elems[:, :, 0])


    def resolve(self):
        """Resolve the connectivity into plex-2 connections.

        Creates a Connectivity table with a plex-2 (edge) connection
        between any two nodes that are connected to a common element.

        There is no point in resolving a plexitude 2 structure.
        Plexitudes lower than 2 can not be resolved.

        Returns a plex-2 Connectivity with all connections between node
        pairs. In each element the nodes are sorted.

        Examples
        --------
        >>> print([ i for i in combinations(range(3),2) ])
        [(0, 1), (0, 2), (1, 2)]
        >>> Connectivity([[0,1,2],[0,2,1],[0,3,2]]).resolve()
        Connectivity([[0, 1],
                      [0, 2],
                      [0, 3],
                      [1, 2],
                      [2, 3]])

        """
        ind = [i for i in combinations(range(self.nplex()), 2)]
        hi, lo = self.insertLevel(ind)
        lo.sort(axis=1)
        ind = at.sortByColumns(lo)
        return lo[ind]


    def reorderNodes(self, schemes, reverse=False):
        # TODO: THIS IS UNTESTED! DO NOT USE!
        """_Convert Elems to/from foreign node numbering schemes.

        The order in which the element's nodes are numbered internally in
        pyFormex may be different than the numbering scheme used in external
        software packages. To allow correct export/import to/from other
        software, the nodes have to be renumbered.
        This function provides such a facility.

        Parameters
        ----------
        schemes: dict
            A dict having pyFormex element names as keys and
            the matching nodal permutation arrays as values. The length of
            the array should match the plexitude of the Elems.
        reverse: bool
            If True, the conversion is from external to internal.
            In this case, the Elems eltype is interpreted as the
            pyFormex target element type (and should be set beforehand).

        Returns
        -------
        Connectivity
            If `schemes` has a key matching the element's name, a Connectivity
            with the renumbered elements is returned.

            - If `reverse` is False (default), the renumbering is done according
              to the permutation given by the `schemes` value matching the
              element name and a Connectivity without eltype is returned.

            - If `reverse` is True, the permutation scheme is reversed prior
              to using it. The target element type is retained in the returned
              Connectivity.

            If the Connectivity has no element type or `scheme` has no matching
            key, the input Connectivity is returned unchanged.

        """
        if self.eltype is not None:
            eltype = self.elName()
            key = eltype.lname
            if key in schemes:
                print(f"key = {key}")
                trl = schemes[key]
                print(f"trl = {trl}")
                elems = self[trl]
                if not reverse:
                    delattr(self, 'eltype')
                return elems

        return self


    def sharedNodes(self, elist=None):
        """Return the list of nodes shared by all elements in elist

        Parameters
        ----------
        elist: int :term:`array_like`
            List of element numbers. If not specified,
            all elements are considered.

        Returns
        -------
        int array
            A 1-dim int array with the list of nodes that are
            common to all elements in the specified list. This array may be
            empty.

        Examples
        --------
        >>> a = Connectivity([[0,1,2],[0,2,1],[0,3,2]])
        >>> a.sharedNodes()
        array([0, 2])
        >>> a.sharedNodes([0,1])
        array([0, 1, 2])

        """
        if elist is None:
            elems = self
        else:
            elems = self[elist]
        m, u = at.multiplicity(elems.ravel())
        return np.asarray(u[m==len(elems)])


    def replic(self, n, inc):
        """Repeat a Connectivity with increasing node numbers.

        Parameters
        ----------
        n: int
            Number of copies to make.
        inc: int
            Increment in node numbers for each copy.

        Returns
        -------
        Connectivity
            A Connectivity with the concatenation of ``n`` replicas of
            ``self``, where the first replica is identical to self and each
            next one has its node numbers increased by ``inc``.

        Examples
        --------
        >>> Connectivity([[0,1,2],[0,2,3]]).replic(2,4)
        Connectivity([[0, 1, 2],
                      [0, 2, 3],
                      [4, 5, 6],
                      [4, 6, 7]])

        """
        return Connectivity(
            np.concatenate([self+i*inc for i in range(n)]), eltype=self.eltype)


    def chain(self, disconnect=None, return_conn=False):
        """Reorder the elements into simply connected chains.

        Chaining the elements involves reordering them such that the first
        node of the next element is equal to the last node of the previous.
        This is especially useful in converting line elements to continuous
        curves or polylines. It will work with any plexitude though, and
        only look at the first and last node of the elements in the chaining
        process.

        Parameters
        ----------
        disconnect: int :term:`array_like` | str, optional
            List of node numbers where the resulting chains should be split.
            None of the resulting chains will have any of the listed node
            numbers as an interior node. A chain may start and end
            at such a node. A special value 'branch' will set the disconnect
            array to all the nodes owned by more than two elements. This will
            split all chains at branching points.
        return_conn: bool
            If True, also return the list of Connectivities corresponding with
            the chains.

        Returns
        -------
        chains: list of int arrays
            A list of tables with the same column length as those in ``conn``,
            and having two columns. The first column contains the original
            element numbers of a chain, and the second column a value +1 or
            -1 depending on whether the element traversal in the connected
            segment is in the original direction (+1) or the reverse (-1).
            The list of chains is sorted in order of decreasing length.
        conn: list of :class:`Connectivity` instances, optional
            Only returned if ``return_conn`` is True: a list a Connectivity
            tables of plexitude ``nplex`` corresponding to each chain.
            The elements in each Connectivity are ordered to form a continuous
            connected segment, i.e. the last node of each element in the table
            is equal to the first node of the following element (if any).

        See Also
        --------
        chained: return only the chained Connectivities

        Examples
        --------
        >>> Connectivity([[0,1],[1,2],[0,4],[4,2]]).chain()
        [array([[ 0,  1],
                [ 1,  1],
                [ 3, -1],
                [ 2, -1]])]
        >>> Connectivity([[0,1],[1,2],[0,4]]).chain()
        [array([[ 1, -1],
           [ 0, -1],
           [ 2,  1]])]
        >>> Connectivity([[0,1],[0,2],[0,3],[5,4]]).chain()
        [array([[ 0, -1],
                [ 1,  1]]),
        array([[3, 1]]),
        array([[2, 1]])]
        >>> Connectivity([[0,1],[0,2],[0,3],[5,4]]).chain(disconnect='branch')
        [array([[3, 1]]), array([[2, 1]]), array([[1, 1]]), array([[0, 1]])]
        >>> Connectivity([[0,1],[0,2],[0,3],[5,4]]).chain(return_conn=True)
        ([array([[ 0, -1],
                 [ 1,  1]]),
        array([[3, 1]]),
        array([[2, 1]])],
        [Connectivity([[1, 0],
                       [0, 2]]),
        Connectivity([[5, 4]]),
        Connectivity([[0, 3]])])
        >>> Connectivity([[0,1,2],[2,0,3],[0,3,1],[4,5,2]]).chain()
        [array([[ 1, -1],
               [ 0, -1],
               [ 2,  1]]),
        array([[3, 1]])]
        >>> Connectivity([[0,1,2],[2,0,3],[0,3,1],[4,5,2]]).chain(
        ...    disconnect=[0])
        [array([[0, 1],
           [1, 1]]), array([[3, 1]]), array([[2, 1]])]
        """
        elems = self[:, [0, -1]]    # this allows for plexitudes > 2
        # Make sure we own the data and can write to it
        elems = np.require(elems, requirements=['O', 'W'])
        elnrs = np.arange(elems.shape[0])  # original element numbers
        if disconnect == 'branch':
            disconnect = np.where(elems.nParents() > 2)[0]
            # !! nParents computes and stores the inverse, which makes
            # elems readonly; so we make it writable again
            elems.inv = None
            elems.flags.writeable = True
        chains = []
        ind = np.zeros((elems.shape[0], 2), dtype=at.Int)
        while elems.size != 0:
            ie = 0
            je = 0
            rev = False
            k = elems[0][0]  # remember startpoint
            while True:
                # Store an element that has been found ok
                if rev:
                    ind[ie] = (je, -1)
                    j = elems[je, 0]
                else:
                    ind[ie] = (je, +1)
                    j = elems[je, 1]
                ie += 1
                elems[je] = -1  # Done with this one
                if j == k or (disconnect is not None and j in disconnect):
                    break
                # Look for the next connected element
                w = np.where(elems[:] == j)
                if w[0].size == 0:
                    # We've reached the end of a branch
                    if disconnect is not None and k in disconnect:
                        # not allowed to revert and continue past start point
                        break
                    # Try reversing
                    w = np.where(elems[:, [0, -1]] == k)
                    if w[0].size == 0:
                        break
                    else:
                        j, k = k, j
                        # reverse the table (colums and rows)
                        ind[:ie] = ind[ie-1::-1].copy()  # rows only
                        ind[:ie, 1] *= -1  # change sign of 2nd column
                je = w[0][0]
                rev = w[-1][0] > 0  # check if the target node is the first or last

            indi = ind[:ie]  # get the relevant part
            indi[:, 0] = elnrs[indi[:, 0]]  # translate element numbers
            chains.append(indi.copy())
            todo = (elems!=-1).any(axis=1)
            elems = elems[todo]
            elnrs = elnrs[todo]

        # sort according to decreasing number of elements
        nel = [len(c) for c in chains]
        srt = np.argsort(nel)[::-1]
        chains = [chains[i] for i in srt]
        if not return_conn:
            return chains

        conn = []
        for i, c in enumerate(chains):
            if c[:, 1].sum() < 0:
                c[:, 1] = - c[:, 1]
                chains[i] = c = c[::-1]
            e = c[:, 0]
            d = c[:, 1] == -1
            els = self[e]
            els[d] = els[d, ::-1]
            conn.append(els)
        return chains, conn


    def chained(self, disconnect=None):
        """Return the Connectivities of the chained elements.

        This is a convenience method calling :meth:`chain` with
        the ``return_conn=True`` parameter and only returning the
        second return value. It is equivalent with::

            self.chain(disconnect, return_conn=True)[1]

        Examples
        --------
        >>> Connectivity([[0,1],[1,2],[0,4],[4,2]]).chained()
        [Connectivity([[0, 1],
                      [1, 2],
                      [2, 4],
                      [4, 0]])]

        >>> Connectivity([[0,1],[1,2],[0,4]]).chained()
        [Connectivity([[4, 0],
                      [0, 1],
                      [1, 2]])]

        >>> Connectivity([[0,1],[0,2],[0,3],[4,5]]).chained()
        [Connectivity([[1, 0],
                      [0, 2]]), Connectivity([[4, 5]]), Connectivity([[0, 3]])]

        >>> Connectivity([[0,1],[0,2],[0,3],[5,4]]).chained(disconnect='branch')
        [Connectivity([[5, 4]]), Connectivity([[0, 3]]),
        Connectivity([[0, 2]]), Connectivity([[0, 1]])]
        >>> Connectivity([[0,1,2],[2,0,3],[0,3,1],[4,5,2]]).chained()
        [Connectivity([[1, 3, 0],
                       [0, 1, 2],
                       [2, 0, 3]]),
        Connectivity([[4, 5, 2]])]
        >>> Connectivity([[0,1,2],[2,0,3],[0,3,1],[4,5,2]],).chained(
        ...     disconnect=[0])
        [Connectivity([[0, 1, 2],
                      [2, 0, 3]]), \
        Connectivity([[4, 5, 2]]), Connectivity([[0, 3, 1]])]
        """
        return self.chain(disconnect, return_conn=True)[1]

    #################################################################
    # class and static methods #

    @staticmethod
    def connect(clist, nodid=None, bias=None, loop=False):
        """Connect nodes from multiple Connectivity objects.

        Parameters
        ----------
        clist: list of Connectivity objects
            The Connectivities to connect.
        nodid: int :term:`array_like`, optional
            List of node indices, same length as ``clist``. This specifies
            which node of the elements will be used in the connect operation.
        bias: int :term:`array_like`, optional
            List of element bias values, same length as ``clist``. If provided,
            then element looping will start at this number instead of at zero.
        loop: bool
            If False (default), new element generation will stop as soon as
            the shortest Connectivity runs out of elements. If set to True,
            the shorter lists will wrap around until all elements of all
            Connectivities have been used.

        Returns
        -------
        Connectivity
            A Connectivity with plexitude equal to the number of
            Connectivities in ``clist``. Each element of the new
            Connectivity consist of a node from the corresponding
            element of each of the Connectivities in ``clist``.
            By default this will be the first node of that element,
            but a ``nodid`` list may be given to specify the node index
            to be used for each of the Connectivities.
            Finally, a list of bias values may be given to specify an offset in
            element number for the subsequent Connectivities.
            If loop==False, the length of the Connectivity will be the minimum
            length of the Connectivities in ``clist``, each minus its respective
            bias. If loop=True, the length will be the maximum
            length in of the Connectivities in ``clist``.

        Examples
        --------
        >>> a = Connectivity([[0,1],[2,3],[4,5]])
        >>> b = Connectivity([[10,11,12],[13,14,15]])
        >>> c = Connectivity([[20,21],[22,23]])
        >>> print(Connectivity.connect([a,b,c]))
        [[ 0 10 20]
         [ 2 13 22]]
        >>> print(Connectivity.connect([a,b,c],nodid=[1,0,1]))
        [[ 1 10 21]
         [ 3 13 23]]
        >>> print(Connectivity.connect([a,b,c],bias=[1,0,1]))
        [[ 2 10 22]]
        >>> print(Connectivity.connect([a,b,c],bias=[1,0,1],loop=True))
        [[ 2 10 22]
         [ 4 13 20]
         [ 0 10 22]]
        """
        try:
            m = len(clist)
            for i in range(m):
                if isinstance(clist[i], Connectivity):
                    pass
                elif isinstance(clist[i], np.ndarray):
                    clist[i] = Connectivity(clist[i])
                else:
                    raise TypeError
        except TypeError:
            raise TypeError("Connectivity.connect(): first argument "
                            "should be a list of Connectivities")

        if not nodid:
            nodid = [0 for i in range(m)]
        if not bias:
            bias = [0 for i in range(m)]
        if loop:
            n = max([clist[i].nelems() for i in range(m)])
        else:
            n = min([clist[i].nelems() - bias[i] for i in range(m)])
        f = np.zeros((n, m), dtype=at.Int)
        for i, j, k in zip(range(m), nodid, bias):
            v = clist[i][k:k+n, j]
            if loop and k > 0:
                v = np.concatenate([v, clist[i][:k, j]])
            f[:, i] = np.resize(v, (n))
        return Connectivity(f)


############################################################################
# Private functions for adjacency multiprocessing

def _elem_adj(inv, els, check):
    """Return elem adj for (part of) the elements"""
    adj = inv[els].reshape((els.shape[0], -1))
    return Adjacency(adj, check_max=check)


def _elem_adj_multi(inv, els, nproc=-1):
    from pyformex import multi
    datablocks = at.splitar(els, nproc)
    datalen = [0] + [d.shape[0] for d in datablocks]
    shift = np.array(datalen[:-1]).cumsum()
    tasks = [(_elem_adj, (inv, e, False)) for e, s in zip(datablocks, shift)]
    return multi.multitask(tasks, nproc=nproc)


######################################
# Deprecated


@utils.deprecated("depr_connectedLineElems")
def connectedLineElems(elems, *args, **kargs):
    raise NotImplementedError(
        "connectedLineElems has been removed. "
        "You should use Connectivity.chained or Connectivity.chain instead.")


# End
