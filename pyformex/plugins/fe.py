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
"""Finite Element Models in pyFormex.

Finite element models are geometrical models that consist of a unique
set of nodal coordinates and one of more sets of elements.
"""

import numpy as np

from pyformex import utils
from pyformex import arraytools as at
from pyformex.coords import Coords
from pyformex.connectivity import Connectivity
from pyformex.mesh import Mesh, mergeMeshes
from pyformex.elements import Elems


######################## Finite Element Model ##########################


class FEModel():
    """A base class for a Finite Element Model.

    An FEModel is a collection of :class:`Mesh` instances which share a
    single set of nodes.

    Examples
    --------
    >>> from ..formex import Formex
    >>> M0 = Formex('4:01234412').toMesh().setProp(1)
    >>> M1 = Formex('3:027138').toMesh().setProp(2)
    >>> FEM = FEModel([M0,M1])
    Finite Element Model
    Number of nodes: 7
    Number of elements: 4
    Number of element groups: 2
    Number of elements per group: [2, 2]
    Plexitude of each group: [4, 3]
    >>> print(FEM.celems)
    [0 2 4]
    >>> print(FEM.coords)
    [[ 0. -1.  0.]
     [ 1. -1.  0.]
     [-1.  0.  0.]
     [ 0.  0.  0.]
     [ 1.  0.  0.]
     [ 0.  1.  0.]
     [ 1.  1.  0.]]
    >>> for e in FEM.elems: print(repr(e))
    Elems([[3, 4, 6, 5],
           [3, 0, 1, 4]], eltype=Quad4)
    Elems([[3, 5, 2],
           [3, 2, 0]], eltype=Tri3)
    >>> for p in FEM.props(): print(p)
    [1 1]
    [2 2]
    >>> for M in FEM.meshes(): print(M)
    Mesh: nnodes: 7, nelems: 2, nplex: 4, level: 2, eltype: quad4
      BBox: [-1. -1.  0.], [1. 1. 0.]
      Size: [2. 2. 0.]
      Length: 6.0  Area: 2.0
    Mesh: nnodes: 7, nelems: 2, nplex: 3, level: 2, eltype: tri3
      BBox: [-1. -1.  0.], [1. 1. 0.]
      Size: [2. 2. 0.]
      Length: 4.82...  Area: 1.0
    >>> glo, loc = FEM.splitElems([0,1,2])
    >>> print(glo)
    [array([0, 1]), array([2])]
    >>> print(loc)
    [array([0, 1]), array([0])]
    >>> FEM.elemNrs(1,[0,1])
    array([2, 3])
    >>> FEM.getElems([[], [0,1]])
    [Elems([], shape=(0, 4), eltype=Quad4), Elems([[3, 5, 2],
           [3, 2, 0]], eltype=Tri3)]
    """
    def __init__(self, meshes, fuse=True, **kargs):
        """Create a new FEModel."""
        if not isinstance(meshes, list):
            meshes = [meshes]

        for m in meshes:
            if not isinstance(m, Mesh):
                raise ValueError("Expected a Mesh or a list thereof.")

        nnodes = [m.nnodes() for m in meshes]
        nelems = [m.nelems() for m in meshes]
        nplex = [m.nplex() for m in meshes]
        coords, elems = mergeMeshes(meshes, fuse=fuse, **kargs)
        prop = [m.prop if m.prop is not None else m.toProp(0) for m in meshes]
        # Store the info
        # We do not store the Meshes, to keep coords/elems info mutable
        self.coords = coords
        self.elems = elems
        self.prop = np.concatenate(prop)
        # Store info to translate node/element numbers from Mesh to FEModel
        self.cnodes = np.cumsum([0] + nnodes)
        self.celems = np.cumsum([0] + nelems)
        print("Finite Element Model")
        print(f"Number of nodes: {self.coords.shape[0]}")
        print(f"Number of elements: {self.celems[-1]}")
        print(f"Number of element groups: {len(nelems)}")
        print(f"Number of elements per group: {nelems}")
        print(f"Plexitude of each group: {nplex}")

    def nelems(self):
        """Return the total number of elements in the model."""
        return self.celems[-1]

    def nnodes(self):
        """Return the total number of nodes in the model."""
        return self.coords.shape[0]

    def ngroups(self):
        """Return the number of element groups in the model."""
        return len(self.elems)

    def mplex(self):
        """Return the plexitude of all the element groups in the model.

        Returns a list of integers.
        """
        return [e.nplex() for e in self.elems]


    def props(self):
        """Return the individual prop arrays for all element groups.

        Returns
        -------
        list of int arrays
            A list with the prop array for each of the element groups
            in the model.
        """
        return [self.prop[i:j] for i, j in
                zip(self.celems[:-1], self.celems[1:])]


    def meshes(self, sel=None):
        """Return the element groups as a list of separate Meshes.

        Parameters
        ----------
        sel: int :term:`array_like`
            The list of global element numbers to be included in the output.
            The default is to include all elements.

        Returns
        -------
        list of :class:`Mesh`
            A list with the Meshes corresponding with the (possibly partial)
            element groups in the model. The Meshes are not compacted and
            may be empty.
        """
        if sel is None:
            elems = self.elems
            props = self.props()
        else:
            elist = self.splitElems(sel)[1]
            elems = self.getElems(elist)
            props = self.getProps(elist)
        return [Mesh(self.coords, e, prop=p) for e, p in zip(elems, props)]


    def splitElems(self, sel=None):
        """Splits a list of element numbers over the element groups.

        Parameters
        ----------
        sel: int :term:`array_like`, optional.
            A list of global element numbers. All values should be in the
            range 0..self.nelems(). If not provided, the list of all elements
            is used.

        Returns
        -------
        global: lists of int arrays
            A list with the global element numbers from the input that
            belong to each of the groups.
        local: list of int arrays
            A list with the local (group) element numbers corresponding
            with the returned global numbers.
        """
        if sel is None:
            sel = np.arange(self.nelems())
        sel = np.unique(sel)
        split = []
        n = 0
        for e in self.celems[1:]:
            i = sel.searchsorted(e)
            split.append(sel[n:i])
            n = i
        return split, [np.asarray(s) - ofs for s, ofs in zip(split, self.celems)]


    def elemNrs(self, group, elems=None):
        """Return the global element numbers for given local group numbers.

        Parameters
        ----------
        group: int
            The group number
        elems: int :term:`array_like`
            A list of local element numbers from the specified group.
            If omitted, the list of all the elements in that group is used.

        Returns
        -------
        int array
            A list with global element numbers corresponding with input.
        """
        if elems is None:
            elems = np.arange(len(self.elems[group]))
        return self.celems[group] + elems


    def getElems(self, sel):
        """Return the definitions of selected elements.

        Parameters
        ----------
        sel: list of int :term:`array_like`
            A list with for each element group the list of local element
            numbers to be included in the output.

        Returns
        -------
        list of :class:`~elements.Elems`
            The connectivity table of the selected elements.
        """
        return [e[s] for e, s in zip(self.elems, sel)]


    def getProps(self, sel):
        """Return the prop values of selected elements.

        Parameters
        ----------
        sel: list of int :term:`array_like`
            A list with for each element group the list of local element
            numbers to be included in the output.

        Returns
        -------
        list of int arrays
            The prop values of the selected elements.
        """
        return [p[s] for p, s in zip(self.props(), sel)]


    def renumber(self, old=None, new=None):
        """Renumber a set of nodes.

        old and new are equally sized lists with unique node numbers, all
        smaller than the number of nodes in the model.
        The old numbers will be renumbered to the new numbers.
        If one of the lists is None, a range with the length of the
        other is used.
        If the lists are shorter than the number of nodes, the remaining
        nodes will be numbered in an unspecified order.
        If both lists are None, the nodes are renumbered randomly.

        This function returns a tuple (old,new) with the full renumbering
        vectors used. The first gives the old node numbers of the current
        numbers, the second gives the new numbers corresponding with the
        old ones.
        """
        nnodes = self.nnodes()
        if old is None and new is None:
            old = np.unique(np.random.randint(0, nnodes-1, nnodes))
            new = np.unique(np.random.randint(0, nnodes-1, nnodes))
            nn = max(old.size, new.size)
            old = old[:nn]
            new = new[:nn]
        elif old is None:
            new = np.asarray(new).reshape(-1)
            at.checkUniqueNumbers(new, 0, nnodes)
            old = np.arange(new.size)
        elif new is None:
            old = np.asarray(old).reshape(-1)
            at.checkUniqueNumbers(old, 0, nnodes)
            new = np.arange(old.size)

        all = np.arange(nnodes)
        old = np.concatenate([old, np.setdiff1d(all, old)])
        new = np.concatenate([new, np.setdiff1d(all, new)])
        oldnew = old[new]
        newold = np.argsort(oldnew)
        self.coords = self.coords[oldnew]
        self.elems = [Connectivity(newold[e], eltype=e.eltype) for e in self.elems]
        return oldnew, newold


@utils.deprecated_by('fe.mergedModel', 'fe.FEModel')
def mergedModel(meshes, **kargs):
    """Returns the fe Model obtained from merging individual meshes.

    The input arguments are (coords,elems) tuples.
    The return value is a merged fe Model.
    """
    return FEModel(meshes, **kargs)


def Model(coords, elems, prop=None, fuse=False, **kargs):
    """Create an FEModel from a single Coords and multiple Elems.

    This is a convenience function to create an FEModel from a single
    Coords block and a list of Elems, and avoid the fusing and renumbering
    of the nodes.

    Parameters
    ----------
    coords: Coords
        A single block of nodes shared by all the meshes in the model.
    elems: list of Elems
        A list of element connectivity tables, that can have different
        element types.
    prop: list of prop
        A list of prop arrays for the meshes. If props are specified,
        they need to be given for all the meshes.
    """
    if 'meshes' in kargs:
        raise ValueError("The use of the 'meshes' argument in fe.Model "
                         "is forbidden. Use fe.FEModel instead.")

    if not isinstance(elems, list):
        elems = [elems]
    if not isinstance(coords, Coords):
        coords = Coords(coords)
    elems = [Elems(e, eltype=e.eltype) for e in elems]
    meshes = [Mesh(coords, e) for e in elems]
    if prop and None not in prop:
        meshes = [m.setProp(p) for m, p in zip(meshes, prop)]
    return FEModel(meshes, fuse=fuse, **kargs)



# End
