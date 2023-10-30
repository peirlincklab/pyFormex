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
"""Formex algebra in Python

This module defines the :class:`Formex` class, which is one of the two
major classes for representing geometry in pyFormex (the other one being
:class:`~mesh.Mesh`). The Formex class represents geometry as a simple
3-dim :class`~coords.Coords` array.
This allows an implementation of most functionality
of Formex algebra with a consistent and easy to use syntax.
"""
import numpy as np

from pyformex import utils
from pyformex import arraytools as at
from pyformex import geomtools
from pyformex.coords import Coords, fpattern, origin  # noqa: F401
from pyformex.geometry import Geometry
from pyformex.olist import List

__all__ = ['Formex', 'connect']


###########################################################################
##
##   Formex class
##
#########################

@utils.pzf_register
class Formex(Geometry):
    """A structured collection of points in 3D space.

    A Formex is a collection of points in a 3D cartesian space.
    The collection is structured into a set of elements all having the
    same number of points (e.g. a collection triangles all having three
    points).

    As the Formex class is derived from :class:`~geometry.Geometry`,
    a Formex object has a :attr:`coords` attribute which is a
    :class:`~coords.Coords` object. In a Formex this is always an
    array with 3 axes (numbered 0,1,2).
    Each scalar element of this array represents a coordinate.
    A row along the last axis (2) is a set of 3 coordinates and represents
    a point (aka. node, vertex).

    For simplicity's sake, the current implementation only deals with points
    in a 3-dimensional space. This means that the length of axis 2 always
    equals 3.
    The user can create Formices (plural of Formex) in a 2-D space, but
    internally these will be stored with 3 coordinates, by adding a third
    value 0. All operations work with 3-D coordinate sets. However, it is
    easy to extract only a limited set of coordinates from the results,
    permitting to return to a 2-D environment

    A plane of the array along the axes 2 and 1 is a set of points:
    we call this an element.
    This can be thought of as a geometrical shape (2 points form a line segment,
    3 points make a triangle, ...) or as an element in Finite Element terms.
    But it really is up to the user as to how this set of points is to be
    interpreted. He can set an element type on the Formex to make this clear
    (see below).

    The whole Formex then represents a collection of such elements.
    The Formex concept and layout is made more clear in
    :ref:`sec:formex` in the :doc:`../tutorial`.

    Additionally, a Formex may have a property set, which is an 1-D array of
    integers. The length of the array is equal to the length of axis 0 of the
    Formex data (i.e. the number of elements in the Formex). Thus, a single
    integer value may be attributed to each element. It is up to the user to
    define the use of this integer (e.g. it could be an index in a table of
    element property records).
    If a property set is defined, it will be copied together with the Formex
    data whenever copies of the Formex (or parts thereof) are made.
    Properties can be specified at creation time, and they can be set,
    modified or deleted at any time. Of course, the properties that are
    copied in an operation are those that exist at the time of performing
    the operation.

    Finally, a Formex object can have an element type, because plexitude
    alone does not uniquely define what the geometric entities are, and how
    they should be rendered. By default, pyFormex will render plex-1 as
    points, plex-2 as line segments, plex-3 as triangles and any higher
    plexitude as polygons. But the user could e.g. set
    ``eltype = 'tet4'`` on a plex-4 Formex, and then that would be rendered
    as tetraeders.


    Parameters
    ----------
    data: Formex, Coords, :term:`array_like` or string
        Data to initialize the coordinates attribute ``coords`` in the Formex.
        See more details below.
    prop: int :term:`array_like`, optional
        1-dim int array with non-negative element property numbers.
        If provided, :meth:`setProp` will be called to assign the
        specified properties.
    eltype: str | :class:`~elements.ElementType`, optional
        The element type of the geometric entities (elements).
        If provided, it should be an :class:`~elements.ElementType`
        instance or the name of such an instance.
        If not provided, the pyFormex default is used when needed and is
        based on the plexitude: 1 = point, 2 = line segment,
        3 = triangle, 4 or more is a polygon.


    The Formex coordinate data can be initialized by another :class:`Formex`,
    by a :class:`Coords`, by a 1D, 2D or 3D :term:`array_like`, or by a string
    that will be passed to :func:`coords.fpattern` to generate the
    coordinates.
    If 2D coordinates are given, a 3-rd coordinate 0.0 is added.
    Internally, Formices always work with 3D coordinates.
    Thus::

      F = Formex([[[1,0],[0,1]],[[0,1],[1,2]]])

    creates a Formex with two elements, each having 2 points in the global
    z-plane. The innermost level of brackets group the coordinates of a
    point, the next level groups the points in an element, and the outermost
    brackets group all the elements of the Formex.
    Because the coordinates are stored in an array with 3 axes,
    all the elements in a Formex must contain the same number of points.
    This number is called the plexitude of the Formex.

    A Formex may be initialized with a string instead of the numerical
    coordinate data. The string is passed to :func:`coords.fpattern` to
    generate the coordinates.
    The following are two equivalent definitions of (the circumference of)
    a triangle::

      F = Formex('2:010207')
      G = Formex('l:127')

    Because the :class:`Formex` class is derived from
    :class:`~geometry.Geometry`, it has the following attributes:

    - :attr:`~geometry.Geometry.coords`,
    - :attr:`~geometry.Geometry.prop`,
    - :attr:`~geometry.Geometry.attrib`,
    - :attr:`~geometry.Geometry.fields`.

    Furthermore it has the following properties and methods that are applied
    on the :attr:`~geometry.Geometry.coords` attribute.

    - :attr:`~geometry.Geometry.xyz`,
    - :attr:`~geometry.Geometry.x`,
    - :attr:`~geometry.Geometry.y`,
    - :attr:`~geometry.Geometry.z`,
    - :attr:`~geometry.Geometry.xy`,
    - :attr:`~geometry.Geometry.yz`,
    - :attr:`~geometry.Geometry.xz`,
    - :meth:`~geometry.Geometry.points`,
    - :meth:`~geometry.Geometry.bbox`,
    - :meth:`~geometry.Geometry.center`,
    - :meth:`~geometry.Geometry.bboxPoint`,
    - :meth:`~geometry.Geometry.centroid`,
    - :meth:`~geometry.Geometry.sizes`,
    - :meth:`~geometry.Geometry.dsize`,
    - :meth:`~geometry.Geometry.bsphere`,
    - :meth:`~geometry.Geometry.bboxes`,
    - :meth:`~geometry.Geometry.inertia`,
    - :meth:`~geometry.Geometry.principalCS`,
    - :meth:`~geometry.Geometry.principalSizes`,
    - :meth:`~geometry.Geometry.distanceFromPlane`,
    - :meth:`~geometry.Geometry.distanceFromLine`,
    - :meth:`~geometry.Geometry.distanceFromPoint`,
    - :meth:`~geometry.Geometry.directionalSize`,
    - :meth:`~geometry.Geometry.directionalWidth`,
    - :meth:`~geometry.Geometry.directionalExtremes`.

    Also, the following Coords transformation methods can be
    directly applied to a :class:`Formex` object.
    The return value is a new Formex identical to the original,
    except for the coordinates,
    which are transformed by the specified method.
    Refer to the corresponding :class:`~coords.Coords` method
    for the usage of these methods:

    - :meth:`~geometry.Geometry.scale`,
    - :meth:`~geometry.Geometry.adjust`,
    - :meth:`~geometry.Geometry.translate`,
    - :meth:`~geometry.Geometry.centered`,
    - :meth:`~geometry.Geometry.align`,
    - :meth:`~geometry.Geometry.rotate`,
    - :meth:`~geometry.Geometry.shear`,
    - :meth:`~geometry.Geometry.reflect`,
    - :meth:`~geometry.Geometry.affine`,
    - :meth:`~geometry.Geometry.toCS`,
    - :meth:`~geometry.Geometry.fromCS`,
    - :meth:`~geometry.Geometry.transformCS`,
    - :meth:`~geometry.Geometry.position`,
    - :meth:`~geometry.Geometry.cylindrical`,
    - :meth:`~geometry.Geometry.hyperCylindrical`,
    - :meth:`~geometry.Geometry.toCylindrical`,
    - :meth:`~geometry.Geometry.spherical`,
    - :meth:`~geometry.Geometry.superSpherical`,
    - :meth:`~geometry.Geometry.toSpherical`,
    - :meth:`~geometry.Geometry.bump`,
    - :meth:`~geometry.Geometry.flare`,
    - :meth:`~geometry.Geometry.map`,
    - :meth:`~geometry.Geometry.map1`,
    - :meth:`~geometry.Geometry.mapd`,
    - :meth:`~geometry.Geometry.copyAxes`,
    - :meth:`~geometry.Geometry.swapAxes`,
    - :meth:`~geometry.Geometry.rollAxes`,
    - :meth:`~geometry.Geometry.projectOnPlane`,
    - :meth:`~geometry.Geometry.projectOnSphere`,
    - :meth:`~geometry.Geometry.projectOnCylinder`,
    - :meth:`~geometry.Geometry.isopar`,
    - :meth:`~geometry.Geometry.addNoise`,
    - :meth:`~geometry.Geometry.rot`,
    - :meth:`~geometry.Geometry.trl`.

    Examples
    --------
    >>> Formex.__str__ = Formex.asFormex
    >>> print(Formex([[0,1],[2,3]]))
    {[0.0,1.0,0.0], [2.0,3.0,0.0]}
    >>> print(Formex('1:0123'))
    {[0.0,0.0,0.0], [1.0,0.0,0.0], [1.0,1.0,0.0], [0.0,1.0,0.0]}
    >>> print(Formex('4:0123'))
    {[0.0,0.0,0.0; 1.0,0.0,0.0; 1.0,1.0,0.0; 0.0,1.0,0.0]}
    >>> print(Formex('2:0123'))
    {[0.0,0.0,0.0; 1.0,0.0,0.0], [1.0,1.0,0.0; 0.0,1.0,0.0]}
    >>> F = Formex('l:1234')
    >>> print(F)
    {[0.0,0.0,0.0; 1.0,0.0,0.0], [1.0,0.0,0.0; 1.0,1.0,0.0], \
    [1.0,1.0,0.0; 0.0,1.0,0.0], [0.0,1.0,0.0; 0.0,0.0,0.0]}
    >>> print(F.info())
    shape    = (4, 2, 3)
    bbox[lo] = [0.  0.  0.]
    bbox[hi] = [1.  1.  0.]
    center   = [0.5  0.5  0. ]
    maxprop  = -1
    <BLANKLINE>
    >>> F.nelems()
    4
    >>> F.level()
    1
    >>> F.x
    array([[0.,  1.],
           [1.,  1.],
           [1.,  0.],
           [0.,  0.]])
    >>> F.center()
    Coords([0.5,  0.5,  0. ])
    >>> F.bboxPoint('+++')
    Coords([1.,  1.,  0.])


    The Formex class defines the following attributes above the ones
    inherited from Geometry:

    Attributes
    ----------
    eltype: None or :class:`~elements.ElementType`

    """

    _special_members_ = ['__add__']
    _exclude_members_ = ['nnodes', 'append', 'actor']

    fieldtypes = ['elemc', 'elemn']

    #######################################################################
    #
    #   Create a new Formex
    #

    def __init__(self, data=None, prop=None, eltype=None):
        """Create a new Formex."""
        Geometry.__init__(self)
        if isinstance(data, Formex):
            coords = data.coords
            if prop is None:
                prop = data.prop
            if eltype is None:
                eltype = data.eltype
        elif isinstance(data, str):
            coords = fpattern(data)
        elif data is None:
            coords = Coords().reshape(0, 1, 3)
        else:
            coords = Coords(data)
            assert coords.shape[-1] == 3
            # check dimensionsionality of data
            if coords.ndim != 3:
                if coords.ndim in (1,2):
                    # expand to 3-d
                    coords = coords.reshape(-1, 1, 3)
                else:
                    raise ValueError(
                        f"Formex init: needs a 1-, 2- or 3-dim. data array, "
                        f"got shape {coords.shape}")

        self.coords = coords
        self.setProp(prop)
        if utils.isString(eltype):
            self.eltype = eltype.lower()
        else:
            if eltype is not None:
                utils.warn("warn_formex_eltype")
            self.eltype = None

    def _set_coords(self, coords):
        """Replace the current coords with new ones.

        """
        coords = Coords(coords)
        if coords.shape == self.coords.shape:
            F = Formex(coords, self.prop, self.eltype)
            F.attrib(**self.attrib)
            return F
        else:
            raise ValueError("Invalid reinitialization of Formex coords")

    def __getitem__(self, i):
        """Return element i of the Formex.

        This allows addressing element i of Formex F as F[i].
        """
        return self.coords[i]

    def __setitem__(self, i, val):
        """Change element i of the Formex.

        This allows writing expressions as F[i] = [[1,2,3]].
        """
        self.coords[i] = val

    def __setstate__(self, state):
        """Set the object from serialized state.

        This allows to read back old pyFormex Project files where the Formex
        class had 'f' and 'p' attributes.
        """
        if 'p' in state:
            state['prop'] = state['p']
            del state['p']
        if 'f' in state:
            state['coords'] = state['f']
            del state['f']
        self.__dict__.update(state)

    #######################################################################
    #
    #   Return information about a Formex
    #
    #################

    @property  # Use a property for analogy with ndarray.shape
    def shape(self):
        """Return the shape of the Formex.

        The shape of a Formex is the shape of its coords array.

        Returns
        -------
        tuple of ints
            A tuple (nelems, nplex, ndim).

        Examples
        --------
        >>> Formex('l:1234').shape
        (4, 2, 3)
        >>> Formex('1:1234').shape
        (4, 1, 3)
        """
        return self.coords.shape

    def nelems(self):
        """Return the number of elements of the :class:`Formex`.

        The number of elements is the length of the first axis of the
        ``coords`` array.

        Returns
        -------
        int
            The number of elements in the Formex

        Examples
        --------
        >>> Formex('l:1234').nelems()
        4
        """
        return self.coords.shape[0]

    __len__ = nelems  # implements len(Formex)

    def nplex(self):
        """Return the plexitude of the :class:`Formex`.

        The plexitude is the number of points per element. This is
        the length of the second axis of the coords array.

        Examples:

        1. unconnected points,
        2. straight line elements,
        3. triangles or quadratic line elements,
        4. tetraeders or quadrilaterals or cubic line elements.

        Returns
        -------
        int
            The plexitude of the elements in the Formex

        Examples
        --------
        >>> Formex('l:1234').nplex()
        2
        """
        return self.coords.shape[1]

    def npoints(self):
        """Return the number of points in the Formex.

        This is the product of the number of elements in the Formex
        with the plexitude of the elements.

        Returns
        -------
        int
            The total number of points in the Formex

        Notes
        -----
        ``ncoords`` is an alias for ``npoints``

        Examples
        --------
        >>> Formex('l:1234').npoints()
        8

        """
        return self.coords.shape[0]*self.coords.shape[1]

    ncoords = npoints

    def elType(self):
        """Return the element type of the Formex.

        Returns
        -------
        :class:`~elements.ElementType` or None
            If an element type was defined for the Formex, returns
            the corresponding ElementType; else returns None.

        See Also
        --------
        elName: Return the name of the ElementType

        Examples
        --------
        >>> Formex('l:1234').elType()
        >>> Formex('l:1234',eltype='line2').elType()
        Line2

        """
        from pyformex.elements import ElementType
        if self.eltype is not None:
            return ElementType.get(self.eltype, self.nplex())
        else:
            return None

    def elName(self):
        """Return the element name of the Formex.

        Returns
        -------
        str or None
            If an element type was defined for the Formex, returns
            the name of the ElementType ; else returns None.

        See Also
        --------
        elType: Return the ElementType

        Examples
        --------
        >>> Formex('l:1234').elName()
        >>> Formex('l:1234',eltype='line2').elName()
        'line2'
        """
        et = self.elType()
        if et:
            return et.lname
        else:
            return None

    def level(self):
        """Return the level (dimensionality) of the Formex.

        The level or dimensionality of a geometrical object is the minimum
        number of parametric directions required to describe the object.
        Thus we have the following values:

        0: points
        1: lines
        2: surfaces
        3: volumes

        If the Formex has an 'eltype' set, the value is determined from
        the Element database. Else, the value is equal to the plexitude minus
        one for plexitudes up to 3, and equal to 2 for any higher plexitude
        (since the default is to interprete a higher plexitude as a polygon).

        Returns
        -------
        int
            An int 0..3 giving the number of parametric dimensions of the
            geometric entities in the Formex.

        Examples
        --------
        >>> Formex('1:123').level()
        0
        >>> Formex('l:123').level()
        1
        >>> Formex('3:123').level()
        2
        >>> Formex('3:123',eltype='line3').level()
        1

        """
        et = self.elType()
        if et:
            return et.ndim
        else:
            if self.nplex() > 2:
                return 2
            else:
                return self.nplex()-1

    # TODO: This should be deprecated.
    def view(self):
        """Return the Formex coordinates as a numpy array (ndarray).

        Returns a view to the Coords array as an ndarray. The use of
        this method is deprecated: use the :attr:`xyz` property
        instead.
        """
        return self.coords.view()

    def element(self, i):
        """Return element i of the Formex.

        Parameters
        ----------
        i: int
            The index of the element to return.

        Returns
        -------
        Coords object
            A Coords with shape (self.nplex(), 3)

        Examples
        --------
        >>> Formex('l:12').element(0)
        Coords([[0.,  0.,  0.],
            [1.,  0.,  0.]])
        >>> Formex('l:12').select(0)
        Formex([[[0.,  0.,  0.],
                 [1.,  0.,  0.]]])
        """
        return self.coords[i]

    def point(self, i, j):
        """Return point j of element i.

        Parameters
        ----------
        i: int
            The index of the element from which to return a point.
        j: int
            The index in element i of the point to be returned.

        Returns
        -------
        Coords object
            A Coords with shape (3,), being point j of element i.

        Examples
        --------
        >>> Formex('l:12').point(0,1)
        Coords([1.,  0.,  0.])
        """
        return self.coords[i, j]

    def coord(self, i, j, k):
        """Return coordinate k of point j of element i.

        Parameters
        ----------
        i: int
            The index of the element from which to return a point.
        j: int
            The index in element i of the point for which to return a coordinate.
        k: int
            The index in point (i,j) of the coordinate to be returned.

        Returns
        -------
        float
            The value of coordinate k of point j of element i.

        Examples
        --------
        >>> Formex('l:12').coord(0,1,0)
        1.0
        """
        return self.coords[i, j, k]

    def centroids(self):
        """Return the centroids of all elements of the Formex.

        The centroid of an element is the point whose coordinates
        are the average values of all points of the element.

        Returns
        -------
        Coords
            A Coords object with shape (:meth:`nelems`, 3), holding the
            centroids of all the elements in the Formex.

        Examples
        --------
        >>> Formex('l:123').centroids()
        Coords([[0.5,  0. ,  0. ],
                [1. ,  0.5,  0. ],
                [0.5,  1. ,  0. ]])

        """
        return self.coords.mean(axis=1)

    #######################################################################
    #
    #   Data conversion
    #
    #################

    # deprecated, silently kept for compatibility?
    def fuse(self, **kargs):
        return self.coords.fuse(**kargs)

    def toMesh(self, **kargs):
        """Convert a Formex to a Mesh.

        Converts a geometry in Formex model to the equivalent Mesh model.
        In the Mesh model, all points with nearly identical coordinates
        are fused into a single point (using :meth:`~coords.Coords.fuse`),
        and elements are defined by a connectivity table with integers
        pointing to the corresponding vertex.

        Parameters
        ----------
        kargs
            Keyword parameters to be passed to :meth:`~coords.Coords.fuse`.

        Returns
        -------
        Mesh
            A Mesh representing the same geometrical model as the input
            Formex. Property numbers :attr:`prop` and element type
            :attr:`eltype` are also set to the same values as in the Formex.

        Examples
        --------
        >>> F = Formex('l:12')
        >>> F
        Formex([[[0.,  0.,  0.],
                 [1.,  0.,  0.]],
        <BLANKLINE>
                [[1.,  0.,  0.],
                 [1.,  1.,  0.]]])
        >>> M = F.toMesh()
        >>> print(M)
        Mesh: nnodes: 3, nelems: 2, nplex: 2, level: 1, eltype: line2
          BBox: [0.  0.  0.], [1.  1.  0.]
          Size: [1.  1.  0.]
          Length: 2.0

        """
        from pyformex.mesh import Mesh
        x, e = self.coords.fuse(**kargs)
        return Mesh(x, e, prop=self.prop, eltype=self.eltype)

    def toSurface(self):
        """Convert a Formex to a Surface.

        Tries to convert the Formex to a TriSurface.
        First the Formex is converted to a Mesh, and then the resulting Mesh
        is converted to a TriSurface.

        Returns
        -------
        TriSurface
            A TriSurface if the conversion is successful, else an error is raised.

        Notes
        -----
        The conversion will only work if the Formex represents a surface and
        its elements are triangles or quadrilaterals.
        If the plexitude of the Formex is 3, the element type is 'tri3' or
        None, the returned TriSurface is equivalent with the Formex.
        If the Formex contains higher order triangles or quadrilaterals,
        the new geometry will be an approximation of the input.
        Any other input geometry will fail to convert.

        Examples
        --------
        >>> F = Formex('3:.12.34')
        >>> F
        Formex([[[0.,  0.,  0.],
             [1.,  0.,  0.],
             [1.,  1.,  0.]],
        <BLANKLINE>
            [[1.,  1.,  0.],
             [0.,  1.,  0.],
             [0.,  0.,  0.]]])
        >>> print(F.toSurface())
        TriSurface: nnodes: 4, nelems: 2, nplex: 3, level: 2, eltype: tri3
          BBox: [0.  0.  0.], [1.  1.  0.]
          Size: [1.  1.  0.]
          Length: 4.0  Area: 1.0
       """
        return self.toMesh().toSurface()


    def toCurve(self, closed=False):
        """Convert a Formex to a Curve.

        The following Formices can be converted to a Curve:
        - plex 1 : to PolyLine, connecting the points
        - plex 2 : to PolyLine
        - plex 3 : to BezierSpline of degree 2
        - plex 4 : to BezierSpline of degree 3

        Parameters
        ----------
        closed: bool
            Create a closed curve

        Returns
        -------
        BezierSpline | PolyLine
            A BezierSpline or PolyLine created from the points in the Formex.

        Notes
        -----
        It is expected that the elements of the Formex form a continuous
        line, i.e. each element of the Formex starts with the same
        point as the previous element ends.
        """
        from pyformex.curve import PolyLine, BezierSpline
        if self.nplex() == 1:
            curve = PolyLine(self.points(), closed=closed)
        elif self.nplex() == 2:
            curve = PolyLine(
                Coords.concatenate([self.coords[:, 0], self.coords[-1, 1]]),
                closed=closed)
        elif self.nplex() in (3, 4):
            curve = BezierSpline(
                Coords.concatenate([self.coords[:, :-1], self.coords[-1, -1]]),
                closed=closed, degree=self.nplex()-1)
        else:
            raise ValueError(
                f"Can not convert {self.nplex()}-plex Formex to a Curve")
        return curve


    #######################################################################
    #
    #  String representations of a Formex
    #
    #################

    def info(self):
        """Return information about a Formex.

        Returns
        -------
        A multiline string with some basic information about the Formex:
        its shape, bounding box, center and maxprop.

        Examples
        --------
        >>> print(Formex('3:.12.34').info())
        shape    = (2, 3, 3)
        bbox[lo] = [0.  0.  0.]
        bbox[hi] = [1.  1.  0.]
        center   = [0.5  0.5  0. ]
        maxprop  = -1
        <BLANKLINE>

        """
        bb = self.bbox()
        return (f"shape    = {self.shape}\n"
                f"bbox[lo] = {bb[0]}\n"
                f"bbox[hi] = {bb[1]}\n"
                f"center   = {self.center()}\n"
                f"maxprop  = {self.maxProp()}")


    def report(self, full=False, **kargs):
        """Create a report on the Formex shape and size.

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
            A multiline string with the report.
        """
        bb = self.bbox()
        s = (f"{self.__class__.__name__}: "
             f"npoints: {self.npoints()}, nelems: {self.nelems()}, "
             f"nplex: {self.nplex()}, level: {self.level()}, "
             f"eltype: {self.eltype}"
             f"\n  BBox: {bb[0]}, {bb[1]}"
             f"\n  Size: {bb[1]-bb[0]}")
        if full:
            with np.printoptions(**kargs):
                s += '\n' + at.stringar("  Coords: ", self.coords)
        return s

    @classmethod
    def point2str(clas, point):
        """Return a string representation of a point

        Parameters
        ----------
        elem: float :term:`array_like` (3,)
            The coordinates of athe point to return as a string.

        Returns
        -------
        str
            A string with the representation of a single point.

        Examples
        --------
        >>> Formex.point2str([1.,2.,3.])
        '1.0,2.0,3.0'
        """
        return ",".join([str(c) for c in point])

    @classmethod
    def element2str(clas, elem):
        """Return a string representation of an element

        Parameters
        ----------
        elem: float :term:`array_like` (nplex,3)
            The element to return as a string.

        Returns
        -------
        str
            A string with the representation of a single element.

        Examples
        --------
        >>> Formex.element2str([[1.,2.,3.],[4.,5.,6.]])
        '[1.0,2.0,3.0; 4.0,5.0,6.0]'
        """
        return '[' + '; '.join([clas.point2str(p) for p in elem]) + ']'

    def asFormex(self):
        """Return string representation of all the coordinates in a Formex.

        Returns
        -------
        str
           A single string with all the coordinates of the Formex.
           Coordinates are separated by commas, points are separated
           by semicolons and grouped between brackets, elements are
           separated by commas and grouped between braces.

        Examples
        --------
        >>> F = Formex([[[1,0],[0,1]],[[0,1],[1,2]]])
        >>> F.asFormex()
        '{[1.0,0.0,0.0; 0.0,1.0,0.0], [0.0,1.0,0.0; 1.0,2.0,0.0]}'
        """
        return '{' + ', '.join([self.element2str(e) for e in self.coords]) + '}'

    def asFormexWithProp(self):
        """Return string representation as Formex with properties.

        Returns
        -------
        str
            The string representation as done by :meth:`asFormex`,
            followed by the words "with prop" and a list of the properties.

        Examples
        --------
        >>> F = Formex([[[1,0],[0,1]],[[0,1],[1,2]]]).setProp([1,2])
        >>> F.asFormexWithProp()
        '{[1.0,0.0,0.0; 0.0,1.0,0.0], [0.0,1.0,0.0; 1.0,2.0,0.0]} with prop [1 2]'
       """
        s = self.asFormex()
        if self.prop is None:
            s += " no prop"
        else:
            s += " with prop " + self.prop.__str__()
        return s

    def asCoords(self):
        """Return string representation as a Coords.

        Returns
        -------
        str
            A multiline string with the coordinates of the Formex as
            formatted by the meth:`coords.Coords.__repr__` method.

        Examples
        --------
        >>> F = Formex([[[1,0],[0,1]],[[0,1],[1,2]]])
        >>> print(F.asCoords())
        Formex([[[1.,  0.,  0.],
                [0.,  1.,  0.]],
        <BLANKLINE>
               [[0.,  1.,  0.],
                [1.,  2.,  0.]]])

        """
        return self.coords.__repr__().replace('Coords', 'Formex')

    def asarray(self):
        """Return string representation as a numpy array.

        Returns
        -------
        str
            A multiline string with the coordinates of the Formex as
            formatted by the meth:`coords.Coords.__str__` method.

        Examples
        --------
        >>> F = Formex([[[1,0],[0,1]],[[0,1],[1,2]]])
        >>> print(F.asarray())
         [[[1.  0.  0.]
          [0.  1.  0.]]
        <BLANKLINE>
         [[0.  1.  0.]
          [1.  2.  0.]]]

        """
        return self.coords.__str__()

    # default string representations
    __repr__ = asCoords
    __str__ = report

    def fprint(self, *args, **kargs):
        self.coords.fprint(*args, **kargs)

    #######################################################################
    #
    #  Methods that change a Formex
    #
    #################

    # TODO: deprecate ?
    def append(self, F):
        """Append the elements of Formex F to self.

        Warning
        -------
        This function changes the calling object and its use is
        discouraged. It is better to use the :meth:`concatenate` method
        or the addition operator, wich just return the concatenation
        without changing the object itself

        Parameters
        ----------
        F: Formex
            A Formex with the same plexitude as self

        Returns
        -------
        Formex
            The original Formex which has been changed by appending
            the elements of F to it.

        See Also
        --------
        concatenate: concatenate a list of Formices
        __add__: concatenate two Formices

        Examples
        --------
        >>> F = Formex([[[1.0,1.0,1.0]]])
        >>> G = F.append(F)
        >>> print(F)
        {[1.0,1.0,1.0], [1.0,1.0,1.0]}
        >>> G is F
        True

        """
        if F.coords.size == 0:
            return self
        if self.coords.size == 0:
            self.coords = F.coords
            self.prop = F.prop
            return self

        self.coords = Coords(np.concatenate((self.coords, F.coords)))
        ## What to do if one of the formices has properties, the other one not?
        ## The current policy is to use zero property values for the Formex
        ## without props
        if self.prop is not None or F.prop is not None:
            if self.prop is None:
                self.prop = np.zeros(shape=self.coords.shape[:1], dtype=at.Int)
            if F.prop is None:
                p = np.zeros(shape=F.coords.shape[:1], dtype=at.Int)
            else:
                p = F.prop
            self.prop = np.concatenate((self.prop, p))
        return self

    #######################################################################
    ##
    ## All the following functions leave the original Formex unchanged and
    ## return a new Formex instead. This is a design decision intended so
    ## that the user can write chained statements as
    ##   G = F.op1().op2().op3()
    ## without having an impact on F. If the user wishes, he can always
    ## change an existing Formex by a statement such as
    ##   F = F.op()
    ## While this may seem to create a lot of intermediate array data,
    ## Python and numpy are clever enough to release the memory that is
    ## no longer used.
    ##
    #######################################################################

    #######################################################################
    #
    #  Create copies, concatenations, subtractions, connections, ...
    #
    #################

    @classmethod
    def concatenate(clas, Flist):
        """Concatenate a list of Formices.

        All the Formices in the list should have the same plexitude,
        If any of the Formices has property numbers, the resulting Formex will
        inherit the properties. In that case, any Formices without properties
        will be assigned property 0.
        If all Formices are without properties, so will be the result.
        The eltype of the resulting Formex will be that of the first Formex in
        the list.

        Parameters
        ----------
        Flist: list of Formex objects
            A list of Formices all having the same plexitude.

        Returns
        -------
        Formex
            The concatenation of all the Formices in the list. The number of
            elements in the Formex is the sum of the number of elements in
            all the Formices.

        Note
        ----
        This is a class method, not an instance method. It is commonly
        invoked as ``Formex.concatenate``.

        See Also
        --------
        __add__: implements concatenation as simple addition (F+G)

        Examples
        --------
        >>> F = Formex([1.,1.,1.]).setProp(1)
        >>> G = Formex([2.,2.,2.])
        >>> H = Formex([3.,3.,3.]).setProp(3)
        >>> K = Formex.concatenate([F,G,H])
        >>> print(K.asFormexWithProp())
        {[1.0,1.0,1.0], [2.0,2.0,2.0], [3.0,3.0,3.0]} with prop [1 0 3]

        """
        def _force_prop(m):
            if m.prop is None:
                return np.zeros(m.nelems(), dtype=at.Int)
            else:
                return m.prop

        f = Coords.concatenate([F.coords for F in Flist])

        # Keep the available props
        prop = [F.prop for F in Flist if F.prop is not None]
        if len(prop) == 0:
            prop = None
        elif len(prop) < len(Flist):
            prop = np.concatenate([_force_prop(F) for F in Flist])
        else:
            prop = np.concatenate(prop)

        return Formex(f, prop, Flist[0].eltype)

    def __add__(self, F):
        """Concatenate two formices.

        Parameters
        ----------
        F: Formex
            A Formex with the same plexitude as self.

        Returns
        -------
        Formex
            The concatenation of the Formices self and F.

        Note
        ----
        This method implements the addition operation and allows to write
        simple expressions as F+G to concatenate the Formices F and G. When
        concatenating many Formices, :meth:`concatenate` is more efficient
        however, because all the Formices in the list are concatenated in
        one operation.

        See Also
        --------
        concatenate: concatenate a list of Formices

        Examples
        --------
        >>> F = Formex([1.,1.,1.]).setProp(1)
        >>> G = Formex([2.,2.,2.])
        >>> H = Formex([3.,3.,3.]).setProp(3)
        >>> K = F+G+H
        >>> print(K.asFormexWithProp())
        {[1.0,1.0,1.0], [2.0,2.0,2.0], [3.0,3.0,3.0]} with prop [1 0 3]

        """
        if len(F) == 0:
            return self
        elif len(self) == 0:
            return Formex(F.coords, F.prop, self.eltype)
        else:
            return Formex.concatenate([self, F])

    def split(self, n=1):
        """Split a Formex in Formices containing n elements.

        Parameters
        ----------
        n: int
            Number of elements per Formex

        Returns
        -------
        list of Formices
            A list of Formices all containing n elements, except for the last,
            which may contain less.

        Examples
        --------
        >>> Formex('l:111').split(2)
        [Formex([[[0.,  0.,  0.],
                [1.,  0.,  0.]],
        <BLANKLINE>
               [[1.,  0.,  0.],
                [2.,  0.,  0.]]]), Formex([[[2.,  0.,  0.],
                [3.,  0.,  0.]]])]

        """
        m = (self.nelems()+n-1) // n
        if self.prop is None:
            return [Formex(self.coords[n*i:n*(i+1)], self.eltype) for i in range(m)]
        else:
            return [Formex(self.coords[n*i:n*(i+1)], self.prop[n*i:n*(i+1)],
                           self.eltype) for i in range(m)]

    def _select(self, selected, **kargs):
        """Return a Formex only holding the selected elements.

        This is the low level select method. The normal user interface
        is via the Geometry.select method.
        """
        selected = at.checkArray1D(selected)
        if self.prop is None:
            return Formex(self.coords[selected], eltype=self.eltype)
        else:
            return Formex(self.coords[selected], self.prop[selected], self.eltype)

    def selectNodes(self, idx):
        """Extract a Formex holding only some points of the parent.

        This creates subentities of all elements in the Formex.
        The returned Formex inherits the properties of the parent.

        Parameters
        ----------
        idx: list of ints
            Indices of the points to retain in the new Formex.

        Notes
        -----
        For example, if F is a plex-3 Formex representing triangles, the
        sides of the triangles are given by
        F.selectNodes([0,1]) + F.selectNodes([1,2]) + F.selectNodes([2,0])

        See Also
        --------
        select: Select elements from a Formex

        Examples
        --------
        >>> F = Formex('3:.12.34')
        >>> print(F.selectNodes((0,1)))
        {[0.0,0.0,0.0; 1.0,0.0,0.0], [1.0,1.0,0.0; 0.0,1.0,0.0]}

        """
        return Formex(self.coords[:, idx, :], self.prop, self.eltype)

    def asPoints(self):
        """Reduce the Formex to a simple set of points.

        This removes the element structure of the Formex.

        Returns
        -------
        Formex
            A Formex with plexitude 1 and number of elements (points) equal
            to ``self.nelems() * self.nplex()``. The Formex shares the
            coordinate data with the parent. If the parent has properties,
            they are multiplexed so that each point has the property of its
            parent element. The eltype of the returned Formex is None.

        See Also
        --------
        points: returns the list of points as a Coords object

        Examples
        --------
        >>> F = Formex('3:.12.34',prop=[1,2]).asPoints()
        >>> print(F.asFormexWithProp())
        {[0.0,0.0,0.0], [1.0,0.0,0.0], [1.0,1.0,0.0], [1.0,1.0,0.0], \
        [0.0,1.0,0.0], [0.0,0.0,0.0]} with prop [1 1 1 2 2 2]
        """
        if self.prop is not None:
            prop = at.repeatValues(self.prop, self.nplex())
        else:
            prop = None
        return Formex(self.coords.reshape((-1, 1, 3)), prop=prop)

    # TODO: it would be better to create a method match()
    # then the user can do with them what he wants
    def remove(self, F, permutations='roll', rtol=1.e-5, atol=1.e-5):
        """Remove elements that also occur in another Formex.

        Parameters
        ----------
        F: Formex
            Another Formex with the same plexitude as self.
        permutations: bool, optional
            If True, elements consisting of the

        This is also the subtraction of the current Formex with F.
        Elements are only removed if they have the same nodes in the same
        order.

        Examples
        --------
        >>> F = Formex('l:111')
        >>> G = Formex('l:1')
        >>> print(F.remove(G))
        {[1.0,0.0,0.0; 2.0,0.0,0.0], [2.0,0.0,0.0; 3.0,0.0,0.0]}
        """
        M = (self+F).toMesh(rtol=rtol, atol=atol)
        VA = at.equalRows(M.elems)
        remove = []
        for row in VA:
            if row.min() < self.nelems() and row.max() >= self.nelems():
                # equal rows in self and F: remove from self
                remove.append(row[row<self.nelems()])
        return self.cselect(remove)

    def removeDuplicate(self, permutations='all', rtol=1.e-5, atol=1.e-8):
        """Return a Formex which holds only the unique elements.

        Parameters
        ----------
        permutations: str
            Defines which permutations of the element points are allowed
            while still considering the elements equal. Possible values are:

            - 'none': no permutations are allowed: elements must have
              matching points at all locations. This is the default;
            - 'roll': rolling is allowed. Elements that can be transformed into
              each other by rolling their points are considered equal;
            - 'all': any permutation of the same points will be considered an
              equal element.
        rtol: float, optional
            Relative tolerance used when considering two points being equal.
        atol: float, optional
            Absolute tolerance used when considering two points being equal.

        Notes
        -----
        ``rtol`` and ``atol`` are passed to :meth:`coords.Coords.fuse` to find
        equal points. ``permutation`` is passed to :func:`arraytools.unique`
        to remove the duplicates.

        Examples
        --------
        >>> F = Formex('l:111') + Formex('l:1')
        >>> print(F.removeDuplicate())
        {[0.0,0.0,0.0; 1.0,0.0,0.0], [1.0,0.0,0.0; 2.0,0.0,0.0], \
        [2.0,0.0,0.0; 3.0,0.0,0.0]}
       """
        x, e = self.coords.fuse(rtol=rtol, atol=atol)
        return self.select(at.uniqueRows(e, permutations))

    # REMOVED IN 1.0.0
    ## unique = removeDuplicate

    #######################################################################
    #
    #  Test and clipping functions
    #
    #################

    def test(self, nodes='all', dir=0, min=None, max=None, atol=0.):
        """Flag elements having coordinates between min and max.

        This is comparable with :meth:`coords.Coords.test` but operates
        at the Formex element level. It tests the position of one or more
        points of the elements of the :class:`Formex` with respect to
        one or two parallel planes. This is very useful in clipping
        a Formex in a specified direction. In most cases the clipping
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

            - a single point index (smaller than self.nplex()),
            - a list of point numbers ( all smaller than < self.nplex()),
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
            index in :meth:`select` or `cselect` to obtain a :class:`Formex`
            with the elements satisfying the test or not. Or you can use
            ``np.where(result)[0]`` to get the indices of the elements passing
            the test.

        Raises
        ------
        ValueError: At least one of min or max have to be specified
            If neither `min` nor `max` are provided.

        See Also
        --------
        select: return only the selected elements
        cselect: return all but the selected elements

        Examples
        --------
        >>> F = Formex('l:1122')
        >>> print(F.asFormex())
        {[0.0,0.0,0.0; 1.0,0.0,0.0], [1.0,0.0,0.0; 2.0,0.0,0.0], \
        [2.0,0.0,0.0; 2.0,1.0,0.0], [2.0,1.0,0.0; 2.0,2.0,0.0]}
        >>> F.test(min=0.0,max=1.0)
        array([ True, False, False, False])
        >>> F.test(nodes=[0],min=0.0,max=1.0)
        array([ True,  True, False, False])
        >>> F.test(dir=[-1.,1.,0.],min=[1.,0.,0.])
        array([ True, False, False,  True])
        >>> F.test(dir=[-1.,1.,0.],min=[1.,0.,0.],nodes='any')
        array([ True,  True,  True,  True])

        """
        if min is None and max is None:
            raise ValueError("At least one of min or max have to be specified.")

        if isinstance(nodes, str):
            nod = np.arange(self.nplex())
        else:
            nod = nodes

        # Perform the test on the selected nodes
        X = self.coords[:, nod]
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


    #######################################################################
    #
    #  Transformations that preserve the topology (but change coordinates)
    #
    #################

    def shrink(self, factor):
        """Scale all elements with respect to their own center.

        Parameters
        ----------
        factor: float
            Scaling factor for the elements. A value < 1.0 will shrink the
            elements, while a facter > 1.0 will enlarge them.

        Returns
        -------
        Formex
            A Formex where each element has been scaled with the specified
            factor in local axes with origin at the element's center.

        Notes
        -----
        This operation is called 'shrink' because it is commonly used
        with a factor smaller that 1 (often around 0.9) to draw an exploded
        view where touching elements are disconnected.

        Examples
        --------
        >>> Formex('l:12').shrink(0.8)
        Formex([[[0.1,  0. ,  0. ],
                 [0.9,  0. ,  0. ]],
        <BLANKLINE>
                [[1. ,  0.1,  0. ],
                 [1. ,  0.9,  0. ]]])

        """
        c = self.coords.mean(1).reshape((self.coords.shape[0], 1, self.coords.shape[2]))
        return Formex(factor*(self.coords-c)+c, self.prop, self.eltype)

    def circulize1(self):
        """Transforms the first octant of the 0-1 plane into 1/6 of a circle.

        Points on the 0-axis keep their position. Lines parallel to the 1-axis
        are transformed into circular arcs. The bisector of the first quadrant
        is transformed in a straight line at an angle Pi/6.
        This function is especially suited to create circular domains where
        all bars have nearly same length. See the Diamatic example.
        """
        with np.errstate(divide='ignore', invalid='ignore'):
            res = self.map(lambda x, y, z:
                           [np.where(x>0, x-y*y/(x+x), 0),
                            np.where(x>0, y*np.sqrt(4*x*x-y*y)/(x+x), y), 0])
        return res

    #######################################################################
    #
    #  Transformations that change the topology
    #
    #################

    def reverse(self):
        """Return a Formex where all elements have been reversed.

        Reversing an element means reversing the order of its points.

        Returns
        -------
        Formex
            A Formex with same shape, where the points of all elements
            are in reverse order.

        Notes
        -----
        This is equivalent to ``self.selectNodes(np.arange(self.nplex()-1,-1,-1))``.

        Examples
        --------
        >>> F = Formex('l:11')
        >>> F.reverse()
        Formex([[[1.,  0.,  0.],
                 [0.,  0.,  0.]],
        <BLANKLINE>
                [[2.,  0.,  0.],
                 [1.,  0.,  0.]]])

        """
        return Formex(self.coords[:, ::-1], self.prop, self.eltype)

    def mirror(self, dir=0, pos=0., keep_orig=True):
        """Add a reflection in one of the coordinate directions.

        This method is like :meth:`~geometry.Geometry.reflect`,
        but by default adds the reflected part to the original.

        Parameters
        ----------
        dir: int (0,1,2)
            Global axis direction of the reflection (default 0 or x-axis).
        pos: float
            Offset of the mirror plane from origin (default 0.0)
        keep_orig: bool, optional
            If True (default) the original plus the mirrored geometry is
            returned. Setting it to False will only return the mirror, and
            thus behaves just like :meth:`~geometry.Geometry.reflect`.

        Returns
        -------
        Formex
            A Formex with the original and the mirrored elements, or
            only the mirrored elements if ``keep_orig`` is False.

        Examples
        --------
        >>> F = Formex('l:11')
        >>> F.mirror()
        Formex([[[ 0.,  0.,  0.],
                 [ 1.,  0.,  0.]],
        <BLANKLINE>
                [[ 1.,  0.,  0.],
                 [ 2.,  0.,  0.]],
        <BLANKLINE>
                [[ 0.,  0.,  0.],
                 [-1.,  0.,  0.]],
        <BLANKLINE>
                [[-1.,  0.,  0.],
                 [-2.,  0.,  0.]]])
        >>> F.mirror(keep_orig=False)
        Formex([[[ 0.,  0.,  0.],
             [-1.,  0.,  0.]],
        <BLANKLINE>
            [[-1.,  0.,  0.],
             [-2.,  0.,  0.]]])

        """
        if keep_orig:
            return self+self.reflect(dir, pos)
        else:
            return self.reflect(dir, pos)

    def translatem(self, *args):
        """Multiple subsequent translations in axis directions.

        Parameters
        ----------
        *args: one or more tuples (axis, step).
            Each argument is a tuple (axis, step) which will do
            a translation over a length ``step`` in the direction
            of the global axis ``axis``.

        Returns
        -------
        Formex
            The input Formex translated over the combined translation
            vector of the arguments.

        Notes
        -----
        This function is especially convenient to translate over computed
        steps.

        See Also
        --------
        translate: translate a Formex

        Examples
        --------
        >>> F = Formex('l:11')
        >>> d = np.random.random(3)
        >>> np.allclose(F.translatem((0,d[0]),(2,d[2]),(1,d[1])).coords, \
            F.translate(d).coords)
        True

        """
        tr = [0., 0., 0.]
        for d, t in args:
            tr[d] += t
        return self.translate(tr)

    def replicate(self, n, dir=0, step=1.0):
        """Create copies at regular distances along a straight line.

        Parameters
        ----------
        n: int
            Number of copies to create
        dir: int (0,1,2) or float :term:`array_like` (3,)
            The translation vector. If an int, it specifies a global axis
            and the translation is in the direction of that axis.
        step: float
            If ``dir`` is an int, this is the length of the translation.
            Else, it is a multiplying factor applied to the translation
            vector.

        Returns
        -------
        Formex
            A Formex with the concatenation of n copies of the original. Each
            copy is equal to the previous one translated over a distance
            ``step * length(dir)`` in the direction ``dir``. The first of
            the copies is equal to the original.

        See Also
        --------
        rep: short alias for replicate
        repm: replicate in multiple directions
        replic2: replicate in two directions with bias and taper

        Examples
        --------
        >>> Formex('l:1').replicate(4,1)
         Formex([[[0.,  0.,  0.],
                 [1.,  0.,  0.]],
        <BLANKLINE>
                [[0.,  1.,  0.],
                 [1.,  1.,  0.]],
        <BLANKLINE>
                [[0.,  2.,  0.],
                 [1.,  2.,  0.]],
        <BLANKLINE>
                [[0.,  3.,  0.],
                 [1.,  3.,  0.]]])

        """
        f = self.coords.replicate(n, dir, step=step)
        f.shape = (f.shape[0]*f.shape[1], f.shape[2], f.shape[3])
        ## the replication of the properties is automatic!
        return Formex(f, self.prop, self.eltype)

    # Easy to use alias
    rep = replicate


    def repm(self, n, dir=(0, 1, 2), step=(1., 1., 1.)):
        """Repeatedly replication in different directions

        This repeatedly applies :meth:`replicate` a number of times.
        The parameters are lists of values like those for replicate.

        Parameters
        ----------
        n: list of int
            Number of copies to create in the subsequent replications.
        dir: list of int (0,1,2) or list of float :term:`array_like` (3,)
            Subsequent translation vectors. See :meth:`replicate`.
        step: list of floats
            The step for the subsequent replications.

        Returns
        -------
        Formex
            A Formex with the concatenation of prod(n) copies of the original,
            translated as specified by the dir and step parameters.
            The first of the copies is equal to the original.

        Note
        ----
        If the parameter lists ``n``, ``dir``, ``step`` have different
        lengths, the operation is executed only for the shortest of the
        three.

        See Also
        --------
        replicate: replicate in a single direction
        replic2: replicate in two directions with bias and taper

        Examples
        --------
        >>> Formex('l:1').repm((2,2),(1,2))
        Formex([[[0.,  0.,  0.],
                 [1.,  0.,  0.]],
        <BLANKLINE>
                [[0.,  1.,  0.],
                 [1.,  1.,  0.]],
        <BLANKLINE>
                [[0.,  0.,  1.],
                 [1.,  0.,  1.]],
        <BLANKLINE>
                [[0.,  1.,  1.],
                 [1.,  1.,  1.]]])

        >>> print(Formex([origin()]).repm((2,2)))
        {[0.0,0.0,0.0], [1.0,0.0,0.0], [0.0,1.0,0.0], [1.0,1.0,0.0]}
        """
        F = self
        if dir is None:
            dir = list(range(len(n)))
        if step is None:
            step = [1.]*len(n)
        for ni, diri, stepi in zip(n, dir, step):
            F = F.replicate(ni, diri, stepi)
        return F

    # TODO:  deprecate replic, but beware: it is used a lot!!!!
    # so maybe keep for compatibility reasons.
    # @utils.deprecated_by('Formex.replic','Formex.replicate')
    def replic(self, n, step=1.0, dir=0):
        """Return a Formex with n replications in direction dir with step.

        Note
        ----
        This works exactly like :meth:`replicate` but has another order
        of the parameters. It is kept for historical reasons, but should
        not be used in new code.
        """
        return self.replicate(n, dir=dir, step=step)

    def replic2(self, n1, n2, t1=1.0, t2=1.0, d1=0, d2=1, bias=0, taper=0):
        """Replicate in two directions with bias and taper.

        Parameters
        ----------
        n1: int
            Number of replications in first direction
        n2: int
            Number of replications in second direction
        t1: float
            Step length in the first direction
        t2: float
            Step length in the second direction
        d1: int
            Global axis of the first direction
        d2: int
            Global axis of the second direction
        bias: float
            Extra translation in direction d1 for each step in direction d2
        taper: int
            Extra number of copies generated in direction d1 for each step
            in direction d2

        Note
        ----
        If no bias nor taper is needed, the use of :meth:`repm` is
        recommended.

        See Also
        --------
        replicate: replicate in a single direction
        repm: replicate in multiple directions

        Examples
        --------
        >>> print(Formex([origin()]).replic2(2,2))
        {[0.0,0.0,0.0], [1.0,0.0,0.0], [0.0,1.0,0.0], [1.0,1.0,0.0]}
        >>> print(Formex([origin()]).replic2(2,2,bias=0.2))
        {[0.0,0.0,0.0], [1.0,0.0,0.0], [0.2,1.0,0.0], [1.2,1.0,0.0]}
        >>> print(Formex([origin()]).replic2(2,2,taper=-1))
        {[0.0,0.0,0.0], [1.0,0.0,0.0], [0.0,1.0,0.0]}

        """
        P = [self.translatem((d1, i*bias), (d2, i*t2)).replic(n1+i*taper, t1, d1)
             for i in range(n2)]
        ## We should replace the Formex concatenation here by
        ## separate data and prop concatenations, because we are
        ## guaranteed that either none or all formices in P have props.
        return Formex.concatenate(P)

    # TODO:  deprecate replicm, but beware: it is used a lot!!!!
    # so maybe keep for compatibility reasons.
    # @utils.deprecated_by('Formex.replicm','Formex.repm')
    def replicm(self, n, step=(1.0, 1.0, 1.0), dir=(0, 1, 2)):
        """Replicate in multiple global axis directions.

        Note
        ----
        This works exactly like :meth:`repm` but has another order
        of the parameters. It is kept for historical reasons, but should
        not be used in new code.

        """
        return self.repm(n, dir=dir, step=step)


    def rosette(self, n, angle=None, axis=2, around=(0., 0., 0.),
                angle_spec=at.DEG):
        """Create rotational replications of a Formex.

        Parameters
        ----------
        n: int
            Number of copies to create
        angle: float
            Angle in between successive copies. If not provided, it is set to
            360 / n.
        axis: int (0,1,2) or float :term:`array_like` (3,)
            The rotation axis. An int speficies one of the global axes.
            Else, it is the direction vector of the axis.
        around: float :term:`array_like` (3,), optional
            If provided, it species a point on the rotation axis. If not,
            the rotation axis goes through the origin of the global axes.
        angle_spec: float, DEG or RAD, optional
            The default (DEG) interpretes the angle in degrees. Use RAD to
            specify the angle in radians.

        Returns
        -------
        Formex
            A Formex with n rotational replications with given angular step.
            The original Formex is the first of the n replicas.

        Examples
        --------
        >>> Formex('l:1').rosette(4,90.)
        Formex([[[ 0.,  0.,  0.],
                 [ 1.,  0.,  0.]],
        <BLANKLINE>
                [[ 0.,  0.,  0.],
                 [ 0.,  1.,  0.]],
        <BLANKLINE>
                [[ 0.,  0.,  0.],
                 [-1.,  0.,  0.]],
        <BLANKLINE>
                [[ 0.,  0.,  0.],
                 [-0., -1.,  0.]]])
        >>> Formex('l:1').rosette(3,90.,around=(0.,1.,0.))
        Formex([[[ 0.,  0.,  0.],
                 [ 1.,  0.,  0.]],
        <BLANKLINE>
                [[ 1.,  1.,  0.],
                 [ 1.,  2.,  0.]],
        <BLANKLINE>
                [[ 0.,  2.,  0.],
                 [-1.,  2.,  0.]]])

        """
        f = self.coords.rosette(n, angle, axis, around, angle_spec)
        f.shape = (f.shape[0]*f.shape[1], f.shape[2], f.shape[3])
        return Formex(f, self.prop, self.eltype)

    ##########################################################################
    #
    #   Transformations that change the plexitude
    #

    def extrude(self, *args, **kargs):
        """Extrude a Formex along a straight line.

        The Formex is extruded over a given length in the given direction.
        This operates by converting the Formex to a :class:`~mesh.Mesh`,
        extruding the Mesh with the given parameters, and converting the
        result back to a Formex.

        Parameters: see :meth:`~mesh.Mesh.extrude`.

        Returns
        -------
        Formex
            The Formex obtained by extruding the input Formex over the
            given `length` in direction `dir`, subdividing this length according
        to the seeds specified by `dir`. The plexitude of the result will be
        double that of the input.

        This method works by converting the Formex to a :class:`~mesh.Mesh`,
        using the :func:`Mesh.extrude` and then converting the result
        back to a Formex.

        See Also
        --------
        connect: create a higher plexitude Formex by connecting Formices

        Examples
        --------
        >>> Formex(origin()).extrude(4,dir=0,length=3)
        Formex([[[0.  ,  0.  ,  0.  ],
                 [0.75,  0.  ,  0.  ]],
        <BLANKLINE>
                [[0.75,  0.  ,  0.  ],
                 [1.5 ,  0.  ,  0.  ]],
        <BLANKLINE>
                [[1.5 ,  0.  ,  0.  ],
                 [2.25,  0.  ,  0.  ]],
        <BLANKLINE>
                [[2.25,  0.  ,  0.  ],
                 [3.  ,  0.  ,  0.  ]]])


        """
        return self.toMesh().extrude(*args, **kargs).toFormex()

    def interpolate(self, G, div, swap=False):
        """Create linear interpolations between two Formices.

        A linear interpolation of two equally shaped Formices F and G at
        parameter value t is an equally shaped Formex H where each coordinate
        is obtained from:  Hijk = Fijk + t * (Gijk-Fijk).
        Thus, a ``F.interpolate(G,[0.,0.5,1.0])`` will contain all elements
        of F and G and all elements with mean coordinates between those of
        F and G.


        Parameters
        ----------
        G: Formex
            A Formex with same shape as `self`.
        div: int or list of floats
            The list of parameter values for which to compute the
            interpolation. Usually, they are in the range 0.0 (self)
            to 1.0 (X). Values outside the range can be used however
            and result in linear extrapolations.

            If an int is provided, a list with ``(div+1)`` parameter
            values is used, obtained by dividing the interval [0..1] into
            `div` equal segments. Then, specifying ``div=n`` is equivalent
            to specifying ``div=np.arange(n+1)/float(n))``.
        swap: bool, optional
            If swap=True, the returned Formex will have the elements of
            the interpolation Formices interleaved. The default is to
            return a simple concatenation.

        Returns
        -------
        Formex
            A Formex with the concatenation of all generated interpolations,
            if swap is False (default). With swap=True, the elements of the
            interpolations are interleaved: first all the first elements
            from all the interpolations, then all the second elements, etc.
            The elements inherit the property numbers from self, if any.
            The Formex has the same eltype as self, if it is set.

        See Also
        --------
        coords.Coords.interpolate

        Notes
        -----
        See also example Interpolate.

        Examples
        --------
        >>> F = Formex([[[0.0,0.0,0.0],[1.0,0.0,0.0]]])
        >>> G = Formex([[[1.5,1.5,0.0],[4.0,3.0,0.0]]])
        >>> F.interpolate(G,div=3)
        Formex([[[0. ,  0. ,  0. ],
                 [1. ,  0. ,  0. ]],
        <BLANKLINE>
                [[0.5,  0.5,  0. ],
                 [2. ,  1. ,  0. ]],
        <BLANKLINE>
                [[1. ,  1. ,  0. ],
                 [3. ,  2. ,  0. ]],
        <BLANKLINE>
                [[1.5,  1.5,  0. ],
                 [4. ,  3. ,  0. ]]])
        >>> F = Formex([[[0.0,0.0,0.0]],[[1.0,0.0,0.0]]])
        >>> G = Formex([[[1.5,1.5,0.0]],[[4.0,3.0,0.0]]])
        >>> F.interpolate(G,div=3)
        Formex([[[0. ,  0. ,  0. ]],
        <BLANKLINE>
                [[1. ,  0. ,  0. ]],
        <BLANKLINE>
                [[0.5,  0.5,  0. ]],
        <BLANKLINE>
                [[2. ,  1. ,  0. ]],
        <BLANKLINE>
                [[1. ,  1. ,  0. ]],
        <BLANKLINE>
                [[3. ,  2. ,  0. ]],
        <BLANKLINE>
                [[1.5,  1.5,  0. ]],
        <BLANKLINE>
                [[4. ,  3. ,  0. ]]])
        >>> F.interpolate(G,div=3,swap=True)
        Formex([[[0. ,  0. ,  0. ]],
        <BLANKLINE>
                [[0.5,  0.5,  0. ]],
        <BLANKLINE>
                [[1. ,  1. ,  0. ]],
        <BLANKLINE>
                [[1.5,  1.5,  0. ]],
        <BLANKLINE>
                [[1. ,  0. ,  0. ]],
        <BLANKLINE>
                [[2. ,  1. ,  0. ]],
        <BLANKLINE>
                [[3. ,  2. ,  0. ]],
        <BLANKLINE>
                [[4. ,  3. ,  0. ]]])

        """
        r = self.coords.interpolate(G.coords, div)  # r is a 4-dim array
        n = r.shape[0]
        prop = self.prop
        if swap:
            if prop is not None:
                prop = at.repeatValues(prop, n)
            r = r.swapaxes(0, 1)
        # Remove the first axis
        r = r.reshape((-1,) + r.shape[-2:])
        return Formex(r, prop=prop, eltype=self.eltype)

    ###########################################################################
    #
    #   Transformations that work only for some plexitudes
    #
    # !! It is not clear if they really belong here, or should go to a subclass

    def subdivide(self, div):
        """Subdivide a plex-2 Formex at the parameter values in div.

        Replaces each element of the plex-2 Formex (line segments) by
        a sequence of elementsobtained by subdividing the Formex
        at the specified parameter values.

        Parameters
        ----------
        div: int or list of floats
            The list of parameter values at which to subdivide the elements.
            Usually, they are in the range 0.0 to 1.0.

            If an int is provided, a list with ``(div+1)`` parameter
            values is used, obtained by dividing the interval [0..1] into
            `div` equal segments. Thus, specifying ``div=n`` is equivalent
            to specifying ``div=np.arange(n+1)/float(n))``.

        Examples
        --------
        >>> Formex('l:1').subdivide(4)
        Formex([[[0.  ,  0.  ,  0.  ],
                 [0.25,  0.  ,  0.  ]],
        <BLANKLINE>
                [[0.25,  0.  ,  0.  ],
                 [0.5 ,  0.  ,  0.  ]],
        <BLANKLINE>
                [[0.5 ,  0.  ,  0.  ],
                 [0.75,  0.  ,  0.  ]],
        <BLANKLINE>
                [[0.75,  0.  ,  0.  ],
                 [1.  ,  0.  ,  0.  ]]])
        >>> Formex('l:1').subdivide([-0.1,0.3,0.7,1.1])
        Formex([[[-0.1,  0. ,  0. ],
                 [ 0.3,  0. ,  0. ]],
        <BLANKLINE>
                [[ 0.3,  0. ,  0. ],
                 [ 0.7,  0. ,  0. ]],
        <BLANKLINE>
                [[ 0.7,  0. ,  0. ],
                 [ 1.1,  0. ,  0. ]]])

        """
        if self.nplex() == 2:
            div = at.unitDivisor(div)
            point0, point1 = self.selectNodes([0]), self.selectNodes([1])
            A = point0.interpolate(point1, div[:-1], swap=True)
            B = point0.interpolate(point1, div[1:], swap=True)
            return connect([A, B])
        else:
            raise ValueError("Can only subdivide Formex with plexitude 2")

    # TODO: returned Formex could inherit properties of parent
    # TODO: remove this and leave it to Mesh subclasses?? TriSurface, WireFrame
    def intersectionWithPlane(self, p, n, atol=0.):
        """Compute the intersection of a Formex with a plane.

        Note
        ----
        This is currently only available for plexitude 2 (lines) and
        3 (triangles).

        Parameters
        ----------
        p: :term:`array_like` (3,)
            A point in the plane
        n: :term:`array_like` (3,)
            The normal vector on the plane.
        atol: float
            A tolerance value: points whose distance from the plane is less
            than ``atol`` are considered to be lying in the plane.

        Returns
        -------
        Formex
            A Formex of plexitude self.nplex()-1 holding the intersection
            with the plane (p,n). For a plex-2 Formex (lines), the returned
            Formex has plexitude 1 (points). For a plex-3 Formex
            (triangles) the returned Formex has plexitude 2 (lines).

        See Also
        --------
        cutWithPlane: return parts of Formex after cutting with a plane

        Examples
        --------
        >>> Formex('l:1212').intersectionWithPlane([0.5,0.,0.],[-1.,1.,0.])
        Formex([[[0.5,  0. ,  0. ]],
        <BLANKLINE>
               [[1. ,  0.5,  0. ]],
        <BLANKLINE>
               [[1.5,  1. ,  0. ]],
        <BLANKLINE>
               [[2. ,  1.5,  0. ]]])
        >>> Formex('3:.12.34').intersectionWithPlane([0.5,0.,0.],[1.,0.,0.])
        Formex([[[0.5,  0. ,  0. ],
                [0.5,  0.5,  0. ]],
        <BLANKLINE>
               [[0.5,  0.5,  0. ],
                [0.5,  1. ,  0. ]]])

        """
        if self.nplex() == 2:
            x, i = geomtools.intersectSegmentWithPlane(
                self.coords, p, n, mode='pair', atol=atol, returns='xi')
            return Formex(x.reshape(-1, 1, 3))
        elif self.nplex() == 3:
            m = self.toSurface().intersectionWithPlane(p, n, atol=atol)
            if m.nelems() > 0:
                return m.toFormex()
            else:
                return Formex(np.asarray([], dtype=at.Float).reshape(0, 2, 3))
        else:
            # OTHER PLEXITUDES NEED TO BE IMPLEMENTED
            raise ValueError("Formex should be plex-2 or plex-3")

    # TODO: The plexitude=3 case allows for multiple cutting planes.
    # However, it is not fully correct in cases where you want to
    # return a concave part. And in case of a convex cutting, one
    # can just as well do the cutting one by one. Therefore, we should
    # probably remove this possibility, because the concave case is
    # difficult to fix. The best option is to do sequential cutting
    # and then merge the parts together again with gts.
    # Anyhow, the docstring does not mention the multiple plane case.

    def cutWithPlane(self, p, n, side='', atol=None, newprops=None):
        """Cut a Formex with the plane (p,n).

        Note
        ----
        This is currently only available for plexitude 2 (lines) and
        3 (triangles).

        Parameters
        ----------
        p: :term:`array_like` (3,)
            A point in the cutting plane.
        n: :term:`array_like` (3,)
            The normal vector to the cutting plane.
        side: str, one of '', '+' or '-'
            Specifies which side of the plane should be returned.
            If an empty string (default), both sides are returned.
            If '+' or '-', only the part at the positive, resp. negative
            side of the plane (as defined by its normal) is returned.

        Returns
        -------
        Fpos: Formex
            Formex with the part of the Formex at the positive side of the plane.
            This part is not returned if side=='-'.
        Fneg: Formex
            Formex with the part of the Formex at the negative side of the plane.
            This part is not returned if side=='+'.

        Notes
        -----
        Elements of the input Formex that are lying completely on one side
        of the plane will return unaltered. Elements that are cut by the
        plane are split up into multiple parts.

        See Also
        --------
        intersectionWithPlane: return intersection of Formex and plane

        """
        if atol is None:
            atol = 1.e-5*self.dsize()
        if self.nplex() == 2:
            return _cut2AtPlane(self, p, n, side, atol, newprops)
        elif self.nplex() == 3:
            return _cut3AtPlane(self, p, n, side, atol, newprops)
        else:
            # OTHER PLEXITUDES NEED TO BE IMPLEMENTED
            raise ValueError("Formex should be plex-2 or plex-3")

    #################### Misc Operations #####################################

    def lengths(self):
        """Compute the length of all elements of a 2-plex Formex.

        The length of an element is the distance between its two points.

        Returns
        -------
        float array (self.nelem(),)
            An array with the length of each element.

        Raises
        ------
        ValueError
            If the Formex is not of plexitude 2.

        Examples
        --------
        >>> Formex('l:127').lengths()
        array([1.    , 1.    , 1.4142])
        """
        if self.nplex() != 2:
            raise ValueError(f"Expected a 2-plex Formex, got {self.nplex()}")
        return geomtools.levelVolumes(self.coords)

    def areas(self):
        """Compute the areas of all elements of a 3-plex Formex.

        The area of an element is the area of the triangle formed by its
        three points.

        Returns
        -------
        float array (self.nelem(),)
            An array with the area of each element.

        Raises
        ------
        ValueError
            If the Formex is not of plexitude 3.

        Examples
        --------
        >>> Formex('3:.12.34').areas()
        array([0.5,  0.5])
        """
        if self.nplex() != 3:
            raise ValueError(f"Expected a 3-plex Formex, got {self.nplex()}")
        return geomtools.levelVolumes(self.coords)

    def volumes(self):
        """Compute the volume of all elements of a 4-plex Formex.

        The volume of an element is the volume of the tetraeder formed
        by its 4 points.

        Returns
        -------
        float array (self.nelem(),)
            An array with the volume of each element.

        Raises
        ------
        ValueError
            If the Formex is not of plexitude 4.

        Examples
        --------
        >>> Formex('4:164I').volumes()
        array([0.1667])
        """
        if self.nplex() != 4:
            raise ValueError(f"Expected a 4-plex Formex, got {self.nplex()}")
        return geomtools.levelVolumes(self.coords)

    #################### Read from string/file ################################
    #
    # See also Geometry.read and Geometry.write
    #

    @classmethod
    def fromstring(clas, s, sep=' ', nplex=1, ndim=3, count=-1):
        """Create a :class:`Formex` reading coordinates from a string.

        This uses the :meth:`Coords.fromstring` method to read coordinates
        from a string and restructures them into a Formex of the specified
        plexitude.

        Parameters
        ----------
        s: str
            A string containing a single sequence of float numbers separated
            by whitespace and a possible separator string.
        sep: str, optional
            The separator used between the coordinates. If not a space,
            all extra whitespace is ignored.
        nplex: int, optional
            Plexitude of the elements to be read.
        ndim: int, optional
            Number of coordinates per point. Should be 1, 2 or 3 (default).
            If 1, resp. 2, the coordinate string only holds x, resp. x,y
            values.
        count: int, optional
            Total number of coordinates to read. This should be a multiple
            of `ndim`. The default is to read all the coordinates in the
            string.

        Returns
        -------
        Formex
            A Formex object of the given plexitude, with the coordinates
            read from the string.

        Raises
        ------
        ValueError
            If count was provided and the string does not contain that exact
            number of coordinates.
            If the number of points read is not a multiple of nplex.

        Examples
        --------
        >>> Formex.fromstring('4 0 0 3 1 2 6 5 7',nplex=3)
        Formex([[[4.,  0.,  0.],
                [3.,  1.,  2.],
                [6.,  5.,  7.]]])

        """
        x = Coords.fromstring(s, sep=sep, ndim=ndim, count=count)
        if x.shape[0] % nplex != 0:
            raise RuntimeError(f"Number of points read: {x.shape[0]}, "
                               f"expected a multiple of {nplex}!")
        return clas(x.reshape(-1, nplex, 3))

    @classmethod
    def fromfile(clas, fil, nplex=1, **kargs):
        """Read the coordinates of a Formex from a file

        This uses :meth:`Coords.fromfile` to read coordinates from a file
        and create a Formex of the specified plexitude.
        Coordinates X, Y and Z for subsequent points
        are read from the file. The total number of coordinates on the file
        should be a multiple of 3.

        Parameters
        ----------
        fil: str or file
            If str, it is a file name. An open file object can also be passed
        nplex: int, optional
            Plexitude of the elements to be read.
        **kargs:
            Arguments to be passed to :func:`numpy.fromfile`.

        Returns
        -------
        Formex
            A Formex object of the given plexitude, with the coordinates
            read from the specified file.

        Raises
        ------
        ValueError
            If the number of coordinates read is not a multiple of 3 * nplex.

        See Also
        --------
        Coords.fromfile: read a Coords object from file
        numpy.fromfile: read an array to file

        """
        x = Coords.fromfile(fil, **kargs)
        if x.shape[0] % nplex != 0:
            raise RuntimeError(
                f"Number of points read: {x.shape[0]}, "
                f"should be multiple of {nplex}!")
        return clas(x.reshape(-1, nplex, 3))

    def actor(self, **kargs):
        """Create a drawable representation of the Formex"""
        from pyformex.opengl.actors import Actor

        if self.nelems() == 0:
            return None

        return Actor(self, **kargs)

    #########################################################################
    #
    # Obsolete and deprecated methods
    #
    nnodes = npoints

    @utils.deprecated_by('Formex.divide', 'Formex.subdivide')
    def divide(self, div):
        return self.subdivide(div)

    @utils.deprecated_by('Formex.withProp', 'Formex.selectProp')
    def withProp(self, val):
        return self.selectProp(val)

    @utils.deprecated_by('Formex.elbbox', 'Formex.bboxes')
    def elbbox(self):
        return Formex(self.bboxes())

    ###################
    ## PZF interface ##

    def pzf_dict(self):
        kargs = Geometry.pzf_dict(self)
        if self.eltype:
            kargs[f"eltype:s__{self.eltype}"] = None
        return kargs

    pzf_args = ['coords']


##############################################################################
#
#    Functions which are not Formex class methods
#
##################################################

# TODO: this should be made a Formex class method

def connect(Flist, nodid=None, bias=None, loop=False, eltype=None):
    """Return a Formex which connects the Formices in list.

    Creates a Formex of any plexitude by combining corresponding
    points from a number of Formices.

    Parameters
    ----------
    Flist: list of Formices
        The Formices to connect. The number of Formices in the list will
        be the plexitude of the newly created Formex. One point of an element
        in each Formex is taken to create a new element in the output Formex.
    nodid: list of int, optional
        List of point indices to be used from each of the input Formices.
        If provided, the list should have the same length as ``Flist``.
        The default is to use the first point of each element.
    bias: list of int, optional
        List of element bias values for each of the input Formices. Element
        iteration in the Formices will start at this number.
        If provided,, the list should have the same length as ``Flist``.
        The default is to start at element 0.
    loop: bool
        If False (default), element generation will stop when the first
        input Formex runs out of elements. If True, element iteration in the
        shorted Formices will wrap around until all elements in all
        Formices have been used.

    Returns
    -------
    Formex
        A Formex with plexitude equal to ``len(Flist)``.
        Each element of the Formex consists of a point from the corresponding
        element of each of the Formices in list. By default
        this is the first point of that element, but a ``nodid`` list may
        specify another point index.
        Corresponding elements in the Formices are by default those with the
        same element index; the ``bias`` argument may specify another value
        to start the element indexing for each of the input Formices.

        If loop is False (default), the number of elements is the minimum
        over all Formices of the number of elements minus the corresponding
        bias. If loop is True, the number of elements is the maximum of the
        number of elements of all input Formices.

    Notes
    -----
    See also example Connect.

    Examples
    --------
    >>> F = Formex('1:1111')
    >>> G = Formex('l:222')
    >>> connect([F,G])
    Formex([[[1.,  0.,  0.],
             [0.,  0.,  0.]],
    <BLANKLINE>
            [[2.,  0.,  0.],
             [0.,  1.,  0.]],
    <BLANKLINE>
            [[3.,  0.,  0.],
             [0.,  2.,  0.]]])
    >>> connect([F,G],nodid=[0,1])
    Formex([[[1.,  0.,  0.],
             [0.,  1.,  0.]],
    <BLANKLINE>
            [[2.,  0.,  0.],
             [0.,  2.,  0.]],
    <BLANKLINE>
            [[3.,  0.,  0.],
             [0.,  3.,  0.]]])
    >>> connect([F,F],bias=[0,1])
    Formex([[[1.,  0.,  0.],
             [2.,  0.,  0.]],
    <BLANKLINE>
            [[2.,  0.,  0.],
             [3.,  0.,  0.]],
    <BLANKLINE>
            [[3.,  0.,  0.],
             [4.,  0.,  0.]]])
    >>> connect([F,F],bias=[0,1],loop=True)
    Formex([[[1.,  0.,  0.],
             [2.,  0.,  0.]],
    <BLANKLINE>
            [[2.,  0.,  0.],
             [3.,  0.,  0.]],
    <BLANKLINE>
            [[3.,  0.,  0.],
             [4.,  0.,  0.]],
    <BLANKLINE>
            [[4.,  0.,  0.],
             [1.,  0.,  0.]]])

    """
    try:
        m = len(Flist)
        for i in range(m):
            if isinstance(Flist[i], Formex):
                pass
            elif isinstance(Flist[i], np.ndarray):
                Flist[i] = Formex(Flist[i])
            else:
                raise TypeError
    except TypeError:
        raise TypeError('connect(): first argument should be a list of formices')

    if not nodid:
        nodid = [0 for i in range(m)]
    if not bias:
        bias = [0 for i in range(m)]
    if loop:
        n = max([Flist[i].nelems() for i in range(m)])
    else:
        n = min([Flist[i].nelems() - bias[i] for i in range(m)])
    f = np.zeros((n, m, 3), dtype=at.Float)
    for i, j, k in zip(range(m), nodid, bias):
        v = Flist[i].coords[k:k+n, j, :]
        if loop and k > 0:
            v = np.concatenate([v, Flist[i].coords[:k, j, :]])
        f[:, i, :] = np.resize(v, (n, 3))
    return Formex(f, eltype=eltype)


def _sane_side(side):
    """Allow some old variants of arguments_"""
    if isinstance(side, str):
        if side.startswith('pos'):
            side = '+'
        if side.startswith('neg'):
            side = '-'
    if not (side == '+' or side == '-'):
        side = ''
    return side


def _select_side(side, alist):
    """Return selected parts dependent on side_"""
    if side == '+':
        return alist[0]
    elif side == '-':
        return alist[1]
    else:
        return List(alist)


def _cut2AtPlane(F, p, n, side='', atol=None, newprops=None):
    """Returns all elements of the Formex cut at plane.

    F is a Formex of plexitude 2.
    p is a point specified by 3 coordinates.
    n is the normal vector to a plane, specified by 3 components.

    The return value is:

    - with side = '+' or '-' :
      a Formex of the same plexitude with all elements
      located completely at the positive/negative side of the plane(s) (p,n)
      retained, all elements lying completely at the negative/positive side
      removed and the elements intersecting the plane(s) replaced by new
      elements filling up the parts at the positive/negative side.
    - with side = '': two Formices of the same plexitude, one representing
      the positive side and one representing the negative side.

    To avoid roundoff errors and creation of very small elements,
    a tolerance can be specified. Points lying within the tolerance
    distance will be considered lying in the plane, and no cutting near
    these points.

    >>> F = Formex('l:2').replic(2)
    """
    side = _sane_side(side)
    if atol is None:
        atol = 1.e-5 * F.dsize()
    tp, tc, tn = F.testPlane(p, n, atol)
    A = F.select(tp)
    B = F.select(tn)
    if newprops:
        A.setProp(newprops[0])
        B.setProp(newprops[1])
    if tc.any():
        G = F.select(tc)
        H = G.copy()
        x = geomtools.intersectSegmentWithPlane(
            G.coords, p, n, mode='pair', atol=atol)
        i0 = G.coords[:, 1].distanceFromPlane(p, n) >= 0.0
        i1 = ~i0
        G[i0, 0, :] = H[i0, 1, :] = x[i0]
        G[i1, 1, :] = H[i1, 0, :] = x[i1]
        if newprops:
            G.setProp(newprops[2])
            H.setProp(newprops[3])
        A += G
        B += H
    return _select_side(side, [A, B])


def _cut3AtPlane(F, p, n, side='', atol=None, newprops=None):
    """_Returns all elements of the Formex cut at plane(s).

    F is a Formex of plexitude 3.
    p is a point or a list of points.
    n is the normal vector to a plane or a list of normal vectors.
    Both p and n have shape (3) or (npoints,3).

    The return value is:

    - with side='+' or '-' or 'positive'or 'negative' :
      a Formex of the same plexitude with all elements
      located completely at the positive/negative side of the plane(s) (p,n)
      retained, all elements lying completely at the negative/positive side
      removed and the elements intersecting the plane(s) replaced by new
      elements filling up the parts at the positive/negative side.
    - with side='': two Formices of the same plexitude, one representing
      the positive side and one representing the negative side.

    Let :math:`dist` be the signed distance of the vertices to a plane.
    The elements located completely at the positive or negative side of
    a plane have three vertices for which :math:`|dist|>atol`.
    The elements intersecting a plane can have one or more vertices for which
    :math:`|dist|<atol`.
    These vertices are projected on the plane so that their distance is zero.

    If the Formex has a property set, the new elements will get the property
    numbers defined in newprops. This is a list of 7 property numbers flagging
    elements with following properties:

    0) no vertices with :math:`|dist|<atol`, triangle after cut
    1) no vertices with :math:`|dist|<atol`, triangle 1 from quad after cut
    2) no vertices with :math:`|dist|<atol`, triangle 2 from quad after cut
    3) one vertex with :math:`|dist|<atol`, two vertices at pos. or neg. side
    4) one vertex with :math:`|dist|<atol`, one vertex at pos. side, one at neg.
    5) two vertices with :math:`|dist|<atol`, one vertex at pos. or neg. side
    6) three vertices with :math:`|dist|<atol`
    """
    if atol is None:
        atol = 1.e-5*F.dsize()
    # make sure we have sane newprops
    if newprops is None:
        newprops = [None, ]*7
    else:
        try:
            newprops = newprops[:7]
            for prop in newprops:
                if not (prop is None or at.isInt(prop)):
                    raise ValueError("newprops values should be int")
        except ValueError:
            newprops = np.arange(7)
    side = _sane_side(side)

    p = np.asarray(p).reshape(-1, 3)
    n = np.asarray(n).reshape(-1, 3)
    nplanes = len(p)
    # elements having part at positive side of all planes
    test = np.stack([F.test('any', n[i], p[i], atol=atol)
                     for i in range(nplanes)]).all(axis=0)
    # save elements having part at positive side of all planes
    F_pos = F.clip(test)
    if side in '-':  # Dirty trick: this also includes side='' !
        # save elements completely at negative side of one of the planes
        F_neg = F.cclip(test)
    else:
        F_neg = None
    if F_pos.nelems() != 0:
        # elements completely at positive side of all planes
        test = np.stack([F_pos.test('all', n[i], p[i], atol=-atol)
                         for i in range(nplanes)]).all(axis=0)
        # save elements that will be cut by one of the planes
        F_cut = F_pos.cclip(test)
        # save elements completely at positive side of all planes
        F_pos = F_pos.clip(test)
        if F_cut.nelems() != 0:
            if nplanes == 1:
                if side == '+':
                    F_pos += _cutElements3AtPlane(
                        F_cut, p[0], n[0], newprops, side, atol)
                elif side == '-':
                    F_neg += _cutElements3AtPlane(
                        F_cut, p[0], n[0], newprops, side, atol)
                elif side == '':
                    cut_pos, cut_neg = _cutElements3AtPlane(
                        F_cut, p[0], n[0], newprops, side, atol)
                    F_pos += cut_pos
                    F_neg += cut_neg
            elif nplanes > 1:
                S = F_cut
                for i in range(nplanes):
                    if i > 0:
                        # due to the projection of vertices with |distance| <
                        # atol on plane i-1, some elements can be completely
                        # at negative side of plane i instead of cut by plane i
                        t = S.test('any', n[i], p[i], atol=atol)
                        if side in '-':
                            # save elements at negative side of plane i
                            F_neg += S.cclip(t)
                        S = S.clip(t)  # save at positive side of plane i
                    t = S.test('all', n[i], p[i], atol=-atol)
                    R = S.clip(t)  # save elements at + side of plane i
                    S = S.cclip(t)  # save elements cut by plane i
                    if side == '+':
                        cut_pos = _cutElements3AtPlane(
                            S, p[i], n[i], newprops, '+', atol)
                    elif side in '-':
                        cut_pos, cut_neg = _cutElements3AtPlane(
                            S, p[i], n[i], newprops, '', atol)
                        F_neg += cut_neg
                    S = R + cut_pos
                F_pos += S

    return _select_side(side, [F_pos, F_neg])


def _cutElements3AtPlane(F, p, n, newprops=None, side='', atol=0.):
    """_This function needs documentation.

    Should it be called by the user? or only via _cut3AtPlane?
    For now, lets suppose the last, so no need to check arguments here.

    newprops should be a list of 7 values: each an integer or None
    side is either '+', '-' or ''
    """
    if atol is None:
        atol = 1.e-5*F.dsize()

    def get_new_prop(p, ind, newp):
        """Determines the value of the new props for a subset.

        p are the original props (possibly None)
        ind is the list of elements to treat
        newp is the new property value.

        The return value is determined as follows:

        - If p is None: return None (no property set)
        - If p is set, but newp is None: return p[ind] : keep original
        - if p is set, and newp is set: return newp (single value)
        """
        if p is None:
            return None
        elif newp is None:
            return p[ind]
        else:
            return newp

    # TODO: this should go via trisurface?
    C = [connect([F, F], nodid=ax) for ax in [[0, 1], [1, 2], [2, 0]]]
    with np.errstate(divide='ignore', invalid='ignore'):
        res = [geomtools.intersectSegmentWithPlane(
            Ci.coords, p, n, mode='pair', atol=atol, returns='tx'
        ) for Ci in C]
    t = np.column_stack([r[0] for r in res])
    P = np.stack([r[1] for r in res], axis=1)
    del res
    T = (t >= 0.)*(t <= 1.)
    d = F.coords.distanceFromPlane(p, n)
    U = abs(d) < atol
    V = U.sum(axis=-1)  # number of vertices with |distance| < atol
    F1_pos = F2_pos = F3_pos = F4_pos = F5_pos = F6_pos = F7_pos = F1_neg = \
        F2_neg = F3_neg = F4_neg = F5_neg = F6_neg = F7_neg = Formex()
    # No vertices with |distance| < atol => triangles with 2 intersections
    w1 = np.where(V==0)[0]
    if w1.size > 0:
        T1 = T[w1]
        P1 = P[w1][T1].reshape(-1, 2, 3)
        F1 = F[w1]
        d1 = d[w1]
        if F.prop is None:
            p1 = None
        else:
            p1 = F.prop[w1]
        # split problem in two cases
        # case 1: triangle at positive side after cut
        w11 = np.where(d1[:, 0]*d1[:, 1]*d1[:, 2] > 0.)[0]
        # case 2: quadrilateral at positive side after cut
        w12 = np.where(d1[:, 0]*d1[:, 1]*d1[:, 2] < 0.)[0]
        # case 1: triangle at positive side after cut
        if w11.size > 0:
            T11 = T1[w11]
            P11 = P1[w11]
            F11 = F1[w11]
            if side in '+':
                v1 = np.where(T11[:, 0]*T11[:, 2] == 1, 0,
                              np.where(T11[:, 0]*T11[:, 1] == 1, 1, 2))
                K1 = np.asarray([F11[j, v1[j]] for j in
                                 range(F11.shape[0])]).reshape(-1, 1, 3)
                E1_pos = np.column_stack([P11, K1])
                F1_pos = Formex(E1_pos, get_new_prop(p1, w11, newprops[0]))
            if side in '-':  # quadrilateral at negative side after cut
                v2 = np.where(T11[:, 0]*T11[:, 2] == 1, 2,
                              np.where(T11[:, 0]*T11[:, 1] == 1, 2, 0))
                v3 = np.where(T11[:, 0]*T11[:, 2] == 1, 1,
                              np.where(T11[:, 0]*T11[:, 1] == 1, 0, 1))
                K2 = np.asarray([F11[j, v2[j]] for j in
                                 range(F11.shape[0])]).reshape(-1, 1, 3)
                K3 = np.asarray([F11[j, v3[j]] for j in
                                 range(F11.shape[0])]).reshape(-1, 1, 3)
                E2_neg = np.column_stack([P11, K2])
                F2_neg = Formex(E2_neg, get_new_prop(p1, w11, newprops[1]))
                E3_neg = np.column_stack([P11[:, 0].reshape(-1, 1, 3), K2, K3])
                F3_neg = Formex(E3_neg, get_new_prop(p1, w11, newprops[2]))
        # case 2: quadrilateral at positive side after cut
        if w12.size > 0:
            T12 = T1[w12]
            P12 = P1[w12]
            F12 = F1[w12]
            if side in '+':
                v2 = np.where(T12[:, 0]*T12[:, 2] == 1, 2,
                              np.where(T12[:, 0]*T12[:, 1] == 1, 2, 0))
                v3 = np.where(T12[:, 0]*T12[:, 2] == 1, 1,
                              np.where(T12[:, 0]*T12[:, 1] == 1, 0, 1))
                K2 = np.asarray([F12[j, v2[j]] for j in
                                 range(F12.shape[0])]).reshape(-1, 1, 3)
                K3 = np.asarray([F12[j, v3[j]] for j in
                                 range(F12.shape[0])]).reshape(-1, 1, 3)
                E2_pos = np.column_stack([P12, K2])
                F2_pos = Formex(E2_pos, get_new_prop(p1, w12, newprops[1]))
                E3_pos = np.column_stack([P12[:, 0].reshape(-1, 1, 3), K2, K3])
                F3_pos = Formex(E3_pos, get_new_prop(p1, w12, newprops[2]))
            if side in '-':  # triangle at negative side after cut
                v1 = np.where(T12[:, 0]*T12[:, 2] == 1, 0,
                              np.where(T12[:, 0]*T12[:, 1] == 1, 1, 2))
                K1 = np.asarray([F12[j, v1[j]] for j in
                                 range(F12.shape[0])]).reshape(-1, 1, 3)
                E1_neg = np.column_stack([P12, K1])
                F1_neg = Formex(E1_neg, get_new_prop(p1, w12, newprops[0]))
    # One vertex with |distance| < atol
    w2 = np.where(V==1)[0]
    if w2.size > 0:
        F2 = F[w2]
        d2 = d[w2]
        U2 = U[w2]
        if F.prop is None:
            p2 = None
        else:
            p2 = F.prop[w2]
        # split problem in three cases
        W = (d2 > atol).sum(axis=-1)
        w21 = np.where(W == 2)[0]  # case 1: two vertices at positive side
        w22 = np.where(W == 1)[0]  # case 2: one vertex at positive side
        w23 = np.where(W == 0)[0]  # case 3: no vertices at positive side
        # case 1: two vertices at positive side
        if w21.size > 0 and side in '+':
            F21 = F2[w21]
            U21 = U2[w21]
            K1 = F21[U21]  # vertices with |distance| < atol
            n = at.normalize(n)
            # project vertices on plane (p,n)
            K1 = (K1 - n*d2[w21][U21].reshape(-1, 1)).reshape(-1, 1, 3)
            K2 = F21[d2[w21]>atol].reshape(-1, 2, 3)  # verts with dist > atol
            E4_pos = np.column_stack([K1, K2])
            F4_pos = Formex(E4_pos, get_new_prop(p2, w21, newprops[3]))
        # case 2: one vertex at positive side
        if w22.size > 0:
            F22 = F2[w22]
            U22 = U2[w22]
            K1 = F22[U22]  # vertices with |distance| < atol
            # project vertices on plane (p,n)
            K1 = (K1 - n*d2[w22][U22].reshape(-1, 1)).reshape(-1, 1, 3)
            # intersection points
            P22 = P[w2][w22][np.roll(U22, 1, axis=-1)].reshape(-1, 1, 3)
            if side in '+':
                K2 = F22[d2[w22]>atol].reshape(-1, 1, 3)  # verts with dist > atol
                E5_pos = np.column_stack([P22, K1, K2])
                F5_pos = Formex(E5_pos, get_new_prop(p2, w22, newprops[4]))
            if side in '-':
                K3 = F22[d2[w22]<-atol].reshape(-1, 1, 3)  # verts with dist < -atol
                E5_neg = np.column_stack([P22, K1, K3])
                F5_neg = Formex(E5_neg, get_new_prop(p2, w22, newprops[4]))
        # case 3: no vertices at positive side
        if w23.size > 0 and side in '-':
            F23 = F2[w23]
            U23 = U2[w23]
            K1 = F23[U23]  # vertices with |distance| < atol
            # project vertices on plane (p,n)
            K1 = (K1 - n*d2[w23][U23].reshape(-1, 1)).reshape(-1, 1, 3)
            # vertices with distance < - atol
            K2 = F23[d2[w23]<-atol].reshape(-1, 2, 3)
            E4_neg = np.column_stack([K1, K2])
            F4_neg = Formex(E4_neg, get_new_prop(p2, w23, newprops[3]))
    # Two vertices with |distance| < atol
    w3 = np.where(V==2)[0]
    if w3.size > 0:
        F3 = F[w3]
        d3 = d[w3]
        U3 = U[w3]
        # split problem in two cases
        W = (d3 > atol).sum(axis=-1)
        w31 = np.where(W == 1)[0]  # case 1: one vertex at positive side
        w32 = np.where(W == 0)[0]  # case 2: no vertices at positive side
        # case 1: one vertex at positive side
        if w31.size > 0 and side in '+':
            F31 = F3[w31]
            U31 = U3[w31]
            K1 = F31[U31]  # vertices with |distance| < atol
            # project vertices on plane (p,n)
            K1 = (K1 - n*d3[w31][U31].reshape(-1, 1)).reshape(-1, 2, 3)
            K2 = F31[d3[w31]>atol].reshape(-1, 1, 3)  # verts with dist > atol
            E6_pos = np.column_stack([K1, K2])
            F6_pos = Formex(E6_pos, get_new_prop(F.prop, w31, newprops[5]))
        # case 2: no vertices at positive side
        if w32.size > 0 and side in '-':
            F32 = F3[w32]
            U32 = U3[w32]
            K1 = F32[U32]  # vertices with |distance| < atol
            # project vertices on plane (p,n)
            K1 = (K1 - n*d3[w32][U32].reshape(-1, 1)).reshape(-1, 2, 3)
            K2 = F32[d3[w32]<-atol].reshape(-1, 1, 3)  # verts with dist < -atol
            E6_neg = np.column_stack([K1, K2])
            F6_neg = Formex(E6_neg, get_new_prop(F.prop, w32, newprops[5]))
    # Three vertices with |distance| < atol
    w4 = np.where(V==3)[0]
    if w4.size > 0:
        F4 = F[w4]
        d4 = d[w4]
        U4 = U[w4]
        if side in '+':
            K1 = F4[U4]  # vertices with |distance| < atol
            # project vertices on plane (p,n)
            K1 = (K1 - n*d4[U4].reshape(-1, 1)).reshape(-1, 3, 3)
            E7_pos = K1
            F7_pos = Formex(E7_pos, get_new_prop(F.prop, w4, newprops[6]))
        if side in '-':
            E7_neg = K1
            F7_neg = Formex(E7_neg, get_new_prop(F.prop, w4, newprops[6]))
    # join all the pieces
    if side in '+':
        cut_pos = F1_pos+F2_pos+F3_pos+F4_pos+F5_pos+F6_pos+F7_pos
    if side in '-':
        cut_neg = F1_neg+F2_neg+F3_neg+F4_neg+F5_neg+F6_neg+F7_neg

    if side == '+':
        return cut_pos
    elif side == '-':
        return cut_neg
    else:
        return [cut_pos, cut_neg]


# End
