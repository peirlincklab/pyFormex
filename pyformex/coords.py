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
"""A structured collection of 3D coordinates.

The :mod:`coords` module defines the :class:`Coords` class, which is the basic
data structure in pyFormex to store the coordinates of points in a 3D space.

This module implements a data class for storing large sets of 3D coordinates
and provides an extensive set of methods for transforming these coordinates.
Most of pyFormex's classes which represent geometry (e.g.
:class:`~formex.Formex`, :class:`~mesh.Mesh`, :class:`~trisurface.TriSurface`,
:class:`~curve.Curve`) use a
:class:`Coords` object to store their coordinates, and thus inherit all the
transformation methods of this class.

While the user will mostly use the higher level classes, he might occasionally
find good reason to use the :class:`Coords` class directly as well.
"""
import re

import numpy as np

from pyformex import arraytools as at
from pyformex import utils

__all__ = ['Coords', 'bbox', 'bboxIntersection', 'origin',
           'pattern', 'xpattern', 'fpattern', 'align']

_numpy_printoptions_ = {'precision': 2}

class ProjectionMissing(Exception):
    pass

###########################################################################
##
##   class Coords
##
#########################


@utils.pzf_register
class Coords(np.ndarray):
    #
    # :DEV
    # Because we have a __new__ constructor and no __init__,
    # we have to put the signature of the object creation explicitely
    # in the first line of the docstring.
    #
    """Coords(data=None,dtyp=at.Float,copy=False)

    A structured collection of points in a 3D cartesian space.

    The :class:`Coords` class is the basic data structure used throughout
    pyFormex to store the coordinates of points in a 3D space.
    It is used by other classes, such as :class:`~formex.Formex`,
    :class:`~mesh.Mesh`, :class:`~trisurface.TriSurface`,
    :class:`~curve.Curve`, which thus inherit the same transformation
    capabilities. Applications will mostly use the higher level
    classes, which have more elaborated consistency checking
    and error handling.

    :class:`Coords` is implemented as a subclass of :class:`numpy.ndarray`,
    and thus inherits all its methods and atttributes.
    The last axis of the :class:`Coords` however always has a length equal
    to 3. Each set of 3 values along the last axis are the coordinates (in a
    global 3D cartesian coordinate system) of a single point in space.
    The full Coords array thus is a collection of points. It the array is
    2-dimensional, the Coords is a flat list of points. But if the array
    has more dimensions, the collection of points itself becomes structured.

    The float datatype is only checked at creation time. It is the
    responsibility of the user to keep this consistent
    throughout the lifetime of the object.

    Note
    ----
    Methods that transform a Coords object, like
    :meth:`scale`, :meth:`translate`, :meth:`rotate`, ...
    do not change the original Coords object, but return a new object.
    Some methods however have an `inplace` option that allows the user
    to force coordinates to be changed in place. This option is seldom
    used however: rather we conveniently use statements like::

        X = X.some_transform()

    and Python can immediately free and recollect the memory used for the old
    object X.


    Parameters
    ----------
    data: float :term:`array_like`, or string
        Data to initialize the Coords. The last axis should have a length
        of 1, 2 or 3, but will be expanded to 3 if it is less, filling the
        missing coordinates with zeros. Thus, if you only specify two
        coordinates, all points are lying in the z=0 plane. Specifying only
        one coordinate creates points along the x-axis.

        As a convenience, data may also be entered as a string, which will be
        passed to the :func:`pattern` function to create the actual
        coordinates of the points.

        If no data are provided, an empty Coords with shape (0,3) is created.
    dtyp: float datatype, optional
        It not provided, the datatype of ``data`` is used, or the default
        :py:attr:`~arraytools.Float` (which is equivalent to
        :data:`numpy.float32`).
    copy: bool
        If True, the data are copied. The default setting will try to use
        the original data if possible, e.g. if `data` is a correctly shaped and
        typed :class:`numpy.ndarray`.

    Returns
    -------
    : Coords
        An instance of the Coords class, which is basically an ndarray
        of floats, with the last axis having a length of 3.


    The Coords instance has a number of attributes that provide views on
    (part of) the data. They are a notational convenience over using indexing.
    These attributes can be used to set all or some of the coordinates
    by direct assignment. The assigned data should however be broadcast
    compatible with the assigned shape: the shape of the Coords can
    not be changed.

    Examples
    --------
    >>> Coords([1.,2.])
    Coords([1., 2., 0.])
    >>> X = Coords(np.arange(6).reshape(2,3))
    >>> print(X)
    [[0. 1. 2.]
     [3. 4. 5.]]
    >>> print(X.y)
    [1. 4.]
    >>> X.z[1] = 9.
    >>> print(X)
    [[0. 1. 2.]
     [3. 4. 9.]]
    >>> print(X.xz)
    [[0. 2.]
     [3. 9.]]
    >>> X.x = 0.
    >>> print(X)
    [[0. 1. 2.]
     [0. 4. 9.]]

    >>> Y = Coords(X)             # Y shares its data with X
    >>> Z = Coords(X, copy=True)  # Z is independent
    >>> Y.y = 5
    >>> Z.z = 6
    >>> print(X)
    [[0.  5.  2.]
     [0.  5.  9.]]
    >>> print(Y)
    [[0.  5.  2.]
     [0.  5.  9.]]
    >>> print(Z)
    [[0.  1.  6.]
     [0.  4.  6.]]
    >>> X.coords is X
    True
    >>> Z.xyz = [1,2,3]
    >>> print(Z)
    [[1.  2.  3.]
     [1.  2.  3.]]

    >>> print(Coords('0123'))  # initialize with string
    [[0. 0. 0.]
     [1. 0. 0.]
     [1. 1. 0.]
     [0. 1. 0.]]

    """
    # REMOVED from docstring:

    # Attributes
    # ----------
    # xyz: float array
    #     The full coordinate array as an ndarray.
    # x: float array
    #     The X coordinates of the points as an ndarray with shape
    #     :meth:`pshape()`.
    # y: float array
    #     The Y coordinates of the points as an ndarray with shape
    #     :meth:`pshape()`.
    # z: float array
    #     The Z coordinates of the points as an ndarray with shape
    #     :meth:`pshape()`.
    # xy: float array
    #     The X and Y coordinates of the points as an ndarray with shape
    #     :meth:`pshape()` + (2,).
    # xz: float array
    #     The X and Z coordinates of the points as an ndarray with shape
    #     :meth:`pshape()` + (2,).
    # yz: float array
    #     The Y and Z coordinates of the points as an ndarray with shape
    #     :meth:`pshape()` + (2,).

    _exclude_members_ = ['actor', 'swapaxes']

    #
    # TODO
    # Because the Coords class is sticky, results that are not conforming
    # to the requirements of being a Coords array, should be converted to
    # the general array class:   e.g.   return asarray(T)
    #
    # This could probably NOT be done in an __array_finalize__ method
    # Maybe by overloading __getitem__, but should we bother???
    #

    def __new__(clas, data=None, dtyp=at.Float, copy=False):
        """Create a new instance of :class:`Coords`."""

        if data is None:
            # create an empty array : we need at least a 2D array
            # because we want the last axis to have length 3 and
            # we also need an axis with length 0 to have size 0
            ar = np.ndarray((0, 3), dtype=dtyp)
        else:
            # turn the data into an array, and copy if requested
            # DO NOT ADD ndmin=1 HERE ! (see below)
            if isinstance(data, str):
                data = pattern(data, aslist=True)
            ar = np.array(data, dtype=dtyp, copy=copy)

        if ar.dtype.kind != 'f':
            raise ValueError("data type should be of kind 'f'")

        #
        # The Coords object needs to be at least 1-D array, no a scalar
        # We could force 'ar' above to be at least 1-D, but that would
        # turn every scalar into a 1-D vector, which would circumvent
        # detection of input errors (e.g. with translation, where input
        # can be either a vector or an axis number)
        #
        if ar.ndim == 0:
            raise ValueError("Expected array data, not a scalar")

        if ar.shape[-1] == 3:
            pass
        elif ar.shape[-1] in [1, 2]:
            # make last axis length 3, adding 0 values
            ar = at.growAxis(ar, 3-ar.shape[-1], -1)
        elif ar.shape[-1] == 0:
            # allow empty coords objects
            ar = ar.reshape(0, 3)
        else:
            raise ValueError("Expected a length 1,2 or 3 for last array axis")

        # Make sure dtype is a float type
        # This should not be needed in view of the above
        assert (ar.dtype.kind == 'f')

        # Transform 'subarr' from an ndarray to our new subclass.
        ar = ar.view(clas)

        return ar


    @staticmethod
    def __is_valid__(obj):
        """Check that an array is valid as Coords"""
        return obj.shape[-1] == 3


    # overload some some ndarray methods that could easily return
    # invalid Coords


    def __getitem__(self, i):
        # this detects simple cases that should return ndarray
        res = np.ndarray.__getitem__(self, i)
        if res.ndim < 1 or res.shape[-1] != 3:
            res = res.view(np.ndarray)
        return res


    def swapaxes(self, *args, **kargs):
        res = np.ndarray.swapaxes(self, *args, **kargs)
        if not Coords.__is_valid__(res):
            res = res.view(np.ndarray)
        return res

    ################ property methods ##########

    @property
    def xyz(self):
        """Returns the coordinates of the points as an ndarray.

        Returns an ndarray with shape `self.shape` except last axis
        is reduced to 2, providing a view on all the coordinates
        of all the points.

        """
        return self.view(np.ndarray)

    @property
    def x(self):
        """Returns the X-coordinates of all points.

        Returns an ndarray with shape `self.pshape()`, providing a view
        on the X-coordinates of all the points.

        """
        return self.xyz[..., 0]

    @property
    def y(self):
        """Returns the Y-coordinates of all points.

        Returns an ndarray with shape `self.pshape()`, providing a view
        on the Y-coordinates of all the points.

        """
        return self.xyz[..., 1]

    @property
    def z(self):
        """Returns the Z-coordinates of all points.

        Returns an ndarray with shape `self.pshape()`, providing a view
        on the Z-coordinates of all the points.

        """
        return self[..., 2].view(np.ndarray)

    @property
    def xy(self):
        """Returns the X- and Y-coordinates of all points.

        Returns an ndarray with shape `self.shape` except last axis
        is reduced to 2, providing a view on the X- and Y-coordinates
        of all the points.

        """
        return self.xyz[..., :2]

    @property
    def xz(self):
        """Returns the X- and Y-coordinates of all points.

        Returns an ndarray with shape `self.shape` except last axis
        is reduced to 2, providing a view on the X- and Z-coordinates
        of all the points.

        """
        return self.xyz[..., (0, 2)]

    @property
    def yz(self):
        """Returns the X- and Y-coordinates of all points.

        Returns an ndarray with shape `self.shape` except last axis
        is reduced to 2, providing a view on the Y- and Z-coordinates
        of all the points.

        """
        return self.xyz[..., 1:]

    ################ property setters ##############

    @xyz.setter
    def xyz(self, value):
        """Set the XYZ coordinates of the points"""
        self[...] = value

    @x.setter
    def x(self, value):
        """Set the X coordinates of the points"""
        self[..., 0] = value

    @y.setter
    def y(self, value):
        """Set the Y coordinates of the points"""
        self[..., 1] = value

    @z.setter
    def z(self, value):
        """Set the Z coordinates of the points"""
        self[..., 2] = value

    @xy.setter
    def xy(self, value):
        """Set the XY coordinates of the points"""
        self[..., :2] = value

    @xz.setter
    def xz(self, value):
        """Set the XZ coordinates of the points"""
        self[..., (0, 2)] = value

    @yz.setter
    def yz(self, value):
        """Set the YZ coordinates of the points"""
        self[..., 1:] = value

    @property
    def coords(self):
        """Returns the `Coords` object .

        This exists only for consistency with other classes.
        """
        return self

    ################ end property methods ##########


    # def __repr__(self):
    #     """String representation of a Coords

    #     Examples
    #     --------
    #     >>> Coords([1.0,2.0,3.0])
    #     Coords([1., 2., 3.])

    #     """
    #     res = np.ndarray.__repr__(self)
    #     if self.dtype == at.Float:
    #         res = res.replace(', dtype=float32','')
    #     return res


    def fprint(self, fmt="%10.3e %10.3e %10.3e"):
        # TODO: this is a candidate for the library
        # (possibly in a more general arrayprint form)
        # (could be common with calpy)
        """Formatted printing of the points of a :class:`Coords` object.

        Parameters
        ----------
        fmt: string
            Format to be used to print a single point.
            The supplied format should contain exactly 3 formatting
            sequences, ome for each of the three coordinates.

        Examples
        --------
        >>> x = Coords([[[0.,0.],[1.,0.]],[[0.,1.],[0.,2.]]])
        >>> x.fprint()
        0.000e+00  0.000e+00  0.000e+00
        1.000e+00  0.000e+00  0.000e+00
        0.000e+00  1.000e+00  0.000e+00
        0.000e+00  2.000e+00  0.000e+00
        >>> x.fprint("%5.2f"*3)
        0.00 0.00 0.00
        1.00 0.00 0.00
        0.00 1.00 0.00
        0.00 2.00 0.00

        """
        for p in self.points():
            print(fmt % tuple(p))


    #######################################################################
    #
    #   Methods that return information about a Coords object or other
    #   views on the object data, without changing the object itself.

    # General


    def pshape(self):
        """Return the points shape of the :class:`Coords` object.

        This is the shape of the :class:`numpy.ndarray` with the last axis
        removed.

        Note
        ----
        The full shape of the Coords array can be obtained from
        the inherited (NumPy) shape attribute.

        Examples
        --------
        >>> X = Coords(np.arange(12).reshape(2,1,2,3))
        >>> X.shape
        (2, 1, 2, 3)
        >>> X.pshape()
        (2, 1, 2)

        """
        return self.shape[:-1]


    def points(self):
        """Return the :class:`Coords` object as a flat set of points.

        Returns
        -------
        : Coords
            The Coords reshaped to a 2-dimensional array, flattening
            the structure of the points.

        Examples
        --------
        >>> X = Coords(np.arange(12).reshape(2,1,2,3))
        >>> X.shape
        (2, 1, 2, 3)
        >>> X.points().shape
        (4, 3)
        """
        return self.reshape((-1, 3))

    def npoints(self):
        """Return the total number of points in the Coords.

        Notes
        -----
        `npoints` and `ncoords` are equivalent. The latter exists to provide
        a common interface with other geometry classes.

        Examples
        --------
        >>> Coords(np.arange(12).reshape(2,1,2,3)).npoints()
        4
        """
        return np.array(self.shape[:-1]).prod()

    ncoords = npoints

    # Size, Bounds

    def bbox(self):
        """Return the bounding box of a set of points.

        The bounding box is the smallest rectangular volume in the global
        coordinates, such that no points of the :class:`Coords` are outside
        that volume.

        Returns
        -------
        : Coords (2,3)
            Coords array with two points: the first point contains the
            minimal coordinates, the second has the maximal ones.

        See Also
        --------
        center: return the center of the bounding box
        bboxPoint: return a corner or middle point of the bounding box
        bboxPoints: return all corners of the bounding box

        Examples
        --------
        >>> X = Coords([[0.,0.,0.],[3.,0.,0.],[0.,3.,0.]])
        >>> print(X.bbox())
        [[0. 0. 0.]
         [3. 3. 0.]]
        """
        if self.size > 0:
            x = self.points()
            bb = np.row_stack([x.min(axis=0), x.max(axis=0)])
        else:
            o = origin()
            bb = [o, o]
        return Coords(bb)


    def center(self):
        """Return the center of the :class:`Coords`.

        The center of a Coords is the center of its bbox().
        The return value is a (3,) shaped :class:`Coords` object.

        See also
        --------
        bbox: return the bounding box of the Coords
        centroid: return the average coordinates of the points

        Examples
        --------
        >>> X = Coords([[0.,0.,0.],[3.,0.,0.],[0.,3.,0.]])
        >>> print(X.center())
        [1.5 1.5 0. ]
        """
        X0, X1 = self.bbox()
        return 0.5 * (X0+X1)


    def bboxPoint(self, position):
        """Return a bounding box point of a Coords.

        Bounding box points are points whose coordinates are either
        the minimal value, the maximal value or the middle value
        for the Coords.
        Combining the three values in three dimensions results in
        3**3 = 27 alignment points. The corner points of the
        bounding box are a subset of these.

        Parameters
        ----------
        position: str
            String of three characters, one for each direction 0, 1, 2.
            Each character should be one of the following

                - '-': use the minimal value for that coordinate,
                - '+': use the minimal value for that coordinate,
                - '0': use the middle value for that coordinate.

            Any other character will set the corresponding coordinate to zero.

        Notes
        -----
        A string '000' is equivalent with center(). The values '---' and
        '+++' give the points of the bounding box.

        See Also
        --------
        Coords.align: translate Coords by bboxPoint

        Examples
        --------
        >>> X = Coords([[0.,0.,0.],[1.,1.,1.]])
        >>> print(X.bboxPoint('-0+'))
        [0.  0.5 1. ]

        """
        bb = self.bbox()
        al = {'-': bb[0], '+': bb[1], '0': 0.5*(bb[0]+bb[1])}
        pt = np.zeros(3)
        for i, c in enumerate(position):
            if c in al:
                pt[i] = al[c][i]
        return Coords(pt)


    def bboxPoints(self):
        """Return all the corners of the bounding box point of a Coords.

        Returns
        -------
        : Coords (8,3)
            A Coords with the eight corners of the bounding box, in the order
            of a :py:attr:`elements.Hex8`.

        See also
        --------
        bbox: return only two points, with the minimum and maximum coordinates

        Examples
        --------
        >>> X = Coords([[0.,0.,0.],[3.,0.,0.],[0.,3.,0.]])
        >>> print(X.bboxPoints())
        [[0.  0.  0.]
         [3.  0.  0.]
         [3.  3.  0.]
         [0.  3.  0.]
         [0.  0.  0.]
         [3.  0.  0.]
         [3.  3.  0.]
         [0.  3.  0.]]
        """
        from pyformex.simple import cuboid
        return cuboid(*self.bbox()).coords.reshape(-1, 3)


    def average(self, wts=None, axis=None):
        """Returns a (weighted) average of the :class:`Coords`.

        The average of a Coords is a Coords that is obtained by averaging
        the points along some or all axes.
        Weights can be specified to get a weighted average.

        Parameters
        ----------
        wts: float :term:`array_like`, optional
            Weight to be attributed to the points. If provided, and `axis` is
            an int, `wts` should be 1-dim with the same length as the
            specified axis. Else, it has a shape equal to self.shape or
            self.shape[:-1].
        axis: int or tuple of ints, optional
            If provided, the average is computed along the specified
            axis/axes only. Else, the average is taken over all the points,
            thus over all the axes of the array except the last.

        Notes
        -----
        Averaging over the -1 axis does not make much sense.

        Examples
        --------
        >>> X = Coords([[[0.,0.,0.],[1.,0.,0.],[2.,0.,0.]], \
                [[4.,0.,0.],[5.,0.,0.],[6.,0.,0.]]])
        >>> X = Coords(np.arange(6).reshape(3,2,1))
        >>> X
        Coords([[[0., 0., 0.],
                 [1., 0., 0.]],
        <BLANKLINE>
                [[2., 0., 0.],
                 [3., 0., 0.]],
        <BLANKLINE>
                [[4., 0., 0.],
                 [5., 0., 0.]]])
        >>> print(X.average())
        [2.5  0.   0. ]
        >>> print(X.average(axis=0))
        [[2. 0. 0.]
         [3. 0. 0.]]
        >>> print(X.average(axis=1))
        [[0.5  0.   0. ]
         [2.5  0.   0. ]
         [4.5  0.   0. ]]
        >>> print(X.average(wts=[0.5,0.25,0.25],axis=0))
        [[1.5  0.   0. ]
         [2.5  0.   0. ]]
        >>> print(X.average(wts=[3,1],axis=1))
        [[0.25  0.    0.  ]
         [2.25  0.    0.  ]
         [4.25  0.    0.  ]]
        >>> print(X.average(wts=at.multiplex([3,1],3,0)))
        [2.25  0.    0.  ]
        """
        if axis is None:
            axis = tuple(range(self.ndim-1))
            if wts is not None:
                wts = np.asarray(wts)
                if wts.shape == self.shape:
                    pass
                elif wts.shape == self.shape[:-1]:
                    wts = at.multiplex(wts, 3, -1)
                else:
                    raise ValueError("Shape of wts should match "
                                     "self.shape or self.pshape()")

        return np.average(self, weights=wts, axis=axis)


    def centroid(self):
        """Return the centroid of the :class:`Coords`.

        The centroid of Coords is the point whose coordinates
        are the mean values of all points.

        Returns
        -------
        : Coords (3,)
            A single point that is the centroid of the Coords.

        See also
        --------
        center: return the center of the bounding box.

        Examples
        --------
        >>> print(Coords([[0.,0.,0.],[3.,0.,0.],[0.,3.,0.]]).centroid())
        [1. 1. 0.]
        """
        return self.points().mean(axis=0)


    def centroids(self):
        """Return the Coords itself.

        Notes
        -----
        This method exists only to have a common interface with
        other geometry classes.
        """
        return self


    def sizes(self):
        """Return the bounding box sizes of the :class:`Coords`.

        Returns
        -------
        : array (3,)
            The length of the bounding box along the three global axes.

        See Also
        --------
        dsize: The diagonal size of the bounding box.
        principalSizes: the sizes of the bounding box along the principal axes

        Examples
        --------
        >>> print(Coords([[0.,0.,0.],[3.,0.,0.],[0.,3.,0.]]).sizes())
        [3. 3. 0.]

        """
        X0, X1 = self.bbox()
        return np.asarray(X1-X0)


    def maxsize(self):
        """Return the maximum size of a Coords in any coordinate direction.

        Returns
        -------
        : float
            The maximum length of any edge of the bounding box.

        Notes
        -----
        This is a convenient shorthand for `self.sizes().max()`.

        See Also
        --------
        sizes: return the length of the bounding box along global axes
        bbox: return the bounding box

        Examples
        --------
        >>> print(Coords([[0.,0.,0.],[3.,0.,0.],[0.,3.,0.]]).maxsize())
        3.0

        """
        return self.sizes().max()


    def dsize(self):
        """Return the diagonal size of the bounding box of the :class:`Coords`.

        Returns
        -------
        : float
            The length of the diagonal of the bounding box.

        Notes
        -----
        All the points of the Coords are inside a sphere with the
        :meth:`center` as center and the :meth:`dsize` as
        length of the diameter (though it is not necessarily the
        smallest bouding sphere).
        :meth:`dsize` is in general a good estimate for the maximum size
        of the cross section to be expected when the object can be rotated
        freely around its center. It is conveniently used to zoom the
        camera on an object, while guaranteeing that the full object
        remains visible during rotations.

        See Also
        --------
        bsphere: return radius of smallest sphere encompassing all points
        sizes: return the length of the bounding box along global axes
        bbox: return the bounding box

        Examples
        --------
        >>> print(Coords([[0.,0.,0.],[3.,0.,0.],[0.,3.,0.]]).dsize())
        4.2426405

        """
        X0, X1 = self.bbox()
        return at.length(X1-X0)


    def bsphere(self):
        """Return the radius of the bounding sphere of the :class:`Coords`.

        The bounding sphere used here is the smallest sphere with center
        in the center() of the :class:`Coords`, and such that no points of the
        Coords are lying outside the sphere.

        Returns
        -------
        : float
            The maximum distance of any point to the `Coords.center`.

        Notes
        -----
        This is not necessarily the absolute smallest bounding sphere,
        because we use the center from looking only in the global axes
        directions.

        Examples
        --------
        >>> X = Coords([[0.,0.,0.],[3.,0.,0.],[0.,3.,0.]])
        >>> print(X.dsize(), X.bsphere())
        4.2426405 2.1213202
        >>> X = Coords([[0.5,0.],[1.,0.5],[0.5,1.0],[0.0,0.5]])
        >>> print(X.dsize(), X.bsphere())
        1.4142135 0.5

        """
        return self.distanceFromPoint(self.center()).max()


    def bboxes(self):
        """Return the bboxes of all subsets of points in the Coords.

        Subsets of points are 2-dim subarrays of the Coords, taken
        along the two last axes. If the Coords has ndim==2, there
        is only one subset: the full Coords.

        Returns
        -------
        float array
            Array with shape (...,2,3). The elements along the penultimate
            axis are the minimal and maximal values of the Coords
            along that axis.

        Examples
        --------
        >>> X = Coords(np.arange(18).reshape(2,3,3))
        >>> print(X)
         [[[ 0.   1.   2.]
           [ 3.   4.   5.]
           [ 6.   7.   8.]]
        <BLANKLINE>
          [[ 9.  10.  11.]
           [12.  13.  14.]
           [15.  16.  17.]]]
        >>> print(X.bboxes())
        [[[ 0.   1.   2.]
          [ 6.   7.   8.]]
        <BLANKLINE>
         [[ 9.  10.  11.]
          [15.  16.  17.]]]
        """
        return at.minmax(self, axis=1)

    # Inertia


    @utils.warning("warn_inertia_changed")
    def inertia(self, mass=None):
        """Return inertia related quantities of the :class:`Coords`.

        Parameters
        ----------
        mass: float array, optional
            If provided, it is a 1-dim array with :meth:`npoints` weight
            values for the points, in the order of the :meth:`points`.
            The default is to attribute a weight 1.0 to each point.

        Returns
        -------
        :class:`~inertia.Inertia`
            The Inertia object has the following attributes:

            - ``mass``: the total mass (float)
            - ``ctr``: the center of mass: float (3,)
            - ``tensor``: the inertia tensor in the central axes: shape (3,3)

        See Also
        --------
        principalCS: Return the principal axes of the inertia tensor

        Examples
        --------
        >>> from pyformex.elements import Tet4
        >>> I = Tet4.vertices.inertia()
        >>> print(I.tensor)
        [[1.5  0.25 0.25]
         [0.25 1.5  0.25]
         [0.25 0.25 1.5 ]]
        >>> print(I.ctr)
        [0.25 0.25 0.25]
        >>> print(I.mass)
        4.0

        """
        from pyformex import inertia
        M, C, I = inertia.point_inertia(self.points(), mass)  # noqa: E741
        I = inertia.Tensor(I)  # noqa: E741
        return inertia.Inertia(I, ctr=C, mass=M)


    def principalCS(self, mass=None):
        """Return a CoordSys formed by the principal axes of inertia.

        Parameters
        ----------
        mass: 1-dim float array (:meth:`points`,), optional
            The mass to be attributed to each of the points, in the order
            of :meth:`npoints`. If not provided, a mass 1.0 will be
            attributed to each point.

        Returns
        -------
        :class:`~coordsys.CoordSys` object.
            Coordinate system aligned along the principal axes of the inertia,
            for the specified point masses. The origin of the CoordSys is
            the center of mass of the Coords.

        See Also
        --------
        centralCS: CoordSys at the center of mass, but axes along global
            directions

        Examples
        --------
        >>> from pyformex.elements import Tet4
        >>> print(Tet4.vertices.principalCS())
        CoordSys: trl=[0.25  0.25  0.25]; rot=[[ 0.58  0.58  0.58]
                                               [ 0.34 -0.81  0.47]
                                               [ 0.82 -0.41 -0.41]]

        """
        from pyformex.coordsys import CoordSys
        I = self.inertia(mass)  # noqa: E741
        prin, axes = I.principal()
        return CoordSys(rot=axes, trl=I.ctr)


    def principalSizes(self):
        """Return the sizes in the principal directions of the :class:`Coords`.

        Returns
        -------
        float array (3,)
            Array with the size of the bounding box along the 3
            principal axes.

        Notes
        -----
        This is a convenient shorthand for:
        ``self.toCS(self.principalCS()).sizes()``

        Examples
        --------
        >>> print(Coords([[[0.,0.,0.],[3.,0.,0.]]]).rotate(30,2).principalSizes())
        [0. 0. 3.]

        """
        return self.toCS(self.principalCS()).sizes()


    def dimensions(self, tol=1.e-5):
        """Return the dimensionality of the Coords cloud.

        The dimensionality is the number of principal sizes of the
        point collection that are larger than some tolerance value.
        This allows to easily test if points are collinear or
        coplanar.

        Parameters
        ----------
        tol: float
            The treshold value to consider a dimension small.

        Returns
        -------
        int (0..3)
            The number of principal direction in which the dimension
            is smaller than tol. This identifies the overall shape of
            the Coords object: 0=point, 1=linear, 2=planar, 3=3D.

        Examples
        --------
        >>> Coords('0...').dimensions()
        0
        >>> Coords('0557').dimensions()
        1
        >>> Coords('012').dimensions()
        2
        >>> Coords('012a').dimensions()
        3
        """
        return (self.principalSizes() > tol).sum()


    def centralCS(self, mass=None):
        """Returns the central coordinate system of the Coords.

        Parameters
        ----------
        mass: 1-dim float array (:meth:`points`,), optional
            The mass to be attributed to each of the points, in the order
            of :meth:`npoints`. If not provided, a mass 1.0 will be
            attributed to each point.

        Returns
        -------
        :class:`~coordsys.CoordSys` object.
            Coordinate system with origin at the center of mass of the
            Coords and axes parallel to the global axes.

        See Also
        --------
        principalCS: CoordSys aligned with principa axes of inertia tensor

        Examples
        --------
        >>> from pyformex.elements import Tet4
        >>> print(Tet4.vertices.centralCS())
        CoordSys: trl=[0.25  0.25  0.25]; rot=[[1.  0.  0.]
                                               [0.  1.  0.]
                                               [0.  0.  1.]]
        """
        from pyformex.coordsys import CoordSys
        C = self.reshape(-1, 3).average(wts=mass, axis=0)
        return CoordSys(trl=C)


    #  Distance


    def distanceFromPoint(self, p):
        """Returns the distance of all points from the point p.

        Parameters
        ----------
        p: float :term:`array_like` with shape (3,) or (1,3)
            Coordinates of a single point in space

        Returns
        -------
        float array
            Array with shape :meth:`pshape` holding the distance of
            each point to point p. All values are positive or zero.

        See Also
        --------
        closestPoint: return the point of Coords closest to given point

        Examples
        --------
        >>> X = Coords([[0.,0.,0.],[2.,0.,0.],[1.,3.,0.],[-1.,0.,0.]])
        >>> print(X.distanceFromPoint([0.,0.,0.]))
        [0.    2.    3.16  1.  ]

        """
        p = at.checkArray(p, size=3, kind='f', allow='i').reshape(3)
        return at.length(self-p)


    def distanceFromLine(self, p, n):
        """Returns the distance of all points from the line (p,n).

        Parameters
        ----------
        p: float :term:`array_like` with shape (3,) or (1,3)
            Coordinates of some point on the line.
        n: float :term:`array_like` with shape (3,) or (1,3)
            Vector specifying the direction of the line.

        Returns
        -------
        float array
            Array with shape :meth:`pshape` holding the distance
            of each point to the line through p and having direction n.
            All values are positive or zero.

        Examples
        --------
        >>> X = Coords([[0.,0.,0.],[2.,0.,0.],[1.,3.,0.],[-1.,0.,0.]])
        >>> print(X.distanceFromLine([0.,0.,0.],[1.,1.,0.]))
        [0.   1.41 1.41 0.71]

        """
        p = at.checkArray(p, size=3, kind='f', allow='i').reshape(3)
        n = at.checkArray(n, size=3, kind='f', allow='i').reshape(3)
        n = at.normalize(n)
        xp = self-p
        xpt = at.dotpr(xp, n)
        a = at.dotpr(xp, xp)-xpt*xpt
        return np.sqrt(a.clip(0))


    def distanceFromPlane(self, p, n):
        """Return the distance of all points from the plane (p,n).

        Parameters
        ----------
        p: float :term:`array_like` with shape (3,) or (1,3)
            Coordinates of some point in the plane.
        n: float :term:`array_like` with shape (3,) or (1,3)
            The normal vector to the plane.

        Returns
        -------
        float array
            Array with shape :meth:`pshape` holding the distance
            of each point to the plane through p and having normal n.
            The values are positive if the point is on the side of the
            plane indicated by the positive normal.

        See Also
        --------
        directionalSize: find the most distant points at both sides of plane

        Examples
        --------
        >>> X = Coords([[0.,0.,0.],[2.,0.,0.],[1.,3.,0.],[-1.,0.,0.]])
        >>> print(X.distanceFromPlane([0.,0.,0.],[1.,0.,0.]))
        [ 0.  2.  1. -1.]

        """
        p = at.checkArray(p, size=3, kind='f', allow='i').reshape(3)
        n = at.checkArray(n, size=3, kind='f', allow='i').reshape(3)
        n = at.normalize(n)
        d = np.inner(self, n) - np.inner(p, n)
        return np.asarray(d)


    def closestToPoint(self, p, return_dist=False):
        """Returns the point closest to a given point p.

        Parameters
        ----------
        p: :term:`array_like` (3,)
            Coordinates of a single point in space

        Returns
        -------
        :int
            Index of the point in the Coords that has the
            minimal Euclidean distance to the point `p`.
            Use this index with self.points() to get the
            coordinates of that point.

        Examples
        --------
        >>> X = Coords([[[0.,0.,0.],[3.,0.,0.],[0.,3.,0.]]])
        >>> X.closestToPoint([2.,0.,0.])
        1
        >>> X.closestToPoint([2.,0.,0.],True)
        (1, 1.0)

        """
        d = self.distanceFromPoint(p)
        i = d.argmin()
        if return_dist:
            return i, d.flat[i]
        else:
            return i


    def directionalSize(self, n, p=None, return_points=False):
        """Returns the extreme distances from the plane p,n.

        Parameters
        ----------
        n: a single int or a float :term:`array_like` (3,)
            The direction of the normal to the plane. If an int, it is the
            number of a global axis. Else it is a vector with 3 components.
        p: :term:`array_like` (3,), optional
            Coordinates of a point in the plane. If not provided,
            the :meth:`center` of the Coords is used.
        return_points: bool
           If True, also return a Coords with two points along the line
           (p,n) and at the extreme distances from the plane(p,n).

        Returns
        -------
        dmin: float
            The minimal (signed) distance of a point of the Coords to the
            plane (p,n). The value can be negative or positive.
        dmax: float
            The maximal (signed) distance of a point of the Coords to the
            plane (p,n). The value can be negative or positive.
        points: Coords (2,3), optional
            If `return_points=True` is provided, also returns a Coords
            holding two points on the line (p,n) with minimal and
            maximal distance from the plane (p,n). These two points
            together with the normal `n` define two parallel planes
            such that all points of `self` are between or on the planes.

        Notes
        -----
        The maximal size of `self` in the direction `n` is found from
        the difference `dmax` - dmin`. See also :meth:`directionalWidth`.

        See also
        --------
        directionalExtremes: return two points in the extreme planes
        directionalWidth: return the distance between the extreme planes
        distanceFromPlane: return distance of all points to a plane

        Examples
        --------
        >>> X = Coords([[[0.,0.,0.],[3.,0.,0.],[0.,3.,0.]]])
        >>> X.directionalSize([1,0,0])
        (-1.5, 1.5)
        >>> X.directionalSize([1,0,0],[1.,0.,0.])
        (-1.0, 2.0)
        >>> X.directionalSize([1,0,0],return_points=True)
        (-1.5, 1.5, Coords([[0. , 1.5, 0. ],
                [3. , 1.5, 0. ]]))

        """
        n = at.unitVector(n)
        if p is None:
            p = self.center()
        else:
            p = Coords(p)
        d = self.distanceFromPlane(p, n)
        dmin, dmax = d.min(), d.max()

        if return_points:
            return dmin, dmax, Coords([p+dmin*n, p+dmax*n])
        else:
            return dmin, dmax


    def directionalExtremes(self, n, p=None):
        """Returns extremal planes in the direction n.

        Parameters: see :meth:`directionalSize`.

        Returns
        -------
        :Coords (2,3)
            A Coords holding the two points on the line (p,n) with minimal
            and maximal distance from the plane (p,n). These two points
            together with the normal `n` define two parallel planes
            such that all points of `self` are between or on the planes.

        See also
        --------
        directionalSize: return minimal and maximal distance from plane

        Notes
        -----
        This is like directionalSize with the return_points options,
        but only returns the extreme points.

        Examples
        --------
        >>> X = Coords([[[0.,0.,0.],[3.,0.,0.],[0.,3.,0.]]])
        >>> X.directionalExtremes([1,0,0])
        Coords([[0. , 1.5, 0. ],
                [3. , 1.5, 0. ]])
        """
        return self.directionalSize(n, p, return_points=True)[2]


    def directionalWidth(self, n):
        """Returns the width of a Coords in the given direction.

        Parameters: see :meth:`directionalSize`.

        Returns
        -------
        :float
            The size of the Coords in the direction `n`. This is the
            distance between the extreme planes with normal `n` touching
            the Coords.

        See also
        --------
        directionalSize: return minimal and maximal distance from plane

        Notes
        -----
        This is like directionalSize but only returns the difference between
        `dmax` and `dmin`.

        Examples
        --------
        >>> X = Coords([[[0.,0.,0.],[3.,0.,0.],[0.,3.,0.]]])
        >>> print(X.directionalWidth([1,0,0]))
        3.0
        """
        dmin, dmax = self.directionalSize(n)
        return dmax-dmin


    # Test position


    def test(self, dir=0, min=None, max=None, atol=0.):
        """Flag points having coordinates between min and max.

        Test the position of the points of the :class:`Coords` with respect to
        one or two parallel planes. This method is very convenient in clipping
        a Coords in a specified direction. In most cases the clipping
        direction is one of the global coordinate axes, but a general
        direction may be used as well.

        Testing along global axis directions is highly efficient. It tests
        whether the corresponding coordinate is above or equal to the `min`
        value and/or below or equal to the `max` value. Testing in a general
        direction tests whether the distance to the `min` plane is positive
        or zero and/or the distance to the `max` plane is negative or zero.

        Parameters
        ----------
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
            A test will return  True if the point's distance from the
            `min` clipping plane is `>= -atol` and/or the distance from the
            `max` clipping plane is `<= atol`. Thus a positive atol widens the
            clipping planes.

        Returns
        -------
        : bool array with shape :meth:`pshape`
            Array flagging whether the points for the Coords pass the test(s)
            or not. The return value can directly be used as an index to
            `self` to obtain a :class:`Coords` with the points satisfying
            the test (or not).

        Raises
        ------
        ValueError: At least one of min or max have to be specified
            If neither `min` nor `max` are provided.

        Examples
        --------
        >>> x = Coords([[[0.,0.],[1.,0.]],[[0.,1.],[0.,2.]]])
        >>> print(x.test(min=0.5))
        [[False  True]
         [False False]]
        >>> t = x.test(dir=1,min=0.5,max=1.5)
        >>> print(x[t])
        [[0. 1. 0.]]
        >>> print(x[~t])
        [[0. 0. 0.]
         [1. 0. 0.]
         [0. 2. 0.]]

        """
        if min is None and max is None:
            raise ValueError("At least one of min or max have to be specified.")

        if np.array(dir).size == 1:
            if min is not None:
                T1 = self[..., dir] >= (min - atol)
            if max is not None:
                T2 = self[..., dir] <= (max + atol)
        else:
            if min is not None:
                T1 = self.distanceFromPlane(min, dir) >= - atol
            if max is not None:
                T2 = self.distanceFromPlane(max, dir) <= atol

        if min is None:
            T = T2
        elif max is None:
            T = T1
        else:
            T = T1 * T2
        return np.asarray(T)



    ########################################################################


    def set(self, f):
        """Set the coordinates from those in the given array.

        Parameters
        ----------
        f: float :term:`array_like`, broadcastable to self.shape.
            The coordinates to replace the current ones. This can not
            be used to chage the shape of the Coords.

        Raises
        ------
        ValueError:
            If the shape of `f` does not allow broadcasting to `self.shape`.

        Examples
        --------
        >>> x = Coords([[0],[1],[2]])
        >>> print(x)
        [[0.  0.  0.]
         [1.  0.  0.]
         [2.  0.  0.]]
        >>> x.set([0.,1.,0.])
        >>> print(x)
        [[0.  1.  0.]
         [0.  1.  0.]
         [0.  1.  0.]]

        """
        f = at.checkArray(f, kind='f', allow='i')
        if at.checkBroadcast(self.shape, f.shape) != self.shape:
            raise ValueError("Invalid array shape")
        self[...] = f      # do not be tempted to use self = f !

##############################################################################
    #
    #   Transformations that preserve the topology (but change coordinates)
    #
    #   A. Affine transformations
    #
    #      Scaling
    #      Translation
    #      Central Dilatation = Scaling + Translation
    #      Rotation
    #      Shear
    #      Reflection
    #      Affine
    #
    #  The following methods return transformed coordinates, but by default
    #  they do not change the original data. If the optional argument inplace
    #  is set True, however, the coordinates are changed inplace.


    def scale(self, scale, dir=None, center=None, inplace=False):
        """Return a scaled copy of the :class:`Coords` object.

        Parameters
        ----------
        scale: float or tuple of 3 floats
            Scaling factor(s). If it is a single value, and no `dir` is
            provided, scaling is uniformly applied to all axes; if `dir`
            is provided, only to the specified directions. If it is a tuple,
            the three scaling factors are applied to the respective
            global axes.
        dir: int or tuple of ints, optional
            One or more global axis numbers (0,1,2), indicating the direction(s)
            that should be scaled with the (single) value `scale`.
        center: point-like, optional
            If provided, use this point as the center of the scaling.
            The default is the global origin.
        inplace: bool,optional
            If True, the coordinates are change in-place.

        Returns
        -------
        : Coords
            The Coords scaled as specified.

        Notes
        -----
        If a `center` is provided,the operation is equivalent with
        ``self.translate(-center).scale(scale,dir).translate(center)``

        Examples
        --------
        >>> X = Coords([1.,1.,1.])
        >>> print(X.scale(2))
        [2. 2. 2.]
        >>> print(X.scale([2,3,4]))
        [2. 3. 4.]
        >>> print(X.scale(2,dir=(1,2)).scale(4,dir=0))
        [4. 2. 2.]
        >>> print(X.scale(2,center=[1.,0.5,0.]))
        [1.   1.5  2. ]

        """
        if center is not None:
            center = np.asarray(center)
            return self.trl(-center).scale(scale, dir).translate(center)

        if inplace:
            out = self
        else:
            out = self.copy()
        if dir is None:
            out *= scale
        else:
            out[..., dir] *= scale
        return out


    def translate(self, dir, step=1.0, inplace=False):
        """Return a translated copy of the :class:`Coords` object.

        Translate the Coords in the direction `dir` over a distance
        `step * at.length(dir)`.

        Parameters
        ----------
        dir: int (0,1,2) or float :term:`array_like` (...,3)
            The translation vector. If an int, it specifies a global axis
            and the translation is in the direction of that axis.
            If an :term:`array_like`, it specifies one or more translation vectors.
            If more than one, the array should be broadcastable to the Coords
            shape: this allows to translate different parts of the Coords over
            different vectors, all in one operation.
        step: float
            If ``dir`` is an int, this is the length of the translation.
            Else, it is a multiplying factor applied to ``dir`` prior to
            applying the translation.

        Returns
        -------
        : Coords
            The Coords translated over the specified vector(s).

        Note
        ----
        :meth:`trl` is a convenient shorthand for :meth:`translate`.

        See Also
        --------
        centered: translate to center around origin
        Coords.align: translate to align bounding box

        Examples
        --------
        >>> x = Coords([1.,1.,1.])
        >>> print(x.translate(1))
        [1. 2. 1.]
        >>> print(x.translate(1,1.))
        [1. 2. 1.]
        >>> print(x.translate([0,1,0]))
        [1. 2. 1.]
        >>> print(x.translate([0,2,0],0.5))
        [1. 2. 1.]
        >>> x = Coords(np.arange(4).reshape(2,2,1))
        >>> x
        Coords([[[0., 0., 0.],
                 [1., 0., 0.]],
        <BLANKLINE>
                [[2., 0., 0.],
                 [3., 0., 0.]]])
        >>> x.translate([[10.,-5.,0.],[20.,4.,0.]]) # translate with broadcasting
        Coords([[[10., -5.,  0.],
                 [21.,  4.,  0.]],
        <BLANKLINE>
                [[12., -5.,  0.],
                 [23.,  4.,  0.]]])

        """
        if inplace:
            out = self
        else:
            out = self.copy()
        if at.isInt(dir):
            out[..., dir] += step
        else:
            dir = Coords(dir, copy=True)
            if step != 1.:
                dir *= step
            out += dir
        return out


    def centered(self):
        """Return a centered copy of the Coords.

        Returns
        -------
        : Coords
            The Coords translated over tus that its :meth:`center`
            coincides with the origin of the global axes.

        Notes
        -----
        This is equivalent with ``self.translate(-self.center())``

        Examples
        --------
        >>> X = Coords('0123')
        >>> print(X)
        [[0.  0.  0.]
         [1.  0.  0.]
         [1.  1.  0.]
         [0.  1.  0.]]
        >>> print(X.centered())
        [[-0.5 -0.5  0. ]
         [ 0.5 -0.5  0. ]
         [ 0.5  0.5  0. ]
         [-0.5  0.5  0. ]]
       """
        return self.translate(-self.center())


    def align(self, alignment='---', point=[0., 0., 0.]):
        """Align a :class:`Coords` object on a given point.

        Alignment involves a translation such that the bounding box
        of the Coords object becomes aligned with a given point.
        The bounding box alignment is done by the translation of a
        to the target point.

        Parameters
        ----------
        alignment: str
            The requested alignment is a string of three characters,
            one for each of the coordinate axes. The character determines how
            the structure is aligned in the corresponding direction:

                - '-': aligned on the minimal value of the bounding box,
                - '+': aligned on the maximal value of the bounding box,
                - '0': aligned on the middle value of the bounding box.

            Any other value will make the alignment in that direction unchanged.

        point: point-like
            The target point of the alignment.

        Returns
        -------
        : Coords
            The Coords translated thus that the `alignment`
            :meth:`bboxPoint` is at `point`.

        Notes
        -----
        The default parameters translate the Coords thus that all points
        are in the octant with all positive coordinate values.

        ``Coords.align(alignment = '000')`` will center the object around
        the origin, just like the :meth:`centered` (which is slightly faster).
        This can however be used for centering around any point.

        See also
        --------
        align: aligning multiple objects with respect to each other.
        """
        return self.translate(point-self.bboxPoint(alignment))


    def rotate(self, angle, axis=2, around=None, angle_spec=at.DEG):
        """Return a copy rotated over angle around axis.

        Parameters
        ----------
        angle: float or float :term:`array_like` (3,3)
            If a float, it is the rotation angle, by default in degrees,
            and the parameters (angle, axis, angel_spec) are passed to
            :func:`~arraytools.rotationMatrix` to produce a (3,3) rotation
            matrix.
            Alternatively, the rotation matrix may be directly provided
            in the `angle` parameter. The `axis` and `angle_spec` are then
            ignored.
        axis: int (0,1,2) or float :term:`array_like` (3,)
            Only used if `angle` is a float.
            If provided, it specifies the direction of the rotation axis:
            either one of 0,1,2 for a global axis, or a vector with
            3 components for a general direction. The default (axis 2)
            is convenient for working with 2D-structures in the x-y plane.
        around: float :term:`array_like` (3,)
            If provided, it specifies a point on the rotation axis. If not,
            the rotation axis goes through the origin of the global axes.
        angle_spec: float, at.DEG or RAD, optional
            Only used if `angle` is a float.
            The default (at.DEG) interpretes the angle in degrees. Use RAD to
            specify the angle in radians.

        Returns
        -------
        Coords
            The Coords rotated as specified by the parameters.

        Note
        ----
        :meth:`rot` is a convenient shorthand for :meth:`rotate`.

        See Also
        --------
        translate: translate a Coords
        affine: rotate and translate a Coords
        arraytools.rotationMatrix:
             create a rotation matrix for use in :meth:`rotate`

        Examples
        --------
        >>> X = Coords('0123')
        >>> print(X.rotate(30))
        [[ 0.    0.    0.  ]
         [ 0.87  0.5   0.  ]
         [ 0.37  1.37  0.  ]
         [-0.5   0.87  0.  ]]
        >>> print(X.rotate(30,axis=0))
        [[0.    0.    0.  ]
         [1.    0.    0.  ]
         [1.    0.87  0.5 ]
         [0.    0.87  0.5 ]]
        >>> print(X.rotate(30,axis=0,around=[0.,0.5,0.]))
        [[ 0.    0.07 -0.25]
         [ 1.    0.07 -0.25]
         [ 1.    0.93  0.25]
         [ 0.    0.93  0.25]]
        >>> m = at.rotationMatrix(30,axis=0)
        >>> print(X.rotate(m))
        [[0.    0.    0.  ]
         [1.    0.    0.  ]
         [1.    0.87  0.5 ]
         [0.    0.87  0.5 ]]
        """
        mat = np.asarray(angle)
        if mat.size == 1:
            mat = at.rotationMatrix(angle, axis=axis, angle_spec=angle_spec)
        mat = at.checkArray(mat, shape=(3, 3), kind='f')
        if around is not None:
            around = np.asarray(around)
            out = self.translate(-around)
        else:
            out = self
        return out.affine(mat, around)


    def shear(self, dir, dir1, skew, inplace=False):
        """Return a copy skewed in the direction of a global axis.

        This translates points in the direction of a global axis,
        over a distance dependent on the coordinates along another axis.

        Parameters
        ----------
        dir: int (0,1,2)
            Global axis in which direction the points are translated.
        dir1: int (0,1,2)
            Global axis whose coordinates determine the length of the
            translation.
        skew: float
            Multiplication factor to the coordinates dir1 defining the
            translation distance.
        inplace: bool, optional
            If True, the coordinates are translated in-place.

        Notes
        -----
        This replaces the  coordinate ``dir`` with ``(dir + skew * dir1)``.
        If dir and dir1 are different, rectangular shapes in the plane
        (dir,dir1) are thus skewed along the direction dir into
        parallellogram shapes. If dir and dir1 are the same direction, the
        effect is that of scaling in the dir direction.

        Examples
        --------
        >>> X = Coords('0123')
        >>> print(X.shear(0,1,0.5))
        [[0.   0.   0. ]
         [1.   0.   0. ]
         [1.5  1.   0. ]
         [0.5  1.   0. ]]
        """
        if inplace:
            out = self
        else:
            out = self.copy()
        out[..., dir] += skew * out[..., dir1]
        return out


    def reflect(self, dir=0, pos=0., inplace=False):
        # TODO: Add mirroring against any plane/axis/point
        """Reflect the coordinates in the direction of a global axis.

        Parameters
        ----------
        dir: int (0,1,2)
            Global axis direction of the reflection (default 0 or x-axis).
        pos: float
            Offset of the mirror plane from origin (default 0.0)
        inplace: bool, optional
            If True, the coordinates are translated in-place.

        Returns
        -------
        :Coords
            A mirror copy with respect to the plane perpendicular to axis `dir`
            and placed at coordinate `pos` along the `dir` axis.

        Examples
        --------
        >>> X = Coords('012')
        >>> print(X)
        [[0.  0.  0.]
         [1.  0.  0.]
         [1.  1.  0.]]
        >>> print(X.reflect(0))
        [[ 0.  0.  0.]
         [-1.  0.  0.]
         [-1.  1.  0.]]
        >>> print(X.reflect(1,0.5))
        [[0.  1.  0.]
         [1.  1.  0.]
         [1.  0.  0.]]
        >>> print(X.reflect([0,1],[0.5,0.]))
        [[ 1.  0.  0.]
         [ 0.  0.  0.]
         [ 0. -1.  0.]]

        """
        if inplace:
            out = self
        else:
            out = self.copy()
        out[..., dir] = 2*np.asarray(pos) - out[..., dir]
        return out


    def affine(self, mat, vec=None):
        """Perform a general affine transformation.

        Parameters
        ----------
        mat: float :term:`array_like` (3,3)
            Matrix used in post-multiplication on a row vector to produce
            a new vector. The matrix can express scaling and/or rotation
            or a more general (affine) transformation.
        vec: float :term:`array_like` (3,)
            Translation vector to add after the transformation with `mat`.

        Returns
        -------
        : Coords
            A Coords with same shape as self, but with coordinates given by
            ``self * mat + vec``. If `mat` is a rotation matrix or a uniform
            scaling plus rotation, the full operation performs a rigid rotation
            plus translation of the object.

        Examples
        --------
        >>> X = Coords('0123')
        >>> S = np.array([[2.,0.,0.],[0.,3.,0.],[0.,0.,4.]]) # non-uniform scaling
        >>> R = at.rotationMatrix(90.,2) # rotation matrix
        >>> T = [20., 0., 2.] # translation
        >>> M = np.dot(S,R)  # combined scaling and rotation
        >>> print(X.affine(M,T))
        [[20.   0.   2.]
         [20.   2.   2.]
         [17.   2.   2.]
         [17.   0.   2.]]

        """
        out = np.dot(self, mat)
        if vec is not None:
            out += vec
        return out


    def toCS(self, cs):
        """Transform the coordinates to another CoordSys.

        Parameters
        ----------
        cs: :class:`~coordsys.CoordSys` object
            Cartesian coordinate system in which to take the coordinates of
            the current Coords object.

        Returns
        -------
        Coords
            A Coords object identical to self but having global coordinates
            equal to the coordinates of self in the `cs` CoordSys axes.

        Note
        ----
        This returns the coordinates of the original points in another
        CoordSys. If you use these coordinates as points in the global axes,
        the transformation of the original points to these new ones is the
        inverse transformation of the transformation of the global axes
        to the `cs` coordinate system.

        See Also
        --------
        fromCS: the inverse transformation

        Examples
        --------
        >>> X = Coords('01')
        >>> print(X)
        [[0.  0.  0.]
         [1.  0.  0.]]
        >>> from pyformex.coordsys import CoordSys
        >>> CS = CoordSys(oab=[[0.5,0.,0.],[1.,0.5,0.],[0.,1.,0.]])
        >>> print(CS)
        CoordSys: trl=[0.5  0.   0. ]; rot=[[ 0.71  0.71  0.  ]
                                           [-0.71  0.71  0.  ]
                                             [ 0.   -0.    1.  ]]
        >>> print(X.toCS(CS))
        [[-0.35  0.35  0.  ]
         [ 0.35 -0.35  0.  ]]
        >>> print(X.toCS(CS).fromCS(CS))
        [[ 0.  0.  0.]
         [ 1. -0.  0.]]

        """
        return self.trl(-cs.trl).rot(cs.rot.transpose())


    def fromCS(self, cs):
        """Transform the coordinates from another CoordSys to global axes.

        Parameters
        ----------
        cs: :class:`~coordsys.CoordSys` object
            Cartesian coordinate system in which the current coordinate
            values are taken.

        Returns
        -------
        Coords
            A Coords object with the global coordinates of the same points
            as the input coordinates represented in the `cs` CoordSys axes.

        See Also
        --------
        toCS: the inverse transformation


        Examples: see :meth:`toCS`
        """
        return self.rot(cs.rot).trl(cs.trl)


    def transformCS(self, cs, cs0=None):
        """Perform a coordinate system transformation on the Coords.

        This method transforms the Coords object by the transformation that
        turns one coordinate system into a another.

        Parameters
        ----------
        cs: :class:`~coordsys.CoordSys`
            The final coordinate system.
        cs0: :class:`~coordsys.CoordSys`, optional
            The initial coordinate system. If not provided, the global
            coordinate system is used.

        Returns
        -------
        Coords
            The input Coords transformed by the same affine transformation
            that turns the axes of the coordinate system `cs0`
            into those of the system `cs`.

        Notes
        -----
        For example, with the default `cs0` and a `cs` CoordSys created with
        the points ::

           0. 1. 0.
          -1. 0. 0.
           0. 0. 1.
           0. 0. 0.

        the transformCS results in a rotation of 90 degrees around the z-axis.

        See Also
        --------
        toCS: transform coordinates to another CS
        fromCS: transfrom coordinates from another CS

        """
        if cs0 is not None:
            f = self.toCS(cs0)
        else:
            f = self
        return f.fromCS(cs)


    def position(self, x, y):
        """Position a :class:`Coords` so that 3 points x are aligned with y.

        Aligning 3 points x with 3 points y is done by a rotation and
        translation in such way that

        - point x0 coincides with point y0,
        - line x0,x1 coincides with line y0,y1
        - plane x0,x1,x2 coincides with plane y0,y1,y2

        Parameters
        ----------
        x: float :term:`array_like` (3,3)
            Original coordinates of three non-collinear points. These points
            can be be part of the Coords or not.
        y: float :term:`array_like` (3,3)
            Final coordinates of the three points.

        Returns
        -------
        Coords
            The input Coords rotated and translated thus that the points
            x are aligned with y.

        Notes
        -----
        This is a convenient shorthand for ``self.affine(*trfmat(x, y))``.

        See Also
        --------
        arraytools.trfmat: compute the transformation matrices from points x to y
        affine: general transform using rotation and translation

        Examples
        --------
        >>> X = Coords([[0,0,0],[1,0,0],[1,1,0]])
        >>> Y = Coords([[1,1,1],[1,10,1],[1,1,100]])
        >>> print(X.position(X,Y))
        [[1.  1.  1.]
         [1.  2.  1.]
         [1.  2.  2.]]
        """
        return self.affine(*at.trfmat(x, y))

#
#
#   B. Non-Affine transformations.
#
#      These always return copies !
#
#        Cylindrical, Spherical, Isoparametric
#

    def cylindrical(self, dir=(0, 1, 2), scale=(1., 1., 1.), angle_spec=at.DEG):
        """Convert from cylindrical coordinates to cartesian.

        A cylindrical coordinate system is defined by a longitudinal axis
        axis (z) and a radial axis (r). The cylindrical coordinates of
        a point are:

        - r: the radial distance from the z-axis,
        - theta: the circumferential angle measured positively around
          the z-axis starting from zero at the (r-z) halfplane,
        - z: the axial distance along the z-axis,

        This function interpretes the 3 coordinates of the points
        as (r,theta,z) values and computes the corresponding global
        cartesian coordinates (x,y,z).

        Parameters
        ----------
        dir: tuple of 3 ints, optional
            If provided, it is a permutation of (0,1,2) and specifies
            which of the current coordinates are interpreted as resp.
            distance(r), angle(theta) and height(z).
            Default order is (r,theta,z).
            Beware that if the permutation is not conserving the order
            of the axes, a left-handed system results, and the Coords will
            appear mirrored in the right-handed systems exclusively used
            by pyFormex
        scale: tuple of 3 floats, optional
            Scaling factors that are applied on the values prior to make the
            conversion from cylindrical to cartesian coordinates. These factors
            are always given in the order (r,theta,z), irrespective of the
            permutation by `dir`.
        angle_spec: float, at.DEG or RAD, optional
            Multiplication factor for angle coordinates.
            The default (at.DEG) interpretes the angle in degrees. Use RAD to
            specify the angle in radians.

        Returns
        -------
        Coords
            The global coordinates of the points that were specified with
            cylindrical coordinates as input.

        Notes
        -----
        The scaling can also be applied independently prior to transforming.
        ``X.cylindrical(scale=s)`` is equivalent with
        ``X.scale(s).cylindrical()``. The scale option is provided here
        because in many cases you need  at least to scale the theta direction
        to have proper angle values.

        See Also
        --------
        hyperCylindrical: similar but allowing scaling as function of angle
        toCylindrical: inverse transformation (cartesian to cylindrical)

        Examples
        --------
        We want to create six points on a circle with radius 2. We start
        by creating the points in cylindrical coordinates with unit distances.

        >>> X = Coords('1'+'2'*5)
        >>> print(X)
        [[1.  0.  0.]
         [1.  1.  0.]
         [1.  2.  0.]
         [1.  3.  0.]
         [1.  4.  0.]
         [1.  5.  0.]]

        Remember these are (r,theta,z) coordinates of the points. So we
        will scale the r-direction with 2 (the target radius) and the
        angular direction theta with 360/6 = 60.
        Then we get the cartesian coordinates of the points from

        >>> Y = X.cylindrical(scale=(2.,60.,1.))
        >>> print(Y)
        [[ 2.    0.    0.  ]
         [ 1.    1.73  0.  ]
         [-1.    1.73  0.  ]
         [-2.   -0.    0.  ]
         [-1.   -1.73  0.  ]
         [ 1.   -1.73  0.  ]]

        Going back to cylindrical coordinates yields

        >>> print(Y.toCylindrical())
        [[   2.    0.    0.]
         [   2.   60.    0.]
         [   2.  120.    0.]
         [   2. -180.    0.]
         [   2. -120.    0.]
         [   2.  -60.    0.]]

        This differs from the original input X because of the scaling
        factors, and the wrapping around angles are reported in the
        range [-180,180].

        """
        f = np.zeros_like(self)
        theta = (scale[1] * angle_spec) * self[..., dir[1]]
        r = scale[0] * self[..., dir[0]]
        f[..., 0] = r * np.cos(theta)
        f[..., 1] = r * np.sin(theta)
        f[..., 2] = scale[2] * self[..., dir[2]]
        return f


    def hyperCylindrical(self, dir=(0, 1, 2), scale=(1., 1., 1.),
                         rfunc=None, zfunc=None, angle_spec=at.DEG):
        """Convert cylindrical coordinates to cartesian with advanced scaling.

        This is similar to :meth:`cylindrical` but allows the specification
        of two functions defining extra scaling factors for the r and z
        directions that are dependent on the theta value.

        Parameters
        ----------
        dir, scale, angle_spec: see :meth:`cylindrical`
        rfunc: callable, optional
            Function r(theta) taking one, float parameter and returning a float.
            Like scale[0] it is multiplied with the provided r values before
            converting them to cartesian coordinates.
        zfunc: callable, optional
            Function z(theta) taking one float parameter and returning a float.
            Like scale[2] it is multiplied with the provided z values before
            converting them to cartesian coordinates.

        See Also
        --------
        cylindrical: similar but without the rfunc and zfunc options.

        """
        f = np.zeros_like(self)
        theta = (scale[1] * angle_spec) * self[..., dir[1]]
        r = scale[0] * self[..., dir[0]]
        if rfunc is not None:
            r *= rfunc(theta)
        f[..., 0] = r * np.cos(theta)
        f[..., 1] = r * np.sin(theta)
        f[..., 2] = scale[2] * self[..., dir[2]]
        if zfunc is not None:
            f[..., 2] *= zfunc(theta)
        return f


    def spiral(self, dir=(0, 1, 2), scale=(1., 1., 1.),
               rfunc=lambda t: 1+t/360, zfunc=lambda t: 0, angle_spec=at.DEG):
        """Perform a spiral transformation

        This is similar to :meth:`cylindrical` but allows the specification
        of two functions defining extra transformation functions for the
        r and z directions to produce spiral and helical geometries.

        Parameters
        ----------
        dir, scale, angle_spec: see :meth:`cylindrical`
        rfunc: callable, optional
            Function r(theta) taking one float parameter and returning a float.
            The values ``rfunc(theta)`` are added to the provided r. The theta
            values are according to angle_spec.
        zfunc: callable, optional
            Function z(theta) taking one float parameter and returning a float.
            The values ``rfunc(theta)`` are added to the provided z. The theta
            values are according to angle_spec.

        Notes
        -----
        The default rfunc converts points along the y-axis into an Archimedes
        spiral.

        Examples
        --------
        Create an Archimedes spiral with two turns and a point every 10 degrees

        >>> from pyformex import simple
        >>> nturns = 3   # how many full turns around the origin
        >>> div = 10     # degrees between subsequent points
        >>> nseg = nturns * 360 / div   # total number of divisions
        >>> # create points along X axis
        >>> X = simple.grid1(nseg+1).scale(nturns*360/nseg)
        >>> Y = X.spiral(dir=(1,0,2))
        >>> print(X[::360//div]) # print one point every turn
        [[   0.    0.    0.]
         [ 360.    0.    0.]
         [ 720.    0.    0.]
         [1080.    0.    0.]]
        """
        rtz = self[..., dir].scale(scale)
        r, t, z = rtz.x, rtz.y, rtz.z
        r = r + rfunc(t)
        z = z + zfunc(t)
        if angle_spec != 1.:
            t *= angle_spec
        x = r * np.cos(t)
        y = r * np.sin(t)
        self = np.stack([x, y, z], axis=-1)
        return Coords(self)


    def toCylindrical(self, dir=(0, 1, 2), angle_spec=at.DEG):
        """Converts from cartesian to cylindrical coordinates.

        Returns a Coords where the values are the coordinates of the
        input points in a cylindrical coordinate system. The three axes
        of the Coords then correspond to (r, theta, z).

        Parameters
        ----------
        dir: tuple of ints
            A permutation of (0,1,2) specifying which of the global axes are
            the radial, circumferential and axial direction of the
            cylindrical coordinate system. Make sure to keep the axes ordering
            in order to get a right-handed system.
        angle_spec: float, at.DEG or RAD, optional
            Multiplication factor for angle coordinates.
            The default (at.DEG) returns angles in degrees. Use RAD to
            return angles in radians.

        Returns
        -------
        Coords
            The cylindrical coordinates of the input points.

        See Also
        --------
        cylindrical: conversion from cylindrical to cartesian coordinates

        Examples
        --------
        see :meth:`cylindrical`

        """
        f = np.zeros_like(self)
        x, y, z = (self[..., i] for i in dir)
        f[..., 0] = np.sqrt(x*x+y*y)
        f[..., 1] = at.arctand2(y, x, angle_spec)
        f[..., 2] = z
        return f


    def spherical(self, dir=(0, 1, 2), scale=(1., 1., 1.),
                  angle_spec=at.DEG, colat=False):
        """Convert spherical coordinates to cartesian coordinates.

        Consider a spherical coordinate system with the global xy-plane as
        its equatorial plane and the z-axis as axis. The zero meridional
        halfplane is taken along th positive x-axis.
        The spherical coordinates of a point are:

        - the longitude (theta): the circumferential angle, measured around
          the z-axis from the zero-meridional halfplane to the meridional
          plane containing the point: this angle normally ranges from -180 to
          +180 degrees (or from 0 to 360);
        - the latitude (phi): the elevation angle of the point's position
          vector, measured from the equatorial plane, positive when the point
          is at the positive side of the plane: this angle is normally
          restricted to the range from -90 (south pole) to +90 (north pole);
        - the distance (r): the radial distance of the point from the origin:
          this is normally positive.

        This function interpretes the 3 coordinates of the points
        as (theta,phi,r) values and computes the corresponding global
        cartesian coordinates (x,y,z).

        Parameters
        ----------
        dir: tuple of 3 ints, optional
            If provided, it is a permutation of (0,1,2) and specifies
            which of the current coordinates are interpreted as resp.
            longitude(theta), latitude(phi) and distance(r). This allows
            the axis to be aligned with any of the global axes.
            Default order is (0,1,2), with (0,1) the equatorial plane
            and 2 the axis.
            Beware that using a permutation that is not conserving the order
            of the globale axes (0,1,2), may lead to a confusing left-handed
            system.
        scale: tuple of 3 floats, optional
            Scaling factors that are applied on the coordinate values prior
            to making the conversion from spherical to cartesian coordinates.
            These factors are always given in the order (theta,phi,rz),
            irrespective of the permutation by `dir`.
        angle_spec: float, at.DEG or RAD, optional
            Multiplication factor for angle coordinates.
            The default (at.DEG) interpretes the angles in degrees. Use RAD to
            specify the angles in radians.
        colat: bool
            If True, the second coordinate is the colatitude instead. The
            colatitude is the angle measured from the north pole towards
            the south. In degrees, it is equal to ``90 - latitude`` and
            ranges from 0 to 180.
            Applications that deal with regions around the pole may
            benefit from using this option.

        Returns
        -------
        Coords
            The global coordinates of the points that were specified with
            spherical coordinates as input.

        See Also
        --------
        toSpherical: the inverse transformation (cartesian to spherical)
        cylindrical: similar function for spherical coordinates

        Examples
        --------
        >>> X = Coords('0123').scale(90).trl(2,1.)
        >>> X
        Coords([[ 0.,  0.,  1.],
                [90.,  0.,  1.],
                [90., 90.,  1.],
                [ 0., 90.,  1.]])
        >>> X.spherical()
        Coords([[ 1.,  0.,  0.],
                [-0.,  1.,  0.],
                [ 0., -0.,  1.],
                [-0., -0.,  1.]])

        Note that the last two points, though having different spherical
        coordinates, are coinciding at the north pole.
        """
        f = self.reshape((-1, 3))
        theta = (scale[0]*angle_spec) * f[:, dir[0]]
        phi = (scale[1]*angle_spec) * f[:, dir[1]]
        r = scale[2] * f[:, dir[2]]
        if colat:
            phi = 90.0*angle_spec - phi
        rc = r*np.cos(phi)
        f = np.column_stack([rc*np.cos(theta), rc*np.sin(theta), r*np.sin(phi)])
        return Coords(f.reshape(self.shape))


    def superSpherical(self, n=1.0, e=1.0, k=0.0, dir=(0, 1, 2),
                       scale=(1., 1., 1.), angle_spec=at.DEG, colat=False):
        """Performs a superspherical transformation.

        superSpherical is much like :meth:`spherical`, but adds some extra
        parameters to enable the quick creation of a wide range of complicated
        shapes.
        Again, the input coordinates are interpreted as
        the longitude, latitude and distance in a spherical coordinate system.

        Parameters
        ----------
        n: float, >=0
            Exponent defining the variation of the distance in nort-south
            (latitude) direction. The default value 1 turns constant r-values
            into circular meridians. See notes.
        e: float, >=0
            Exponent defining the variation of the distance in north-south
            (latitude) direction. The default value 1 turns constant r-values
            into a circular latitude lines. See notes.
        k: float, -1 < k < 1
            Eggness factor. If nonzero, creates asymmetric northern and
            southern hemisheres. Values > 0 enlarge the southern hemisphere
            and shrink the northern, while negative values yield the
            opposite.
        dir: tuple of 3 ints, optional
            If provided, it is a permutation of (0,1,2) and specifies
            which of the current coordinates are interpreted as resp.
            longitude(theta), latitude(phi) and distance(r). This allows
            the axis to be aligned with any of the global axes.
            Default order is (0,1,2), with (0,1) the equatorial plane
            and 2 the axis.
            Beware that using a permutation that is not conserving the order
            of the globale axes (0,1,2), may lead to a confusing left-handed
            system.
        scale: tuple of 3 floats, optional
            Scaling factors that are applied on the coordinate values prior
            to making the conversion from spherical to cartesian coordinates.
            These factors are always given in the order (theta,phi,rz),
            irrespective of the permutation by `dir`.
        angle_spec: float, at.DEG or RAD, optional
            Multiplication factor for angle coordinates.
            The default (at.DEG) interpretes the angles in degrees. Use RAD to
            specify the angles in radians.
        colat: bool
            If True, the second coordinate is the colatitude instead. The
            colatitude is the angle measured from the north pole towards
            the south. In degrees, it is equal to ``90 - latitude`` and
            ranges from 0 to 180.
            Applications that deal with regions around the pole may
            benefit from using this option.

        Raises
        ------
        ValueError
            If one of `n`, `e` or `k` is out of the acceptable range.

        Notes
        -----
        Values of `n` and `e` should not be negative. Values equal to 1
        create a circular shape. Other values keep the radius at angles
        corresponding to mmultiples of 90 degrees, while the radius at the
        intermediate 45 degree angles will be  maximally changed. Values
        larger than 1 shrink at 45 degrees directions, while lower values
        increase it. A value 2 creates a straight line between the 90 degrees
        points (the radius at 45 degrees being reduced to 1/sqrt(2).

        See also example SuperShape.

        Examples
        --------
        >>> X = Coords('02222').scale(22.5).trl(2,1.)
        >>> X
        Coords([[  0. ,  0. ,  1. ],
                [  0. , 22.5,  1. ],
                [  0. , 45. ,  1. ],
                [  0. , 67.5,  1. ],
                [  0. , 90. ,  1. ]])
        >>> X.superSpherical(n=3).toSpherical()
        Coords([[90.  ,  0.  ,  1.  ],
                [85.93,  0.  ,  0.79],
                [45.  ,  0.  ,  0.5 ],
                [ 4.07,  0.  ,  0.79],
                [-0.  , -0.  ,  1.  ]])

        The result is smaller radius at angle 45.
        """
        if n < 0. or e < 0. or k <= -1. or k >= 1.:
            raise ValueError("n, e or k out of acceptable range")

        def c(o, m):
            c = np.cos(o)
            return np.sign(c)*abs(c)**m

        def s(o, m):
            c = np.sin(o)
            return np.sign(c)*abs(c)**m

        f = self.reshape((-1, 3))
        theta = (scale[0]*angle_spec) * f[:, dir[0]]
        phi = (scale[1]*angle_spec) * f[:, dir[1]]
        r = scale[2] * f[:, dir[2]]
        if colat:
            phi = 90.0*angle_spec - phi
        rc = r*c(phi, n)
        if k != 0:   # k should be > -1.0 !!!!
            x = np.sin(phi)
            rc *= (1.-k*x)/(1.+k*x)
        f = np.column_stack([rc*c(theta, e), rc*s(theta, e), r*s(phi, n)])
        return Coords(f.reshape(self.shape))


    def toSpherical(self, dir=[0, 1, 2], angle_spec=at.DEG):
        """Converts from cartesian to spherical coordinates.

        Returns a Coords where the values are the coordinates of the
        input points in a spherical coordinate system. The three axes
        of the Coords then correspond to (theta, phi, r).

        Parameters
        ----------
        dir: tuple of ints
            A permutation of (0,1,2) specifying how the spherical coordinate
            system is oriented in the global axes. The last value is the axis
            of the system; the first two values are the equatorial plane;
            the first and last value define the meridional zero plane.
            Make sure to preserve the axes ordering in order to get a
            right-handed system.
        angle_spec: float, at.DEG or RAD, optional
            Multiplication factor for angle coordinates.
            The default (at.DEG) returns angles in degrees. Use RAD to
            return angles in radians.

        Returns
        -------
        Coords
            The spherical coordinates of the input points.

        See Also
        --------
        spherical: conversion from spherical to cartesian coordinates

        Examples
        --------
        See :meth:`superSpherical`

        """
        v = self[..., dir].reshape((-1, 3))
        dist = at.length(v)
        long = at.arctand2(v[:, 0], v[:, 2], angle_spec)
        lat = np.where(dist <= 0.0, 0.0, at.arcsind(v[:, 1]/dist, angle_spec))
        f = np.column_stack([long, lat, dist])
        return Coords(f.reshape(self.shape))


    def circulize(self, n):
        """Transform sectors of a regular polygon into circular sectors.

        Parameters
        ----------
        n: int
            Number of edges of the regular polygon.

        Returns
        -------
        Coords
            A Coords where the points inside each sector of a n-sided
            regular polygon around the origin are reposition to fill
            a circular sector. The polygon is in the x-y-plane and has a
            vertex on the x-axis.

        Notes
        -----
        Points on the x-axis and on radii at i * 360 / n degrees are not moved.
        Points on the bisector lines between these radii are move maximally
        outward. Points on a regular polygon will become points on a circle
        if circulized with parameter n equal to the number of sides of the
        polygon.

        Examples
        --------
        >>> Coords([[1.,0.],[0.5,0.5],[0.,1.]]).circulize(4)
        Coords([[ 1.  , 0.  , 0.  ],
                [ 0.71, 0.71, 0.  ],
                [-0.  , 1.  , 0.  ]])
        """
        if n < 3:
            raise ValueError("n should be at least 3")
        angle = 360./n
        X = self.toCylindrical()
        t = X.y / angle  # ranges from 0 to 1 for sector 0..angle degrees
        # Reduce values to a single sector
        while t.min() < 0.0:
            t[t<0.0] += 1.0
        while t.max() > 1.0:
            t[t>1.0] -= 1.0
        u = abs(0.5-t) * angle
        c = at.cosd(u) / at.cosd(angle/2)
        X.x *= c
        return X.cylindrical()


    def bump(self, dir, a, func=None, dist=None, xb=1.):
        """Create a 1-, 2-, or 3-dimensional bump in a Coords.

        A bump is a local modification of the coordinates of a collection
        of points. The bump can be 1-, 2- or 3-dimensional, meaning that
        the intensity of the coordinate modification varies in 1, 2 or 3
        axis directions. In all cases, the bump only changes one coordinate
        of the points.
        This method can produce various effects, but one of the most common
        uses is to force a surface to be indented at some point.

        Parameters
        ----------
        dir: int, one of (0,1,2)
            The axis of the coordinates to be modified.
        a: point (3,)
            The point that sets the bump location and intensity.
        func: callable, optional
            A function that returns the bump intensity in function
            of the distance from the bump point `a`. The distance is the
            Euclidean distance over all directions except `dir`.
            The function takes a single (positive) float value and
            returns a float (the bump intensity). Its value should
            not be zero at the origin. The function may include constants,
            which can be specified as `xb`. If no function is specified,
            the default function will be used:
            ``lambda x: np.where(x<xb,1.-(x/3)**2,0)``
            This makes the bump quadratically die out over a distance `xb`.
        dist: int or tuple of ints, optional
            Specifies how the distance from points to the bump point `a` is
            measured. It can be a single axis number (0,1,2) or a tuple of
            two or three axis numbers. If a single axis, the bump
            will vary only in one direction and distance is measured
            along that direction and is signed.
            If two or three axes, distance is the (always positive)
            euclidean distance over these directions and the bump will
            vary in these directions. Default value is the set of 3 axes
            minus the direction of modification `dir`.
        xb: float or list of floats
            Constant(s) to be used in func. Often, this includes the
            distance over which the bump will extend. The default
            bump function will reach zero at this distance.

        Returns
        -------
        Coords
            A Coords with same shape as input, but having a localized
            change of coordinates as specified by the parameters.

        Notes
        -----
        This function replaces the `bump1` and `bump2` functions in older
        pyFormex versions. The default value of `dist` makes it work like
        `bump2`. Specifyin a single axis for `dist` makes it work like `bump1`.

        See also examples BaumKuchen, Circle, Clip, Novation

        Examples
        --------
        One-dimensional bump in a linear set of points.

        >>> X = Coords(np.arange(6).reshape(-1,1))
        >>> X.bump1(1,[3.,5.,0.],dist=0)
        Coords([[0., 0., 0.],
                [1., 0., 0.],
                [2., 0., 0.],
                [3., 5., 0.],
                [4., 0., 0.],
                [5., 0., 0.]])
        >>> X.bump(1,[3.,5.,0.],dist=0,xb=3.)
        Coords([[0.  , 0.  , 0.  ],
                [1.  , 2.78, 0.  ],
                [2.  , 4.44, 0.  ],
                [3.  , 5.  , 0.  ],
                [4.  , 4.44, 0.  ],
                [5.  , 2.78, 0.  ]])

        Create a grid a points in xz-plane, with a bump in direction y
        with a maximum 5 at x=1.5, z=0., extending over a distance 2.5.

        >>> X = Coords(np.arange(4).reshape(-1,1)).replicate(4,dir=2)
        >>> X.bump(1,[1.5,5.,0.],xb=2.5)
        Coords([[[0.  , 3.75, 0.  ],
                 [1.  , 4.86, 0.  ],
                 [2.  , 4.86, 0.  ],
                 [3.  , 3.75, 0.  ]],
        <BLANKLINE>
                [[0.  , 3.19, 1.  ],
                 [1.  , 4.31, 1.  ],
                 [2.  , 4.31, 1.  ],
                 [3.  , 3.19, 1.  ]],
        <BLANKLINE>
                [[0.  , 0.  , 2.  ],
                 [1.  , 2.64, 2.  ],
                 [2.  , 2.64, 2.  ],
                 [3.  , 0.  , 2.  ]],
        <BLANKLINE>
                [[0.  , 0.  , 3.  ],
                 [1.  , 0.  , 3.  ],
                 [2.  , 0.  , 3.  ],
                 [3.  , 0.  , 3.  ]]])

        """
        if func is None:
            func = lambda x: np.where(abs(x)<xb, 1.-(x/3)**2, 0)
        if func(0.) == 0.:
            raise ValueError("Invalid func: f(0)=0")
        f = self.copy()
        if dist is None:
            dist = ((dir+1) % 3, (dir+2) % 3)
        if at.isInt(dist):
            dist = (dist,)
        d = f[..., dist[0]] - a[dist[0]]
        if len(dist) > 1:
            # compute euclidean distance
            d = d*d
            for i in dist[1:]:
                d1 = f[..., i] - a[i]
                d += d1*d1
            d = np.sqrt(d)
        f[..., dir] += func(d)*a[dir]/func(0)
        return f


    def flare(self, xf, f, dir=(0, 2), end=0, exp=1.):
        """Create a flare at the end of a :class:`Coords` block.

        A flare is a local change of geometry (widening, narrowing)
        at the end of a structure.

        Parameters
        ----------
        xf: float
            Length over which the local change occurs, measured along ``dir[0]``.
        f: float
            Maximum amplitude of the flare, in the direction ``dir[1]``.
        dir: tuple of two ints (0,1,2)
            Two axis designations. The first axis defines the direction along
            which the flare decays. The second is the direction of the
            coordinate modification.
        end: 0 or 1
            With end=0, the flare exists at the end with the smallest
            coordinates in ``dir[0]]`` direction; with end=1, at the
            end with the highest coordinates.
        exp: float
            Exponent setting the speed of decay of the flare. The default
            makes the flare change linearly over the length `f`.

        Returns
        -------
        Coords
            A Coords with same shape as the input, but having a localized
            change of coordinates at one end of the point set.

        Examples
        --------
        >>> Coords(np.arange(6).reshape(-1,1)).flare(3.,1.6,(0,1),0)
        Coords([[0.  , 1.6 , 0.  ],
                [1.  , 1.07, 0.  ],
                [2.  , 0.53, 0.  ],
                [3.  , 0.  , 0.  ],
                [4.  , 0.  , 0.  ],
                [5.  , 0.  , 0.  ]])
        """
        ix, iz = dir
        bb = self.bbox()
        if end == 0:
            xmin = bb[0][ix]
            endx = self.test(dir=ix, max=xmin+xf)
            func = lambda x: (1.-(x-xmin)/xf) ** exp
        else:
            xmax = bb[1][ix]
            endx = self.test(dir=ix, min=xmax-xf)
            func = lambda x: (1.-(xmax-x)/xf) ** exp
        x = self.copy()
        x[endx, iz] += f * func(x[endx, ix])
        return x


    def map(self, func):
        """Map a :class:`Coords` by a 3-D function.

        This allows any mathematical transformation being applied to the
        coordinates of the Coords.

        Parameters
        ----------
        func: callable
            A function taking three float arguments (x,y,z coordinates of a
            point) and returning a tuple of three float values: the new
            coordinate values to replace (x,y,z).

            The function must be applicable to NumPy arrays, so it should
            only include numerical operations and functions understood by the
            numpy module.

            Often an inline lambda function is used, but a normally defined
            function will work as well.

        Returns
        -------
        Coords object
            The input Coords mapped through the specified function

        See Also
        --------
        map1: apply a 1-dimensional mapping to one coordinate direction
        mapd: map one coordinate by a function of the distance to a point

        Notes
        -----
        See also examples Cones, Connect, HorseTorse, Manantiales, Moebius,
        ScallopDome

        Examples
        --------
        >>> print(Coords([[1.,1.,1.]]).map(lambda x,y,z: [2*x,3*y,4*z]))
        [[2. 3. 4.]]

        """
        # we flatten coordinate sets to ease use of complicated functions
        # we should probably do this for map1 and mapd too
        X = self.points()
        f = np.zeros_like(X)
        f[..., 0], f[..., 1], f[..., 2] = func(X.x, X.y, X.z)
        return f.reshape(self.shape)


    def map1(self, dir, func, x=None):
        """Map one coordinate by a 1-D function of one coordinate.

        Parameters
        ----------
        dir: int (0,1 or 2)
            The coordinate axis to be modified.
        func: callable
            Function taking a single float argument (the coordinate `x`)
            and returning a float value: the new coordinate to replace the
            `dir` coordinate.

            The function must be applicable to NumPy arrays, so it should
            only include numerical operations and functions understood by the
            numpy module.

            Often an inline lambda function is used, but a normally defined
            function will work as well.
        x: int(0,1,2), optional
            If provided, specifies the coordinate that is used as argument
            in `func`. Default is to use the same as `dir`.

        Returns
        -------
        Coords object
            The input Coords where the `dir` coordinate has been mapped
            through the specified function.

        See Also
        --------
        map: apply a general 3-dimensional mapping function
        mapd: map one coordinate by a function of the distance to a point

        Notes
        -----
        See also example SplineSurface

        Examples
        --------
        >>> Coords(np.arange(4).reshape(-1,1)).map1(1,lambda x:0.1*x,0)
        Coords([[0. , 0. , 0. ],
                [1. , 0.1, 0. ],
                [2. , 0.2, 0. ],
                [3. , 0.3, 0. ]])

        """
        if x is None:
            x = dir
        f = self.copy()
        f[..., dir] = func(self[..., x])
        return f


    def mapd(self, dir, func, point=(0., 0., 0.), dist=None):
        """Map one coordinate by a function of the distance to a point.

        Parameters
        ----------
        dir: int (0, 1 or 2)
           The coordinate that will be replaced with ``func(d)``, where `d`
           is calculated as the distance to `point`.
        func: callable
            Function taking one float argument (distance to `point`) and
            returning a float: the new value for the `dist` coordinate.
            `dir` coordinate.

            The function must be applicable to NumPy arrays, so it should
            only include numerical operations and functions understood by the
            numpy module.

            Often an inline lambda function is used, but a normally defined
            function will work as well.
        point: float :term:`array_like` (3,)
            The point to where the distance is computed.
        dist: int or tuple of ints (0, 1, 2)
             The coordinate directions that are used to compute the distance
             to `point`. The default is to use 3-D distances.

        Examples
        --------
        Map a regular 4x4 point grid in the xy-plane onto a sphere with
        radius 1.5 and center at the corner of the grid.

        >>> from .simple import regularGrid
        >>> X = Coords(regularGrid([0.,0.],[1.,1.],[3,3]))
        >>> X.mapd(2,lambda d:np.sqrt(1.5**2-d**2),X[0,0],[0,1])
        Coords([[[0.  , 0.  , 1.5 ],
                 [0.33, 0.  , 1.46],
                 [0.67, 0.  , 1.34],
                 [1.  , 0.  , 1.12]],
        <BLANKLINE>
                [[0.  , 0.33, 1.46],
                 [0.33, 0.33, 1.42],
                 [0.67, 0.33, 1.3 ],
                 [1.  , 0.33, 1.07]],
        <BLANKLINE>
                [[0.  , 0.67, 1.34],
                 [0.33, 0.67, 1.3 ],
                 [0.67, 0.67, 1.17],
                 [1.  , 0.67, 0.9 ]],
        <BLANKLINE>
                [[0.  , 1.  , 1.12],
                 [0.33, 1.  , 1.07],
                 [0.67, 1.  , 0.9 ],
                 [1.  , 1.  , 0.5 ]]])

        """
        f = self.copy()
        if dist is None:
            dist = [0, 1, 2]
        try:
            ld = len(dist)
        except TypeError:
            ld = 1
            dist = [dist]
        d = f[..., dist[0]] - point[dist[0]]
        if ld==1:
            d = abs(d)
        else:
            d = d*d
            for i in dist[1:]:
                d1 = f[..., i] - point[i]
                d += d1*d1
            d = np.sqrt(d)
        f[..., dir] = func(d)
        return f


    def copyAxes(self, i, j, other=None):
        """Copy the coordinates along the axes j to the axes i.

        Parameters
        ----------
        i: int (0,1 2) or tuple of ints (0,1,2)
            One or more coordinate axes that should have replaced their
            coordinates by those along the axes `j`.
        j: int (0,1 2) or tuple of ints (0,1,2)
            One or more axes whose coordinates should be copied along the
            axes `i`. `j` should have the same type and length as `i`.
        other: Coords object, optional
            If provided, this is the source Coords for the coordinates. It
            should have the same shape as self. The default is to take the
            coords from self.

        Returns
        -------
        Coords object
            A Coords where the coordinates along axes `i` have been replaced
            by those along axes `j`.

        Examples
        --------
        >>> X = Coords([[1],[2]]).trl(2,5)
        >>> X
        Coords([[1., 0., 5.],
                [2., 0., 5.]])
        >>> X.copyAxes(1,0)
        Coords([[1., 1., 5.],
                [2., 2., 5.]])
        >>> X.copyAxes((0,1),(1,0))
        Coords([[0., 1., 5.],
                [0., 2., 5.]])
        >>> X.copyAxes((0,1,2),(1,2,0))
        Coords([[0., 5., 1.],
                [0., 5., 2.]])

        """
        if other is None:
            other = self
        f = self.copy()
        f[..., i] = other[..., j]
        return f


    def permuteAxes(self, order):
        """Permute the coordinate axes.

        Parameters
        ----------
        order: list of 3 int
            The new order of the axes. Normally this is a list of the 3 values
            0, 1, 2. It is however allowed to have identical value, like
            0, 0, 2. The latter will effectively project all points in the
            y-direction onto the (x,y) bisector plane.


        Returns
        -------
        Coords

        Examples
        --------
        >>> X = Coords(np.arange(6).reshape(-1,3))
        >>> X
        Coords([[0., 1., 2.],
                [3., 4., 5.]])
        >>> X.permuteAxes([2,1,0])
        Coords([[2., 1., 0.],
                [5., 4., 3.]])
        >>> X.permuteAxes([1,2,0])
        Coords([[1., 2., 0.],
                [4., 5., 3.]])
        >>> X.permuteAxes([0,2,2])
        Coords([[0., 2., 2.],
                [3., 5., 5.]])
        """
        if len(order) == 3 and min(order) >= 0 and max(order) <= 2:
            return self[..., order]
        raise ValueError("Expectd a list of three values 0, 1, 2")


    def swapAxes(self, i, j):
        """Swap two coordinate axes.

        Parameters
        ----------
        i: int (0,1,2)
            First coordinate axis
        j: int (0,1,2)
            Second coordinate axis

        Returns
        -------
        Coords
            A Coords with interchanged `i` and `j` coordinates.

        Warning
        -------
        Coords.swapAxes merely changes the order of the elements
        along the last axis of the ndarray.
        This is quite different from :meth:`numpy.ndarray.swapaxes`,
        which is inherited  by the Coords class. The latter method
        interchanges the array axes of the ndarray, and will not yield
        a valid Coords object if the interchange involves the last axis.

        Notes
        -----
        This is equivalent with ``self.copyAxes((i,j),(j,i))``

        Swapping two coordinate axes has the same effect as mirroring
        against the bisector plane between the two axes.

        Examples
        --------
        >>> X = Coords(np.arange(6).reshape(-1,3))
        >>> X
        Coords([[0., 1., 2.],
                [3., 4., 5.]])
        >>> X.swapAxes(2,0)
        Coords([[2., 1., 0.],
                [5., 4., 3.]])
        >>> X.swapaxes(1,0)
        array([[0., 3.],
               [1., 4.],
               [2., 5.]])
        """
        order = [0, 1, 2]
        order[i], order[j] = j, i
        return self[..., order]


    def rollAxes(self, n=1):
        """Roll the coordinate axes over the given amount.

        Parameters
        ----------
        n: int
            Number of positions to roll the axes. With the default (1), the
            old axes (0,1,2) become the new axes (2,0,1).

        Returns
        -------
        Coords
            A Coords where the coordinate axes of the points have been rolled
            over `n` positions.

        Notes
        -----
        ``X.rollAxes(1)`` can also be obtained by
        ``X.copyAxes((0,1,2),(2,0,1))``. It is also equivalent with
        a rotation over -120 degrees around the trisectrice of the first
        quadrant.

        Examples
        --------
        >>> X = Coords('0123')
        >>> X
        Coords([[0., 0., 0.],
                [1., 0., 0.],
                [1., 1., 0.],
                [0., 1., 0.]])
        >>> X.rollAxes(1)
        Coords([[0., 0., 0.],
                [0., 1., 0.],
                [0., 1., 1.],
                [0., 0., 1.]])
        >>> X.rotate(120,axis=[1.,1.,1.])
        Coords([[ 0.,  0.,  0.],
                [-0.,  1., -0.],
                [-0.,  1.,  1.],
                [-0., -0.,  1.]])

        """
        return np.roll(self, int(n) % 3, axis=-1)


    def projectOnPlane(self, n=2, P=(0., 0., 0.)):
        """Project a :class:`Coords` on a plane.

        Creates a parallel projection of the Coords on a plane.

        Parameters
        ----------
        n: int (0,1,2) or float :term:`array_like` (3,)
            The normal direction to the plane on which to project the Coords.
            If an int, it is a global axis.
        P: float :term:`array_like` (3,)
            A point in the projection plane, by default the global origin.

        Returns
        -------
        Coords
            The points of the Coords projected on the specified plane.

        Notes
        -----
        For projection on a plane parallel to a coordinate plane,
        it is far more efficient to specify the normal by an axis
        number rather than by a three component vector.

        This method will also work if any or both of P and n have
        the same shape as self, or can be reshaped to the same shape.
        This will project each point on its individual plane.

        See also example BorderExtension

        Examples
        --------
        >>> X = Coords(np.arange(6).reshape(2,3))
        >>> X.projectOnPlane(0,P=[2.5,0.,0.])
        Coords([[2.5, 1. , 2. ],
                [2.5, 4. , 5. ]])
        >>> X.projectOnPlane([1.,1.,0.])
        Coords([[-0.5, 0.5, 2. ],
                [-0.5, 0.5, 5. ]])
        """
        x = self.reshape(-1, 3).copy()
        P = Coords(P).reshape(-1, 3)
        if at.isInt(n):
            x[:, n] = P[:, n]
        else:
            n = at.normalize(Coords(n).reshape(-1, 3))
            d = at.dotpr(n, x-P).reshape(-1, 1)
            x -= d * n
        return x.reshape(self.shape)


    def projectOnSphere(self, radius=1., center=(0., 0., 0.)):
        """Project a :class:`Coords` on a sphere.

        Creates a central projection of a Coords on a sphere.

        Parameters
        ----------
        radius: float, optional
            The radius of the sphere, default 1.
        center: float :term:`array_like` (3,), optional
            The center of the sphere.
            The default is the origin of the global axes.

        Returns
        -------
        Coords
            A Coords with the input points projected from the center
            of the sphere onto its surface.

        Notes
        -----
        Points coinciding with the center of the sphere are returned
        unchanged.

        This is a central projection from the center of the sphere.
        For a parallel projection on a spherical surface, use
        :meth:`map`. See the Examples there.

        Examples
        --------
        >>> X = Coords([[x,x,1.] for x in range(1,4)])
        >>> X
        Coords([[1., 1., 1.],
                [2., 2., 1.],
                [3., 3., 1.]])
        >>> X.projectOnSphere()
        Coords([[0.58, 0.58, 0.58],
                [0.67, 0.67, 0.33],
                [0.69, 0.69, 0.23]])

        """
        d = self.distanceFromPoint(center)
        with np.errstate(all='ignore'):
            s = radius / d
            x = (self - center) * s[..., np.newaxis] + center
        return x


    def projectOnCylinder(self, radius=1., dir=0, center=[0., 0., 0.]):
        """Project the Coords on a cylinder with axis parallel to a global axis.

        Given a cylinder with axis parallel to a global axis, the points
        of the Coords are projected from the axis onto the surface of the
        cylinder.
        The default cylinder has its axis along the x-axis and a unit radius.
        No points of the :class:`Coords` should belong to the axis.

        Parameters
        ----------
        radius: float, optional
            The radius of the sphere, default 1.
        dir: int (0,1,2), optional
            The global axis parallel to the cylinder's axis.
        center: float :term:`array_like` (3,), optional
            A point on the axis of the cylinder. Default is the origin of
            the global axes.

        Returns
        -------
        Coords
            A Coords with the input points projected on the specified cylinder.

        Notes
        -----
        This is a projection from the axis of the cylinder. If you
        want a parallel projection on a cylindrical surface, you can use
        :meth:`map`.

        Examples
        --------
        >>> X = Coords([[x,x,1.] for x in range(1,4)])
        >>> X
        Coords([[1., 1., 1.],
                [2., 2., 1.],
                [3., 3., 1.]])
        >>> X.projectOnCylinder()
        Coords([[1.  , 0.71, 0.71],
                [2.  , 0.89, 0.45],
                [3.  , 0.95, 0.32]])
        """
        d = self.distanceFromLine(center, at.unitVector(dir))
        s = radius / d
        c = np.resize(np.asarray(center), self.shape)
        c[..., dir] = self[..., dir]
        f = self - c
        for i in range(3):
            if i != dir:
                f[..., i] *= s
        f += c
        return f


    def projectOnSurface(self, S, dir=0, missing='e', return_indices=False):
        """Project a :class:`Coords` on a triangulated surface.

        The points of the Coords are projected in the specified direction `dir`
        onto the surface S. If a point has multiple projecions in the direction,
        the one nearest to the original is returned.

        Parameters
        ----------
        S: :class:`~trisurface.TriSurface`
            A triangulated surface
        dir: int (0,1,2) or float :term:`array_like` (3,)
            The direction of the projection, either a global axis direction
            or specified as a vector with three components.
        missing: 'o', 'r' or 'e'
            Specifies how to treat cases where the projective line does not
            intersect the surface:

            - 'o': return the original point,
            - 'r': remove the point from the result.
              Use `return_indices` = True to find out which original
              points correspond with the projections.
            - 'e': raise a ProjectionMissing exception (default).
        return_indices: bool, optional
            If True, also returns the indices of the points that have a
            projection on the surface.

        Returns
        -------
        x: Coords
            A Coords with the projections of the input points on the surface.
            With `missing='o'`, this will have the same shape as the input,
            but some points might not actually lie on the surface.
            With `missing='r'`, the shape will be (npoints,3) and the number
            of points may be less than the input.
        ind: int array, optional
            Only returned if `return_indices` is True: an index in the input
            Coords of the points that have a projection on the surface.
            With `missing='r'`, this gives the indices of the orginal
            points corresponding with the projections.
            With `missing='o'`, this can be used to check which points
            are located on the surface.
            The index is sequential, no matter what the shape of the input
            Coords is.

        Examples
        --------
        >>> from pyformex import simple
        >>> S = simple.sphere().scale(2).trl([0.,0.,0.2])
        >>> x = pattern('0123')
        >>> print(x)
        [[0. 0. 0.]
         [1. 0. 0.]
         [1. 1. 0.]
         [0. 1. 0.]]
        >>> xp = x.projectOnSurface(S,[0.,0.,1.])
        >>> print(xp)
        [[ 0.    0.   -1.8 ]
         [ 1.    0.   -1.52]
         [ 1.    1.   -1.2 ]
         [ 0.    1.   -1.53]]
        """
        from pyformex.geomtools import anyPerpendicularVector
        if missing not in ('e', 'o', 'r'):
            raise ValueError("Invalid value for 'missing'")

        if at.isInt(dir):
            dir = at.unitVector(dir)
        else:
            dir = np.asarray(dir)
        x = self.reshape(-1, 3)
        # Create planes through x in direction n
        # WE SHOULD MOVE THIS TO geomtools?
        v1 = anyPerpendicularVector(dir)
        v2 = np.cross(dir, v1)
        # Create set of cuts with set of planes
        cuts = [S.intersectionWithPlane(xi, v1) for xi in x]
        nseg = [c.nelems() for c in cuts]
        cutid = [i for i, n in enumerate(nseg) if n > 0]
        # remove the empty intersections
        cuts = [cuts[i] for i in cutid]

        # cut the cuts with second set of planes
        cuts = [c.toFormex().intersectionWithPlane(xi, v2).coords
                for c, xi in zip(cuts, x[cutid])]
        npts = [p.shape[0] for p in cuts]
        # remove the empty intersections
        cuts = [c for c, n in zip(cuts, npts) if n > 0]
        cutid = [c for c, n in zip(cutid, npts) if n > 0]

        # find the points closest to self
        cuts = [p.points()[p.closestToPoint(xi)]
                for p, xi in zip(cuts, x[cutid])]
        cuts = Coords.concatenate(cuts)

        if cuts.shape[0] < x.shape[0]:
            if missing == 'e':
                raise ProjectionMissing(
                    "The projection of some point(s) in the "
                    "specified direction does not cut the surface")
            elif missing == 'o':
                x = x.copy()
                x[cutid] = cuts
                cuts = x.reshape(self.shape)

        if return_indices:
            return cuts, cutid
        else:
            return cuts


    # Extra transformations implemented by plugins


    def isopar(self, eltype, coords, oldcoords):
        """Perform an isoparametric transformation on a Coords.

        This creates an isoparametric transformation
        :class:`~plugins.isopar.Isopar` object
        and uses it to transform the input Coords. It is equivalent to::

          Isopar(eltype,coords,oldcoords).transform(self)

        See :class:`~plugins.isopar.Isopar` for parameters.
        """
        from pyformex.plugins.isopar import Isopar
        return Isopar(eltype, coords, oldcoords).transform(self)


    def addNoise(self, rsize=0.05, asize=0.0):
        """Add random noise to a Coords.

        A random amount is added to each individual coordinate of the Coords.
        The maximum difference of the coordinates from their original value
        is controled by two parameters `rsize` and `asize` and will not
        exceed ``asize+rsize*self.maxsize()``.

        Parameters
        ----------
        rsize: float
            Relative size of the noise compared with the maximum size
            of the input Coords.
        asize: float
            Absolute size of the noise

        Examples
        --------
        >>> X = Coords(np.arange(6).reshape(2,3))
        >>> print((abs(X.addNoise(0.1) - X) < 0.1 * X.sizes()).all())
        True
        """
        max = asize + rsize * self.maxsize()
        return self + at.randomNoise(self.shape, -max, +max)


############################################################################
    #
    #   Transformations that change the shape of the Coords array
    #

    def replicate(self, n, dir=0, step=1.):
        """Replicate a Coords n times with a fixed translation step.

        Parameters
        ----------
        n: int
            Number of times to replicate the Coords.
        dir: int (0,1,2) or float :term:`array_like` (3,)
            The translation vector. If an int, it specifies a global axis
            and the translation is in the direction of that axis.
        step: float
            If ``dir`` is an int, this is the length of the translation.
            Else, it is a multiplying factor applied to the translation
            vector.

        Returns
        -------
        Coords
            A Coords with an extra first axis with length `n`. The new
            shape thus becomes ``(n,) + self.shape``.
            The first component along the axis 0 is identical to the
            original Coords. Each following component is equal to the
            previous translated over `(dir,step)`, where `dir` and `step` are
            interpreted just like in the :meth:`translate` method.

        Notes
        -----
        :meth:`rep` is a convenient shorthand for :meth:`replicate`.

        Examples
        --------
        >>> Coords([0.,0.,0.]).replicate(4,1,1.2)
        Coords([[0. , 0. , 0. ],
                [0. , 1.2, 0. ],
                [0. , 2.4, 0. ],
                [0. , 3.6, 0. ]])
        >>> Coords([0.]).replicate(3,0).replicate(2,1)
        Coords([[[0., 0., 0.],
                 [1., 0., 0.],
                 [2., 0., 0.]],
        <BLANKLINE>
                [[0., 1., 0.],
                 [1., 1., 0.],
                 [2., 1., 0.]]])

        """
        n = int(n)
        f = np.resize(self, (n,)+self.shape)
        if at.isInt(dir):
            for i in range(1, n):
                f[i, ..., dir] += i*step
        else:
            dir = Coords(dir, copy=True)
            if step != 1.:
                dir *= step
            for i in range(1, n):
                f[i] += i*dir
        return Coords(f)


    def rosette(self, n, angle=None, axis=2, around=(0., 0., 0.),
                angle_spec=at.DEG):
        """Create rotational replications of a Coords.

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
        Coords
            A Coords array with an extra first dimension equal to n.
            The Coords holds n rotational replications with given angular step.
            The input Coords is the first of the n replicas.

        Examples
        --------
        >>> Coords([1., 0., 0.]).rosette(4, 90.)
        Coords([[ 1.,  0.,  0.],
                [ 0.,  1.,  0.],
                [-1.,  0.,  0.],
                [-0., -1.,  0.]])
        >>> Coords([1., 0., 0.]).rosette(3, 90., around=(0.,1.,0.))
        Coords([[ 1.,  0.,  0.],
                [ 1.,  2.,  0.],
                [-1.,  2.,  0.]])
        """
        if angle is None:
            angle = 360. / n
        f = self - around
        f = np.array([f for i in range(n)])
        for i in range(1, n):
            m = np.array(at.rotationMatrix(i*angle, axis, angle_spec))
            f[i] = np.dot(f[i], m)
        return Coords(f + around)


    def split(self):
        """Split the Coords in blocks along first axis.

        Returns
        -------
        list of Coords objects
            A list of Coords objects being the subarrays takeb along the
            axis 0. The number of objects in the list is ``self.shape[0]``
            and each Coords has the shape ``self.shape[1:]``.

        Raises
        ------
        ValueError
            If ``self.ndim < 2``.

        Examples
        --------
        >>> Coords(np.arange(6).reshape(2,3)).split()
        [Coords([0., 1., 2.]), Coords([3., 4., 5.])]
        """
        if self.ndim < 2:
            raise ValueError("Can only split arrays with dim >= 2")
        return [self[i] for i in range(self.shape[0])]


    def sort(self, order=(0, 1, 2)):
        """Sort points in the specified order of their coordinates.

        Parameters
        ----------
        order: int (0,1,2) or tuple of ints (0,1,2)
            The order in which the coordinates have to be taken into
            account during the sorting operation.

        Returns
        -------
        int array
            An index into the sequential point list ``self.points()``
            thus that the points are sorted in order of the specified
            coordinates.

        Examples
        --------
        >>> X = Coords([[5,3,0],[2,4,3],[2,3,3],[5,6,2]])
        >>> X.sort()
        array([2, 1, 0, 3])
        >>> X.sort((2,1,0))
        array([0, 3, 2, 1])
        >>> X.sort(1)
        array([0, 2, 1, 3])
        """
        if at.isInt(order):
            order = (order,)
        return at.sortByColumns(self.points()[:, order])


    def boxes(self, ppb=1, shift=0.5, minsize=1.e-5):
        """Create a grid of equally sized boxes spanning the :class:`Coords`.

        A regular 3D grid of equally sized boxes is created enclosing all
        the points of the Coords. The size, position and number of boxes
        are determined from the specified parameters.

        Parameters
        ----------
        ppb: int
            Average number of points per box. The box sizes and number
            of boxes will be determined to approximate this number.
        shift: float (0.0 .. 1.0)
            Relative shift value for the grid. Applying a shift of 0.5
            will make the lowest coordinate values fall at the center
            of the outer boxes.
        minsize: float
            Absolute minimal size of the boxes, in each coordinate direction.

        Returns
        -------
        ox: float array (3,)
            The minimal coordinates of the box grid.
        dx: float array (3,)
            The box size in the three global axis directions.
        nx: int array (3,)
            Number of boxes in each of the coordinate directions.

        Notes
        -----
        The primary purpose of this method is its use in the :meth:`fuse`
        method. The boxes allow to quickly label the points inside each
        box with an integer value (the box number), so that it becomes
        easy to find close points by their same label.

        Because of the possibility that two very close points fall in
        different boxes (if they happen to be close to a box border),
        procedures based on these boxes are often repeated twice, with
        a different shift value.

        Examples
        --------
        >>> X = Coords([[5,3,0],[2,4,3],[2,3,3],[5,6,2]])
        >>> print(*X.boxes())
        [ 0.5  1.5 -1.5] [3.  3.  3.] [2 2 2]
        >>> print(* X.boxes(shift=0.1))
        [ 1.7  2.7 -0.3] [3.  3.  3.] [2 2 2]
        >>> X = Coords([[1.,1.,0.],[1.001,1.,0.],[1.1,1.,0.]])
        >>> print(*X.boxes())
        [ 0.98  0.98 -0.02] [0.03  0.03  0.03] [4 1 1]
        """
        # serialize points
        x = self.reshape(-1, 3)
        nnod = x.shape[0]
        # Calculate box size
        lo, hi = x.bbox()
        sz = hi-lo
        esz = sz[sz > 0.0]  # only keep the nonzero dimensions

        if esz.size == 0:
            # All points are coincident
            ox = np.zeros(3, dtype=at.Float)
            dx = np.ones(3, dtype=at.Float)
            nx = np.ones(3, dtype=at.Int)

        else:
            nboxes = max(1, nnod // ppb)  # ideal total number of boxes
            vol = esz.prod()
            # avoid error message on the global sz/nx calculation
            with np.errstate(all='ignore'):
                # set ideal box size, but not smaller than minsize
                boxsz = max(minsize, (vol/nboxes) ** (1./esz.shape[0]))
                nx = (sz/boxsz).astype(np.int32)
                dx = np.where(nx>0, sz/nx, boxsz)

        # perform the origin shift and adjust nx to make sure we enclose all
        ox = lo - dx*shift
        ex = ox + dx*nx
        adj = np.ceil((hi-ex)/dx).astype(at.Int).clip(min=0)
        nx += adj
        return ox, dx, nx


    def fuse(self, ppb=1, shift=0.5, rtol=1.e-5, atol=1.e-8, repeat=True):
        """Find (almost) coinciding points and return a compressed set.

        This method finds the points that are very close to each other
        and replaces them with a single point. See Notes below for
        explanation about the method being used and the parameters being
        used. In most cases, `atol` and `rtol` are probably the only
        ones you want to change from the defaults. Two points are
        considered the same if all their coordinates differ less than
        the maximum of `atol` and `rtol * self.maxsize()`.

        Parameters
        ----------
        ppb: int, optional
            Average number of points per box. The box sizes and number
            of boxes will be determined to approximate this number.
        shift: float (0.0 .. 1.0), optional
            Relative shift value for the box grid. Applying a shift of 0.5
            will make the lowest coordinate values fall at the center
            of the outer boxes.
        rtol: float, optional
            Relative tolerance used when considering two points for fusing.
        atol: float, optional
            Absolute tolerance used when considering two points for fusing.
        repeat: bool, optional
            If True, repeat the procedure with a second shift value.

        Returns
        -------
        coords: Coords object (npts,3)
            The unique points obtained from merging the very close points
            of a Coords.
        index: int array
            An index in the unique coordinates array `coords` for each of
            the original points. The shape of the index array is equal to
            the point shape of the input Coords (``self.pshape()``). All
            the values are in the range 0..npts.


        Note
        ----
        From the return values ``coords[index]`` will restore the original
        Coords (with accuracy equal to the tolerance used in the fuse
        operation)

        Notes
        -----
        The procedure works by first dividing the 3D space in a number of
        equally sized boxes, with a average population of `ppb` points. The
        arguments `pbb` and `shift` are passed to :meth:`boxes` for this
        purpose.
        The boxes are identified by 3 integer coordinates, from which a
        unique integer scalar is computed, which is then used to sort the
        points.
        Finally only the points inside the same box need to be compared.
        Two points are considered equal if all their coordinates differ less
        than the maximum of `atol` and `rtol * self.maxsize()`.
        Points considered very close are replaced by a single one, and an index
        is kept from the original points to the new list of points.

        Running the procedure once does not guarantee finding all close nodes:
        two close nodes might be in adjacent boxes. The performance hit for
        testing adjacent boxes is rather high, and the probability of separating
        two close nodes with the computed box limits is very small.
        Therefore, the most sensible way is to run the procedure twice, with
        a different shift value (they should differ more than the tolerance).
        Specifying repeat=True will automatically do this with a second
        shift value equal to shift+0.25.

        Because fusing points is a very important and frequent step in many
        geometrical modeling and conversion procedures, the core part of
        this function is available in a C as well as a Python version,
        in the module pyformex.lib.misc. The much faster C version will be used
        if available.

        Examples
        --------
        >>> X = Coords([[1.,1.,0.],[1.001,1.,0.],[1.1,1.,0.]])
        >>> x,e = X.fuse(atol=0.01)
        >>> print(x)
        [[1.  1.  0. ]
         [1.1 1.  0. ]]
        >>> print(e)
        [0 0 1]
        >>> np.allclose(X,x[e],atol=0.01)
        True

        """
        from pyformex.lib import misc
        if self.size == 0:
            # allow empty coords sets
            return Coords(), np.array([], dtype=at.Int).reshape(self.pshape())

        if repeat:
            # Apply twice with different shift value
            coords, index = self.fuse(ppb, shift, rtol, atol, repeat=False)
            newshift = shift + (0.25 if shift <= 0.5 else -0.25)
            coords, index2 = coords.fuse(ppb, newshift, rtol, atol, repeat=False)
            index = index2[index]
            return coords, index

        #########################################
        # This is the single pass
        x = self.points()

        if (self.sizes()==0.).all():
            # All points are coincident
            e = np.zeros(x.shape[0], dtype=np.int32)
            x = x[:1]
            return x, e

        # Compute boxes
        ox, dx, nx = self.boxes(ppb=ppb, shift=shift, minsize=atol)

        # Create box coordinates for all nodes
        ind = np.floor((x-ox)/dx).astype(np.int32)
        # Create unique box numbers in smallest direction first
        o = np.argsort(nx)
        val = (ind[:, o[2]] * nx[o[2]] + ind[:, o[1]]) * nx[o[1]] + ind[:, o[0]]
        # sort according to box number
        srt = np.argsort(val)
        # rearrange the data according to the sort order
        val = val[srt]
        x = x[srt]
        # make sure we use np.int32 (for the fast C fuse function)
        # Using np.int32 limits this procedure to 10**9 points, which is more
        # than enough for all practical purposes
        x = x.astype(np.float32)
        val = val.astype(np.int32)
        tol = np.float32(max(rtol*self.maxsize(), atol))
        nnod = val.shape[0]
        flag = np.ones((nnod,), dtype=np.int32)   # 1 = new, 0 = existing node
        # new fusing algorithm
        sel = np.arange(nnod).astype(np.int32)      # replacement unique node nr
        misc.coordsfuse(x, val, flag, sel, tol)     # fuse the close points
        x = x[flag>0]          # extract unique nodes
        s = sel[np.argsort(srt)]  # and indices for old nodes
        return (x, s.reshape(self.shape[:-1]))


    def unique(self, **kargs):
        """Returns the unique points after fusing.

        This is just like :meth:`fuse` and takes the same arguments,
        but only returns the first argument: the unique points in the Coords.
        """
        return self.fuse(**kargs)[0]


    def adjust(self, **kargs):
        """Find (almost) identical nodes and adjust them to be identical.

        This is like the :meth:`fuse` operation, but it does not fuse the
        close neigbours to a single point.
        Instead it adjust the coordinates of the points to be identical.

        The parameters are the same as for the :meth:`fuse` method.

        Returns
        -------
        Coords
            A Coords with the same shape as the input, but where close
            points now have identical coordinates.

        Examples
        --------
        >>> X = Coords([[1.,1.,0.],[1.001,1.,0.],[1.1,1.,0.]])
        >>> print(X.adjust(atol=0.01))
        [[1.  1.  0. ]
         [1.  1.  0. ]
         [1.1 1.  0. ]]

        """
        coords, index = self.fuse(**kargs)
        return coords[index]


    def match(self, coords, **kargs):
        """Match points in another :class:`Coords` object.

        Find the points from another Coords object that coincide with
        (or are very close to) points of ``self``.
        This method works by concatenating the serialized point sets of
        both Coords and then fusing them.

        Parameters
        ----------
        coords: Coords
            The Coords object to compare the points with.
        **kargs: keyword arguments
            Keyword arguments passed to the :meth:`fuse` method.

        Returns
        -------
        : 1-dim int array
            The array has a length of `coords.npoints()`. For each point
            in `coords` it holds the index of a point in `self` coinciding
            with it, or a value -1 if there is no matching point.
            If there are multiple matching points in `self`, it is undefined
            which one will be returned. To avoid this ambiguity, you can
            first fuse the points of `self`.

        See Also
        --------
        hasMatch
        fuse

        Examples
        --------
        >>> X = Coords([[1.],[2.],[3.],[1.]])
        >>> Y = Coords([[1.],[4.],[2.00001]])
        >>> print(X.match(Y))
        [ 0 -1  1]

        """
        if 'clean' in kargs:
            utils.warn('warn_coords_match_changed')
            del kargs['clean']

        x = Coords.concatenate([self.points(), coords.points()])
        c, e = x.fuse(**kargs)
        e0, e1 = e[:self.npoints()], e[self.npoints():]
        return at.findFirst(e0, e1)


    def hasMatch(self, coords, **kargs):
        # TODO: This is incorrect: doubles in self are not reported
        # It is documented, but should we fix it or remove this method??
        """Find out which points are also in another Coords object.

        Find the points from self that coincide with (or are very close to)
        some point of `coords`.
        This method is very similar to :meth:`match`, but does not give
        information about which point of `self` matches which point of
        `coords`.

        Parameters
        ----------
        coords: Coords
            The Coords object to compare the points with.
        **kargs: keyword arguments
            Keyword arguments passed to the :meth:`fuse` method.

        Returns
        -------
        int array
            A 1-dim int array with the unique sorted indices of the points
            in `self` that have a (nearly) matching point in `coords`.

        Warning
        -------
        If multiple points in `self` coincide with the same point in
        `coords`, only one index will be returned for this case. To avoid
        this, you can fuse `self` before using this method.

        See also
        --------
        match

        Examples
        --------
        >>> X = Coords([[1.],[2.],[3.],[1.]])
        >>> Y = Coords([[1.],[4.],[2.00001]])
        >>> print(X.hasMatch(Y))
        [0 1]

        """
        matches = self.match(coords, **kargs)
        return np.unique(matches[matches>-1])


    def append(self, coords):
        """Append more coords to a Coords object.

        The appended coords should have matching dimensions in all
        but the first axis.

        Parameters
        ----------
        coords: Coords object
            A Coords having a shape with ``shape[1:]`` equal to
            ``self.shape[1:]``.

        Returns
        -------
        Coords
            The concatenated Coords object (self,coords).

        Notes
        -----
        Unlike Python's list.append, this does not change the object
        in place, but returns the enlraged object.
        It is like :func:`numpy.append`, but the result
        is a :class:`Coords` object, the default axis is the first one
        instead of the last, and it is a method rather than a function.

        See Also
        --------
        concatenate: concatenate a list of Coords

        Examples
        --------
        >>> X = Coords([[1],[2]])
        >>> Y = Coords([[3],[4]])
        >>> X.append(Y)
        Coords([[1., 0., 0.],
                [2., 0., 0.],
                [3., 0., 0.],
                [4., 0., 0.]])
        """
        coords = Coords(coords).reshape((-1,) + self.shape[1:])
        return Coords(np.append(self, coords, axis=0))


    @classmethod
    def concatenate(clas, L, axis=0):
        """Concatenate a list of :class:`Coords` objects.

        Class method to concatenate a list of Coords along the given axis.

        Parameters
        ----------
        L: list of Coords objects
            The Coords objects to be concatenated. All should have the same
            shape except for the length of the specified axis.

        Returns
        -------
        Coords
            A Coords with at least two dimensions, even when the list contains
            only a single Coords with a single point, or is empty.

        Raises
        ------
        ValueError
            If the shape of the Coords in the list do not match or if
            concatenation along the last axis is attempted.

        Notes
        -----
        This is a class method. It is commonly invoked as
        ``Coords.concatenate``, and if used as a method on a Coords object,
        that object will not be included in the list.

        It is like :func:`numpy.concatenate` (which it uses internally),
        but makes sure to return :class:`Coords` object, and sets the first
        axis as default instead of the last (which would not make sense).

        See Also
        --------
        append: append a Coords to self

        Examples
        --------
        >>> X = Coords([1.,1.,0.])
        >>> Y = Coords([[2.,2.,0.],[3.,3.,0.]])
        >>> print(Coords.concatenate([X,Y]))
        [[1. 1. 0.]
         [2. 2. 0.]
         [3. 3. 0.]]
        >>> print(Coords.concatenate([X,X]))
        [[1. 1. 0.]
         [1. 1. 0.]]
        >>> print(Coords.concatenate([X]))
        [[1. 1. 0.]]
        >>> print(Coords.concatenate([Y]))
        [[2. 2. 0.]
         [3. 3. 0.]]
        >>> print(X.concatenate([Y]))
        [[2. 2. 0.]
         [3. 3. 0.]]
        >>> Coords.concatenate([])
        Coords([], shape=(0, 3))
        >>> Coords.concatenate([[Y],[Y]],axis=1)
        Coords([[[2., 2., 0.],
                 [3., 3., 0.],
                 [2., 2., 0.],
                 [3., 3., 0.]]])
        """
        L2 = np.atleast_2d(*L)
        if len(L2) == 0 or max([len(x) for x in L2]) == 0:
            return Coords()
        if len(L) == 1:
            return L2
        else:
            return Coords(data=np.concatenate(L2, axis=axis))


    @classmethod
    def fromstring(clas, s, sep=' ', ndim=3, count=-1):
        """Create a :class:`Coords` object with data from a string.

        This uses :func:`numpy.fromstring` to read coordinates from a
        string and creates a Coords object from them.

        Parameters
        ----------
        s: str
            A string containing a single sequence of float numbers separated
            by whitespace and a possible separator string.
        sep: str
            The separator used between the coordinates. If not a space,
            all extra whitespace is ignored.
        ndim: int,
            Number of coordinates per point. Should be 1, 2 or 3 (default).
            If 1, resp. 2, the coordinate string only holds x, resp. x,y
            values.
        count: int, optional
            Total number of coordinates to read. This should be a multiple
            of `ndim`. The default is to read all the coordinates in the
            string.

        Returns
        -------
        Coords
            A Coords object with the coordinates read from the string.

        Raises
        ------
        ValueError
            If count was provided and the string does not contain that exact
            number of coordinates.

        Notes
        -----
        For writing the coordinates to a string, :func:`numpy.tostring` can
        be used.

        Examples
        --------
        >>> Coords.fromstring('4 0 0 3 1 2 6 5 7')
        Coords([[4., 0., 0.],
                [3., 1., 2.],
                [6., 5., 7.]])
        >>> Coords.fromstring('1 2 3 4 5 6',ndim=2)
        Coords([[1., 2., 0.],
                [3., 4., 0.],
                [5., 6., 0.]])

        """
        x = np.fromstring(s, dtype=at.Float, sep=sep, count=count)
        if count > 0 and x.size != count:
            raise ValueError(f"Number of coordinates read: {x.size}, "
                             f"expected {count}!")
        if x.size % ndim != 0:
            raise ValueError(f"Number of coordinates read: {x.size}, "
                             f"expected a multiple of {ndim}!")
        return Coords(x.reshape(-1, ndim))


    @classmethod
    def fromfile(clas, fil, **kargs):
        """Read a :class:`Coords` from file.

        This uses :func:`numpy.fromfile` to read coordinates from a file
        and create a Coords. Coordinates X, Y and Z for subsequent points
        are read from the file. The total number of coordinates on the file
        should be a multiple of 3.

        Parameters
        ----------
        fil: str or file
            If str, it is a file name. An open file object can also be passed
        **kargs:
            Arguments to be passed to :func:`numpy.fromfile`.

        Returns
        -------
        Coords
            A Coords formed by reading all coordinates from the specified file.

        Raises
        ------
        ValueError
            If the number of coordinates read is not a multiple of 3.

        See Also
        --------
        numpy.fromfile: read an array to file
        numpy.tofile: write an array to file

        """
        x = np.fromfile(fil, dtype=at.Float, **kargs)
        if x.size % 3 != 0:
            raise ValueError(f"Number of coordinates read: {x.size}, "
                             "should be multiple of 3!")
        return Coords(x.reshape(-1, 3))


    def interpolate(self, X, div):
        """Create linear interpolations between two Coords.

        A linear interpolation of two equally shaped Coords X and Y at
        parameter value t is a Coords with the same shape as X and Y
        and with coordinates given by ``X * (1.0-t) + Y * t``.

        Parameters
        ----------
        X: Coords object
            A Coords object with same shape as `self`.
        div: :term:`seed`
            This parameter is sent through the :func:`arraytools.smartSeed`
            to generate a list of parameter values for which to compute the
            interpolation. Usually, they are in the range 0.0 (self)
            to 1.0 (X). Values outside the range can be used however
            and result in linear extrapolations.

        Returns
        -------
        Coords
            A Coords object with an extra (first) axis, containing the
            concatenation of the interpolations of `self` and `X` at all
            parameter values in `div`.
            Its shape is (n,) + self.shape, where n is the number of values
            in `div`.

        Examples
        --------
        >>> X = Coords([0])
        >>> Y = Coords([1])
        >>> X.interpolate(Y,4)
        Coords([[0.  , 0.  , 0.  ],
                [0.25, 0.  , 0.  ],
                [0.5 , 0.  , 0.  ],
                [0.75, 0.  , 0.  ],
                [1.  , 0.  , 0.  ]])
        >>> X.interpolate(Y,[-0.1, 0.5, 1.25])
        Coords([[-0.1 , 0.  , 0.  ],
                [ 0.5 , 0.  , 0.  ],
                [ 1.25, 0.  , 0.  ]])
        >>> X.interpolate(Y,(4,0.3,0.2))
        Coords([[0.  , 0.  , 0.  ],
                [0.21, 0.  , 0.  ],
                [0.47, 0.  , 0.  ],
                [0.75, 0.  , 0.  ],
                [1.  , 0.  , 0.  ]])

        """
        if self.shape != X.shape:
            raise RuntimeError("`X` should have same shape as `self`")
        div = at.smartSeed(div)
        return self + np.outer(div, X-self).reshape((-1,)+self.shape)


    def convexHull(self, dir=None, return_mesh=False):
        """Return the 2D or 3D convex hull of a :class:`Coords`.

        Parameters
        ----------
        dir: int (0,1,2), optional
            If provided, it is one if the global axes and the 2D convex
            hull in the specified viewing direction will be computed.
            The default is to compute the 3D convex hull.
        return_mesh: bool, optional
            If True, returns the convex hull as a :class:`~mesh.Mesh` object
            instead of a :class:`~connectivity.Connectivity`.

        Returns
        -------
        :class:`~connectivity.Connectivity` or :class:`~mesh.Mesh`
            The default is to return a Connectivity table containing the
            indices of the points that constitute the convex hull of the
            Coords. For a 3D hull, the Connectivity has plexitude 3, and
            eltype 'tri3'; for a 2D hull these are respectively 2 and 'line2'.
            The values in the Connectivity refer to the flat points list
            as obtained from :meth:`points`.

            If `return_mesh` is True, a compacted Mesh is returned
            instead of the Connectivity. For a 3D hull, the Mesh will be a
            :class:`~trisurface.TriSurface`, otherwise
            it is a Mesh of 'line2' elements.

            The returned Connectivity or Mesh will be empty if all the points
            are in a plane for the 3D version, or an a line in the viewing
            direction for the 2D version.

        Notes
        -----
        This uses SciPy to compute the convex hull. You need to have
        SciPy version 0.12.0 or higher. On Debian/Ubuntu-likes install
        package 'python3-scipy'.

        See also example ConvexHull.

        """
        from pyformex.plugins import scipy_itf
        points = self.points()
        if dir is not None and at.isInt(dir):
            ind = list(range(3))
            ind.remove(dir)
            points = points[:, ind]
        hull = scipy_itf.convexHull(points)
        if return_mesh:
            from pyformex.mesh import Mesh
            hull = Mesh(self.points(), hull).compact()
            if dir is not None and at.isInt(dir):
                hull.coords[:, dir] = 0.0

        return hull


    def actor(self, **kargs):
        """This allows a Coords object to be drawn as Geometry"""
        if self.npoints() == 0:
            return None

        from pyformex.formex import Formex
        return Formex(self.reshape(-1, 3)).actor(**kargs)


    # Convenient shorter notations
    rot = rotate
    trl = translate
    rep = replicate

    # deprecated but kept for compatibility
    def bump1(self, dir, a, func=None, dist=0):
        return self.bump(dir, a, func, dist=dist)


    ###################
    ## PZF interface ##

    def pzf_dict(self):
        return {'data': self}


###########################################################################
##
##   functions
##
#########################

def otherAxes(i):
    # TODO: this can be removed
    """Return all global axes except the specified one

    Parameters
    ----------
    i: int (0,1,2)
        One of the global axes.

    Returns
    -------
    tuple of ints
        Two ints (j,k) identifying the other global axes in such order
        that (i,j,k) is a right-handed coordinate system.

    >>> otherAxes(1)
    (2, 0)
    """
    return ((i+1) % 3, (i+2) % 3)


def bbox(objects):
    """Compute the bounding box of a list of objects.

    The bounding box of an object is the smallest rectangular cuboid
    in the global Cartesian coordinates, such that no points of the
    objects lie outside that cuboid. The resulting bounding box of the list
    of objects is the smallest bounding box that encloses all the objects
    in the list.

    Parameters
    ----------
    objects: object or list of objects
        One or more (list or tuple) objects that have a method :meth:`bbox`
        returning the object's bounding box as a Coords with two points.

    Returns
    -------
    Coords
        A Coords object with two points: the first contains the minimal
        coordinate values, the second has the maximal ones of the overall
        bounding box encompassing all objects.

    Notes
    -----
    Objects that do not have a :meth:`bbox` method or whose :meth:`bbox`
    method returns invalid values, are silently ignored.

    See Also
    --------
    Coords.bbox: compute the bounding box of a :class:`Coords` object.

    Examples
    --------
    >>> bbox((Coords([-1.,1.,0.]),Coords([2,-3])))
    Coords([[-1., -3.,  0.],
            [ 2.,  1.,  0.]])

    """
    if not isinstance(objects, (list, tuple)):
        objects = [objects]
    bboxes = [f.bbox() for f in objects
              if hasattr(f, 'bbox') and not np.isnan(f.bbox()).any()]
    bboxes = [bb for bb in bboxes if bb is not None]
    if len(bboxes) == 0:
        o = origin()
        bboxes = [[o, o]]
    return Coords(np.concatenate(bboxes)).bbox()


def bboxIntersection(A, B):
    """Compute the intersection of the bounding box of two objects.

    Parameters
    ----------
    A: first object
        An object having a bbox method returning its boundary box.
    B: second object
        Another object having a bbox method returning its boundary box.

    Returns
    -------
    Coords (2,3)
        A Coords specifying the intersection of the bounding boxes of
        the two objects. This again has the format of a bounding box:
        a coords with two points: one with the minimal and one with
        the maximal coordinates. If the two bounding boxes do not
        intersect, an empty Coords is returned.

    Notes
    -----
    Since bounding boxes are Coords objects, it is possible to pass
    computed bounding boxes as arguments. The bounding boxes are indeed
    their own bounding box.

    Examples
    --------
    >>> A = Coords([[-1.,1.],[2,-3]])
    >>> B = Coords([[0.,1.],[4,2]])
    >>> C = Coords([[0.,2.],[4,2]])
    >>> bbox((A,B))
    Coords([[-1., -3.,  0.],
            [ 4.,  2.,  0.]])

    The intersection of the bounding boxes of A and B
    degenerates into a line segment parallel to the x-axis:

    >>> bboxIntersection(A,B)
    Coords([[0., 1., 0.],
            [2., 1., 0.]])

    The bounding boxes of A and C do not intersect:

    >>> bboxIntersection(A,C)
    Coords([], shape=(0, 3))

    """
    Amin, Amax = A.bbox()
    Bmin, Bmax = B.bbox()
    min = np.where(Amin>Bmin, Amin, Bmin)
    max = np.where(Amax<Bmax, Amax, Bmax)
    if (min > max).any():
        bb = Coords()
    else:
        bb = Coords([min, max])
    return bb


def origin():
    """ReturnCreate a Coords holding the origin of the global coordinate system.

    Returns
    -------
    Coords (3,)
        A Coords holding a single point with coordinates (0.,0.,0.).

    Exmaples
    --------
    >>> origin()
    Coords([0., 0., 0.])

    """
    return Coords(np.zeros((3)))


def pattern(s, aslist=False):
    """Generate a sequence of points on a regular grid.

    This function creates a sequence of points that are on a regular grid
    with unit step. These points are created from a simple string input,
    interpreting each character as a code specifying how to move from the
    last to the next point.
    The start position is always the origin (0.,0.,0.).

    Currently the following codes are defined:

    - 0 or +: goto origin (0.,0.,0.)
    - 1..8: move in the x,y plane
    - 9 or .: remain at the same place (i.e. duplicate the last point)
    - A..I: same as 1..9 plus step +1. in z-direction
    - a..i: same as 1..9 plus step -1. in z-direction
    - /: do not insert the next point

    Any other character raises an error.

    When looking at the x,y-plane with the x-axis to the right and the
    y-axis up, we have the following basic moves:
    1 = East, 2 = North, 3 = West, 4 = South, 5 = NE, 6 = NW, 7 = SW, 8 = SE.

    Adding 16 to the ordinal of the character causes an extra move of +1. in
    the z-direction. Adding 48 causes an extra move of -1. This means that
    'ABCDEFGHI', resp. 'abcdefghi', correspond with '123456789' with an extra
    z +/-= 1. This gives the following schema::

                 z+=1             z unchanged            z -= 1

             F    B    E          6    2    5         f    b    e
                  |                    |                   |
                  |                    |                   |
             C----I----A          3----9----1         c----i----a
                  |                    |                   |
                  |                    |                   |
             G    D    H          7    4    8         g    d    h

    The special character '/' can be put before any character to make the
    move without inserting the new point. The string should start
    with a '0' or '9' to include the starting point (the origin) in the output.

    Parameters
    ----------
    s: str
        A string with characters generating subsequent points.
    aslist: bool, optional
        If True, the points are returned as lists of **integer**
        coordinates instead of a :class:`Coords` object.

    Returns
    -------
    Coords | list
        The default is to return the generated points as a Coords.
        With ``aslist=True`` however, the points are returned as a list
        of tuples holding 3 integer grid coordinates.

    See Also
    --------
    xpattern: create a Coords from a pattern and group them into elements
    fpattern: create a Coords from a pattern with a grouping prefix

    Examples
    --------
    >>> pattern('0123')
    Coords([[0., 0., 0.],
            [1., 0., 0.],
            [1., 1., 0.],
            [0., 1., 0.]])
    >>> pattern('2'*4)
    Coords([[0., 1., 0.],
            [0., 2., 0.],
            [0., 3., 0.],
            [0., 4., 0.]])
    """
    x = y = z = 0
    L = []
    insert = True
    for c in s:
        if c == '/':
            insert = False
            continue
        elif c == '0' or c == '+':
            x = y = z = 0
        elif c == '.':
            pass
        else:
            j, i = divmod(ord(c), 16)
            if j == 3:
                pass
            elif j == 4:
                z += 1
            elif j == 6:
                z -= 1
            else:
                raise RuntimeError(f"Invalid character '{c}' in pattern input")
            if i == 1:
                x += 1
            elif i == 2:
                y += 1
            elif i == 3:
                x -= 1
            elif i == 4:
                y -= 1
            elif i == 5:
                x += 1
                y += 1
            elif i == 6:
                x -= 1
                y += 1
            elif i == 7:
                x -= 1
                y -= 1
            elif i == 8:
                x += 1
                y -= 1
            elif i == 9:
                pass
            else:
                raise RuntimeError(f"Unknown character '{c}' in pattern input")
        if insert:
            L.append((x, y, z))
        insert = True
    if not aslist:
        L = Coords(L)
    return L


def xpattern(s, nplex=1):
    """Create a Coords from a string pattern and group them into elements.

    Creates a sequence of points using :func:`pattern`, and groups the
    points by ``nplex`` to create a Coords with shape ``(-1,nplex,3)``.

    Parameters
    ----------
    s: str
        The string to pass to :func:`pattern` to produce the sequence
        of points.
    nplex: int
        The number of subsequent points to group together to create
        the structured Coords.

    Returns
    -------
    Coords
        A Coords with shape (-1,nplex,3).

    Raises
    ------
    ValueError
        If the number of points produced by the input string `s` is not
        a multiple of `nplex`.

    Examples
    --------
    >>> print(xpattern('.12.34',3))
    [[[0. 0. 0.]
      [1. 0. 0.]
      [1. 1. 0.]]
    <BLANKLINE>
     [[1. 1. 0.]
      [0. 1. 0.]
      [0. 0. 0.]]]
    """
    x = Coords(pattern(s))
    try:
        x = x.reshape(-1, nplex, 3)
    except Exception:
        raise ValueError(f"Can not reshape {len(x)} points to plexitude {nplex}"
                         ) from None  # avoids printing numpy exception

    return x


# re for fpattern strings
_re_fpattern = re.compile(r"(((?P<base>([0-9]+|l)):)?(?P<data>.*))")

def fpattern(s, nplex=1):
    """Create a Coords from a string pattern containing a grouping prefix.

    Create a sequence of points using :func:`pattern`, and group the
    points as described by the string prefix. The input string is of the
    form '#:pattern' where # is either a number or 'l', and pattern is a
    valid input string for :func:`pattern`.
    The pattern is used to generate a series of points on a regular grid.
    Then # prefix is then used to create point groups:

    - If # is an int, its value is the plexitude of the point groups
      to be created by :func:`xpattern`.
    - If # is an 'l' (line), a first point equal to the origin is added,
      and then plex-2 elements are created from each point to the next.
      This is an efficient way to create line elements connected into
      a polyline. In this case the
      '/' character in the pattern makes the next point not being
      connected to the previous and the point thus becomes the start of
      a new polyline. A '+' in the pattern is equivalent to '/0' and
      creates a disconnected line starting again from the origin.

    Parameters
    ----------
    s: str
        A string of the form '#:pattern' where # is either an int
        or 'l', and pattern is a valid input string for :func:`pattern`.

    Returns
    -------
    Coords
        A Coords with shape (-1,nplex,3), where nplex is # if it was an
        int, or 2 if it was an 'l'.

    Raises
    ------
    ValueError
        If the pattern is invalid, if the prefix is invalid or absent, or
        if the number of points produced by the pattern is not a multiple
        of the plexitude specified in the prefix.

    Examples
    --------
    Create six points and split them in elements per three.

    >>> print(fpattern('3:.12.34'))
    [[[0. 0. 0.]
      [1. 0. 0.]
      [1. 1. 0.]]
    <BLANKLINE>
     [[1. 1. 0.]
      [0. 1. 0.]
      [0. 0. 0.]]]
    >>> fpattern('3:012')
    Coords([[[0., 0., 0.],
             [1., 0., 0.],
             [1., 1., 0.]]])
    >>> fpattern('l:012')
    Coords([[[0., 0., 0.],
             [0., 0., 0.]],
    <BLANKLINE>
            [[0., 0., 0.],
             [1., 0., 0.]],
    <BLANKLINE>
            [[1., 0., 0.],
             [1., 1., 0.]]])
    >>> fpattern('012')
    Traceback (most recent call last):
    ...
    ValueError: Invalid or missing prefix in fpattern string
    >>> fpattern('4:012')
    Traceback (most recent call last):
    ...
    ValueError: Can not reshape 3 points to plexitude 4
    """
    d = _re_fpattern.match(s).groupdict()
    base, data = d['base'], d['data']
    if base is None:
        raise ValueError("Invalid or missing prefix in fpattern string")
    elif base == 'l':
        # The '+' must be handled differently: replace with '/0'
        data = data.replace('+', '/0')
        # The '/' must be handled differently in this case !!!
        # Remove the '/' characters, and remember their positions
        slashes = []
        while True:
            i = data.find('/')
            if i >= 0:
                slashes.append(i)
                data = data[:i] + data[i+1:]
            else:
                break
        data = Coords.concatenate([origin(), pattern(data)])
        data = np.stack([data[:-1], data[1:]], axis=1)
        if slashes:
            keep = at.complement(slashes, data.shape[0])
            data = data[keep]
        return Coords(data)
    else:
        return xpattern(data, int(base))


def align(L, align='|--', offset=(0., 0., 0.)):
    """Align a list of geometrical objects.

    Parameters
    ----------
    L: list of Coords or Geometry objects
        A list of objects that have an appropriate ``align`` method,
        like the :class:`Coords` and :class:`~geometry.Geometry`
        (and its subclasses).
    align: str
        A string of three characters, one for each coordinate direction,
        that define how the subsequent objects have to be aligned in each of
        the global axis directions:

            - '-' : align on the minimal coordinate value
            - '+' : align on the maximal coordinate value
            - '0' : align on the middle coordinate value
            - '|' : align the minimum value on the maximal value of the
                    previous item

        Thus the string ``'|--'`` will juxtapose the objects in the x-direction,
        while aligning them on their minimal coordinates in the y- and
        z- direction.
    offset: float :term:`array_like` (3,), optional
        An extra translation to be given to each subsequent object. This can
        be used to create a space between the objects, instead of
        juxtaposing them.

    Returns
    -------
    list of objects
        A list with the aligned objects.

    Notes
    -----
    See also example Align.

    See Also
    --------
    Coords.align: align a single object with respect to a point.

    """
    r = L[:1]
    al = am =''
    for i in range(3):
        if align[i] == '|':
            al += '-'
            am += '+'
        else:
            al += align[i]
            am += align[i]
    for o in L[1:]:
        r.append(o.align(al, r[-1].bboxPoint(am)+offset))
    return r


# End
