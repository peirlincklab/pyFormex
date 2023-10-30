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
#
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program.  If not, see http://www.gnu.org/licenses/.
##

"""Finite element meshes in pyFormex.

This module defines the Mesh class, which can be used to describe discrete
geometrical models like those used in Finite Element models.
It also contains some useful functions to create such models.
"""

import itertools

import numpy as np

from pyformex import utils
from pyformex import arraytools as at

from pyformex.coords import Coords
from pyformex.formex import Formex
from pyformex.connectivity import Connectivity
from pyformex.elements import ElementType, Elems
from pyformex.geometry import Geometry


__all__ = ['Mesh', 'mergeNodes', 'mergeMeshes', 'quadgrid', 'rectangle',
           'rectangleWithHole', 'quadrilateral', 'continuousCurves',
           'triangleQuadMesh', 'quarterCircle']

##############################################################


# TODO: replace Connectivity with Elems wherever needed
@utils.pzf_register
class Mesh(Geometry):
    """A Mesh is a discrete geometrical model defined by nodes and elements.

    The Mesh class is one of the two basic geometrical models in pyFormex,
    the other one being the :class:`Formex`. Both classes have a lot in
    common: they represent a collection of geometrical entities of the same
    type (e.g., lines, or triangles, ...). The geometrical entities are
    also called 'elements', and the number of elements in the Mesh is
    :meth:`nelems`. The :term:`plexitude` (the number of points in an
    element) of a Mesh is found from :meth:`nplex`. Each point has
    ``ndim=3`` coordinates. While in a :class:`Formex` all these points
    are stored in an array with shape (nelems, nplex, 3), the :class:`Mesh`
    stores the information in two arrays: the coordinates of all the points
    are gathered in a single twodimensional array with shape (ncoords,3).
    The individual geometrical elements are then described by indices into
    that array: we call that the connectivity, with shape (nelems, nplex).

    This model has some advantages over the :class:`Formex` data model:

    - a more compact storage, because coordinates of coinciding points
      require only be stored once (and we usually call the points
      :term:`node` s);
    - the single storage of coinciding points represents the notion
      of connections between elements (a :class:`Formex` to the contrary
      is always a loose collection of elements);
    - connectivity related algorithms are generally faster;
    - the connectivity info also allows easy identification of geometric
      subentities (entities of a lower :term:`level`, like the border
      lines of a surface).

    The downside is that geometry generating and replicating algorithms are
    often far more complex and possibly slower.

    In pyFormex we therefore mostly use the Formex data model when creating,
    copying and replicating geometry, but when we come to the point of needing
    connectivity related algorithms or exporting the geometry to file (and to
    other programs), a Mesh data model usually becomes more appropriate.
    A :class:`Formex can be converted into a Mesh with the :meth:`Formex.toMesh`
    method, while the :meth:`Mesh.toFormex` method performs the inverse
    conversion.


    Parameters
    ----------
    coords: :class:`~coords.Coords` or other object.
        Usually, a 2-dim Coords object holding the coordinates of all the
        nodes used in the Mesh geometry.
        See details below for different initialization methods.
    elems: :class:`~connectivity.Connectivity` (nelems,nplex)
        A Connectivity object, defining the elements of the geometry
        by indices into the ``coords`` Coords array. All values in elems
        should be in the range 0 <= value < ncoords.
    prop: int :term:`array_like`, optional
        1-dim int array with non-negative element property numbers.
        If provided, :meth:`setProp` will be called to assign the
        specified properties.
    eltype: str or :class:`~elements.ElementType`, optional
        The element type of the geometric entities (elements).
        This is only needed if the element type has not yet been
        set in the ``elems`` Connectivity. See below.


    A Mesh object can be initialized in many different ways, depending on
    the values passed for the ``coords`` and ``elems`` arguments.

    - Coords, Connectivity: This is the most obvious case:
      ``coords`` is a 2-dim :class:`~coords.Coords` object holding
      the coordinates of all the nodes in the Mesh,
      and ``elems`` is a :class:`~connectivity.Connectivity` object
      describing the geometric elements by indices into the ``coords``.

    - Coords, : If A Coords is passed as first argument, but no ``elems``,
      the result is a Mesh of points, with plexitude 1. The Connectivity
      will be constructed automatically.

    - object with ``toMesh``, : As a convenience, if another object is
      provided that has a ``toMesh`` method and ``elems`` is not provided,
      the result of the ``toMesh`` method will be used to initialize
      both ``coords`` and ``elems``.

    - None: If neither ``coords`` nor ``elems`` are specified, but ``eltype``
      is, a unit sized single element Mesh of the specified
      :class:`~elements.ElementType` is created.

    - Specifying no parameters at all creates an empty Mesh, without any data.


    Setting the element type can also be done in different ways. If ``elems``
    is a Connectivity, it will normally already have a element type.
    If not, it can be done by passing it in the ``eltype`` parameter.
    In case you pass a simple array or list in the ``elems`` parameter,
    an element type is required.
    Finally, the user can specify an eltype to override the one in the
    Connectivity. It should however match the plexitude of the connectivity
    data.

    ``eltype`` should be one of the :class:`~elements.ElementType`
    instances or the name of such an instance.
    If required but not provided, the pyFormex default is used, which is
    based on the plexitude: 1 = point, 2 = line segment,
    3 = triangle, 4 or more is a polygon.


    A properly initialized Mesh has the following attributes:


    Attributes
    ----------
    coords: :class:`~coords.Coords` (ncoords,3)
        A 2-dim Coords object holding the coordinates of all the nodes used
        to describe the Mesh geometry.
    elems: :class:`~connectivity.Connectivity` (nelems,nplex)
        A Connectivity object, defining the elements of the geometry
        by indices into the :attr:`coords` Coords array. All values in elems
        should be in the range ``0 <= value < ncoords``.

        The Connectivity also stores the element type of the Mesh.
    prop: int array, optional
        Element property numbers. See :attr:`geometry.Geometry.prop`.
    attrib: :class:`~attributes.Attributes`
        An Attributes object. See :attr:`geometry.Geometry.attrib`.
    fields: dict
        The Fields defined on the Mesh. See :attr:`geometry.Geometry.fields`.

    Note
    ----
    The `coords`` attribute of a Mesh can hold points that are not used
    or needed to describe the Geometry. They do not influence the result
    of Mesh operations, but use more memory than needed. If their number
    becomes large, you may want to free that memory by calling the
    :meth:`compact` method. Also, before exporting a Mesh (e.g. to a
    numerical simulation program), you may want to compact the Mesh first.

    Examples
    --------
    Create a Mesh with four points and two triangle elements of type 'tri3'.

    >>> coords = Coords('0123')
    >>> elems = [[0,1,2], [0,2,3]]
    >>> M = Mesh(coords,elems,eltype='tri3')
    >>> print(M.report(full=True))
    Mesh: nnodes: 4, nelems: 2, nplex: 3, level: 2, eltype: tri3
      BBox: [0.  0.  0.], [1.  1.  0.]
      Size: [1.  1.  0.]
      Length: 4.0  Area: 1.0
      Coords: [[0.  0.  0.]
               [1.  0.  0.]
               [1.  1.  0.]
               [0.  1.  0.]]
      Elems: [[0 1 2]
              [0 2 3]]
    >>> M.nelems(), M.ncoords(), M.nplex(), M.level(), M.elName()
    (2, 4, 3, 2, 'tri3')

    And here is a line Mesh converted from a Formex:

    >>> M1 = Formex('l:112').toMesh()
    >>> print(M1.report(full=True))
    Mesh: nnodes: 4, nelems: 3, nplex: 2, level: 1, eltype: line2
      BBox: [0. 0. 0.], [2. 1. 0.]
      Size: [2. 1. 0.]
      Length: 3.0
      Coords: [[0. 0. 0.]
               [1. 0. 0.]
               [2. 0. 0.]
               [2. 1. 0.]]
      Elems: [[0 1]
              [1 2]
              [2 3]]

    Indexing returns the full coordinate set of the specified element(s).
    See :meth:`__getitem__`.

    >>> M1[1:]
    Coords([[[1., 0., 0.],
             [2., 0., 0.]],
    <BLANKLINE>
            [[2., 0., 0.],
             [2., 1., 0.]]])

    The Mesh class inherits from :class:`Geometry` and therefore has
    all the coordinate transform methods defined there readily
    available:

    >>> M2 = M1.rotate(90)
    >>> print(M2.coords)
    [[ 0.  0.  0.]
     [ 0.  1.  0.]
     [ 0.  2.  0.]
     [-1.  2.  0.]]

    """
    ###################################################################
    ## DEVELOPERS: ATTENTION
    ##
    ## The Mesh class is intended to be subclassable: TriSurface is an
    ## example of a class derived from Mesh.
    ## Therefore, all methods returning a Mesh and also operating correctly
    ## on a subclass, should use self.__class__ to return the proper class.
    ## The self.__class__ initiator should be called with the 'prop' and
    ## 'eltype' arguments, using keyword arguments, because only the first
    ## two arguments ('coords', 'elems') are guaranteed.
    ## See the copy() method for an example.
    ###################################################################

    _special_members_ = ['__getitem__']
    _exclude_members_ = ['matchLowerEntitiesMesh', 'matchFaces']

    fieldtypes = ['node', 'elemc', 'elemn']

    def __init__(self, coords=None, elems=None, prop=None, eltype=None):
        """Initialize a new Mesh."""
        Geometry.__init__(self)
        self.coords = self.elems = self.prop = None
        self.conn = self.econn = self.fconn = None

        if coords is None:
            if eltype is None:
                # Create an empty Mesh object
                return

            else:
                # Create unit Mesh of specified type
                el = ElementType.get(eltype)
                coords = el.vertices
                elems = el.getElement()

        if elems is None:
            # initialize from a single object
            if isinstance(coords, Coords):
                # Create a Mesh of points
                M = Mesh(coords, np.arange(coords.ncoords()))
            elif isinstance(coords, Mesh):
                # Create a Mesh
                M = coords
            elif hasattr(coords, 'toMesh'):
                M = coords.toMesh()
            else:
                raise ValueError(
                    "No `elems` specified and the first argument can not "
                    "be converted to a Mesh.")
            coords, elems = M.coords, M.elems

        if not isinstance(coords, Coords):
            coords = Coords(coords)
        if coords.ndim != 2:
            raise ValueError(f"\nExpected 2D coordinate array, got {coords.ndim}")
        elems = Connectivity(elems, eltype=eltype)
        if elems.size > 0 and (
                elems.max() >= coords.shape[0] or elems.min() < 0):
            raise ValueError(
                "\nInvalid connectivity data: "
                "some node number(s) not in coords array "
                f"(min={elems.min()}, max={elems.max()}, "
                f"ncoords={coords.shape[0]}")

        self.coords = coords
        self.elems = elems
        self.eltype = eltype  # This sanitizes the eltype
        self.setProp(prop)


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
            M = self.__class__(coords, self.elems, prop=self.prop,
                               eltype=self.eltype)
            M.attrib(**self.attrib)
            return M
        else:
            raise ValueError(
                f"Invalid reinitialization of {self.__class__} coords")


    @property
    def eltype(self):
        """Return the element type of the Mesh.

        Returns
        -------
        :class:`elements.ElementType`
            The eltype attribute of the :attr:`elems` attribute.

        Examples
        --------
        >>> M = Mesh(eltype='tri3')
        >>> M.eltype
        Tri3
        >>> M.eltype = 'line3'
        >>> M.eltype
        Line3
        >>> print(M)
        Mesh: nnodes: 3, nelems: 1, nplex: 3, level: 1, eltype: line3
        BBox: [0.  0.  0.], [1.  1.  0.]
        Size: [1.  1.  0.]
        Length: 1.0

        One cannot set an element type with nonmatching plexitude:

        >>> M.eltype = 'quad4'
        Traceback (most recent call last):
        ...
        p...InvalidElementType: Data plexitude (3) != eltype plexitude (4)
        """
        return self.elems.eltype


    @eltype.setter
    def eltype(self, eltype):
        """Set the eltype from a character string.

        Parameters
        ----------
        eltype: str or :class:`~elements.ElementType`, optional
            The element type to be set in the ``elems`` Connectivity.
            It is either one of the ElementType instances defined in
            elements.py, or the name of such an instance.
            The plexitude of the ElementType should match the plexitude
            of the Mesh.

        Note
        ----
        Setting the eltype sanitizes the eltype stored in the elems attribute
        and promotes the elems attribute to Elems class.
        """
        if eltype is None and hasattr(self.elems, 'eltype'):
            eltype = self.elems.eltype
        try:
            self.elems = Elems(self.elems, eltype)
        except Exception as e:
            # We need this in intermediary states of a Mesh.convert,
            # where element types are used that are not (yet) defined.
            self.elems.eltype = f'plex{self.nplex()}'
            raise e


    @utils.deprecated('mesh_eltype')  # 2021-12
    def setEltype(self, eltype=None):
        """Set the eltype of the Mesh."""
        self.eltype = eltype
        return self

    @utils.deprecated('mesh_eltype')  # 2021-12
    def elType(self):
        """Return the element type of the Mesh."""
        return self.elems.eltype


    def elName(self):
        # TODO: deprecate this in favor of self.eltype.name?
        """Return the element name of the Mesh.

        Returns
        -------
        str
            The name of the ElementType of the Mesh.

        See Also
        --------
        elType: returns the ElementType instance

        Examples
        --------
        >>> Formex('4:0123').toMesh().elName()
        'quad4'
        """
        return self.eltype.lname


    # TODO: this needs sanitizing: purpose, normals(), see also TriSurface
    def setNormals(self, normals=None):
        """Set/Remove the normals of the mesh.

        Parameters
        ----------
        normals: float :term:`array_like`
            A float array of shape (ncoords,3) or (nelems,nplex,3).
            If provided, this will set these normals for use in
            rendering, overriding the automatically computed ones.
            If None, this will clear any previously set user normals.

        """
        from pyformex import geomtools as gt
        if normals is None:
            pass
        elif utils.isString(normals):
            if normals == 'auto':
                normals = gt.polygonNormals(self.coords[self.elems])
            elif normals == 'avg':
                normals = gt.polygonAvgNormals(self.coords, self.elems,
                                               atnodes=False)
        else:
            normals = at.checkArray(normals, (self.nelems(), self.nplex(), 3), 'f')
        self._normals = normals


    def __getitem__(self, i):
        """Return element i of the Mesh.

        This allows addressing element i of Mesh M as M[i].

        Parameters
        ----------
        i: :term:`index`
            The index of the element(s) to return. This can be a single
            element number, a slice, or an array with a list of numbers.

        Returns
        -------
        Coords
            A Coords with a shape (nplex, 3), or if multiple elements are
            requested, a shape (nelements, nplex, 3), holding the
            coordinates of all points of the requested elements.

        Notes
        -----
        This is normally used in an expression as ``M[i]``, which will
        return the element i. Then ``M[i][j]`` will return the coordinates
        of node j of element i.
        """
        return self.coords[self.elems[i]]


    def __setstate__(self, state):
        """Set the object from serialized state.

        This allows to read back old pyFormex Project files where the Mesh
        class did not set element type yet.
        """
        elems = state['elems']
        if 'eltype' in state:
            if state['eltype'] is not None:
                # We acknowledge this eltype, even if it is also stored
                # in elems. This makes the restore also work for older projects
                # where eltype was not in elems.
                elems.eltype = ElementType.get(state['eltype'])
            # Do not store the eltype in the Mesh anymore
            del state['eltype']
        else:
            # No eltype in Mesh
            if hasattr(elems, 'eltype'):
                # eltype in elems: leave as it is
                pass
            else:
                # Try to set elems eltype from plexitude
                try:
                    elems.eltype = ElementType.get(nplex=elems.nplex())
                except Exception:
                    raise ValueError("I can not restore a Mesh without eltype")
        self.__dict__.update(state)


    def level(self):
        """Return the level of the elements in the Mesh.

        Returns
        -------
        int
            The dimensionality of the elements: 0 (point), 1(line),
            2 (surface), 3 (volume).
        """
        return self.eltype.ndim


    def nelems(self):
        """Return the number of elements in the Mesh.

        Returns
        -------
        int
            The first dimension of the :attr:`elems` array.
        """
        return self.elems.shape[0]


    def nplex(self):
        """Return the plexitude of the elements in the Mesh.

        Returns
        -------
        int
            The second dimension of the :attr:`elems` array.
        """
        return self.elems.shape[1]


    def ncoords(self):
        """Return the number of nodes in the Mesh.

        Returns
        -------
        int
             The first dimension of the :attr:`~mesh.Mesh.coords` array.
        """
        return self.coords.shape[0]

    nnodes = ncoords
    npoints = ncoords


    def shape(self):
        """Returns the shape of the :attr:`elems` array."""
        return self.elems.shape


    def info(self):
        """
        Return short info about the Mesh.

        Returns
        -------
        str
            A string with info about the shape of the
            :attr:`~mesh.Mesh.coords` and :attr:`elems` attributes.
        """
        return "coords" + str(self.coords.shape) + "; elems" + str(self.elems.shape)


    def report(self, full=False, **kargs):
        """Create a report on the Mesh shape and size.

        Parameters
        ----------
        full: bool
            If False (default), the report only contains the number of points,
            the number of elements, the plexitude, the dimensionality, and the
            element type (None in most cases).
            If True, it also contains the coordinates array.
        **kargs:
            Numpy print options to be used in the formatting of the coords
            array.

        Returns
        -------
        str
        """
        prec = np.get_printoptions()['precision']
        bb = self.bbox()
        s = (f"{self.__class__.__name__}: "
             f"nnodes: {self.ncoords()}, nelems: {self.nelems()}, "
             f"nplex: {self.nplex()}, level: {self.level()}, "
             f"eltype: {self.elName()}"
             f"\n  BBox: {bb[0]}, {bb[1]}"
             f"\n  Size: {bb[1]-bb[0]}")
        metrics = ''
        if self.level() in (1, 2):
            metrics += f"  Length: {self.length():.{prec}}"
        if self.level() in (2, 3):
            metrics += f"  Area: {self.area():.{prec}}"
        if self.level() == 3 or (
                self.__class__.__name__ == 'TriSurface' and
                self.isClosedManifold()):
            metrics += f"  Volume: {self.volume():.{prec}}"
        if metrics:
            s += f"\n{metrics}"

        if full:
            s += '\n' + at.stringar("  Coords: ", self.coords) + \
                 '\n' + at.stringar("  Elems: ", self.elems)
        return s


    # default str formatting
    __str__ = report


    def shallowCopy(self, prop=None):
        """
        Return a shallow copy.

        Parameters
        ----------
        prop: int :term:`array_like`, optional
            1-dim int array with non-negative element property numbers.

        Returns
        -------

            A shallow copy of the Mesh, using the same data arrays
            for ``coords`` and ``elems``. If ``prop`` was provided,
            the new Mesh can have other property numbers.
            This is a convenient method to use the same Mesh
            with different property attributes.
        """
        if prop is None:
            prop = self.prop
        return self.__class__(self.coords, self.elems, prop=prop)


    def toFormex(self):
        """
        Convert a Mesh to a Formex.

        Returns
        -------
        Formex
            A Formex equivalent with the calling Mesh. The Formex inherits
            the element property numbers and eltype from the Mesh.
            Drawing attributes and Fields are not transfered though.

        Examples
        --------
        >>> M = Mesh([[0,0,0],[1,0,0]],[[0,1],[1,0]],eltype='line2')
        >>> M.toFormex()
        Formex([[[0.,  0.,  0.],
                 [1.,  0.,  0.]],
        <BLANKLINE>
                [[1.,  0.,  0.],
                 [0.,  0.,  0.]]])
        """
        return Formex(self.coords[self.elems], self.prop, self.elName())


    def toMesh(self):
        """
        Convert to a Mesh.

        Returns
        -------
        Mesh
            The Mesh itself. This is provided as a convenience for use
            in functions that need to work on different Geometry types.
        """
        return self


    def toSurface(self):
        """
        Convert a Mesh to a TriSurface.

        Only Meshes of level 2 (surface) and 3 (volume) can be converted to a
        TriSurface. For a level 3 Mesh, the border Mesh is taken first.
        A level 2 Mesh is converted to element type 'tri3' and then to a
        TriSurface.

        Returns
        -------
        :class:`TriSurface`
            A TriSurface corresponding with the input Mesh. If that has
            eltype 'tri3', the resulting TriSurface is fully equivalent.
            Otherwise, a triangular approximation is returned.

        Raises
        ------
        ValueError
            If the Mesh can not be converted to a TriSurface.

        """
        from pyformex.trisurface import TriSurface
        if self.level() == 3:
            obj = self.getBorderMesh()
        elif self.level() == 2:
            obj = self
        else:
            raise ValueError(
                f"Can not convert a Mesh of level {self.level()} to a Surface")

        obj = obj.convert('tri3')
        return TriSurface(obj)


    def toLines(self):
        """
        Convert a Mesh to a line2 mesh.

        All Meshes of level 1 or higher can be converted to a line2 Mesh.
        For level 2 and 3 Meshes, first the :meth:`edgeMesh` is taken.
        The level 1 Mesh is then converted to 'line2' elements.

        Returns
        -------
        :class:`Mesh`
            A Mesh of eltype 'line2' containing all the linearized edges of
            the input Mesh.

        Raises
        ------
        ValueError
            If the input Mesh has level < 1..

        """
        if self.level() >= 2:
            obj = self.edgeMesh()
        elif self.level() == 2:
            obj = self
        else:
            raise ValueError(
                f"Can not convert a Mesh of level {self.level()} to Lines")
        return obj.convert('line2')


    def toCurve(self, connect=False):
        """
        Convert a Mesh to a Curve.

        If the element type is one of 'line*' types, the Mesh is converted
        to a Curve. The type of the returned Curve is dependent on the
        element type of the Mesh:

        - 'line2': :class:`PolyLine`,
        - 'line3': :class:`BezierSpline` (degree 2),
        - 'line4': :class:`BezierSpline` (degree 3)

        If connect is False, this is equivalent to ::

          self.toFormex().toCurve()

        Any other type will raise an exception.
        """
        if self.elName() in ['line2', 'line3', 'line4']:
            if connect:
                elems = self.elems.chained()
                if len(elems)!=1:
                    # BV: We should return all connected parts
                    raise ValueError("Can not convert a Mesh to a single continuos curve")
                else:
                    elems=elems[0]
                    closed = elems[-1, -1] == elems[0, 0]
                    # BV: This should be done without conversion to Formex
                    M = Mesh(self.coords, elems, eltype=self.eltype)
                    return M.toFormex().toCurve(closed=closed)

            else:
                closed = self.elems[-1, -1] == self.elems[0, 0]
                return self.toFormex().toCurve(closed=closed)

        else:
            raise ValueError(
                f"Can not convert a Mesh of type '{self.elName()}' to a curve")


    def centroids(self):
        """
        Return the centroids of all elements of the Mesh.

        The centroid of an element is the point with coordinates
        equal to the average of those of all nodes of the element.

        Returns
        -------
        Coords
            A Coords object with shape (:meth:`nelems`, 3), holding the
            centroids of all the elements in the Mesh.

        Examples
        --------
        >>> rectangle(L=3,W=2,nl=3,nw=2).centroids()
        Coords([[0.5,  0.5,  0. ],
                [1.5,  0.5,  0. ],
                [2.5,  0.5,  0. ],
                [0.5,  1.5,  0. ],
                [1.5,  1.5,  0. ],
                [2.5,  1.5,  0. ]])

        """
        return self.coords[self.elems].mean(axis=1)


    def bboxes(self):
        """
        Returns the bboxes of all elements in the Mesh.

        Returns
        -------
        float array (nelems,2,3).
            An array with the minimal and maximal values of the
            coordinates of the nodes of each element, stored along
            the 1-axis.
        """
        return self.coords[self.elems].bboxes()


#######################################################################
    ## Entity selection and mesh traversal ##


    def getLowerEntities(self, level=-1):
        """
        Get the entities of a lower dimensionality.

        Parameters
        ----------
        level: int
            The :term:`level` of the entities to return. If negative,
            it is a value relative to the level of the caller. If non-negative,
            it specifies the absolute level. Thus, for a Mesh with a 3D
            element type, getLowerEntities(-1) returns the faces, while for a
            2D element type, it returns the edges.
            For both meshes however, getLowerEntities(+1) returns the edges.

        Returns
        -------
        :class:`~connectivity.Connectivity`
            A Connectivity defining the lower entities of the specified
            level in terms of the nodes of the Mesh.

            The return value may be an empty table, if the element type does
            not have the requested entities (e.g. 'quad4' Mesh does not
            have entities of level 3).

            If the targeted entity level is outside the range 0..3, the return
            value is None.

        Notes
        -----
        This returns all entities for all elements and entities shared
        by multiple elements will appear multiple times. If you only want
        the unique lower entities, apply :meth:`~Connectivity.removeDuplicate`
        on the result, or use::

          sel = self.eltype.getEntities(level)
          lower = self.elems.insertLevel(sel)[1]

        See Also
        --------
        level: return the dimensionality of the Mesh
        :meth:`connectivity.Connectivity.insertLevel`: returns two tables:
            elems vs. lower entities, lower enitites vs. nodes.

        Examples
        --------
        Mesh with one 'quad4' element and 4 nodes.

        >>> M = Mesh(eltype='quad4')

        The element defined in function of the nodes.

        >>> print(M.elems)
        [[0 1 2 3]]

        The edges of the element defined in function of the nodes.

        >>> print(M.getLowerEntities(-1))
        [[0 1]
         [1 2]
         [2 3]
         [3 0]]

        And finally, the nodes themselves: not very useful, but works.

        >>> print(M.getLowerEntities(-2))
        [[0]
         [1]
         [2]
         [3]]
        """
        sel = self.eltype.getEntities(level)
        ent = self.elems.selectNodes(sel)
        ent.eltype = sel.eltype
        return ent


    def getNodes(self):
        """Return the set of unique node numbers in the Mesh.

        Returns
        -------
        int array
            The sorted node numbers that are actually used in the connectivity
            table.
            For a compacted Mesh, it is equal to ``np.arange(self.nelems)``.
        """
        return np.unique(self.elems)


    def getPoints(self):
        """Return the nodal coordinates of the Mesh.

        Returns
        -------
        :class:`~coords.Coords`
            The coordinates of the nodes that are actually used in
            the connectivity table. For a compacted Mesh, it is equal to
            the coords attribute.
        """
        return self.coords[self.getNodes()]

    # Only for use in self.edges and self.elem_edges
    def _get_elem_edges(self):
        """Compute edges and elem_edges and memoize them"""
        res = self.elems.insertLevel(1)
        self._memory['elem_edges'], self._memory['edges'] = res
        return res


    # Only for use in self.faces and self.elem_faces
    def _get_elem_faces(self):
        """Compute faces and elem_faces and memoize them"""
        res = self.elems.insertLevel(2)
        self._memory['elem_faces'], self._memory['faces'] = res
        return res


    @property
    @utils.memoize
    def edges(self):
        """Return the unique edges of all the elements in the Mesh.

        Returns
        ------
        :class:`~elements.Elems`
            A connectivity table defining the unique element edges in function
            of the nodes.

        Notes
        -----
        This is like ``self.elems.insertLevel(1)[1]`` but the result is
        memoized in the Mesh object to avoid recomputation on a next call.

        Examples
        --------
        >>> Mesh(eltype='quad4').subdivide(2,1).edges
        Elems([[0, 1],
               [3, 0],
               [1, 2],
               [1, 4],
               [2, 5],
               [4, 3],
               [5, 4]], eltype=Line2)
        """
        return self._get_elem_edges()[1]


    @property
    @utils.memoize
    def elem_edges(self):
        """Defines the elements in function of its edges.

        Returns
        -------
        :class:`~connectivity.Connectivity`
            A connectivity table with the elements defined in
            function of the edges.

        Notes
        -----
        As a side effect, this also stores the definition of the edges
        and the returned element to edge connectivity in the attributes
        `edges`, resp. `elem_edges`.

        See Also
        --------
        edges: Return the definition of the edges

        Examples
        --------
        >>> Mesh(eltype='quad4').subdivide(2,1).elem_edges
        Connectivity([[0, 3, 5, 1],
                      [2, 4, 6, 3]])
        """
        return self._get_elem_edges()[0]


    @property
    @utils.memoize
    def faces(self):
        """Return the unique faces of all the elements in the Mesh.

        Returns
        -------
        :class:`~elements.Elems`
            A connectivity table defining all the element faces in function
            of the nodes.

        Notes
        -----
        This is like ``self.elems.insertLevel(2)[1]`` but the result is
        memoized in the Mesh object to avoid recomputation on a next call.

        Examples
        --------
        >>> Mesh(eltype='hex8').subdivide(2,1,1).faces
        Elems([[ 0,  3,  4,  1],
               [ 0,  1,  7,  6],
               [ 0,  6,  9,  3],
               [ 1,  4,  5,  2],
               [ 1,  2,  8,  7],
               [ 1,  4, 10,  7],
               [ 2,  5, 11,  8],
               [ 3,  9, 10,  4],
               [ 4, 10, 11,  5],
               [ 6,  7, 10,  9],
               [ 7,  8, 11, 10]], eltype=Quad4)
        """
        return self._get_elem_faces()[1]


    @property
    @utils.memoize
    def elem_faces(self):
        """Defines the elements in function of its faces.

        Returns
        -------
        :class:`~elements.Elems`
            A connectivity table with the elements defined in
            function of the faces.

        Notes
        -----
        As a side effect, this also stores the definition of the faces
        and the returned element to face connectivity in the attributes
        `faces`, resp. `elem_faces`.

        See Also
        --------
        faces: Return the definition of the faces

        Examples
        --------
        >>> Mesh(eltype='hex8').subdivide(2,1,1).elem_faces
        Connectivity([[ 2,  5,  1,  7,  0,  9],
                      [ 5,  6,  4,  8,  3, 10]])
        """
        return self._get_elem_faces()[0]


    @property
    def cells(self):
        """Return the 3D cells in the Mesh.

        For a level 3 Mesh, this is equivalent to self.elems.
        For other Meshes, an empty connectivity is returned.
        """
        return self.elems.insertLevel(3)[1]


    @utils.deprecated('depr_mesh_getedges')
    def getElemEdges(self):
        return self.elem_edges

    @utils.deprecated('depr_mesh_getedges')
    def getEdges(self):
        return self.edges

    @utils.deprecated('depr_mesh_getedges')
    def getFaces(self):
        return self.faces

    @utils.deprecated('depr_mesh_getedges')
    def getCells(self):
        return self.cells


    def edgeMesh(self):
        """Return a Mesh with the unique edges of the elements.

        This can only be used with a Mesh of level >= 1.
        """
        return Mesh(self.coords, self.edges)


    def faceMesh(self):
        """Return a Mesh with the unique faces of the elements.

        This can only be used with a Mesh of level >= 2.
        """
        return Mesh(self.coords, self.faces)


    def getFreeEntities(self, level=-1, return_indices=False):
        """Return the free entities of the specified level.

        Parameters
        ----------
        level: int
            The :term:`level` of the entities to return. If negative,
            it is a value relative to the level of the caller. If non-negative,
            it specifies the absolute level.
        return_indices: bool
            If True, also returns an index array (nentities,2) for inverse
            lookup of the higher entity (column 0) and its local
            lower entity number (column 1).

        Returns
        -------
        :class:`~elements.Elems`
            A connectivity table with the free entities of the
            specified level of the Mesh. Free entities are entities
            that are only connected to a single element.

        See Also
        --------
        getFreeEntitiesMesh: return the free entities as a Mesh
        getBorder: return the free entities of the first lower level

        Examples
        --------
        >>> M = Formex('3:.12.34').toMesh()
        >>> print(M.report(full=True))
        Mesh: nnodes: 4, nelems: 2, nplex: 3, level: 2, eltype: tri3
          BBox: [0.  0.  0.], [1.  1.  0.]
          Size: [1.  1.  0.]
          Length: 4.0  Area: 1.0
          Coords: [[0.  0.  0.]
                   [1.  0.  0.]
                   [0.  1.  0.]
                   [1.  1.  0.]]
          Elems: [[0 1 3]
                  [3 2 0]]
        >>> M.getFreeEntities(1)
        Elems([[0, 1],
               [2, 0],
               [1, 3],
               [3, 2]], eltype=Line2)
        >>> M.getFreeEntities(1,True)[1]
        array([[0, 0],
               [1, 1],
               [0, 1],
               [1, 0]])

        """
        return self.elems.getFreeEntities(level, return_indices)


    def getFreeEntitiesMesh(self, level=-1, compact=True):
        """Return a Mesh with lower entities.

        Parameters
        ----------
        level: int
            The :term:`level` of the entities to return. If negative,
            it is a value relative to the level of the caller. If non-negative,
            it specifies the absolute level.
        compact: bool
            If True (default), the returned Mesh will be compacted. If False,
            the returned Mesh will contain all the nodes present in the
            input Mesh.

        Returns
        -------
        :class:`Mesh`
            A Mesh containing the lower entities of the specified
            level. If the Mesh has property numbers, the lower entities inherit
            the property of the element to which they belong.

        See Also
        --------
        getFreeEdgesMesh: return a Mesh with the free entities of the level 1
        getBorderMesh: return the free entities Mesh of the first lower level

        """
        if self.prop is None:
            M = Mesh(self.coords, self.getFreeEntities(level=level))

        else:
            brd, indices = self.getFreeEntities(return_indices=True, level=level)
            enr = indices[:, 0]  # pylint: disable=E1126
            M = Mesh(self.coords, brd, prop=self.prop[enr])

        if compact:
            M = M.compact()
        return M


    def getFreeEdgesMesh(self, compact=True):
        """Return a Mesh with the free edges.

        Parameters
        ----------
        compact: bool
            If True (default), the returned Mesh will be compacted. If False,
            the returned Mesh will contain all the nodes present in the
            input Mesh.

        Returns
        -------
        :class:`Mesh`
            A Mesh containing the free edges of the input Mesh.
            If the input Mesh has property numbers, the edge elements inherit
            the property of the element to which they belong.

        See Also
        --------
        getFreeEntitiesMesh: return the free entities  Mesh of any lower level
        getBorderMesh: return the free entities Mesh of level -1
        """
        return self.getFreeEntitiesMesh(level=1, compact=compact)


    def border(self, return_indices=False):
        """Return the border of the Mesh.

        Border entities are the free entities of the first lower level.

        Parameters
        ----------
        return_indices: bool
            If True, also returns an index array (nentities,2) for inverse
            lookup of the higher entity (column 0) and its local
            lower entity number (column 1).

        Returns
        -------
        :class:`~elements.Elems`
            A connectivity table with the border entities of the
            specified level of the Mesh. Free entities are entities
            that are only connected to a single element.

        See Also
        --------
        getFreeEntities: return the free entities of any lower level
        getBorderMesh: return the border as a Mesh

        Notes
        -----
        This is a convenient shorthand for ::

          self.getFreeEntities(level=-1,return_indices=return_indices)
        """
        return self.getFreeEntities(level=-1, return_indices=return_indices)


    def borderMesh(self, compact=True):
        """Return a Mesh representing the border.

        Parameters
        ----------
        compact: bool
            If True (default), the returned Mesh will be compacted. If False,
            the returned Mesh will contain all the nodes present in the
            input Mesh.

        Returns
        -------
        :class:`Mesh`
            A Mesh containing the border of the input Mesh. The level of the
            Mesh is one less than that of the input Mesh.
            If the input Mesh has property numbers, the border elements inherit
            the property of the element to which they belong.

        Notes
        -----
        This is a convenient shorthand for ::

          self.getFreeEntitiesMesh(level=-1,compact=compact)
        """
        return self.getFreeEntitiesMesh(level=-1, compact=compact)


    def borderElems(self):
        """Find the elements that are touching the border of the Mesh.

        Returns
        -------
        int array
            A list of the numbers of the elements that fully contain at
            least one of the elements of the border Mesh.
            Thus, in a volume Mesh, elements only touching the border
            by a vertex or an edge are not considered border elements.
        """
        brd, ind = self.getBorder(True)
        return np.unique(ind[:, 0])  # pylint: disable=E1126


    def borderNodes(self):
        """Find the nodes that are on the border of the Mesh.

        Returns
        -------
        int array
            A list of the numbers of the nodes that are on the
            border of the Mesh.
        """
        brd = self.getBorder()
        return np.unique(brd)


    def innerNodes(self):
        """Find the nodes that are not on the border of the Mesh.

        Returns
        -------
        int array
            A list of the numbers of the nodes that are not on the
            border of the Mesh.
        """
        return at.complement(self.getBorderNodes(), self.ncoords())


    # retained for compatibility, may be deprecated later
    getBorder = border
    getBorderMesh = borderMesh
    getBorderElems = borderElems
    getBorderNodes = borderNodes
    getInnerNodes = innerNodes


    def peel(self, nodal=False):
        """Remove the border elements from a Mesh.

        Parameters
        ----------
        nodal: bool
            If True, all elements connected to a border node are removed.
            The default will only remove the elements returned by
            :meth:`getBorderElems`.

        Returns
        -------
        Mesh
            A Mesh with the border elements removed.

        """
        if nodal:
            brd = self.connectedTo(self.getBorderNodes())
        else:
            brd = self.getBorderElems()
        return self.cselect(brd)


    @utils.warning("mesh_connectedTo")
    def connectedTo(self, entities, level=0):
        # TODO: the level parameter here seems useless: how does one know
        # the indices of the lower level entities??
        """Find the elements connected to specific lower entities.

        Parameters
        ----------
        entities: int or int :term:`array_like`
            The indices of the lower entities to which connection should
            exist.
        level: int
            The :term:`level` of the entities to which connection should
            exist. If negative, it is a value relative to the level of the
            caller. If non-negative, it specifies the absolute level.
            Default is 0 (nodes).

        Returns
        -------
        int array
            A list of the numbers of the elements that contain at
            least one of the specified lower entities.
        """
        if level == 0:
            elems = self.elems
        else:
            elems, lo = self.elems.insertLevel(level)
        return elems.connectedTo(entities)


    def adjacentTo(self, elements, level=0):
        """Find the elements adjacent to the specified elements.

        Adjacent elements are elements that share some lower entity.

        Parameters
        ----------
        elements: int or int :term:`array_like`
            Element numbers to find the adjacent elements for.
        level: int
            The :term:`level` of the entities used to define adjacency.
            If negative, it is a value relative to the level of the
            caller. If non-negative, it specifies the absolute level.
            Default is 0 (nodes).

        Returns
        -------
        int array
            A list of the numbers of all the elements in the Mesh that are
            adjacent to any of the specified elements.

        """
        if level == 0:
            elems = self.elems
        else:
            elems = self.elems.insertLevel(level)[0]
        return np.unique(elems.adjacentElements(elements))


    def reachableFrom(self, elements, level=0):
        """Select the elements reachable from the specified elements.

        Elements are reachable if one can travel from one of the origin
        elements to the target, by only following the specified level
        of connections.

        Parameters
        ----------
        elements: int or int :term:`array_like`
            Element number(s) from where to start the walk.
        level: int
            The :term:`level` of the entities used to define connections.
            If negative, it is a value relative to the level of the
            caller. If non-negative, it specifies the absolute level.
            Default is 0 (nodes).

        Returns
        -------
        int array
            A list of the numbers of all the elements in the Mesh reachable
            from any of the specified elements by walking over entities of the
            specified level. The list will include the original set of elements.
        """
        return np.where(self.frontWalk(
            startat=elements, level=level,
            frontinc=0, partinc=1, maxval=1) == 0)[0]


    #########################################################################
    # Adjacency #


    def adjacency(self, level=0, diflevel=-1, kind='e'):
        """Create an element adjacency table.

        This creates an element adjacenty table (kind='e') or a node adjacency
        table (kind='n').
        Two elements are said to be adjacent if they share a lower
        entity of the specified level. Two nodes are said to be adjacent if
        they share a higher entity of the specified level.

        Parameters
        ----------
        level: int
            Hierarchic level of the geometric items connecting two elements:
            0 = node, 1 = edge, 2 = face. Only values of a lower hierarchy than
            the level of the Mesh itself make sense. Default is to consider
            nodes as the connection between elements.
        diflevel: int, optional
            Only used with kind='e'.
            If >= level, and smaller than the level of the Mesh itself,
            elements that have a connection of this level are removed.
            Thus, in a Mesh with volume elements, self.adjacency(0,1) gives the
            adjacency of elements by a node but not by an edge.
        kind: 'e' or 'n'
            Select element ('e') or node (n') adjacency table. Default is
            element adjacency.

        Returns
        -------
        adj: :class:`~adjacency.Adjacency`
            An Adjacency table specifying for each element or node its
            neighbours connected by the specified geometrical subitems.
        """
        if kind == 'e' and diflevel > level:
            return self.adjacency(level, kind=kind).symdiff(
                self.adjacency(diflevel, kind=kind))

        if level == 0:
            elems = self.elems
        else:
            elems = self.elems.insertLevel(level)[0 if kind=='e' else 1]
        return elems.adjacency(kind=kind)


    def frontWalk(self, level=0, startat=0, frontinc=1, partinc=1, maxval=-1):
        """Visit all elements using a frontal walk.

        In a frontal walk a forward step is executed simultanuously from all
        the elements in the current front. The elements thus reached become
        the new front. An element can be reached from the current element if
        both are connected by a lower entity of the specified level. Default
        level is 'point'.

        Parameters
        ----------
        level: int
            Hierarchy of the geometric items connecting two elements:
            0 = node, 1 = edge, 2 = face. Only values of a lower hierarchy than
            the elements of the Mesh itself make sense. There are no
            connections on the upper level.
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
            the element was reached by the walker. Unwalked elements have
            a value -1.

        See Also
        --------
        :meth:`adjacency.Adjacency.frontWalk`

        Examples
        --------
        >>> M = Mesh(eltype='quad4').subdivide(5,2)
        >>> print(M.frontWalk())
        [0 1 2 3 4 1 1 2 3 4]
        >>> print(M.frontWalk(maxval=2))
        [ 0  1  2 -1 -1  1  1  2 -1 -1]
        """
        return self.adjacency(level).frontWalk(
            startat=startat, frontinc=frontinc, partinc=partinc, maxval=maxval)


    def maskedEdgeFrontWalk(self, mask=None, startat=0, frontinc=1,
                            partinc=1, maxval=-1):
        """Perform a front walk over masked edge connections.

        This is like `frontWalk(level=1)`, but has an extra parameter `mask`
        to select the edges that are used as connectors between elements.
        The remainder of the parameters are like in :meth:`frontWalk`.

        Parameters
        ----------
        mask: :term:`array_like`, bool or int
            A boolean array or index flagging the nodes  which are to be
            considered as connectors between elements. If None, all nodes
            are connections.

        See Also
        --------
        :meth:`frontWalk`
        """
        if self.level() != 1:
            hi, lo = self.elems.insertLevel(1)
        else:
            hi = self.elems
        adj = hi.adjacency(mask=mask)
        return adj.frontWalk(startat=startat, frontinc=frontinc,
                             partinc=partinc, maxval=maxval)


    def partitionByConnection(self, level=0, startat=0, sort='number', nparts=-1):
        """Detect the connected parts of a Mesh.

        The Mesh is partitioned in parts in which all elements are
        connected. Two elements are connected if it is possible to draw a
        continuous line from a point in one element to a point in
        the other element without leaving the Mesh.

        Parameters
        ----------
        sort: str, optional
            One of 'number' (default), 'length', 'area', 'volume'. Defines
            the weights to be used in sorting the parts. Specifying another
            string will leave the parts unsorted.
        level: int, optional
            Hierarchy of the geometric items connecting two elements:
            0 = node, 1 = edge, 2 = face. Only values of a lower hierarchy than
            the elements of the Mesh itself make sense. There are no
            connections on the upper level.
        startat: int or list of ints, optional
            Initial element number(s) in the front. Beware: if you specify
            unconnected elements, their parts will be returned as a single
            part.
        nparts: int, optional
            Maximum number of parts to detect. If negative, the procedure
            continues until all elements have been attributed to some part.

        Returns
        -------
        int array
            An int array specifying for each element the part number to which
            it belongs. By default the parts are sorted in decreasing order
            of the number of elements.
        """
        p = self.frontWalk(level=level, startat=startat, frontinc=0, partinc=1,
                           maxval=nparts)
        if sort=='number':
            p = at.sortSubsets(p)
        if sort=='length':
            p = at.sortSubsets(p, self.lengths())
        if sort=='area':
            p = at.sortSubsets(p, self.areas())
        if sort=='volume':
            p = at.sortSubsets(p, self.volumes())
        return p


    def splitByConnection(self, level=0, startat=0, sort='number', nparts=-1):
        """Split a Mesh into connected parts.

        This is like :meth:`partitionByConnection` but returns a list
        of partial Meshes.
        The parameters are like in :meth:`partitionByConnection`

        See Also
        --------
        largestByConnection

        Returns
        -------
        list of Mesh
            A list of Meshes that each form a connected part.
            By default the parts are sorted in decreasing order of the number
            of elements.
        """
        p = self.partitionByConnection(level=level, startat=startat, sort=sort)
        return self.splitProp(p)


    def largestByConnection(self, level=0):
        """Return the largest connected part of the Mesh.

        See Also
        --------
        splitByConnection

        Notes
        -----
        This is equivalent with, but more efficient than ::

          self.splitByConnection(level)[0]
        """
        p = self.partitionByConnection(level=level)
        return self.clip(p==0)


    def growSelection(self, sel, mode='node', nsteps=1):
        """Grow a selection of a Mesh by frontal steps.

        Parameters
        ----------
        sel: int or list of ints
            Initial element number(s) in the selection.
        mode: str
            Specifies how a single frontal step is done:

            - 'node' : add all elements that have a node in common,
            - 'edge' : add all elements that have an edge in common.
        nsteps: int
            Number of frontal steps to undertake.

        Returns
        -------
        int array
            The list of element numbers obtained by growing the front
            `nsteps` times.
        """
        level = {'node': 0, 'edge': 1}[mode]
        p = self.frontWalk(level=level, startat=sel, maxval=nsteps)
        return np.where(p>=0)[0]


    def partitionByCurve(self, edges, sort='number'):
        """Partition a level-2 Mesh by closed curve(s) along the edges.

        Parameters
        ----------
        edges: bool or int :term:`array_like` | level-1 Mesh
            If a bool type array, it flags for every edge with a True value
            whether the edge is part of the partitioning curve(s).
            The ordering of the edges is that as obtained from :attr:`edges`.

            If an int type array, it is a list of edge nummers that constitute
            the curve(s). Numbers refer to the :attr:`edges` order of edges.
            The order in which the edge numbers are given is irrelevant though.

            If a level-1 Mesh, it is a Mesh containing the edges that constitute
            the partitioning curve(s). In this case the edge numbers will be
            determined by matching the edges centroids on the level-2 Mesh.
        sort: str
            Defines how the resulting parts are sorted (by assigning them
            increasing part numbers). The following sort criteria are currently
            defined (any other value will return the parts unsorted):

            - 'number': sort in decreasing order of the number of triangles
              in the part. This is the default.
            - 'area': sort according to decreasing surface area of the part.

        Returns
        -------
        int array
            An int array specifying for each triangle to which part it belongs.
            Values are in the range 0..nparts.

        Notes
        -----
        In order for the operation to be non-trivial, the specified edges,
        possibly together with (parts of) the border, should form one or
        more closed loops.
        """
        if not self.level() == 2:
            raise ValueError(
                "partitionByCurve can only be applied to level-2 Meshes")
        if isinstance(edges, Mesh):
            print(edges)
            if not edges.level() == 1:
                raise ValueError(
                    "edges should be a level-1 Mesh")
            edges = self.edgeMesh().matchCentroids(edges)

        nedges = self.edges.shape[0]
        mask = at.complement(edges, nedges)
        p = self.maskedEdgeFrontWalk(mask=mask, frontinc=0)

        if sort == 'number':
            p = at.sortSubsets(p)
        elif sort == 'area':
            p = at.sortSubsets(p, self.areas())

        return p


    def partitionByAngle(self, **kargs):
        """Partition a level-2 Mesh by the angle between adjacent elements.

        The Mesh is partitioned in parts bounded by the sharp edges in the
        surface. The arguments and return value are the same as in
        :meth:`trisurface.TriSurface.partitionByAngle`.

        For eltypes other than 'tri3',
        a conversion to 'tri3' is done before computing the partitions.
        """
        if self.elName() == 'tri3':
            p = self.toSurface().partitionByAngle(**kargs)
        else:
            S = self.copy().setProp(np.arange(self.nelems())).toSurface()
            p = S.partitionByAngle(**kargs)
            j = np.unique(S.prop, return_index=True)[1]
            p = p[j]
        return p


    #######################################################################
    #
    # TODO: Should we move these up to Connectivity ?
    #       That would also avoid some possible problems
    #       with storing conn and econn
    #


    # @utils.warn("Mesh.nodeConnections now returns a Varray")
    def nodeConnections(self):
        """Find and store the elems connected to nodes.

        Examples
        --------
        >>> M = Mesh(eltype='quad4').subdivide(2,2)
        >>> M.nodeConnections()
        Varray([[0], [0, 1], [1], [0, 2], [0, 1, 2, 3], [1, 3], [2], [2, 3], [3]])
        """
        if self.conn is None:
            self.conn = self.elems.inverse()
        return self.conn


    def nNodeConnected(self):
        """Find the number of elems connected to nodes.

        Examples
        --------
        >>> M = Mesh(eltype='quad4').subdivide(2,2)
        >>> M.nNodeConnected()
        array([1, 2, 1, 2, 4, 2, 1, 2, 1])
        """
        return self.nodeConnections().lengths


    def edgeConnections(self):
        """Find and store the elems connected to edges.

        Examples
        --------
        >>> Mesh(eltype='quad4').subdivide(2,1).edgeConnections()
        array([[-1,  0],
               [-1,  0],
               [-1,  1],
               [ 0,  1],
               [-1,  1],
               [-1,  0],
               [-1,  1]])
        """
        if self.econn is None:
            self.econn = self.elem_edges.inverse(expand=True)
        return self.econn


    def nEdgeConnected(self):
        """Find the number of elems connected to edges.

        Examples
        --------
        >>> Mesh(eltype='quad4').subdivide(2,1).nEdgeConnected()
        array([1, 1, 1, 2, 1, 1, 1])
        """
        return (self.edgeConnections() >=0).sum(axis=-1)


    # TODO:
    # Are these really needed? better use adjacency(level)


    def nodeAdjacency(self):
        """Find the elems adjacent to each elem via one or more nodes."""
        return self.elems.adjacency()


    def nNodeAdjacent(self):
        """Find the number of elems which are adjacent by node to each elem."""
        return (self.nodeAdjacency() >=0).sum(axis=-1)


    def edgeAdjacency(self):
        """Find the elems adjacent to elems via an edge.

        Examples
        --------
        >>> Mesh(eltype='quad4').subdivide(2,1).edgeAdjacency()
        Adjacency([[1],
                   [0]])
        """
        return self.elem_edges.adjacency()


    def nEdgeAdjacent(self):
        """Find the number of adjacent elems."""
        return (self.edgeAdjacency() >=0).sum(axis=-1)


    def nonManifoldNodes(self):
        """Return the non-manifold nodes of a Mesh.

        Non-manifold nodes are nodes where subparts of a mesh of level >= 2
        are connected by a node but not by an edge.

        Returns an integer array with a sorted list of non-manifold node
        numbers. Possibly empty (always if the dimensionality of the Mesh
        is lower than 2).
        """
        if self.level() < 2:
            return []

        ML = self.splitByConnection(1, sort='')
        nm = [np.intersect1d(Mi.elems, Mj.elems)
              for Mi, Mj in itertools.combinations(ML, 2)]
        return np.unique(at.concat(nm))


    def nonManifoldEdges(self):
        # TODO: Explain how this is sorted
        """Return the non-manifold edges of a Mesh.

        Non-manifold edges are edges where subparts of a mesh of level 3
        are connected by an edge but not by a face.

        Returns an integer array with a sorted list of non-manifold edge
        numbers. Possibly empty (always if the dimensionality of the Mesh
        is lower than 3).

        As a side effect, this constructs the list of edges in the object.
        The definition of the nonManifold edges in terms of the nodes can
        thus be got from ::

          self.edges[self.nonManifoldEdges()]
        """
        if self.level() < 3:
            return []

        elems = self.elem_edges
        p = self.partitionByConnection(2, sort='')
        eL = [elems[p==i] for i in np.unique(p)]
        nm = [np.intersect1d(ei, ej) for ei, ej in itertools.combinations(eL, 2)]
        return np.unique(at.concat(nm))


    def nonManifoldEdgeNodes(self):
        """Return the non-manifold edge nodes of a Mesh.

        Non-manifold edges are edges where subparts of a mesh of level 3
        are connected by an edge but not by an face.

        Returns an integer array with a sorted list of numbers of nodes
        on the non-manifold edges.
        Possibly empty (always if the dimensionality of the Mesh
        is lower than 3).
        """
        if self.level() < 3:
            return []

        ML = self.splitByConnection(2, sort='')
        nm = [np.intersect1d(Mi.elems, Mj.elems)
              for Mi, Mj in itertools.combinations(ML, 2)]
        return np.unique(at.concat(nm))


    def fuse(self, parts=None, nodes=None, **kargs):
        """Fuse the nodes of a Meshes.

        Nodes that are within the tolerance limits of each other
        are merged into a single node.

        Parameters
        ----------
        parts: int :term:`array_like`, optional
            If provided, it is an int array with length equal to the number
            of elements that will be used to split the Mesh into parts (see
            :func:`splitProp`) and the fuse operation will be executed per part.
            Elements for which the value of `nparts` is negative will not
            be involved in the fuse operations.
        nodes: int :term:`array_like`, optional
            A list of node numbers. If provided, only these nodes will be
            involved in the fuse operation. This option can not be used
            together with the `parts` option.
        **kargs:
            Extra arguments for tuning the fuse operation are passed to the
            :meth:`coords.Coords:fuse` method.

        """
        if parts is None:
            if nodes is None:
                coords, index = self.coords.fuse(**kargs)
            else:
                keep = at.complement(nodes, self.nnodes())
                coords, fusindex = self.coords[nodes].fuse(**kargs)
                coords = Coords.concatenate([self.coords[keep], coords])
                index = -np.ones(self.nnodes(), dtype=at.Int)
                index[keep] = np.arange(len(keep), dtype=at.Int)
                index[nodes] = len(keep) + fusindex
            return self.__class__(coords, index[self.elems], prop=self.prop,
                                  eltype=self.eltype)
        else:
            parts = at.checkArray(parts, (self.nelems(),), 'i')
            ML = self.splitProp(parts)
            if parts.min() >= 0:
                n = (np.unique(parts) < 0).sum()
            else:
                n = 0
            ML = ML[:n] + [M.fuse(**kargs) for M in ML[n:]]
            return Mesh.concatenate(ML, fuse=False)


    def matchCoords(self, coords, **kargs):
        """Match nodes of coords with nodes of self.

        coords can be a Coords or a Mesh object
        This is a convenience function equivalent to ::

           self.coords.match(mesh.coords,**kargs)

        or ::

           self.coords.match(coords,**kargs)

        See also :meth:`coords.Coords.match`
        """
        if not(isinstance(coords, Coords)):
            coords=coords.coords
        return self.coords.match(coords, **kargs)


    def matchCentroids(self, mesh, **kargs):
        """Match elems of Mesh with elems of self.

        self and Mesh are same eltype meshes
        and are both without duplicates.

        Elems are matched by their centroids.
        """
        c = Mesh(self.centroids(), np.arange(self.nelems()))
        mc = Mesh(mesh.centroids(), np.arange(mesh.nelems()))
        return c.matchCoords(mc, **kargs)


    def matchLowerEntitiesMesh(self, mesh, level=-1):
        # BV: I'm not sure that we need this. Looks like it can or should
        # be replaced with a method applied on the BorderMesh
        # FI It has been tested on quad4-quad4, hex8-quad4, tet4-tri3
        """_Match lower entity of mesh with the lower entity of self.

        self and Mesh can be same eltype meshes or different eltype but of the
        same hierarchical type (i.e. hex8-quad4 or tet4 - tri3)
        and are both without duplicates.

        Returns the indices array of the elems of self that matches
        the lower entity of mesh, and the matched lower entity number
        """
        if level < 0:
            raise NotImplementedError
            # m1 is undefined!
            # level = m1.eltype.ndim + level

        sel = self.eltype.getEntities(level)
        hi, lo = self.elems.insertLevel(sel)
        hiinv = hi.inverse(expand=True)
        fm = Mesh(self.coords, lo)
        sel1 = mesh.eltype.getEntities(level)
        mesh = Mesh(mesh.coords, mesh.elems.insertLevel(sel1)[1])
        c = fm.matchCentroids(mesh)
        hiinv = hiinv[c]
        hpos = at.findFirst(c, hi).reshape(hi.shape)
        enr = np.unique(hiinv[hiinv >= 0])  # element number
        fnr=np.column_stack(np.where(hpos!=-1))  # face number
        return enr, fnr


    def matchFaces(self, mesh):
        """_Match faces of mesh with faces of self.

        self and Mesh can be same eltype meshes or different eltype but of the
        same hierarchical type (i.e. hex8-quad4 or tet4 - tri3)
        and are both without duplicates.

        eturns the indices array of the elems of self that matches
        the faces of mesh, and the matched face number
        """
        enr, fnr = self.matchLowerEntitiesMesh(mesh, level=2)
        return enr, fnr


    def compact(self, return_index=False):
        """Remove unconnected nodes and renumber the mesh.

        Returns a mesh where all nodes that are not used in any
        element have been removed, and the nodes are renumbered to
        a compacter scheme.

        If return_index is True, also returns an index specifying the
        index of the new nodes in the old node scheme.

        Examples
        --------
        >>> x = Coords([[i] for i in np.arange(5)])
        >>> M = Mesh(x,[[0,2],[1,4],[4,2]])
        >>> M,ind = M.compact(True)
        >>> print(M.coords)
        [[0. 0. 0.]
         [1. 0. 0.]
         [2. 0. 0.]
         [4. 0. 0.]]
        >>> print(M.elems)
        [[0 2]
         [1 3]
         [3 2]]
        >>> M = Mesh(x,[[0,2],[1,3],[3,2]])
        >>> M = M.compact()
        >>> print(M.coords)
        [[0. 0. 0.]
         [1. 0. 0.]
         [2. 0. 0.]
         [3. 0. 0.]]
        >>> print(M.elems)
        [[0 2]
         [1 3]
         [3 2]]
        >>> print(ind)
        [0 1 2 4]
        >>> M = M.cselect([0,1,2])
        >>> M.coords.shape, M.elems.shape
        ((4, 3), (0, 2))
        >>> M = M.compact()
        >>> M.coords.shape, M.elems.shape
        ((0, 3), (0, 2))

        """
        if self.nelems() == 0:
            ret = self.__class__(Coords(), self.elems)
            nodes = np.array([], dtype=at.Int)
        else:
            elems, nodes = self.elems.renumber()
            if elems is self.elems:
                # node numbering is compact
                if self.coords.shape[0] > len(nodes):
                    # remove extraneous nodes
                    self.coords = self.coords[:len(nodes)]
                # numbering has not been changed, safe to use same object
                ret = self
            else:
                # numbering has been changed, return new object
                coords = self.coords[nodes]
                ret = self.__class__(coords, elems, prop=self.prop,
                                     eltype=self.eltype)

        if return_index:
            return ret, nodes
        else:
            return ret

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
        if compact:
            M = M.compact()
        return M


    def selectNodes(self, nodsel, eltype=None):
        """Return a Mesh with subsets of the original nodes.

        Parameters
        ----------
        nodsel: 1-dim or 2-dim int :term:`array_like`
            An object that can be converted to a 1-dim or 2-dim array.
            Each row of `nodsel` holds a list of local node numbers that
            should be retained in the new connectivity table. See also
            :meth:`connectivity.Connectivity.selectNodes`.
        eltype: :class:`ElementType` or str, optional
            The element type or name for the new Mesh. It should be specified
            if the default for the plexitude would not be correct.

        Returns
        -------
        Mesh
            A Mesh with the same node set as the input but other element
            connectivity and eltype

        Examples
        --------
        From a Mesh of triangles, create a Mesh with the edges.

        >>> M = Formex('3:.12.34').toMesh()
        >>> M.elems
        Elems([[0, 1, 3],
               [3, 2, 0]], eltype=Tri3)
        >>> M1 = M.selectNodes([(0,1), (1,2), (2,0)])
        >>> M1.elems
        Elems([[0, 1],
               [1, 3],
               [3, 0],
               [3, 2],
               [2, 0],
               [0, 3]], eltype=Line2)
        """
        elems = self.elems.selectNodes(nodsel)
        prop = self.prop
        if prop is not None:
            prop = np.column_stack([prop]*len(nodsel)).reshape(-1)
        return Mesh(self.coords, elems, prop=prop, eltype=eltype)


    @utils.deprecated_by('Mesh.withProp', 'Mesh.selectProp')
    def withProp(self, val):
        return self.selectProp(val, compact=False)

    @utils.deprecated_by('Mesh.withoutProp', 'Mesh.cselectProp')
    def withoutProp(self, val):
        return self.cselectProp(val, compact=False)

    @utils.deprecated_by('Mesh.hits', 'Mesh.elems.hits')
    def hits(self, entities, level=0):
        """Count the lower entities from a list connected to the elements.

        `entities`: a single number or a list/array of entities
        """
        if level == 0:
            return self.elems.hits(nodes=entities)
        else:
            raise ValueError(
                "The use of level != 0 in Mesh.hits has been removed. "
                "Use hi,lo = M.elems.insertLevel(level) and hi.hits() instead.")


    def splitRandom(self, n, compact=True):
        """Split a Mesh in n parts, distributing the elements randomly.

        Returns a list of n Mesh objects, constituting together the same
        Mesh as the original. The elements are randomly distributed over
        the subMeshes.

        By default, the Meshes are compacted. Compaction may be switched
        off for efficiency reasons.
        """
        sel = np.random.randint(0, n, (self.nelems()))
        return [self.select(sel==i, compact=compact) for i in range(n) if i in sel]


    #######################################################################
    ## simple mesh transformations ##


    def reverse(self, sel=None, inplace=False):
        """Reverse some or all elements of a Mesh.

        Reversing an element has the following meaning:

        - for 1D elements: reverse the traversal direction,
        - for 2D elements: reverse the direction of the positive normal,
        - for 3D elements: reverse inside and outside directions of the
          element's border surface. This also changes the sign of the
          element's volume.

        Parameters
        ----------
        sel: int or boolean :term:`array_like`, optional
            The selected elements to be reversed. Default is to reverse all
            elements.

        Returns
        -------
        Mesh
            A Mesh like the input but with the specified elements reversed.

        Notes
        -----
        The :meth:`reflect` method by default calls this method to undo
        the element reversal caused by the reflection operation.
        """
        rev = self.eltype.reverse
        if sel is None:
            sel = np.s_[:]
        if inplace:
            self.elems[sel] = self.elems[sel, rev]
            return self
        else:
            elems = self.elems.copy()
            elems[sel] = elems[sel, rev]
            return self.__class__(self.coords, elems, prop=self.prop,
                                  eltype=self.eltype)


    def reflect(self, dir=0, pos=0.0, reverse=True, **kargs):
        """Reflect the coordinates in one of the coordinate directions.

        This applies the :meth:`~coords.Coords.reflect` transformation
        on the coords of the Mesh, and then by default does a reversal
        of the elements.

        Parameters
        ----------
        dir: int (0,1,2)
            Global axis direction of the reflection (default 0 or x-axis).
        pos: float
            Offset of the mirror plane from origin (default 0.0)
        reverse: bool,optional
            If True (default), the :meth:`reverse` method is called after
            the reflection to undo the element reversal caused by the
            reflection of its coordinates. This has in most cases
            the desired effect. If not, the user can set this to False
            to skip the element reversal.
        """
        if reverse is None:
            reverse = True
            utils.warn("warn_mesh_reflect")

        M = Geometry.reflect(self, dir=dir, pos=pos)
        if reverse:
            # do not reverse inplace, or you'll reverse the input as well!
            M = M.reverse(inplace=False)
        return M


    def pointsAt(self, rst):
        """Compute points at parametric values.

        Parameters
        ----------
        rst: :term:`array_like`
            A float array with shape (ndim, npts) specifying the
            parameter values for the point to be computed.

        Returns
        -------
        coords: Coords
            A Coords array of shape (nelems, npts, 3) with npts points
            at parametric values rst for each element.

        """
        rst = at.checkArray(rst, shape=(self.eltype.ndim, -1), kind='f')
        H = self.elems.eltype.H(rst)
        X = self.coords[self.elems]
        X = np.dot(X.transpose((0, 2, 1)), H).transpose((0, 2, 1))
        return X


    def addNodes(self, newcoords, eltype=None):
        """Add new nodes to elements.

        Parameters
        ----------
        newcoords: :term:`coords_like`
            A Coords array with shape `(nelems,nnod,3)` or`(nelems*nnod,3)`.
            Each element gets exactly `nnod` extra nodes from this array.
        eltype: str, optional
            An optional element type for the returned Mesh. If not provided,
            or if the plexitude of the specified element does not match
            the constructed plexitude, a temporary 'plex..' element type
            is set. The user then has to set the correct element type
            afterwards.

        Returns
        -------
        Mesh
            A Mesh where the coords are the concatenation of self.coords
            and newcoords, and the connectivity table defining the new
            elements has a plexitude `self.nplex() + nnod`.

        Notes
        -----
        This is mainly intended for use in :meth:`convert`.
        """
        newcoords = newcoords.reshape(-1, 3)
        coords = Coords.concatenate([self.coords, newcoords])
        newnodes = np.arange(newcoords.shape[0]).reshape(
            self.elems.shape[0], -1) + self.coords.shape[0]
        elems = np.concatenate([self.elems, newnodes], axis=-1)
        nplex = elems.shape[-1]
        if ElementType.get(eltype).nplex != nplex:
            eltype = f"plex{nplex}"
        elems = Elems(elems, eltype=eltype)
        return Mesh(coords, elems, self.prop)


    def addNewNodes(self, rst, eltype):
        """Add new nodes to elements at given parametric values.

        Parameters
        ----------
        rst: :term:`array_like`
            A float array with shape (ndim, npts) specifying the
            parameter values for the new nodes.
        eltype: :term:`eltype_like`
            The element type for the enlarged element. It should have
            plexitude self.nplex+npts.

        Returns
        -------
        Mesh
            A Mesh of plexitude nplex+npts and the specified eltype.

        See Also
        --------
        addMeanNodes: add nodes at average positions of existing nodes.
        convert: convert a Mesh to another eltype

        Notes
        -----
        The use of the Mesh.convert method is the prefered way to convert
        the element type.
        """
        return self.addNodes(self.pointsAt(rst), eltype)


    def addMeanNodes(self, nodsel, eltype):
        """Add new nodes to elements by averaging existing ones.

        Parameters
        ----------
        nodsel: :term:`array_like`
            A local node selector as in :meth:`selectNodes`.
        eltype: str, optional
            An optional element type for the returned Connecitivity.

        Returns
        -------
        Mesh
            A Mesh of plexitude nplex+npts and the specified eltype.

        See Also
        --------
        addNewNodes: add nodes at parametric positions

        Notes
        -----
        The use of the Mesh.convert method is the prefered way to convert
        the element type.
        """
        elems = self.elems.selectNodes(nodsel)
        newcoords = self.coords[elems].mean(axis=1)
        return self.addNodes(newcoords, eltype)


    def convert(self, totype, fuse=None, verbose=False):
        """Convert a Mesh to another element type.

        Converting a Mesh from one element type to another can only be
        done if both element types are of the same dimensionality.
        Thus, 3D elements can only be converted to 3D elements.

        Parameters
        ----------
        totype: str or ElementType
            The name or type of the target element to which to convert.
            A generic type 'linear' may be specified to convert to the
            linear element type of the same family.
        fuse: bool, optional
            If True, the resulting Mesh will be run through :meth:`fuse`
            before returning. If False, no fuse will be done.
            The default (None) is a smart mode: a fuse will be
            applied if new nodes were added during the conversion.
        verbose: bool, optional
            If True, intermediate steps during the conversion will
            be reported.

        Returns
        -------
        Mesh
            A Mesh of the requested element type, representing
            the same geometry (possibly approximatively) as the original Mesh.

        Raises
        ------
        ValueError
            If the Mesh can not be transformed to the specified eltype.

        Notes
        -----
        The conversion uses two basic methods for converting the element
        type: split the elements in smaller parts and add new nodes to the
        elements. Adding new nodes may produce duplicate nodes at the common
        border of elements. Not using a final fuse operation will then
        likely produce unwanted results.

        In many cases a conversion is done over one (or more) intermediary
        element types. The fuse operation is only done once, after all
        transformation steps have occurred.

        If the user wants/needs to apply multiple conversions in sequence,
        he may opt to switch off the fusing for all but the last conversion.

        Not all conversions between elements of the same dimensionality
        are possible. The possible conversion strategies are implemented
        in a table in :mod:`elements`. New strategies may be added however.

        Examples
        --------
        >>> M = Mesh(eltype='quad4').convert('tri3')
        >>> M.coords
        Coords([[0.,  0.,  0.],
                [1.,  0.,  0.],
                [1.,  1.,  0.],
                [0.,  1.,  0.]])
        >>> M.elems
        Elems([[0, 1, 2],
               [2, 3, 0]], eltype=Tri3)
        """
        if totype == 'linear':
            totype = self.eltype.linear

        if not isinstance(totype, str):
            totype = totype.lname

        if totype == self.elName():
            return self

        strategy = self.eltype.conversions.get(totype, None)

        while not isinstance(strategy, list):
            # This allows for aliases in the conversion database
            strategy = self.eltype.conversions.get(strategy, None)

            if strategy is None:
                raise ValueError(
                    f"Don't know how to convert {self.elName()} -> {totype}")

        # 'r' and 'v' steps can only be the first and only step
        steptype, stepdata = strategy[0]
        if steptype == 'r':
            # Randomly convert elements to one of the types in list
            return self.convertRandom(stepdata)
        elif steptype == 'v':
            return self.convert(stepdata, fuse=fuse, verbose=verbose).convert(
                totype, fuse=fuse, verbose=verbose)

        # Execute a strategy
        if verbose:
            print(f"Convert Mesh from {self.elName()} to {totype}")
        mesh = self
        totype = totype.split('-')[0]
        for step in strategy:
            steptype, stepdata = step

            if fuse is None and steptype in 'ax':
                fuse = True

            if steptype == 'a':
                mesh = mesh.addMeanNodes(stepdata, totype)

            elif steptype == 'n':
                mesh = mesh.addNewNodes(stepdata, totype)

            elif steptype == 's':
                mesh = mesh.selectNodes(stepdata, totype)

            elif steptype == 'c':
                mesh = mesh.compact()

            elif steptype == 'x':
                mesh = globals()[stepdata](mesh)

            else:
                raise ValueError(
                    f"Unknown conversion step type '{steptype}'")
        if not mesh.elName() == totype:
            mesh.eltype = totype
        if fuse:
            mesh = mesh.fuse()
        return mesh


    def convertRandom(self, choices):
        """Convert choosing randomly between choices

        Returns a Mesh obtained by converting the current Mesh by a
        randomly selected method from the available conversion type
        for the current element type.
        """
        ml = self.splitRandom(len(choices), compact=False)
        ml = [m.convert(c) for m, c in zip(ml, choices)]
        prop = self.prop
        if prop is not None:
            prop = np.concatenate([m.prop for m in ml])
        elems = np.concatenate([m.elems for m in ml], axis=0)
        eltype = {m.elName() for m in ml}
        if len(eltype) > 1:
            raise RuntimeError("Invalid choices for random conversions")
        eltype = eltype.pop()
        return Mesh(self.coords, elems, prop, eltype)


    def subdivide(self, *ndiv, fuse=None):
        """Subdivide the elements of a Mesh.

        Parameters
        ----------
        *ndiv: sequence
            A sequence of divisor specifications for the parametric directions
            of the element. There can not be more divisor specifications
            than the number of parametric directions (self.eltype.ndim).
            If there are less specifications, the last one is repeated up
            to the elements ndim.
            Each divisor specification should be either

            - an int, specifying the number of equidistant partitions of
              the parameter space along that direction, or
            - an ordered list of float values specifying the partitioning
              points in the parametric range (normally 0..1).
              In order to completely fill the element, the first and last
              values in the list should be the start and end of the parameter
              range.

        fuse: bool, optional
            If True (default), the resulting Mesh is completely fused.
            If False, the Mesh is only fused over each individual
            element of the original Mesh.

        Returns
        -------
        Mesh
            A Mesh where each element is replaced by a number of
            smaller elements of the same type.

        Notes
        -----
        Some element types can not be subdivided: the non-dimensional Point
        and the complex structures Octa and Icosa.

        Examples
        --------
        >>> M = Mesh(eltype='quad4').subdivide(3,2)
        >>> print(M)
        Mesh: nnodes: 12, nelems: 6, nplex: 4, level: 2, eltype: quad4
          BBox: [0.  0.  0.], [1.  1.  0.]
          Size: [1.  1.  0.]
          Length: 4.0  Area: 1.0
        >>> M = Mesh(eltype='quad4').subdivide(3,2)
        >>> print(M.coords)
        [[0.     0.     0.    ]
         [0.3333 0.     0.    ]
         [0.6667 0.     0.    ]
         [1.     0.     0.    ]
         [0.     0.5    0.    ]
         [0.3333 0.5    0.    ]
         [0.6667 0.5    0.    ]
         [1.     0.5    0.    ]
         [0.     1.     0.    ]
         [0.3333 1.     0.    ]
         [0.6667 1.     0.    ]
         [1.     1.     0.    ]]
        >>> print(M.elems)
        [[ 0  1  5  4]
         [ 1  2  6  5]
         [ 2  3  7  6]
         [ 4  5  9  8]
         [ 5  6 10  9]
         [ 6  7 11 10]]
        >>> M = Mesh(eltype='hex8').subdivide(2,1,1)
        >>> print(M)
        Mesh: nnodes: 12, nelems: 2, nplex: 8, level: 3, eltype: hex8
          BBox: [0. 0. 0.], [1. 1. 1.]
          Size: [1. 1. 1.]
          Area: 6.0  Volume: 1.0
        >>> print(M.coords)
        [[0.  0.  0. ]
         [0.5 0.  0. ]
         [1.  0.  0. ]
         [0.  1.  0. ]
         [0.5 1.  0. ]
         [1.  1.  0. ]
         [0.  0.  1. ]
         [0.5 0.  1. ]
         [1.  0.  1. ]
         [0.  1.  1. ]
         [0.5 1.  1. ]
         [1.  1.  1. ]]
        >>> print(M.elems)
        [[ 0  1  4  3  6  7 10  9]
         [ 1  2  5  4  7  8 11 10]]
        """
        eltype = self.eltype
        proxy = getattr(eltype, 'subdiv_proxy', None)
        if proxy:
            return self.convert(proxy).subdivide(*ndiv, fuse=fuse).convert(
                eltype).compact()

        if len(ndiv) > eltype.ndim:
            raise ValueError(
                "Got more ndiv items than the element ndim")
        ndiv_isint = [at.isInt(nd) for nd in ndiv]
        if not all(ndiv_isint) and fuse is None:
            fuse = True

        try:
            lndiv = [nd if isint else len(nd)-1
                     for nd, isint, d in zip(ndiv, ndiv_isint, eltype.degree)]
            els = eltype.els(*lndiv)
            wts = eltype.wts(*ndiv)
        except AttributeError:
            # TODO: use element per element isopar method as a last resort?
            if fuse is None:
                fuse = True
            raise ValueError(f"Can not subdivide Mesh of eltype {eltype}")
        X = self.coords[self.elems]
        U = np.dot(wts, X).transpose([1, 0, 2]).reshape(-1, 3)
        e = np.concatenate([els+i*wts.shape[0] for i in range(self.nelems())])
        M = self.__class__(U, e, eltype=eltype)
        if self.prop is not None:
            M.setProp(at.repeatValues(self.prop, np.prod(lndiv)))
        if fuse:
            M = M.fuse()
        return M


    @utils.warning('mesh_reduce_degenerate')
    def reduceDegenerate(self, *arg, **kargs):
        return self.splitDegenerate(**kargs)


    def splitDegenerate(self, reduce=True, return_indices=False):
        """Split a Mesh in non-degenerate and degenerate elements.

        Splits a Mesh in non-degenerate elements and degenerate elements,
        and tries to reduce degenerate elements to lower plexitude elements.

        Parameters
        ----------
        reduce: bool or :class:`~elements.ElementType` name
            If True, the degenerate elements will be tested against
            known degeneration patterns, and the matching elements will be
            transformed to non-degenerate elements of a lower plexitude.
            If a string, it is an element name and only transforms to this
            element type will be considered.
            If False, no reduction of the degenerate elements will be
            attempted.
        return_indices: bool, optional
            If True, also returns the element indices in the original
            Mesh for all of the elements in the derived Meshes.

        Returns
        -------
        ML: list of Mesh objects
            The list of Meshes resulting from the split operation. The first
            holds the non-degenerate elements of the original Mesh. The last
            holds the remaining degenerate elements.
            The intermediate Meshes, if any, hold elements of a lower plexitude
            than the original.

        Warning
        -------
        The Meshes that hold reduced elements may still contain degenerate
        elements for the new element type

        Examples
        --------
        >>> M = Mesh(np.zeros((4,3)),
        ...     [[0,0,0,0],
        ...      [0,0,0,1],
        ...      [0,0,1,2],
        ...      [0,1,2,3],
        ...      [1,2,3,3],
        ...      [2,3,3,3],
        ...     ],eltype='quad4')
        >>> M.elems.listDegenerate()
        array([0, 1, 2, 4, 5])
        >>> for Mi in M.splitDegenerate(): print(Mi)
        Mesh: nnodes: 4, nelems: 1, nplex: 4, level: 2, eltype: quad4
          BBox: [0.  0.  0.], [0.  0.  0.]
          Size: [0.  0.  0.]
          Length: 0.0  Area: 0.0
        Mesh: nnodes: 4, nelems: 5, nplex: 3, level: 2, eltype: tri3
          BBox: [0.  0.  0.], [0.  0.  0.]
          Size: [0.  0.  0.]
          Length: 0.0  Area: 0.0
        >>> conn,ind = M.splitDegenerate(return_indices=True)
        >>> print(ind[0],ind[1])
        [3] [0 1 2 5 4]
        >>> print(conn[1].elems)
        [[0 0 0]
         [0 0 1]
         [0 1 2]
         [2 3 3]
         [1 2 3]]
        """
        if reduce is False:
            deg = self.elems.testDegenerate()
            ML = [self.select(~deg, compact=False),
                  self.select(deg, compact=False)]
            if return_indices:
                ind = [np.where(~deg)[0], np.where(deg)[0]]

        else:
            target = None if reduce is True else reduce
            conn, ind = self.elems.reduceDegenerate(target, return_indices=True)
            ML = [Mesh(self.coords, e) for e in conn]
            if self.prop is not None:
                ML = [M.setProp(self.prop[i]) for M, i in zip(ML, ind)]

        if return_indices:
            return ML, ind
        else:
            return ML


    def removeDegenerate(self):
        """Remove the degenerate elements from a Mesh.

        Returns
        -------
        Mesh
            A Mesh with all degenerate elements removed.
        """
        deg = self.elems.testDegenerate()
        return self.select(~deg, compact=False)


    def removeDuplicate(self, permutations='all'):
        """Remove the duplicate elements from a Mesh.

        Duplicate elements are elements that consist of the same nodes.

        Parameters
        ----------
        permutations: str
            Defines which permutations of the nodes are allowed while still
            considering the elements duplicates. Possible values are:

        - 'none': no permutations are allowed: the node list of the elements
          must have the same value at every position in order to be considered
          duplicates;
        - 'roll': rolling is allowed. Node lists that can be transformed into
          each other by rolling are considered equal;
        - 'all': any permutation of the same set of nodes will be considered
          a duplicate element. This is the default.

        Returns
        -------
        Mesh
            A Mesh with all duplicate elements removed.
        """
        return self.select(at.uniqueRows(self.elems, permutations))


    def renumber(self, order='elems'):
        """Renumber the nodes of a Mesh in the specified order.

        Parameters
        ----------
        order: int :term:`array_like` or str
            If an array, it is an index with length equal to the number of
            nodes. It should be a permutation of ``np.arange(self.nnodes())``.
            The index specifies the node number that should come at this
            position. Thus, the order values are the old node numbers on
            the new node number positions.

            ``order`` can also be a predefined string that will generate the
            node index automatically:

            - 'elems': the nodes are number in order of their appearance in the
              Mesh connectivity.
            - 'random': the nodes are numbered randomly.
            - 'front': the nodes are numbered in order of their frontwalk.

        Returns
        -------
        Mesh
            A Mesh equivalent with the input, but with the nodes numbered
            differently.

        """
        if order == 'elems':
            order = at.renumberIndex(self.elems, order='pos')
        elif order == 'random':
            order = np.arange(self.nnodes())
            np.random.shuffle(order)
        elif order == 'front':
            adj = self.elems.adjacency('n')
            p = adj.frontWalk()
            order = p.argsort()
        newnrs = at.inverseUniqueIndex(order)
        return self.__class__(self.coords[order], newnrs[self.elems],
                              prop=self.prop, eltype=self.eltype)


    def reorder(self, order='nodes'):
        """Reorder the elements of a Mesh.

        Parameters
        ----------
        order: :term:`array_like` or str
            If an array, it is a permutation of the numbers in
            ``np.arange(self.nelems())``, specifying the requested order of
            the elements.

            ``order`` can also be one of the following predefined strings:

            - 'nodes': order the elements in increasing node number order.
            - 'random': number the elements in a random order.
            - 'reverse': number the elements in reverse order.

        Returns
        -------
        Mesh
            A Mesh equivalent with self but with the elements ordered as
            specified.

        """
        order = self.elems.reorder(order)
        if self.prop is None:
            prop = None
        else:
            prop = self.prop[order]
        return self.__class__(self.coords, self.elems[order],
                              prop=prop, eltype=self.eltype)


    def connectedElements(self, startat, mask, level=0):
        # TODO: Should we create some general 'masked mesh' class?
        """Return the elements reachable from startat.

        Finds the elements which can be reached from startat by walking along
        a mask (a subset of elements). Walking is possible over nodes, edges
        or faces, as specified in level.

        Parameters
        ----------
        startat: int or :term:`array_like`, int.
            The starting element number(s).
        level: int
            Specifies how elements can be reached: via node (0), edge (1)
            or face (2).
        mask: :term:`array_like`, bool or int
            Flags the elements that are considered walkable. It is an int array
            with the walkable element numbers, or a bool array flagging
            these elements with a value True. If none of the start elements
            is in mask, the result will obviously be nil.

        Returns
        -------
        array
            List of element indices that can be reached from any of the start
            elements by walking only over elements in mask.
        """
        startat = np.asarray(startat).reshape(-1)
        if len(np.intersect1d(startat, np.arange(self.nelems()))) < len(startat):
            raise ValueError("Wrong elem index found in startat, "
                             f"outside range 0 - {self.nelems()}")
        mask = np.asarray(mask)
        if mask.dtype == bool:
            if len(mask)!=self.nelems():
                raise ValueError(
                    "If mask is an array of boolean, it should have all "
                    f"{self.nelems()} elements , got {len(mask)}")
            mask = np.where(mask)[0]
        if len(np.intersect1d(mask, np.arange(self.nelems()))) < len(mask):
            raise ValueError("Wrong elem index found in mask, "
                             f"outside range 0 - {self.nelems()}")
        startat = np.intersect1d(startat, mask)
        if len(startat) == 0:
            return []
        startat = at.findFirst(mask, startat)
        return mask[self.select(mask).reachableFrom(startat, level=level)]


    ##############################################################
    #
    # Cutting
    #

    # TODO:

    # def cutWithPlane(self, p, n, side='', atol=None, newprops=None):
    #     """Cut a Mesh with the plane (p,n).

    #     Note
    #     ----
    #     This is currently limited to 'line2' Mesh.

    #     Parameters
    #     ----------
    #     p: :term:`array_like` (3,)
    #         A point in the cutting plane.
    #     n: :term:`array_like` (3,)
    #         The normal vector to the cutting plane.
    #     side: str, one of '', '+' or '-'
    #         Specifies which side of the plane should be returned.
    #         If an empty string (default), both sides are returned.
    #         If '+' or '-', only the part at the positive, resp. negative
    #         side of the plane (as defined by its normal) is returned.

    #     Returns
    #     -------
    #     Mpos: Mesh
    #         Mesh with the part of the input Mesh at the positive side of
    #         the plane. Not returned if side=='-'.
    #     Mneg: Mesh
    #         Mesh with the part of the input Mesh at the negative side of
    #         the plane. Not returned if side=='+'.

    #     Notes
    #     -----
    #     Elements of the input Mesh that are lying completely on one side
    #     of the plane will return unaltered. Elements that are cut by the
    #     plane are split up into multiple parts.

    #     See Also
    #     --------
    #     intersectionWithPlane: return intersection of Formex and plane

    #     """
    #     return
    #     if atol is None:
    #         atol = 1.e-5*self.dsize()
    #     if self.nplex() == 2:
    #         return _cut2AtPlane(self, p, n, side, atol, newprops)
    #     elif self.nplex() == 3:
    #         return _cut3AtPlane(self, p, n, side, atol, newprops)
    #     else:
    #         # OTHER PLEXITUDES NEED TO BE IMPLEMENTED
    #         raise ValueError("Formex should be plex-2 or plex-3")




    ##############################################################
    #
    # Connection, Extrusion, Sweep, Revolution
    #


    def connect(self, coordslist, div=1, degree=1, loop=False, eltype=None):
        """Connect a sequence of topologically congruent Meshes into a hypermesh.

        Parameters
        ----------
        coordslist: list of Coords | list of Mesh | Mesh
          If Mesh objects are given, they should (all) have the same element
          type as `self`. Their connectivity tables will not be used.
          They will only serve to construct a list of Coords objects by
          taking the `coords` attribute of each of the Meshes. If only a single
          Mesh was specified, `self.coords` will be added as the first Coords
          object in the list.

          All Coords objects in the coordslist (either specified or
          constructed from the Mesh objects), should have the exact same
          shape as `self.coords`. The number of Coords items in the list should
          be a multiple of `degree`, plus 1.

          Each of the Coords in the final coordslist is combined with the
          connectivity table, element type and property numbers of `self` to
          produce a list of toplogically congruent Meshes.
          The return value is the hypermesh obtained by connecting
          each consecutive slice of (degree+1) of these Meshes.

          Note that unless a single Mesh was specified as `coordslist`
          parameter, the coords of `self` are not used. In many cases
          however `self` or `self.coords` will be one of the items in
          the specified `coordslist`.

        degree: int
            The degree of the connection. Currently only degree 1 and 2
            are supported:

            - If degree is 1, every Coords from the `coordslist`
              is connected with hyperelements of a linear degree in the
              connection direction.

            - If degree is 2, quadratic hyperelements are
              created from one Coords item and the next two in the list.
              Note that all Coords items should contain the same number of nodes,
              even for higher order elements where the intermediate planes
              contain less nodes.

              Currently, degree=2 is not allowed when `coordslist` is specified
              as a single Mesh.

        loop: bool, optional
            If True, the connections with loop around the list and
            connect back to the first. This is accomplished by adding the first
            Coords item back at the end of the list.

        div: :term:`seed`
            This parameter can only be used for degree==1.

            With this parameter the generated connections can be further
            subdivided along the connection direction. `div` can be any of the
            values accepted by :func:`~arraytools.smartSeed`, or a list thereof.
            In the latter case, the length of the list should be one less
            than the length of the `coordslist`. Each pair of consecutive
            items from the coordinate list will be connected using the
            seeds generated by the corresponding value from `div`, passed to
            :func:`~arraytools.smartSeed`.

            If seed values are specified directly as a list of floats, the list
            should start with a value 0.0 and end with 1.0.

        eltype: str or :class:`ElementType`, optional
            The element type of the constructed hypermesh. Normally,
            this is set automatically from the base element type and the
            connection degree. If a different element type is specified,
            a final conversion to the requested element type is attempted
            (using :meth:`convert`).


        Returns
        -------
        Mesh
            The hypermesh obtained by connecting each consecutive slice of
            (degree+1) of the Meshes created as explained above under the
            parameters. The hypermesh has a dimensionality that is one higher
            than the original Mesh (i.e. points become lines, lines become
            surfaces, surfaces become volumes).
            The resulting elements are of the given `degree` in the
            direction of the connection.

        """
        if isinstance(coordslist, list):
            if isinstance(coordslist[0], Mesh):
                if sum([c.eltype != self.eltype for c in coordslist]):
                    raise ValueError(
                        "All Meshes in the list should have same element type")
                clist = [c.coords for c in coordslist]
            else:
                clist = coordslist
        elif isinstance(coordslist, Mesh):
            clist = [self.coords, coordslist.coords]
            if degree == 2:
                raise ValueError("This only works for linear connection")
            ## BV: Any reason why this would not work??
            ##     xm = 0.5 * (clist[0]+clist[1])
            ##     clist.insert(1, xm)
        else:
            raise ValueError("Invalid coordslist argument")

        if sum([c.shape != self.coords.shape for c in clist]):
            raise ValueError("Incompatible shape  in coordslist")

        # implement loop parameter
        if loop:
            clist.append(clist[0])

        if (len(clist)-1) % degree != 0:
            raise ValueError("Invalid length of coordslist "
                             f"({len(clist)}) for degree {degree}.")

        # set divisions
        if degree > 1:
            div = 1
        if not isinstance(div, list) or at.isFloat(div[0]):
            div=[div]

        # now we should have list of: ints, tuples or floatlists
        div = [at.smartSeed(divi)[1:] for divi in div]
        # check length
        nsteps = (len(clist)-1) // degree
        if len(div) == 1:
            div = div * nsteps
        elif len(div)!=nsteps:
            raise ValueError("A list of div seeds must have a length equal "
                             f"to (len(clist)-1)//degree) = {nsteps}")

        # For higher order non-lagrangian elements the procedure could be
        # optimized by first compacting the coords and elems.
        # Instead we opted for the simpler method of adding the maximum
        # number of nodes, and then selecting the used ones.
        # A final compact() throws out the unused points.

        # Concatenate the coordinates
        if degree == 1:
            # We do not have a 2nd degree interpolation yet
            x = [Coords.interpolate(xi, xj, d).reshape(-1, 3)
                 for xi, xj, d in zip(clist[:-1], clist[1:], div)]
            clist = clist[:1] + x
        x = Coords.concatenate(clist)

        # Create the connectivity table
        nnod = self.ncoords()
        nrep = (x.shape[0]//nnod - 1) // degree
        e = self.elems.extrude(nnod, degree).replic(nrep, nnod*degree)

        # Create the Mesh
        M = Mesh(x, e).setProp(self.prop)
        # convert to proper eltype
        if eltype:
            M = M.convert(eltype)
        return M


    def extrude(self, div, dir=0, length=1., degree=1, eltype=None):
        """Extrude a Mesh along a straight line.

        The Mesh is extruded over a given length in the given direction.

        Parameters
        ----------
        div: smartseed
            Specifies how the extruded direction will be subdivided in
            elements. It can be anything that is acceptable as input for
            :func:`~arraytools.smartSeed`.
        dir: int (0,1,2) or float :term:`array_like` (3,)
            The direction of the extrusion: either a global axis
            number or a direction vector.
        length: float
            The length of the extrusion, measured along the direction ``dir``.

        Returns
        -------
        Mesh
            A Mesh obtained by extruding the input Mesh over the
            given ``length`` in direction ``dir``, subdividing this
            length according to the seeds generated
            by ``smartSeed(div)``.

        See Also
        --------
        sweep: extrusion along a general path

        Examples
        --------
        >>> M = Mesh(Formex([0])).extrude(3,0,3)
        >>> print(M)
        Mesh: nnodes: 4, nelems: 3, nplex: 2, level: 1, eltype: line2
          BBox: [0.  0.  0.], [3.  0.  0.]
          Size: [3.  0.  0.]
          Length: 3.0

        """
        if at.isFloat(dir):
            # Probably old style extrude parameters?
            utils.warn("warn_mesh_extrude")
        t = at.smartSeed(div)
        if degree > 1:
            t2 = 0.5 * (t[:-1] + t[1:])
            t = np.concatenate([t[:1], np.column_stack([t2, t[1:]]).ravel()])
        x0 = self.coords
        x1 = x0.trl(dir, length)
        dx = x1-x0
        x = [x0 + ti*dx for ti in t]
        return self.connect(x, degree=degree, eltype=eltype)


    def revolve(self, n, axis=0, angle=360., around=None, loop=False, eltype=None):
        """Revolve a Mesh around an axis.

        Revolving a Mesh extrudes the Mesh along a circular path.

        Parameters
        ----------
        n: int
            Number of circumferential steps
        axis: int (0,1,2) or float :term:`array_like` (3,)
            The direction of the rotation axis:
            either one of 0,1,2 for a global axis, or a vector with
            3 components for a general direction.
        angle: float
            The total angle (in degrees) of the revolve operation.
        around: float :term:`array_like` (3,)
            If provided, it specifies a point on the rotation axis. If not,
            the rotation axis goes through the origin of the global axes.
        loop: bool
            If True, the end of the revolution will be connected back to the
            start.
        eltype: str of :class:`ElementType`, optional.
            The final element type. If specified, and it does not match the
            natural extruded element type, a final conversion to this target
            type will be attempted.

        Returns
        -------
        Mesh
            A Mesh obtained by revolving the given Mesh
            over an angle around an axis in n steps, while extruding
            the mesh from one step to the next.
            This extrudes points into lines, lines into surfaces and surfaces
            into volumes.

        See Also
        --------
        sweep: extrusion along a general path
        """
        angles = np.arange(n+1) * angle / n
        seq = [self.coords.rotate(angle=a, axis=axis, around=around) for a in angles]
        return self.connect(seq, loop=loop, eltype=eltype)


    def sweep(self, path, eltype=None, **kargs):
        """Sweep a mesh along a path, creating an extrusion.

        Parameters
        ----------
        path: Curve object. The path over which to sweep the Mesh.
        - `eltype`: string. Name of the element type on the
          returned Meshes.
        - `**kargs`: keyword arguments that are passed to
          :meth:`curve.Curve.sweep2`, with the same meaning.
          Usually, you will need to at least set the `normal` parameter.

        Returns a Mesh obtained by sweeping the given Mesh over a path.
        The returned Mesh has double plexitude of the original.
        If `path` is a closed Curve connect back to the first.

        This operation is similar to the extrude() method, but the path
        can be any 3D curve.

        See Also
        --------
        extrude: extrusion along a straight path
        revolve: extrusion along a circular path
        connect: general connection of Meshes into a hypermesh
        """
        loop = path.closed
        seq = path.sweep2(self.coords, **kargs)
        return self.connect(seq, eltype=eltype, loop=loop)


    def __add__(self, other):
        """Return the sum of two Meshes.

        The sum of the Meshes is simply the concatenation thereof.
        It allows us to write simple expressions as M1+M2 to concatenate
        the Meshes M1 and M2. Both meshes should be of the same plexitude
        and have the same eltype.
        The result will be of the same class as self (either a Mesh or a
        subclass thereof).
        """
        return self.concatenate([self, other])


    @classmethod
    def concatenate(clas, meshes, fuse=True, **kargs):
        """Concatenate a list of meshes of the same plexitude and eltype.

        Parameters
        ----------
        meshes: list of Mesh
            A list of Meshes all having the same plexitude.
            Meshes without plexitude are silently ignored: this allows empty
            Meshes to be appear in the list.
        fuse: bool
            If True, the resulting concatenation will be fused.
        *kargs:
            Optional extra parameters for the :meth:`fuse` operation.

        Notes
        -----
        If any of the meshes has property numbers, the resulting mesh will
        inherit the properties. In that case, any meshes without properties
        will be assigned property 0.
        If all meshes are without properties, so will be the result.

        This is a class method, and should be invoked as follows::

          Mesh.concatenate([mesh0,mesh1,mesh2])

        Examples
        --------
        >>> M0 = Mesh(eltype='quad4')
        >>> M1 = M0.trl(0,1.)
        >>> M = Mesh.concatenate([M0,M1])
        >>> print(M.coords)
        [[0.  0.  0.]
         [0.  1.  0.]
         [1.  0.  0.]
         [1.  1.  0.]
         [2.  0.  0.]
         [2.  1.  0.]]
        >>> print(M.elems)
        [[0 2 3 1]
         [2 4 5 3]]

        Concatenate Meshes using the same Coords block

        >>> M0 = Mesh(M.coords, M.elems[:1])
        >>> M1 = Mesh(M.coords, M.elems[1:])
        >>> M2 = Mesh.concatenate([M0,M1])
        >>> id(M.coords) == id(M2.coords)
        False
        >>> M2 = Mesh.concatenate([M0,M1], fuse=False)
        >>> id(M.coords) == id(M2.coords)
        True
        """
        meshes = [m for m in meshes if m.nplex() > 0]
        # This is superfluous, as checking eltype makes sure nplex matches
        # # check nplex:
        # nplex = {m.nplex() for m in meshes}
        # if len(nplex) > 1:
        #     raise ValueError("Cannot concatenate meshes with different "
        #                      f"plexitude: {nplex}")
        # check eltype
        eltype = {m.eltype for m in meshes}
        if len(eltype) > 1:
            raise ValueError("Cannot concatenate meshes with different"
                             f"eltype: {[m.elName() for m in meshes]}")

        if all([m.prop is None for m in meshes]):
            # There are no props
            prop = None
        else:
            # Keep the available props
            prop = np.concatenate([m.prop if m.prop is not None else
                                   np.zeros(m.nelems(), dtype=at.Int)
                                   for m in meshes])

        coords, elems = mergeMeshes(meshes, fuse=fuse, **kargs)
        elems = np.concatenate(elems, axis=0)
        return clas(coords, Elems(elems, eltype=eltype.pop()), prop=prop)


    # Test and clipping functions


    def test(self, nodes='all', dir=0, min=None, max=None, atol=0.):
        """Flag elements having nodal coordinates between min and max.

        This is comparable with :meth:`coords.Coords.test` but operates
        at the Mesh element level. It tests the position of one or more
        nodes of the elements of the :class:`Mesh` with respect to
        one or two parallel planes. This is very useful in clipping
        a mesh in a specified direction. In most cases the clipping
        direction is one of the global coordinate axes, but a general
        direction may be used as well.

        Testing along global axis directions is highly efficient. It tests
        whether the corresponding coordinate is above or equal to the `min`
        value and/or below or equal to the `max` value. Testing in a general
        direction tests whether the distance to the `min` plane is positive
        or zero and/or the distance to the `max` plane is negative or zero.

        Parameters
        ----------
        nodes: int, list of ints or string
            Specifies which points of the elements are taken into account
            in the tests. It should be one of the following:

            - a single node index (smaller than self.nplex()),
            - a list of node indices (all smaller than self.nplex()),
            - one of the special strings: 'all', 'any', 'none'.

            The default ('all') will flag the elements that have all their
            nodes between the planes x=min and x=max, i.e. the elements that
            fall completely between these planes.
        dir: a single int or a float :term:`array_like` (3,)
            The direction in which to measure distances. If an int, it is
            one of the global axes (0,1,2). Else it is a vector with 3
            components. The default direction is the global x-axis.
        min: float or point-like, optional
            Position of the minimal clipping plane.
            If `dir` is an int, this is a single float giving the coordinate
            along the specified global axis. If `dir` is a vector, this must
            be a point and the minimal clipping plane is defined by this point
            and the normal vector `dir`. If not provided, there is no clipping
            at the minimal side.
        max: float or point-like.
            Position of the maximal clipping plane.
            If `dir` is an int, this is a single float giving the coordinate
            along the specified global axis. If `dir` is a vector, this must
            be a point and the maximal clipping plane is defined by this point
            and the normal vector `dir`. If not provided, there is no clipping
            at the maximal side.
        atol: float
            Tolerance value added to the tests to account for accuracy
            and rounding errors.
            A `min` test will be ok if the point's distance from the
            `min` clipping plane is `> -atol` and/or the distance from the
            `max` clipping plane is `< atol`. Thus a positive atol widens the
            clipping planes.

        Returns
        -------
        : 1-dim bool array
            Array with length ``self.nelems()`` flagging the elements that
            pass the test(s). The return value can directly be used as an
            index in :meth:`select` or `cselect` to obtain a :class:`Mesh`
            with the elements satisfying the test or not. Or you can use
            ``np.where(result)[0]`` to get the indices of the elements passing
            the test.

        Raises
        ------
        ValueError: At least one of min or max have to be specified
            If neither `min` nor `max` are provided.

        See Also
        --------
        :meth:`coords.Coords.test`: testing individual points
        select: return only the selected elements
        cselect: return all but the selected elements

        Examples
        --------
        >>> M = Mesh(eltype='tri3').subdivide(2)
        >>> M.coords
        Coords([[0. ,  0. ,  0. ],
                [0.5,  0. ,  0. ],
                [1. ,  0. ,  0. ],
                [0. ,  0.5,  0. ],
                [0.5,  0.5,  0. ],
                [0. ,  1. ,  0. ]])
        >>> M.elems
        Elems([[0, 1, 3],
               [1, 2, 4],
               [3, 4, 5],
               [1, 4, 3]], eltype=Tri3)
        >>> M.test(min=0.0,max=0.5)
        array([ True, False,  True,  True])
        >>> M.test(nodes=[0],min=0.0,max=0.2)
        array([ True, False,  True, False])
        >>> M.test(dir=(-1.,1.,0.), min=(0.,0.,0.))
        array([False, False,  True, False])
        >>> M.test(dir=(-1.,1.,0.), min=(0.,0.,0.), nodes='any')
        array([ True,  True,  True,  True])
        >>> M.test(dir=(-1.,1.,0.), min=(0.,0.,0.), nodes='any', atol=-1.e-5)
        array([ True, False,  True,  True])
        """
        if min is None and max is None:
            raise ValueError("At least one of min or max have to be specified.")

        if utils.isString(nodes):
            nod = np.arange(self.nplex())
        else:
            nod = nodes

        # Perform the test on the selected nodes
        X = self.coords[self.elems][:, nod]
        T = X.test(dir=dir, min=min, max=max, atol=atol)

        if len(T.shape) > 1:
            # We have results for more than 1 node per element
            if nodes == 'any':
                T = T.any(axis=1)
            elif nodes == 'none':
                T = ~T.any(axis=1)
            else:
                T = T.all(axis=1)

        return np.asarray(T)


    def clipAtPlane(self, p, n, nodes='any', side='+'):
        """Return the Mesh clipped at plane (p,n).

        This is a convenience function returning the part of the Mesh
        at one side of the plane (p,n)
        """
        if side == '-':
            n = -n
        return self.clip(self.test(nodes=nodes, dir=n, min=p))


    def intersectionWithLines(self, approximated=True, **kargs):
        """Return the intersections of a surface Mesh with lines.

        The Mesh is intersected with lines. The arguments and return values are
        the same as in :meth:`trisurface.TriSurface.intersectionWithLines`,
        except for the `approximated`.

        For a Mesh with eltype 'tri3', the intersections are exact. For other
        eltypes, if `approximated` is True a conversion to 'tri3' is done before
        computing the intersections. This may produce an exact result,
        an approximate result or no result (if the conversion fails).
        Of course the user can create his own approximation to a 'tri3'
        surface first, before calling this method.
        """
        if self.elName() == 'tri3':
            p, i = self.toSurface().intersectionWithLines(**kargs)
        else:
            if approximated:
                S = self.copy().setProp(list(range(self.nelems()))).toSurface()
                p, i = S.intersectionWithLines(**kargs)
                i[:, 2] = S.prop[i[:, 2]]
            else:
                raise ValueError("Exact intersectionWithLines not implemented "
                                 f"for {self.elName()} mesh")
        return p, i


    def levelVolumes(self):
        """Return the level volumes of all elements in a Mesh.

        The level volume of an element is defined as:

        - the length of the element if the Mesh is of level 1,
        - the area of the element if the Mesh is of level 2,
        - the (signed) volume of the element if the Mesh is of level 3.

        The level volumes can be computed directly for Meshes of eltypes
        'line2', 'tri3' and 'tet4' and will produce accurate results.
        All other Mesh types are converted to one of these before computing
        the level volumes. Conversion may result in approximation of the
        results. If conversion can not be performed, None is returned.

        If successful, returns an (nelems,) float array with the level
        volumes of the elements.
        Returns None if the Mesh level is 0, or the conversion to the
        level's base element was unsuccessful.

        Note that for level-3 Meshes, negative volumes will be returned
        for elements having a reversed node ordering.
        """
        from pyformex.geomtools import levelVolumes

        base_elem = {
            1: 'line2',
            2: 'tri3',
            3: 'tet4'
        }

        try:
            base = base_elem[self.level()]
        except Exception:
            return None

        if self.elName() == base:
            M = self
        else:
            try:
                M = self.shallowCopy(prop=np.arange(self.nelems())).convert(base)
            except Exception:
                print(f"CONVERSION TO {base} FAILED!")
                return None

        V = levelVolumes(M.coords[M.elems])
        if V is not None and M != self:
            V = at.binsum(V, M.prop, self.nelems())
        return V


    def lengths(self):
        """Return element or perimeter lengths for a Mesh of level 1 or 2.

        Returns
        -------
        array | None
            For a level 1 Mesh, the length of the elements.
            For a level 2 Mesh, the length of the elements' perimeter.
            If the elements or its edges are of eltype 'line2', the lengths are
            exact. For other eltypes, a conversion to 'line2' is done before
            computing the lengths. This can produce an exact result,
            an approximate result or no result (if the conversion fails).
            If successful, returns an (nelems,) float array with the lengths.

            Returns None if the Mesh level is not 1 or 2, or the conversion to
            'line2' does not succeed.

        Examples
        --------
        >>> nx = 4
        >>> M = Mesh(eltype='line2').subdivide(nx)
        >>> a = M.lengths()
        >>> print(a)        # each equals 1. / nx
        [0.25 0.25 0.25 0.25]
        >>> print(a.sum())  # equals 1.
        1.0

        >>> nx, ny = 3, 2
        >>> M = Mesh(eltype='quad4').subdivide(nx, ny)
        >>> a = M.lengths()
        >>> print(a)        # each equals (nx + ny) * 2 / (nx * ny)
        [1.6667 1.6667 1.6667 1.6667 1.6667 1.6667]
        >>> print(a.sum())  # equals (nx + ny) * 2
        10.0...
        """
        if self.level() == 1:
            return self.levelVolumes()
        elif self.level() == 2:
            lens = Mesh(self.coords, self.edges).lengths()
            return lens[self.elem_edges].sum(axis=1)
        else:
            return None


    def areas(self):
        """Return the areas of all elements in a Mesh of level 2 or 3.

        Returns
        -------
        array | None
            For a level 2 Mesh, the area of the elements.
            For a level 3 Mesh, the area of the elements' surface.
            If the elements or its faces are of eltype 'tri3', the areas are
            exact. For other eltypes, a conversion to 'tri3' is done before
            computing the areas. This can produce an exact result,
            an approximate result or no result (if the conversion fails).
            If successful, returns an (nelems,) float array with the areas.

            Returns None if the Mesh level is < 2, or the conversion to
            'tri3' does not succeed.

        Examples
        --------
        >>> nx, ny = 3, 2
        >>> M = Mesh(eltype='quad4').subdivide(nx, ny)
        >>> a = M.areas()
        >>> print(a)        # each equals 1. / (nx * ny)
        [0.1667 0.1667 0.1667 0.1667 0.1667 0.1667]
        >>> print(a.sum())  # equals 1.
        1.0

        >>> nx, ny, nz = 4, 3, 2
        >>> M = Mesh(eltype='hex8').subdivide(nx, ny, nz)
        >>> a = M.areas()
        >>> print(a)        # each equals (nx + ny + nz) * 2 / (nx * ny * nz)
        [0.75 0.75 ...
        >>> print(a.sum())  # equals (nx + ny + nz) * 2
        18.0...
        """
        if self.level() == 2:
            return self.levelVolumes()
        elif self.level() == 3:
            ars = Mesh(self.coords, self.faces).areas()
            return ars[self.elem_faces].sum(axis=1)
        else:
            return None


    def volumes(self):
        """Return the signed volume of the elements in Mesh of level 3.

        Returns
        -------
        array | None
            For a level 3 Mesh, the signed volume of the elements.
            If the elements are of eltype 'tet4', the volumes are exact.
            For other eltypes, a conversion to 'tet4' is done before
            computing the volumes. This can produce an exact result,
            an approximate result or no result (if the conversion fails).
            If successful, returns an (nelems,) float array with the volumes.

            Returns None if the Mesh level is < 3, or the conversion to
            'tri3' does not succeed.

        Examples
        --------
        >>> nx, ny, nz = 2, 2, 1
        >>> M = Mesh(eltype='hex8').subdivide(nx, ny, nz)
        >>> a = M.volumes()
        >>> print(a)        # each equals 1. / (nx * ny * nz)
        [0.25 0.25 0.25 0.25]
        >>> print(a.sum())  # equals 1.
        1.0
        """
        if self.level() == 3:
            return self.levelVolumes()
        else:
            return None


    def length(self):
        """Return the total length of a Mesh.

        Returns
        -------
        float
            For a level 1 Mesh, the sum of all element :meth:`lengths`;
            for a level 2 Mesh, the length of the :meth:`borderMesh`;
            0.0 if :meth:`lengths` returned None.

        Examples
        --------
        >>> Mesh(eltype='line2').subdivide(4).length()
        1.0

        For a level 2 Mesh, note the difference between these three:
        the length of the border, the length of all edges (includes non-border
        edges), the sum of all element perimeters (includes edges multiple
        times).

        >>> M = Mesh(eltype='quad4').subdivide(2,1)
        >>> M.length(), M.edgeMesh().length(), M.lengths().sum()
        (4.0, 5.0, 6.0)
        """
        if self.level() == 2:
            return self.borderMesh().length()
        try:
            return self.lengths().sum()
        except Exception:
            return 0.0


    def area(self):
        """Return the total area of a Mesh.

        Returns
        -------
        float
            For a level 2 Mesh, the sum of all element :meth:`areas`;
            for a level 3 Mesh, the area of the :meth:`borderMesh`;
            0.0 if :meth:`lengths` returned None.

        Examples
        --------
        >>> Mesh(eltype='quad4').subdivide(3,2).area()
        1.0

        For a level 3 Mesh, note the difference between these three:
        the area of the border, the area of all faces (includes non-border
        faces), the sum of all element face areas (includes faces multiple
        times).

        >>> M = Mesh(eltype='hex8').subdivide(4,3,2)
        >>> M.area(), M.faceMesh().area(), M.areas().sum()
        (6.0..., 12.0..., 18.0...)

        """
        if self.level() == 3:
            return self.borderMesh().area()
        try:
            return self.areas().sum()
        except Exception:
            return 0.0


    def volume(self):
        """Return the total volume of a Mesh.

        Returns
        -------
        float
            For a level 3 Mesh, the total volume of all elements
            (see Notes). For a Mesh of level < 3, returns 0.

        Notes
        -----
            The total volume of the Mesh is computed by taking its border
            surface (see :meth:`toSurface`) and computing the volume inside
            that surface. It is equivalent with::

                self.toSurface().volume()

            This is far more efficient than::

                self.volumes().sum().

        Examples
        --------
        >>> nx, ny, nz = 4, 3, 2
        >>> M = Mesh(eltype='hex8').subdivide(nx, ny, nz)
        >>> print(M.volume(), M.volumes().sum())
        1.0... 1.0...
        """
        if self.level() == 3:
            return self.toSurface().volume()
        else:
            return 0.0


    # TODO: there are likely folding schemes that are not fixed by reverse
    def fixVolumes(self):
        """Reverse the elements with negative volume.

        Elements with negative volume may result from incorrect
        local node numbering. This method will reverse all elements
        in a Mesh of dimensionality 3, provided the volumes of these
        elements can be computed.
        """
        return self.reverse(self.volumes() < 0.)
#
# TODO: what with other element types ?
#       can this be generalized to 2D meshes?
#       can the listed numerica data not be found from elements.py?
#

    def scaledJacobian(self, scaled=True, blksize=100000):
        """Compute a quality measure for volume meshes.

        Parameters
        ----------
        scaled: bool
            If False returns the Jacobian at the corners of each
            element. If True, returns a quality metrics, being the
            minimum value of the scaled Jacobian in each element (at one corner,
            the Jacobian divided by the volume of a perfect brick).

        blksize: int
            If > 0 and the number of elements is larger than blksize,
            the Mesh is split in blocks with this number of elements,
            to reduce the memory required in handling large meshes.
            If <= 0, all elements are handled at once.

        Returns
        -------
        todo:
            @DEVS: This needs to be filled in.

        Notes
        -----
        If `scaled` is True each tet or hex element gets a value between
        -1 and 1.
        Acceptable elements have a positive scaled Jacobian. However, good
        quality requires a minimum of 0.2.
        Quadratic meshes are first converted to linear.
        If the mesh contain mainly negative Jacobians, it probably has negative
        volumes and can be fixed with the correctNegativeVolumes.
        """
        eltype = self.eltype
        if eltype.ndim != 3:
            raise ValueError(
                "scaledJacobian is currently only available for 3D elements")

        ne = self.nelems()
        if blksize>0 and ne>blksize:
            slices = at.splitrange(n=self.nelems(), nblk=self.nelems()//blksize)
            return np.concatenate([
                self.select(np.arange(slices[i], slices[i+1])).scaledJacobian(
                    scaled=scaled, blksize=-1) for i in range(len(slices)-1)])
        if self.elName()=='hex20':
            self = self.convert('hex8')
        elif self.elName()=='tet10':
            self = self.convert('tet4')
        if self.elName()=='tet4':
            iacre=np.array([
                [[0, 1], [1, 2], [2, 0], [3, 2]],
                [[0, 2], [1, 0], [2, 1], [3, 1]],
                [[0, 3], [1, 3], [2, 3], [3, 0]],
            ], dtype=int)
            nc = 4
        elif self.elName()=='hex8':
            iacre=np.array([
                [[0, 4], [1, 5], [2, 6], [3, 7], [4, 7], [5, 4], [6, 5], [7, 6]],
                [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4]],
                [[0, 3], [1, 0], [2, 1], [3, 2], [4, 0], [5, 1], [6, 2], [7, 3]],
            ], dtype=int)
            nc = 8
        acre = self.coords[self.elems][:, iacre]
        vacre = acre[:, :, :, 1]-acre[:, :, :, 0]
        cvacre = np.concatenate(vacre, axis=1)
        J = at.vectorTripleProduct(*cvacre).reshape(ne, nc)
        if not scaled:
            return J
        else:
            # volume of 3 normal edges
            normvol = np.prod(at.length(cvacre), axis=0).reshape(ne, nc)
            Jscaled = J/normvol
            return Jscaled.min(axis=1)


    def smooth(self, niter=1, lamb=0.5, *, mu=None,
               border='sep', level=1, exclude=[], weight='uniform',
               data=None, **kargs):
        """Smooth the geometry of a Mesh or data defined over a Mesh.

        Uses Taubin lambda/mu method to smooth the node positions or any
        other float data defined on the nodes of the Mesh. This is a two-step
        iteration method. In the first (smoothing) step, the new nodal values
        are set to a weighted interpolation of the old values and the weighted
        mean values at the neighboring nodes. The relaxation factor lambda
        determines how far the value moves towards the local centroid.
        As this smoothing causes shrinkage of the model, it is followed
        by a compensating scaling (expansion) step, governed by the value mu.
        The more iterations the smoother the result will be, possibly at the
        cost of increased shrinkage. Options are available to tune the
        weights, exclude nodes from smoothing, or separately smooth border
        and inner nodes.

        Parameters
        ----------
        niter: int
            The number of smoothing iterations to be performed.
        lamb: float
            Relaxation factor (0 <= lamb <= 1) for the smoothing step.
            A value 0 keeps the old values, while a value 1 replaces them
            with the (weighted) mean values at the neighbors.
        mu: float
            Relaxation factor for the expansion step (mu < -lambda).
            The value should be negative to undo the shrinkage of the first
            step. If not provided, the default value used is
            ``-lamb / (1.0 - 0.1*lamb)``. The higher the absolute value of
            mu, the more the shrinkage is reduced, and the model may even
            start to expand. If a value of 0.0 is specified, no second
            step is done.
        border: 'sep' | 'fix' | 'incl'
            Specifies how border nodes are handled.
            With 'sep' (default), border nodes are smoothed independently
            from internal nodes. Internal nodes still remain dependent on
            border nodes though.
            With 'fix', border nodes remain in place and do not take part
            in the smoothing.
            With 'incl', border nodes are included in the smoothing process
            just like other nodes.
            For a borderless mesh (like a closed surface), 'sep' and 'incl'
            are obviously the same.
        level: int
            The level of connections between the nodes that will define the
            neighbors in the smoothing process. If an int, nodes are only
            considered neighbors if the belong to the same lower level
            entities: 1 for edges, 2 for faces, 3 for 3D-cells. The default
            uses neigbors by edge. A value 0 will use the highest (element)
            level. For simplex meshes (line2, tri3, tet4) the value makes no
            difference, as all nodes in an element are connected by an edge.
            Using a value different from 1 tends to produce more shrinkage.
            Therefore the default is set to 1 even for non-simplex meshes.
        exclude: list of int
            A list of nodes that should retain their position throughout
            the smoothing process. When using ``border='fix'``, the border
            nodes are automatically added to this list.
        weight: 'uniform' | 'inverse' | 'distance'
            Specifies how the relative weight of the neighboring points is
            calculated. With 'uniform' all neighbor points have the
            same weight. With 'distance', neighbor points have a
            weight proportional to their distance to the point to
            be moved. With 'inverse', the weight is proportional to
            the inverse of the distances. Prepending 'sq' to 'inverse'
            or  'distance' will make the weights proportional to the
            square (inverse) distances.
        data: :term:`array_like`
            An array of floating point data defined at the nodes. The first
            dimension of the array should be equal to the number of nodes.
            If data is provided, returns the smoothed data instead of a
            Mesh with smoothed geometry.

        Returns
        -------
        :Mesh | array
            If no data was provided, returns a smoothed Mesh with otherwise
            same characteristics. If data was provided, returns an array
            of the same shape containing the smoothed data.

        Notes
        -----
        For the smoothing algorithm, see Taubin, Curve and Surface
        Smoothing without Shrinkage, ICCV 1995.

        The default ``border='sep'`` works well in most cases. For models
        with a border, shrinkage is prominent near the border and the
        setting helps in reducing it. For models without a border, there
        is no difference between 'sep' and 'incl'.

        The weights are currently only computed once before starting the
        smoothing iterations. As a result, there is a difference between
        using a single smooth with niter iterations and using niter
        successive smooths with a single iteration.
        This behavior may be changed in future.
        """
        # TODO: add a ring parameter that specifies the depth of connections
        # to include in the neighbors

        if kargs:
            # Probably using old API?
            utils.warn("The Mesh.smooth and TrisSurface.smooth methods have"
                       " changed. Consult the docs for the new API")

        if mu is None:
            k = 0.1
            mu = -lamb/(1.-k*lamb)
        # compute adjaceny table
        adj = self.adjacency(kind='n', level=level)
        # identify movable nodes
        incl = np.full((self.ncoords(),), True)
        if exclude:
            incl[exclude] = False
        if border== 'fix':
            incl[self.getBorderNodes()] = False
        elif border == 'sep':
            bordernodes = self.getBorderNodes()
            a = adj[bordernodes].ravel()
            internal = at.complement(bordernodes, self.ncoords())
            a[at.findFirst(internal, a) != -1] = -2
            adj[bordernodes] = a.reshape(adj[bordernodes].shape)
        # compute weigths
        w = np.ones(adj.shape, dtype=at.Float)
        if weight[-7:] == 'inverse':
            dist = at.length(self.coords[adj]-self.coords.reshape(-1, 1, 3))
            w[dist!=0] /= dist[dist!=0]
        elif weight == 'distance':
            w = at.length(self.coords[adj]-self.coords.reshape(-1, 1, 3))
        if weight[:2] == 'sq':
            w = w*w
        w[adj<0] = 0.
        w /= w.sum(axis=-1).reshape(-1, 1)
        w = w[..., np.newaxis]
        # make a copy of original data, because we change in-place
        if data is None:
            x = self.coords.copy()
        else:
            if data.shape[0] != self.coords.shape[0]:
                raise ValueError('data should have same length as coords')
            x = data.copy()
        # perform smoothing iterations
        for i in range(niter):
            x[incl] = (1.-lamb)*x[incl] + lamb*(w[incl] *x[adj][incl]).sum(1)
            if mu != 0.0:
                x[incl] = (1.-mu)*x[incl] + mu*(w[incl] *x[adj][incl]).sum(1)
        if data is None:
            return self.__class__(x, self.elems, prop=self.prop,
                                  eltype=self.eltype)
        else:
            return x


    ##########################################
    ## Deprecated ##


    @utils.deprecated_by('Mesh.nodalToElement', 'Field.convert')
    def nodalToElement(self, val):
        return val[self.elems].mean(axis=1)


    @utils.deprecated_by('Mesh.getLowerEntitiesSelector', 'Element.getEntities')
    def getLowerEntitiesSelector(self, level=-1):
        return self.eltype.getEntities(level)


    ##########################################
    ## Allow drawing ##


    def actor(self, **kargs):

        if self.nelems() == 0:
            return None

        from pyformex.opengl.actors import Actor
        return Actor(self, **kargs)


    ###################
    ## PZF interface ##

    def pzf_dict(self):
        kargs = Geometry.pzf_dict(self)
        kargs['elems'] = self.elems
        kargs[f"eltype:s__{self.elName()}"] = None
        return kargs

######################## Functions #####################


def mergeNodes(nodes, fuse=True, **kargs):
    """Merge a list of Coords into a single one.

    Merging the Coords creates a single Coords object containing all points,
    and the indices to find the points of the original Coords in the
    merged set.

    Parameters
    ----------
    nodes: list of Coords
        A list of Coords objects, all having the same shape, except
        possibly for their first dimension.
    fuse: bool, optional
        If True (default), coincident (or very close) points are fused
        into a single point. If False, a simple concatenation will result.
    **kargs:
        Keyword arguments that are passed to the fuse operation.

    Returns
    -------
    coords: Coords
        A single Coords with the coordinates of all (unique) points.
    index: list of int arrays
        A list of indices giving for each Coords in the input list the position
        of its nodes in the merged output Coords.

    Examples
    --------
    >>> M1 = Mesh(eltype='quad4')
    >>> M1.coords
    Coords([[0.,  0.,  0.],
            [1.,  0.,  0.],
            [1.,  1.,  0.],
            [0.,  1.,  0.]])
    >>> M2 = Mesh(eltype='tri3').rot(90)
    >>> M2.coords
    Coords([[ 0.,  0.,  0.],
            [ 0.,  1.,  0.],
            [-1.,  0.,  0.]])
    >>> coords, index = mergeNodes([M1.coords, M2.coords])
    >>> print(coords)
    [[-1.  0.  0.]
     [ 0.  0.  0.]
     [ 0.  1.  0.]
     [ 1.  0.  0.]
     [ 1.  1.  0.]]
    >>> print(index)
    [array([1, 3, 4, 2]), array([1, 2, 0])]
    """
    coords = Coords(np.concatenate([x for x in nodes], axis=0))
    if fuse:
        coords, index = coords.fuse(**kargs)
    else:
        index = np.arange(coords.shape[0])
    n = np.array([0] + [x.npoints() for x in nodes]).cumsum()
    ind = [index[f:t] for f, t in zip(n[:-1], n[1:])]
    return coords, ind


def mergeMeshes(meshes, fuse=True, **kargs):
    """Merge a list of Meshes to a single list of nodes.

    Parameters
    ----------
    meshes: list of Mesh instances
        The Meshes to be merged.
    fuse: bool
        If True (default), coinciding nodes will be fused to single nodes.
        If set False, all original nodes are retained, only renumbered.
    **kargs: other parameters to pass to the :meth:`mergeNodes` method.

    Returns
    -------
    coords: Coords
        The single list of nodal coordinates obtained from merging the Meshes.
    elems: list of Elems
        A list of Elems instances corresponding to those of the input Meshes,
        but with numbers referring to the new (single) coords array.

    Notes
    -----
    This method cleverly detects if the input Meshes use the same
    coords block, and will not concatenate and fuse these. The fuse parameter
    still might change the single coords. If you want to make sure that the
    coords remains unaltered, either fuse the Meshes in advance, or use the
    fuse=False argument. See Examples in :meth:`Mesh.concatenate`.

    """
    # First check if Meshes are using same coords block
    ids = [id(m.coords) for m in meshes]
    uniq, ind = np.unique(ids, return_index=True)
    elems = [m.elems for m in meshes]
    if len(uniq) == 1:
        # A single coords block is used: the elems use same node numbers
        coords = meshes[0].coords
        if fuse:
            # fuse the single coords block
            coords, index = coords.fuse(**kargs)
            return coords, [Elems(index[e], eltype=e.eltype) for e in elems]
        else:
            # Return coords, elems as is
            return coords, elems

    # general case: the elems use different node numbers
    coords = [m.coords for m in meshes]
    coords, index = mergeNodes(coords, fuse, **kargs)
    return coords, [Elems(i[e], eltype=e.eltype) for i, e in zip(index, elems)]


def quadgrid(seed0, seed1, roll=0):
    """Create a quadrilateral mesh of unit size with the specified seeds.

    Parameters
    ----------
    seed0: :term:`seed`
        Seed for the elements along the parametric direction 0.
    seed1: :term:`seed`
        Seed for the elements along the parametric direction 1.
    roll: int, optional
        If provided, the set of axis direction are rolled this number of
        positions, allowing the quadgrid to be created in the (x,y), (y,z)
        or (z,x) plane.

    Returns
    -------
    Mesh
        A Mesh of Quad4 elements filling a unit square between the values
        0 and 1 in the two parametric directions (default x,y).
        The node and element numbers vary first in the direction0, then in the
        direction 1.
    """
    from pyformex.elements import Quad4
    seed0 = at.smartSeed(seed0)
    seed1 = at.smartSeed(seed1)
    wts = at.gridpoints(seed0, seed1)
    n0 = len(seed0)-1
    n1 = len(seed1)-1
    E = Mesh(eltype='quad4')
    if roll:
        E = E.rollAxes(roll)
    X = E.coords.reshape(-1, 4, 3)
    U = np.dot(wts, X).transpose([1, 0, 2]).reshape(-1, 3)
    els = Quad4.els(n0, n1)
    e = np.concatenate([els+i*wts.shape[0] for i in range(E.nelems())])
    M = Mesh(U, e, eltype=E.eltype)
    return M.fuse()


def rectangle(L=1., W=1., nl=1, nw=1):
    """Create a plane rectangular mesh of quad4 elements.

    Parameters
    ----------
    L: float
        The length of the rectangle.
    W: float
        The width of the rectangle.
    nl: :term:`seed`
        The element seed along the length.
    nw: :term:`seed`
        The element seed along the width.

    Returns
    -------
    Mesh
        A Mesh of eltype Quad4 representing a rectangular domain.

    Notes
    -----
        This is syntactical sugar for::

            quadgrid(nl, nw).resized([L, W, 1.0])
    """
    return quadgrid(nl, nw).resized([L, W, 1.0])


def rectangleWithHole(L, W, r, nr, nl, nw=None):
    """Create a Mesh of quarter of a rectangle with a central circular hole.

    Parameters
    ----------
    L: float
        Length of the (quarter) rectangle.
    W: float
        Width of the (quarter) rectangle.
    r: float
        Radius of the hole.
    nr: :term:`seed`
        The element seed in radial direction.
    nl: :term:`seed`
        The element seed in tangential direction along L.
    nw: :term:`seed`, optional
        The element seed in tangential direction along W.
        If not provided, it is set equal to `nl`.

    Returns
    -------
    Mesh
        A Mesh of eltype Quad4 representing a quarter of a rectangular
        domain with a central hole.
    """
    from pyformex.elements import Quad9
    if nw is None:
        nw = nl
    base = Quad9.vertices.scale([L, W, 1.])
    F0 = Formex([[[r, 0., 0.]]]).rosette(5, 90./4)
    F2 = Formex([[[L, 0.]], [[L, W/2.]], [[L, W]], [[L/2., W]], [[0., W]]])
    F1 = F0.interpolate(F2, div=[0.5])
    FL = [F0, F1, F2]
    X0, X1, X2 = [F.coords.reshape(-1, 3) for F in FL]
    trf0 = Coords([X0[0], X2[0], X2[2], X0[2], X1[0], X2[1], X1[2], X0[1], X1[1]])
    trf1 = Coords([X0[2], X2[2], X2[4], X0[4], X1[2], X2[3], X1[4], X0[3], X1[3]])

    seedr = at.smartSeed(nr)
    seedl = at.smartSeed(nl)
    seedw = at.smartSeed(nw)
    gridl = quadgrid(seedr, seedl).resized([L, W, 1.0])
    gridw = quadgrid(seedr, seedw).resized([L, W, 1.0])

    gridl = gridl.isopar('quad9', trf0, base)
    gridw = gridw.isopar('quad9', trf1, base)
    return (gridl+gridw).fuse()


def quadrilateral(x, n1, n2):
    """Create a quadrilateral mesh.

    Parameters
    ----------
    x: Coords(4,3)
        The four corners of the mesh, in anti-clockwise order.
    n1: int
        The number of elements along the sides x0-x1 and x2-x3.
    n2: int
        The number of elements along the sides x1-x2 and x3-x4.

    Returns
    -------
    Mesh
        A Mesh of quads filling the quadrilateral defined  by the four
        points `x`.
    """
    from pyformex.elements import Quad4
    x = at.checkArray(x, (4, 3), 'f')
    M = rectangle(1., 1., n1, n2).isopar('quad4', x, Quad4.vertices)
    return M


def continuousCurves(c0, c1):
    """Make two curves continuous.

    Ensures that the end point of curve c0 and the start point of curve c1
    are coincident.

    Parameters
    ----------
    c0: :class:`Curve`
        First Curve.
    c1: :class:`Curve`
        Second Curve.

    Note
    ----
    This is done by replacing these two points with their mean value.
    If the points are originally far apart, the curves may change shape
    considerably.

    The curves are changed inplace! There is no return value.
    """
    c0.coords[-1] = c1.coords[0] = 0.5 * (c0.coords[-1] + c1.coords[0])


def triangleQuadMesh(P0, C0, n, P0wgt=0.0):
    """Create a quad Mesh over a (quasi-)triangular domain.

    The domain is described by a point and a curve. The point is
    connected with straight lines to the curve end points. The result
    is a quasi-triangular domain with possibly one non-straight edge.
    For example, a circular sector is defined by a circular arc and the
    center of the circle.

    Parameters
    ----------
    P0: :term:`coords_like` (3,)
        The coordinates of the point connecting two straight edges.
    C0: :class:`Curve`
        A Curve defining the edge of the domain opposite to the point P0.
        Use a :class:`Line` ([P1, P2]) to create a triangular domain
        (P0, P1,P2).
    n: tuple of 3 ints
        Specifies the number of elements along the subdomain edges.
        Near the point is a quad kernel with n0*n1 elements (n0 along the
        straight line to the startpoint of the curve, n1 along the straight
        line to the endpoint of the curve.
        The boundary zone near the curve has n0+n1 elements along the curve,
        and n2 elements perpendicular to the curve.
    """
    from pyformex.curve import PolyLine
    # Make sure we have PolyLines
    P0 = Coords(P0)
    C = [
        PolyLine([P0, C0.coords[0]]),
        C0.approx(),
        PolyLine([C0.coords[-1], P0]),
    ]
    # Make sure the end points are connected
    (continuousCurves(C[i], C[(i+1) % 3]) for i in range(3))
    # Number of divisions along each side
    n = np.array(n)
    nt = np.array([n[0]+n[2], n[1]+n[0], n[2]+n[1]])
    # Divide the three sides
    C = [C[i].approx(nseg=nt[i], equidistant=True) for i in range(3)]
    # Split the curves in two parts
    C = [C[i].split(n[i]) for i in range(3)]
    # Create the center point
    P1 = Coords.concatenate([Ci[1].coords[0] for Ci in C]).mean(axis=0)
    if P0wgt != 0.0:
        P1 = (3.*P1 + P0wgt*P0) / (3.+P0wgt)
    # Create the central PolyLines
    D = [PolyLine([C[i][1].coords[0], P1]).approx(
        nseg=n[(i+1) % 3], equidistant=True) for i in range(3)]
    # Create the submeshes
    M = [Ci.toMesh().connect(Di.toMesh(), div=ni) for Ci, Di, ni in [
        (C[0][0], D[2], n[1]),
        (C[1][0], D[0], n[2]),
        (C[1][1], D[2].reverse(), n[2]),
    ]]
    # Concatenate Meshes
    return Mesh.concatenate(M)


# This is retained for convenience.
def quarterCircle(n1, n2):
    """Create a mesh of quadrilaterals filling a quarter circle.

    Parameters
    ----------
    n1: int
        Number of elements along the edges 01 and 23
    n2: int
        Number of elements along the edges 12 and 30

    Returns
    -------
    Mesh
       A 'quad4' Mesh filling a quarter circle with radius 1 and
       center at the origin, in the first quadrant of the axes.

    Notes
    -----
    The quarter circle mesh has a kernel of n1*n1 cells, and two
    border meshes of n1*n2 cells. The resulting mesh has n1+n2 cells
    in radial direction and 2*n1 cells in tangential direction (in the
    border mesh).
    """
    from pyformex.curve import Arc
    A = Arc(angles=(0, 90))
    return triangleQuadMesh(A.center, A, n=(n1, n1, n2), P0wgt=0.4)


def wedge6_roll(elems):
    """Roll wedge6 elems to make the lowest node of bottom plane the first

    This is a helper function for the :meth:`wedge6_tet4` conversion.
    """
    elems = elems.reshape(-1, 2, 3)
    r = elems[:, 0, :].argmin(axis=-1)
    elemsout = []
    for i in range(3):
        w = np.where(r==i)[0]
        if len(w) > 0:
            els = np.roll(elems[w], -i, axis=-1)
            elemsout.append(els)
    elems = np.concatenate(elemsout)
    return Connectivity(elems.reshape(-1, 6), eltype='wedge6')


def wedge6_tet4(M):
    """Convert a Mesh from wedge6 to tet4

    Converts a 'wedge6' Mesh to 'tet4', by replacing each wedge
    element with three tets. The conversion ensures that the subdivisions
    of the wedge elements are compatible in the common quad faces of
    any two wedge elements.

    Note
    ----
    This is a helper function for the :meth:`convert` method. It is
    better to use Mesh.convert('tet4') instead of calling this function
    directly.

    Parameters
    ----------
    M: Mesh
        A Mesh of eltype 'wedge6'.

    Returns
    -------
    Mesh
        A Mesh of eltype 'tet4' representing the same domain as the
        input Mesh. The nodes are the same as those of the input Mesh.
        The number of elements is three times that of the input Mesh.
        The order of numbering of the elements is dependent on the
        conversion algorithm.
    """
    from pyformex.elements import Wedge6

    # First roll to put lowest node first
    elems = wedge6_roll(M.elems)
    M = Mesh(M.coords, elems, eltype='wedge6', prop=M.prop)

    # Now convert to tet4
    sl, sr = [Wedge6.conversions[c][0][1] for c in ['tet4-3l', 'tet4-3r']]
    elems = M.elems.reshape(-1, 2, 3)
    wl = np.where(elems[:, 0, 1] < elems[:, 0, 2])[0]
    wr = at.complement(wl, elems.shape[0])
    Ml = M.select(wl).selectNodes(sl, 'tet4')
    Mr = M.select(wr).selectNodes(sr, 'tet4')
    return Ml+Mr

# Some functions to help fixing badly connected quad surfaces.

def quad4_checkFolded(self):
    """Check which quads are folded. Returns two sets for different unfold."""
    from pyformex import geomtools as gt
    normals = gt.polygonNormals(self.coords[self.elems])
    p = at.projection(normals[:, 0], normals[:, 1])
    q = at.projection(normals[:, 0], normals[:, 3])
    return at.where_1d(p < 0.), at.where_1d(q < 0.)

def quad4_unFold(self, ids, jds):
    """Unfold quad elements: ids switch node 1,2; jds switch node 2,3"""
    self.elems[ids, 1:3] = self.elems[ids, 2:0:-1]
    self.elems[jds, 2:4] = self.elems[jds, 3:1:-1]

def quad4_checkNormals(self):
    """Find out which elements have reversed surface orientation"""
    from pyformex.trisurface import TriSurface
    t0 = TriSurface(self.convert('tri3'))
    t1 = t0.fixNormals_internal()[0]
    return (t0.elems[range(0, t0.nelems(), 2)] !=
            t1.elems[range(0, t1.nelems(), 2)]).any(axis=1)

def quad4_fixNormals(self, ids):
    """Fixes orientation of some quad4 surface elements"""
    return self.reverse(sel=ids, inplace=True)

def quad4_fixSurface(self):
    """Do all fixes inplace"""
    if self.elName() != 'quad4':
        raise ValueError("fixSurface is currently only available for Quad4 Mesh")
    quad4_unFold(self, *quad4_checkFolded(self))
    quad4_fixNormals(self, quad4_checkNormals(self))


# End
