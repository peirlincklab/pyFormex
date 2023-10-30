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

"""Polygon meshes.

This module defines the Polygons class, which can be used to describe
discrete geometrical models consisting of polygons.
"""
import numpy as np

from pyformex import utils
from pyformex import arraytools as at
from pyformex import geomtools as gt
from pyformex.coords import Coords
from pyformex.mesh import Mesh
from pyformex.varray import Varray
from pyformex.geometry import Geometry
from pyformex.elements import Elems, ElementType

# These are here for the read/write functions
# from pyformex.path import Path

__all__ = ['Polygons', 'nodalVSum']


def table_func(key):
    @property
    def wrapper(self):
        if key not in self._memory:
            self.compute_tables()
        return self._memory[key]
    return wrapper

##############################################################

@utils.pzf_register
class Polygons(Geometry):
    """Polygons is a discrete geometrical model consisting of polygons.

    The Polygons class is implemented in a similar manner as the
    :class:`Mesh` and :class`TriSurface` classes: the coordinates of
    all the vertices are collected in a single :class:`Coords` array,
    and the 'elements' (polygons) are defined using indices into that
    array. While the :class:`Mesh` and :class`TriSurface` classes store
    the elements in an :class:`Elems` array (requiring a fixed plexitude
    for all elements), the Polygons class uses a :class:`Varray` so that
    the polygons can have a variable number of vertices.

    Parameters
    ----------
    coords: :term:`coords_like`
        A 2-dim :class:`~coords.Coords` (or data to initalize it) with the
        coordinates of all the vertices used to define the polygons.
    elems: :class:`~varray.Varray`
        A :class:`~varray.Varray` (or data to initalize it) with the indices
        of the vertices that define each of the polygons. All values in elems
        should be in the range 0 <= value < len(coords).
    prop: int :term:`array_like`, optional
        1-dim int array with non-negative element property numbers.
        If provided, :meth:`setProp` will be called to assign the
        specified properties.

    Examples
    --------
    A Polygons with a triangle and a square.

    >>> P = Polygons(Coords('0123'), [[0,1,2], [0,1,2,3]])
    >>> print(P.report())
    Polygons: nnodes: 4, nelems: 2, nplex: min 3, max 4, eltype: polygon
      BBox: [0. 0. 0.], [1. 1. 0.]
      Size: [1. 1. 0.]
      Coords: [[0. 0. 0.]
               [1. 0. 0.]
               [1. 1. 0.]
               [0. 1. 0.]]
      Elems: Varray (nrows=2, width=3..4)
               [0 1 2]
               [0 1 2 3]

    """
    def __init__(self, coords=None, elems=None, *, prop=None, check=True):
        """Initialize a new Mesh."""
        Geometry.__init__(self)

        if coords is None or elems is None:
            if coords is None and elems is None:
                # Create an empty Polygons object
                self.coords = Coords()
                self.elems = Varray()
                self.prop = None
                return
            else:
                raise ValueError("Both coords and elems need to be specified")

        if not isinstance(coords, Coords):
            coords = Coords(coords)
        if coords.ndim != 2:
            raise ValueError(
                f"\nExpected 2D coordinate array, got {coords.ndim}")
        if not isinstance(elems, Varray):
            elems = Varray(elems)
        if elems.size > 0 and (
                elems.data.max() >= coords.shape[0] or elems.data.min() < 0):
            raise ValueError(
                "\nInvalid connectivity data: "
                "some node number(s) not in coords array "
                f"(min={elems.data.min()}, max={elems.data.max()}, "
                f"ncoords={coords.shape[0]}")

        self.coords = coords
        self.elems = elems
        self.setProp(prop)
        if check:
            self.check()
        self._memory = {}


    def check(self):
        """Check that all polygons have at least length 3"""
        if (self.elems.lengths < 3).any():
            raise ValueError(
                "Invalid Polygons: Some elements have less than 3 vertices")


    def _set_coords(self, coords):
        """Replace the current coords with new ones.

        Parameters
        ----------
        coords: Coords
             A Coords with same shape as self.coords.

        Returns
        -------
        Mesh
           A Mesh (or subclass) instance with same connectivity, eltype
           and properties as the current, but with possible changes in the
           coordinates of the nodes.
        """
        if isinstance(coords, Coords) and coords.shape == self.coords.shape:
            M = self.__class__(coords, self.elems, prop=self.prop)
            M.attrib(**self.attrib)
            return M
        else:
            raise ValueError(
                f"Invalid reinitialization of {self.__class__} coords")


    @property
    def eltype(self):
        """Return the element type of the Polygons.

        Returns
        -------
        str
            Always 'polygon'
        """
        return 'polygon'


    def elName(self):
        # TODO: deprecate this in favor of self.eltype.name?
        """Return the element name of the Polygons.

        Returns
        -------
        str
            Always 'polygon'
        """
        return 'polygon'


    # @property
    def level(self):
        """Return the level of dimensionality of the polygons.

        Returns
        -------
        int
            Always 2.
        """
        return 2

    @property
    def shape(self):
        """Return the shape of the :attr:`elems` Varray."""
        return self.elems.shape

    # @property
    def nelems(self):
        """Return the number of polygons.

        This is the number of 'rows' in the :attr:`elems` Varray.
        """
        return self.elems.shape[0]

    # @property
    def nplex(self):
        """Return the plexitude of the polygon elements.

        Always returns None, as there is no fixed plexitude of the
        polygons.
        """
        return None

    @property
    def plex(self):
        """Return the plexitude of each of the elements"""
        return self.elems.lengths

    # @property
    def ncoords(self):
        """Return the number of points used to define the polygons.

        This is the first dimension of the :attr:`coords` array.

        Notes
        -----
        This may be different from the total number of vertices in all
        the polygons, as polygons may share some vertices.

        See also
        size: The total number of vertices in all the polygons.
        """
        return self.coords.shape[0]

    @property
    def size(self):
        """Return the total number of polygon vertices.

        This is the total number of entries in the :attr:`elems` Varray.
        """
        return self.elems.size


    def info(self):
        """Return short info about the Mesh.

        Returns
        -------
        str
            A string with info about the shape of the
            :attr:`~mesh.Mesh.coords` and :attr:`elems` attributes.
        """
        return "coords" + str(self.coords.shape) + "; elems" + str(self.elems.shape)


    def report(self, full=True):
        # TODO: We need an option here to let numpy print the full tables.
        """Create a report on the Mesh shape and size.

        The report always contains the number of nodes, number of elements,
        plexitude, dimensionality, element type, bbox and size.
        If full==True(default), it also contains the nodal coordinate
        list and element connectivity table. Because the latter can be rather
        bulky, they can be switched off.

        Note
        ----
        NumPy normally limits the printed output. You will have to change
        numpy settings to actually print the full arrays.
        """
        bb = self.bbox()
        s = (f"{self.__class__.__name__}: "
             f"nnodes: {self.ncoords()}, nelems: {self.nelems()}, ")
        if self.nelems() > 0:
            s += (f"nplex: min {self.plex.min()}, max {self.plex.max()}, "
                  f"eltype: {self.elName()}"
                  f"\n  BBox: {bb[0]}, {bb[1]}"
                  f"\n  Size: {bb[1]-bb[0]}")
        # if self.level() == 2:
        #     s += f"\n  Area: {self.area()}"

        if full:
            s += '\n' + at.stringar("  Coords: ", self.coords) + \
                 '\n' + at.stringar("  Elems: ", self.elems)
        return s


    def __str__(self):
        """Format a Mesh in a string.

        This creates a detailed string representation of a Mesh,
        containing the report() and the lists of nodes and elements.
        """
        return self.report(False)


    def shallowCopy(self, prop=None):
        """Return a shallow copy.

        Parameters
        ----------
        prop: int :term:`array_like`, optional
            1-dim int array with non-negative element property numbers.

        Returns
        -------
        Polygons
            A shallow copy of the Mesh, using the same data arrays
            for ``coords`` and ``elems``. If ``prop`` was provided,
            the new Mesh can have other property numbers.
            This is a convenient method to use the same Mesh
            with different property attributes.
        """
        if prop is None:
            prop = self.prop
        return self.__class__(self.coords, self.elems, prop=prop)


    # NB: It does not make sense putting compact=True here as default,
    # since _select is normally used via select, which has compact=False
    def _select(self, selected, compact=False):
        """Return a Mesh only holding the selected elements.

        This is the low level select method. The normal user interface
        is via the :meth:`select` method.
        """
        selected = at.checkArray1D(selected)
        M = self.__class__(self.coords, self.elems[selected])
        if self.prop is not None:
            M.setProp(self.prop[selected])
        # if compact:
        #     M = M.compact()
        return M


    ##########################################
    ## Allow drawing ##

    def actor(self, **kargs):

        if self.nelems() == 0:
            return None

        from pyformex.opengl.drawable import Actor
        return Actor(self, **kargs)


    @classmethod
    @utils.memoize
    def triangleSelector(clas, n):
        """Return a selector to get triangle fan elements from polygons.

        Examples
        --------
        >>> Polygons.triangleSelector(5)
        array([[0, 1, 2],
               [0, 2, 3],
               [0, 3, 4]])
        """
        i0 = np.zeros(n-2, dtype=at.Int)
        i1 = np.arange(1, n-1, dtype=at.Int)
        i2 = i1+1
        return np.column_stack([i0, i1, i2])


    @classmethod
    @utils.memoize
    def edgeSelector(clas, n):
        """Return a selector to get edge elements from polygons.

        Examples
        --------
        >>> Polygons.edgeSelector(5)
        array([[0, 1],
               [1, 2],
               [2, 3],
               [3, 4],
               [4, 0]])
        """
        i0 = np.arange(n)
        i1 = np.roll(i0, -1)
        return np.column_stack([i0, i1])


    def triangles(self, layout='fan'):
        """Return an Elems with the triangles of the polygons

        layout = 'fan' | 'strip' | 'edglen'

        TODO: only 'fan' is implemented!
        """
        sels = [self.__class__.triangleSelector(l) for l in self.elems.lengths]
        elems = np.row_stack([e[s] for e, s in zip(self.elems, sels)])
        return Elems(elems, eltype='tri3')


    def edges(self, layout='fan'):
        """Return an Elems with the edges of the polygons

        layout = 'fan' | 'strip' | 'edglen'

        TODO: only 'fan' is implemented!
        """
        sels = [self.__class__.edgeSelector(l) for l in self.elems.lengths]
        elems = np.row_stack([e[s] for e, s in zip(self.elems, sels)])
        return Elems(elems, eltype='line2')


    def compute_tables(self):
        faces = self.elems
        edges = np.row_stack([
            faces.data[i:j][Polygons.edgeSelector(j-i)]
            for i, j in faces.rowlimits()])
        uniq, uniqid = at.uniqueRowsIndex(edges, permutations='all')
        self._memory['f_v'] = faces
        self._memory['f_e'] = Varray(uniqid, ind=faces.ind)
        self._memory['e_v'] = Varray(edges[uniq])
        self._memory['e_f'] = self._memory['f_e'].inverse()
        self._memory['v_f'] = self._memory['f_v'].inverse()
        self._memory['v_e'] = self._memory['e_v'].inverse()

    f_v = table_func('f_v')
    f_e = table_func('f_e')
    e_v = table_func('e_v')
    e_f = table_func('e_f')
    v_f = table_func('v_f')
    v_e = table_func('v_e')


    def isManifold(self):
        return self.e_f.maxwidth == 2

    def isClosedManifold(self):
        return self.e_f.maxwidth == self.e_f.minwidth == 2

    def isOrientable(self):
        return self.e_f.maxwidth == self.e_f.minwidth == 2

    def print_tables(self):
        """Print all the tables"""
        print("Connection tables")
        print(f"f_v (faces to vertices) = {self.f_v}")
        print(f"f_e (faces to edges) = {self.f_e}")
        print(f"e_v (edges to vertices) = {self.e_v}")
        print(f"e_f (edges to faces) = {self.e_f}")
        print(f"v_f (vertices to faces) = {self.v_f}")
        print(f"v_e (vertices to edges) = {self.v_e}")


    @property
    def vertices(self):
        """Return all vertices of all polygons.

        Returns
        -------
        Coords
            The coordinates of all vertices of all polygons, in the order
            of the :attr:`elems` data.

        Examples
        --------
        >>> P = Polygons(Coords('0123'), [[0,1,2], [0,1,2,3]])
        >>> P.vertices
        Coords([[0., 0., 0.],
                [1., 0., 0.],
                [1., 1., 0.],
                [0., 0., 0.],
                [1., 0., 0.],
                [1., 1., 0.],
                [0., 1., 0.]])
        """
        return self.coords[self.elems.data]


    def vectors(self):
        """Return vectors along all edges of all polygons.

        Returns
        -------
        Coords
            The vectors along all the edges of all polygons, in the order
            of the :attr:`elems` data. The vectors point from each vertex to
            the next vertex in the polygon.

        Examples
        --------
        >>> P = Polygons(Coords('0123'), [[0,1,2], [0,1,2,3]])
        >>> P.vectors()
        Coords([[ 1.,  0.,  0.],
                [ 0.,  1.,  0.],
                [-1., -1.,  0.],
                [ 1.,  0.,  0.],
                [ 0.,  1.,  0.],
                [-1.,  0.,  0.],
                [ 0., -1.,  0.]])
        """
        ni = self.elems
        return self.coords[ni.roll(-1).data] - self.coords[ni.data]


    @utils.memoize
    def vectorPairs(self):
        """Compute vector pairs along the edges at each vertex of the polygons.

        Returns
        -------
        vec1: float array (nel, nplex, 3)
            The vectors from each vertex to the previous vertex in the polygon.
        vec2: float array (nel, nplex, 3)
            The vectors from each vertex to the next vertex in the polygon.

        Examples
        --------
        >>> P = Polygons(Coords('0123'), [[0,1,2], [0,1,2,3]])
        >>> v1, v2 = P.vectorPairs()
        >>> print(v1)
        [[-1. -1.  0.]
         [ 1.  0.  0.]
         [ 0.  1.  0.]
         [ 0. -1.  0.]
         [ 1.  0.  0.]
         [ 0.  1.  0.]
         [-1.  0.  0.]]
        >>> print(v2)
        [[ 1.  0.  0.]
         [ 0.  1.  0.]
         [-1. -1.  0.]
         [ 1.  0.  0.]
         [ 0.  1.  0.]
         [-1.  0.  0.]
         [ 0. -1.  0.]]
        """
        # This is an alternate implementation
        # ni = Varray(np.arange(self.elems.size), self.elems.ind)
        # nj = ni.roll(1).data
        # v2 = self.vectors()
        # v1 = v2[ni.roll(1).data]
        ni = self.elems
        v1 = self.coords[ni.data] - self.coords[ni.roll(1).data]
        v2 = self.coords[ni.roll(-1).data] - self.coords[ni.data]
        return (v1, v2)


    @property
    @utils.memoize
    def vnormals(self):
        """Return normals at vertices of polygons.

        Returns
        -------
        normals: float array (self.size,3)
            The unit normals on the two edges ending at each vertex.

        Examples
        --------
        >>> P = Polygons(Coords('0123'), [[0,1,2], [0,1,2,3]])
        >>> n = P.vnormals
        >>> print(n.round(2)+0.)
        [[0. 0. 1.]
         [0. 0. 1.]
         [0. 0. 1.]
         [0. 0. 1.]
         [0. 0. 1.]
         [0. 0. 1.]
         [0. 0. 1.]]
        """
        v1, v2 = self.vectorPairs()
        vnormals = at.vectorPairNormals(v1, v2)
        # check for nans (colinear vector pairs)
        w = np.where(np.isnan(vnormals).any(axis=-1))[0]
        if len(w) > 0:
            # replace nans with mean for polygon
            v = self.elems.where(w)[:, 0]
            for r, p in zip(w, v):
                vnormals[r] = np.nanmean(
                    vnormals[self.elems.rowslice(p)], axis=0)
        return vnormals


    @property
    @utils.memoize
    def angles(self):
        """Compute internal angles at vertices of polygons.

        Returns
        -------
        angles: float array (nel, nplex)
            The internal angles made by the two polygon edges at the vertex.

        Examples
        --------
        >>> P = Polygons(Coords('0123'), [[0,1,2], [0,1,2,3]])
        >>> a = P.angles
        >>> print(a)
        [45. 90. 45. 90. 90. 90. 90.]
        """
        v1, v2 = self.vectorPairs()
        return 180. - at.vectorPairAngle(v1, v2)


    @property
    @utils.memoize
    def fnormals(self):
        """Compute mean face normals of polygons.

        Returns
        -------
        fnormals: float array (self.nelems, 3)
            For each polygon, the mean of the normals at all its vertices.

        Examples
        --------
        >>> P = Polygons(Coords('0123'), [[0,1,2], [0,1,2,3], [2,1,0]])
        >>> f = P.fnormals
        >>> print(f)
        [[ 0.  0.  1.]
         [ 0.  0.  1.]
         [ 0.  0. -1.]]
        """
        n = self.vnormals
        f = np.empty((self.nelems(), 3), dtype=at.Float)
        for i in range(self.nelems()):
            f[i] = n[self.elems.rowslice(i)].mean(axis=0)
        return f


    def avg_normals(self, weights='angle', full=False, treshold=None):
        """Compute averaged normals at the nodes of a Polygons.

        Parameters
        ----------
        coords: float :term:`array_like` (ncoords, 3)
            Array with the coordinates of the nodes
        elems: int :term:`array_like` (nelems, nplex, 3)
            Definitions of the polygons in terms of the nodes. All polygons
            should have the same plexitude.
        weights: float :term:`array_like` | 'angle' | None
            Weights to apply to the polygon normals at a node during averaging.
            The default 'angle' will weigh the contribution of the polygons
            by the angle their edges make at the node. Custom values should be
            an array with shape (nelems, nplex). Specifying None will result
            in giving the same weight to all normals.
        full: bool, optional
            If False (default), unique averaged normals at the nodes
            are returned.
            If True, the averaged normals are returned for each vertex
            of each polygon. This is mainly intended for rendering purposes.
        treshold: float, optional
            Only used with ``full=True``. If provided, element vertex normals
            making an angle with the averaged normal having a cosinus smaller
            than treshold, will be returned as the original normal.
            This allows the rendering of feature edges.

        Returns
        -------
        normals: float array
            (ncoords, 3)
            The unit normals at the nodes, obtained by (weighted) averaging
            the normals on the polygons attached to that node. The default
            ``full=False`` returns an array with shape (ncoords, 3). With
            ``full=True``, an array with shape (nelems, nplex, 3) is
            returned.

        Examples
        --------
        This example is the surface of a unit cube.
        Notice that the average normals come out nicely symmetric, even without
        weights, because all polygons have the same angles at the nodes.

        >>> from pyformex.simple import Cube
        >>> M = Cube()
        >>> P = Polygons(M.coords, M.elems)
        >>> print(P.avg_normals())
        [[-0.5774 -0.5774 -0.5774]
         [ 0.5774 -0.5774 -0.5774]
         [ 0.5774  0.5774 -0.5774]
         [-0.5774  0.5774 -0.5774]
         [-0.5774 -0.5774  0.5774]
         [ 0.5774 -0.5774  0.5774]
         [ 0.5774  0.5774  0.5774]
         [-0.5774  0.5774  0.5774]]
        >>> print(P.avg_normals(weights=None))
        [[-0.5774 -0.5774 -0.5774]
         [ 0.5774 -0.5774 -0.5774]
         [ 0.5774  0.5774 -0.5774]
         [-0.5774  0.5774 -0.5774]
         [-0.5774 -0.5774  0.5774]
         [ 0.5774 -0.5774  0.5774]
         [ 0.5774  0.5774  0.5774]
         [-0.5774  0.5774  0.5774]]
        """
        normals = self.vnormals
        if weights == 'angle':
            weights = self.angles
        if weights is not None:
            normals *= weights[..., np.newaxis]
        normals, cnt = nodalVSum(normals, self.elems, self.coords.shape[0])
        # No need to take average, since we are going to normalize anyway
        normals = at.normalize(normals)
        # if not atnodes:
        #     normals = normals[elems]
        #     if treshold is not None:
        #         fnormals = at.normalize(fnormals.reshape(-1,3))
        #         normals = normals.reshape(-1,3)
        #         cosa = at.vectorPairCosAngle(normals, fnormals)
        #         w = np.where(cosa<treshold)[0]
        #         normals[w, :] = fnormals[w, :]
        #         normals = normals.reshape(elems.shape[0], 3, 3)
        return normals


    @property
    @utils.memoize
    def anormals(self):
        return self.avg_normals()


    @property
    def fanormals(self):
        return self.anormals[self.elems.data]


    def centroids(self):
        return Coords.concatenate([
            self.coords[r].mean(axis=0) for r in self.elems])


    ##############################################
    ##  add, merge, fuse, compact


    def __add__(self, other):
        """Return the sum of two Polygons.

        The sum of the Meshes is simply the concatenation thereof.
        It allows us to write simple expressions as M1+M2 to concatenate
        the Meshes M1 and M2. Both meshes should be of the same plexitude
        and have the same eltype.
        The result will be of the same class as self (either a Mesh or a
        subclass thereof).
        """
        return self.concatenate([self, other])


    @classmethod
    def concatenate(clas, polys):
        """Concatenate a list of Polygons.

        Parameters
        ----------
        polys: list of Polygons
            A list of Polygons instance to be concatenated to a single one.

        Notes
        -----
        The concatenation itself does not fuse the vertices that happen to be
        (nearly) conincident. You may want to call the :meth:`fuse` method.

        If any of the Polygons has property numbers, the resulting Polygons
        will inherit the properties. In that case, any elements from
        Polygons without properties will be assigned property 0.
        If all input objects are without properties, so will be the result.

        Examples
        --------
        >>> M0 = Mesh(eltype='quad4')
        >>> P0 = Polygons(M0.coords, M0.elems)
        >>> P1 = Polygons(M0.coords.trl(0, 1.), [[0,1,2],[0,2,3]])
        >>> P = Polygons.concatenate([P0,P1])
        >>> print(P.coords)
        [[0. 0. 0.]
        [1. 0. 0.]
        [1. 1. 0.]
        [0. 1. 0.]
        [1. 0. 0.]
        [2. 0. 0.]
        [2. 1. 0.]
        [1. 1. 0.]]
        >>> print(P.elems)
        Varray (nrows=3, width=3..4)
          [0 1 2 3]
          [4 5 6]
          [4 6 7]
        >>> P = P.fuse()
        >>> print(P.coords)
        [[0. 0. 0.]
         [0. 1. 0.]
         [1. 0. 0.]
         [1. 1. 0.]
         [2. 0. 0.]
         [2. 1. 0.]]
        >>> print(P.elems)
        Varray (nrows=3, width=3..4)
          [0 2 3 1]
          [2 4 5]
          [2 5 3]
        """
        coords = Coords.concatenate([p.coords for p in polys])
        offset = at.cumsum0([p.coords.shape[0] for p in polys])
        ndata = at.cumsum0([p.elems.size for p in polys])
        elems = Varray.concatenate([p.elems for p in polys])
        for i in range(1, len(polys)):
            elems.data[ndata[i]:ndata[i+1]] += offset[i]
        if all([p.prop is None for p in polys]):
            # There are no props
            prop = None
        else:
            # Keep the available props
            prop = np.concatenate([p.prop if p.prop is not None else
                                   np.zeros(p.nelems(), dtype=at.Int)
                                   for p in polys])
        P = clas(coords, elems, prop=prop)
        return P


    def fuse(self, nodes=None, **kargs):
        """Fuse the nodes of a Polygons.

        Nodes that are within the tolerance limits of each other
        are merged into a single node.

        Parameters
        ----------
        nodes: int :term:`array_like`, optional
            A list of node numbers. If provided, only these nodes will be
            involved in the fuse operation.
        **kargs:
            Extra arguments for tuning the fuse operation are passed to the
            :meth:`coords.Coords:fuse` method.

        Examples: see :meth:`concatenate`
        """
        if nodes is None:
            coords, index = self.coords.fuse(**kargs)
        else:
            keep = at.complement(nodes, self.ncoords())
            coords, fusindex = self.coords[nodes].fuse(**kargs)
            coords = Coords.concatenate([self.coords[keep], coords])
            index = -np.ones(self.ncoords(), dtype=at.Int)
            index[keep] = np.arange(len(keep), dtype=at.Int)
            index[nodes] = len(keep) + fusindex
        elems = Varray(index[self.elems.data], ind=self.elems.ind)
        return self.__class__(coords, elems, prop=self.prop)


    def compact(self):
        """Remove unconnected nodes and renumber the Polygons.

        Returns
        -------
        Polygons
            The input object, where any unconnected nodes have been removed
            and the nodes are renumbered to a compacter scheme.

        Notes
        -----
        This changes the object in-place.

        If the node-numbering has been changed, the object will have
        an attribute 'oldnumbers' which is an int array giving the
        old node number for in the position of the new node number.

        Examples
        --------
        >>> x = Coords([[i] for i in np.arange(5)])
        >>> P = Polygons(x, [[0,1,2],[2,3,1,0]])
        >>> print(P.coords)
        [[0. 0. 0.]
         [1. 0. 0.]
         [2. 0. 0.]
         [3. 0. 0.]
         [4. 0. 0.]]
        >>> P1 = P.compact()
        >>> print(P1.coords)
        [[0. 0. 0.]
         [1. 0. 0.]
         [2. 0. 0.]
         [3. 0. 0.]]
        >>> print(P1.elems)
        Varray (nrows=2, width=3..4)
          [0 1 2]
          [2 3 1 0]
        >>> P1 is P
        True
        >>> print(P.oldnumbers)
        None
        >>> P = Polygons(x, [[4,1,2],[2,3,1,4]])
        >>> P.compact()
        <pyformex.polygons.Polygons object at ...>
        >>> print(P.coords)
        [[1. 0. 0.]
         [2. 0. 0.]
         [3. 0. 0.]
         [4. 0. 0.]]
        >>> print(P.elems)
        Varray (nrows=2, width=3..4)
          [3 0 1]
          [1 2 0 3]
        >>> print(P.oldnumbers)
        [1 2 3 4]
        """
        old = np.unique(self.elems.data)
        nmax = old.max() + 1
        if old.min() == 0 and nmax == old.size:
            # We have compact elems.
            if len(self.coords) > nmax:
                self.coords = self.coords[:nmax]
            self.oldnumbers = None
        else:
            # Renumber the nodes
            new = at.inverseUniqueIndex(old)
            self.elems = Varray(new[self.elems.data], ind=self.elems.ind)
            self.coords = self.coords[old]
            self.oldnumbers = old
        return self


    def _reduce(self, mplex):
        """Reduce the Polygons to a specified maximum plexitude.

        Notes
        -----
        This is a low level function. Users shoudl invoke it through
        :meth:`reduce` or :meth:`split`.

        Returns
        -------
        dict
           A dictionary where the keys are plexitudes and the values are
           the faces having that plexitude.

        See Also
        --------
        reduce: reduce the maximum plexitude of the polygons
        split: split the Polygons into Mesh objects.
        """
        # TODO: inherit the props
        def split_max():
            """Split the polygons with highest plexitude"""
            for e in gt.split_polygon(self.coords, elems.pop(max(elems))):
                nplex = e.shape[-1]
                if nplex in elems:
                    elems[nplex] = np.concatenate([elems[nplex], e], axis=0)
                else:
                    elems[nplex] = e

        elems = self.elems.split()
        if len(elems) > 0 and elems[-1].shape[1] > mplex:
            elems = dict((e.shape[1], e) for e in elems)
            while max(elems) > mplex:
                split_max()
            elems = [elems[nplex] for nplex in sorted(elems.keys())]
        return elems


    def reduce(self, mplex):
        """Reduce the Polygons to a specified maximum plexitude.

        Parameters
        ----------
        mplex: int
            The maximal plexitude of the output polygons. Thus, with mplex=3
            only triangles will results; mplex=4 will yield triangles and quads.

        Returns
        -------
        Polygons
            A Polygons where all of the polygons with more than mplex vertices
            have been split into smaller ones.

        Notes
        -----
        Splitting a polygon is done along the shortest diagonal.

        See Also
        --------
        split: split (and optionally reduce) the Polygons into Mesh objects.

        Examples
        --------
        >>> x = Coords([[i] for i in np.arange(5)])
        >>> P = Polygons(x, [[0,1,2],[0,1,2,3],[0,1,2,3,4]])
        >>> print(P.reduce(4).elems)
        Varray (nrows=4, width=3..4)
          [0 1 2]
          [0 1 2]
          [0 1 2 3]
          [2 3 4 0]
        >>> print(P.reduce(3).elems)
        Varray (nrows=6, width=3..3)
          [0 1 2]
          [0 1 2]
          [0 1 2]
          [2 3 4]
          [2 3 0]
          [4 0 2]
        >>>
        """
        if self.elems.maxwidth <= mplex:
            # nothing to be done
            return self
        else:
            return Polygons(self.coords, Varray.fromArrays(self._reduce(mplex)))


    def split(self, mplex=None):
        """Split the Polygons into Meshes of fixed plexitude

        Parameters
        ----------
        mplex: int, optional
            The maximal plexitude of the resulting Meshes. Thus, with mplex=3
            only triangles will results; mplex=4 will yield triangles and quads.
            If needed, polygons will be split up to be smaller that the
            maximum plexitude. If not provided, the original plexitudes
            are kept.

        Returns
        -------
        list of Mesh
            A list of Mesh objects with plexitude >= 3.
            The eltype of the Mesh objects is Tri3, Quad4 or Poly# for
            plexitudes > 4. All the Mesh objects use the same coords object.
            The list is sorted in order of increasing plexitude.

        Notes
        -----
        While reducing and splitting the Polygons can also be achieved with
        ``self.reduce(mplex).split()``, using the mplex argument here is
        slightly faster.

        See Also
        --------
        reduce: reduce the maximum plexitude of the polygons
        """
        if mplex is None or mplex >= self.elems.maxwidth:
            # no need to reduce polygons
            elems = self.elems.split()
        else:
            elems = self._reduce(mplex)
        return [Mesh(self.coords, e, eltype=ElementType.polygon(e.shape[1]))
                for e in elems]


    def toSurface(self, method='reduce'):
        """Convert the Polygons to a TriSurface

        Parameters
        ----------
        method: str
            The method to use to convert polygons into triangles. One of:

            - 'reduce': use the :meth:`reduce` method, splitting the polygons
              along the shortest diagonals. This is the default.
            - 'fan': split the polygons into a fan of triangles with apex
              at the first point. This corresponds to hoe the polygons are
              rendered.
            - 'prune': simply removes all non-triangle polygons.

        Notes
        -----
        Currently, the 'reduce' method does not retain the 'prop' values.
        """
        from pyformex.trisurface import TriSurface
        prop = self.prop
        if method == 'fan':
            elems = self.triangles('fan')
            if prop is not None:
                prop = np.repeat(prop, self.elems.lengths-2)
        elif method == 'prune':
            elems = self.elems.split()[0]
            ok = self.plex == 3
            if prop is not None:
                prop = prop[ok]
        else:
            elems = self.reduce(3).elems
        return TriSurface(self.coords, elems, prop=prop)


    ###################
    ## PZF interface ##

    def pzf_dict(self):
        kargs = Geometry.pzf_dict(self)
        kargs['elems'] = self.elems.data
        kargs['ind'] = self.elems.ind
        return kargs

    @classmethod
    def pzf_load(clas, coords, elems, ind, **kargs):
        return clas(coords, Varray(elems, ind), **kargs)


########## IO functions ###########


def _install_writePOLYGONS():
    """Install a method to write to PGF file"""
    def writePolygons(self, F, name=None, sep=None):
        """Write a Polygons.

        Parameters
        ----------
        F: :class:`Polygons`
            The object to be written.
        name: str
            See :meth:`writeGeometry`
        sep: str
            See :meth:`writeGeometry`

        Notes
        -----
        This writes a header line with these attributes and arguments:
        objtype, ncoords, nelems, size, props(True/False),
        eltype, normals(True/False), color, sep, name.
        This is followed by the array data for: coords, elems.data,
        elems.ind, prop, normals, color
        """
        objtype = F.__class__.__name__
        if not isinstance(F, Polygons):
            raise ValueError(
                f"Invalid object type {type(F)}, expected Polygons")
        if sep is None:
            sep = self.sep
        hasprop = F.prop is not None
        hasnorm = hasattr(F, 'normals') and \
            isinstance(F.normals, np.ndarray) and \
            F.normals.shape == (F.size, 3)
        color = None
        colormap = None
        Fc = F.attrib['color']
        if Fc is not None:
            if isinstance(Fc, str):
                color = Fc
            else:
                try:
                    Fc = at.checkArray(Fc, kind='f')
                    colormap = None
                    colorshape = Fc.shape
                except Exception:
                    Fc = at.checkArray(Fc, kind='i')
                    colormap = 'default'
                    colorshape = Fc.shape + (3,)
                if colorshape == (3,):
                    color = tuple(Fc)
                elif colorshape == (F.nelems(), 3):
                    color = 'element'
                elif colorshape == (F.size, 3):
                    color = 'vertex'
                else:
                    raise ValueError(f"Incorrect color shape: {str(colorshape)}")

        head = (    # parentheses to allow string continuation
            f"# objtype='{objtype}'; "
            f"ncoords={F.ncoords()}; nelems={F.nelems()}; size={F.size}; "
            f"props={hasprop}; normals={hasnorm};  "
            f"color={repr(color)}; sep='{sep}'"
        )
        if name:
            head += f"; name='{name}'"
        if F.elName():
            head += f"; eltype='{F.elName()}'"
        if colormap:
            head += f"; colormap='{colormap}'"
        self.writeline(head)
        self.writeData(F.coords, sep)
        self.writeData(F.elems.data, sep)
        self.writeData(F.elems.ind, sep)
        if hasprop:
            self.writeData(F.prop, sep)
        if hasnorm:
            self.writeData(F.normals, sep)
        if color == 'element' or color == 'vertex':
            self.writeData(Fc, sep)
        for field in F.fields:
            fld = F.fields[field]
            self.writeline(f"# field='{fld.fldname}'; fldtype='{fld.fldtype}'; "
                           f"shape={repr(fld.data.shape)}; sep='{sep}'")
            self.writeData(fld.data, sep)

    def readPolygons(self, ncoords, nelems, size, props, sep):
        """Read a Polygons from a pyFormex geometry file.

        The following arrays are read from the file:
        - a coordinate array with `ncoords` points,
        - a Varray data array of length `size`
        - a Varray ind array with `nelems+1` elements
        - if present, a property number array for `nelems` elements.

        Returns the Mesh constructed from these data, or a subclass if
        an objtype is specified.
        """
        ndim = 3
        x = at.readArray(self.fil, at.Float, (ncoords, ndim), sep=sep)
        e = at.readArray(self.fil, at.Int, (size,), sep=sep)
        i = at.readArray(self.fil, at.Int, (nelems+1,), sep=sep)
        if props:
            p = at.readArray(self.fil, at.Int, (nelems,), sep=sep)
        else:
            p = None
        M = Polygons(x, Varray(e, ind=i), prop=p)
        return M
    from pyformex import geomfile
    geomfile.GeometryFile.writePolygons = writePolygons
    geomfile.GeometryFile.readPolygons = readPolygons


_install_writePOLYGONS()


def nodalVSum(val, elems, nnod=None):
    """Compute the nodal sum of values defined at polygon vertices.

    This is like :func:`arraytools.nodalSum`, but where elems is defined
    as a Varray and val contains the value in order of that Varray.

    Parameters
    ----------
    val: float array (nsize, nval)
        Defines nval values at elems.nsize vertices.
    elems: Varray
        The node indices of nelems polygons.
    nnod: int
        The number of nodes. This should be higher than the maximum
        value in elems. If not specified, it will be set to the highest
        value in elems + 1.

    Returns
    -------
    sum: float ndarray (nnod, nval)
        The sum of all the values at the same node.
    cnt: int ndarray (nnod)
        The number of values summed at each node.
    """
    nmax = elems.data.max()
    if nnod is None:
        nnod = nmax + 1
    if nnod <= nmax:
        raise ValueError(f"nnod should at least be {nmax+1}")

    # create return arrays
    nval = val.shape[-1]
    sum = np.zeros((nnod, nval), dtype=np.float32)
    cnt = np.zeros((nnod,), dtype=np.int32)
    for i in range(elems.nrows):
        ind = elems.rowslice(i)
        nodes = elems.data[ind]
        sum[nodes] += val[ind]
        cnt[nodes] += 1

    return sum, cnt

# End
