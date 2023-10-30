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

"""Using NURBS in pyFormex.

The :mod:`nurbs` module defines functions and classes to manipulate
NURBS curves and surfaces in pyFormex. The most important classes and
functions for the end user are:

- the :class:`NurbsCurve` class
- the :class:`NurbsSurface` class
- :func:`cubicInterpolate`: construct a cubic NurbsCurve through given points
- :func:`quadraticInterpolate`: construct a quadratic NurbsCurve through given points

"""

import numpy as np

from pyformex import arraytools as at
from pyformex import geomtools as gt
from pyformex import lib
from pyformex.coords import Coords
from pyformex.attributes import Attributes
from pyformex.mesh import Mesh
from pyformex.elements import Quad4
from pyformex import curve
from pyformex import utils

_py2rst_order_ = [ 'NurbsCurve', 'NurbsSurface' ]   # for docs only

###########################################################################
##
##   class Coords4
##
#########################
#
class Coords4(np.ndarray):
    """A collection of points represented by their homogeneous coordinates.

    While most of the pyFormex implementation is based on the 3D Cartesian
    coordinates class :class:`Coords`, some applications may benefit from using
    4-dimensional coordinates. The :class:`Coords4` class provides some basic
    functions, including conversion to and from cartesian coordinates.
    Through the conversion, all pyFormex functions defined on :class:`Coords`,
    such as transformations, are possible.

    :class:`Coords4` is implemented as a float type :class:`numpy.ndarray`
    whose last axis has a length equal to 4.
    Each set of 4 values (x,y,z,w) along the last axis represents a
    single point in 3D space. The cartesian coordinates of the point
    are obtained by dividing the first three values by the fourth:
    (x/w, y/w, z/w). A zero w-value represents a point at infinity.
    Converting such points to :class:`Coords` will result in Inf or NaN
    values in the resulting object.

    The float datatype is only checked at creation time. It is the
    responsibility of the user to keep this consistent throughout the
    lifetime of the object.

    Just like :class:`Coords`, the class :class:`Coords4` is derived from
    :class:`numpy.ndarray`.

    Parameters
    ----------
    data: :term:`array_like`, optional
        An array of floats, with the length of its last axis not larger
        than 4. If equal to four, each tuple along the last axis
        represents a single point in homogeneous coordinates.
        If smaller than four, the last axis is expanded to four by
        adding zero values in the second and third position and unity
        values in the last position (the w-coordinate).
        If no data are given, a single point (0.,0.,0.,1.) is created.
    w: :term:`array_like`, optional
      If specified, the w values are used to denormalize the
      homogeneous data such that the last component becomes w.
    dtyp: data-type, optional
      The datatype to be used. It not specified, the datatype of `data`
      is used, or the default :data:`Float` (which is equivalent to
      :data:`numpy.float32`).
    copy: bool, optional
      If ``True``, the data are copied. By default, the original data
      are used if possible, e.g. if a correctly shaped and typed
      :class:`numpy.ndarray` is provided.
    """

    def __new__(cls, data=None, w=None, normalize=True, dtyp=at.Float,
                copy=False):
        """Create a new instance of :class:`Coords4`."""
        if data is None:
            # create an empty array
            ar = np.ndarray((0, 4), dtype=dtyp)
        else:
            # turn the data into an array, and copy if requested
            ar = np.array(data, dtype=dtyp, copy=copy)

        if ar.shape[-1] in [3, 4]:
            pass
        elif ar.shape[-1] in [1, 2]:
            # make last axis length 3, adding 0 values
            ar = at.growAxis(ar, 3-ar.shape[-1], -1)
        elif ar.shape[-1] == 0:
            # allow empty coords objects
            ar = ar.reshape(0, 3)
        else:
            raise ValueError("Expected a length 1,2,3 or 4 for last array axis")

        # Make sure dtype is a float type
        if ar.dtype.kind != 'f':
            ar = ar.astype(at.Float)

        # We should now have a float array with last axis 3 or 4
        if ar.shape[-1] == 3:
            # Expand last axis to length 4, adding values 1
            ar = at.growAxis(ar, 1, -1, 1.0)

        if w is not None:
            if normalize:
                ar[..., :3] /= w
            else:
                # Insert weight
                ar[..., 3] = w

        # Transform 'subarr' from an ndarray to our new subclass.
        ar = ar.view(cls)

        return ar


    def normalize(self):
        """Normalize the homogeneous coordinates.

        Two sets of homogeneous coordinates that differ only by a
        multiplicative constant refer to the same points in cartesian space.
        Normalization of the coordinates is a way to make the representation
        of a single point unique. Normalization is done so that the last
        component (w) is equal to 1.

        The normalization of the coordinates is done in place.

        .. warning:: Normalizing points at infinity will result in Inf or
           NaN values.

        Examples
        --------
        >>> X4 = Coords4([2, 3, 4, 2])
        >>> X4.normalize()
        >>> X4
        Coords4([1. , 1.5, 2. , 1. ])
        """
        self /= self[..., 3:]


    def deNormalize(self, w):
        """Denormalize the homogeneous coordinates.

        This multiplies the homogeneous coordinates with the values w.
        w normally is a constant or an array with shape
        self.shape[:-1] + (1,).
        It then multiplies all 4 coordinates of a point with the same
        value, thus resulting in a denormalization while keeping the
        position of the point unchanged.

        The denormalization of the coordinates is done in place.
        If the Coords4 object was normalized, it will have precisely w as
        its 4-th coordinate value after the call.

        Examples
        --------
        >>> X4 = Coords4([1, 2, 3, 1])
        >>> X4.deNormalize(2)
        >>> X4
        Coords4([2., 4., 6., 2.])
        """
        self *= w


    def toCoords(self):
        """Convert homogeneous coordinates to cartesian coordinates.

        Returns
        -------
        A :class:`Coords` object with the cartesian coordinates
        of the points. Points at infinity (w=0) will result in
        Inf or NaN value. If there are no points at infinity, the
        resulting :class:`Coords` point set is equivalent to the
        :class:`Coords4` input.

        Examples
        --------
        >>> Coords4([2, 3, 4, 2]).toCoords()
        Coords([1. , 1.5, 2. ])
        """
        return Coords(self[..., :3] / self[..., 3:])


    def npoints(self):
        """Return the total number of points in the Coords4."""
        return np.asarray(self.shape[:-1]).prod()


    ncoords = npoints


    def x(self):
        """Return the x-plane"""
        return self[..., 0]

    def y(self):
        """Return the y-plane"""
        return self[..., 1]

    def z(self):
        """Return the z-plane"""
        return self[..., 2]

    def w(self):
        """Return the w-plane"""
        return self[..., 3]


    def bbox(self):
        """Return the bounding box of a set of points.

        Returns the bounding box of the cartesian coordinates of
        the object.
        """
        return self.toCoords().bbox()


    def actor(self, **kargs):
        """Graphical representation"""
        return self.toCoords().actor(**kargs)


class Geometry4():
    """This is a preliminary class intended to provide some transforms in 4D

    """
    def __init__(self):
        """Initialize a Geometry4"""
        self.attrib = Attributes()

    def scale(self, *args, **kargs):
        self.coords4[..., :3] = Coords(self.coords4[..., :3]).scale(*args, **kargs)
        return self


class KnotVector():
    """A knot vector.

    A knot vector is sequence of float values sorted in ascending order.
    Values can occur multiple times. In the typical use case (NURBS) most
    values do indeed occur multiple times, and the
    multiplicity of the values is an important quantity.
    Therefore, the knot vector is stored in two arrays of the same length:
    val and mul.

    Attributes
    ----------
    val: float array (nval)
        The unique float values, in a strictly ascending sequence.
    mul: int array (nval)
        The multiplicity of each of the values in val.

    See Also
    --------
    genKnotVector: generate a knot vector for a NURBS curve

    Examples
    --------
    >>> K = KnotVector([0.,0.,0.,0.5,0.5,1.,1.,1.])
    >>> print(K.val)
    [0.  0.5 1. ]
    >>> print(K.mul)
    [3 2 3]
    >>> print(K)
    KnotVector(8): 0*3, 0.5*2, 1*3
    >>> print([(v,m) for v,m in zip(K.val,K.mul)])
    [(0.0, 3), (0.5, 2), (1.0, 3)]
    >>> print(K.values())
    [0.  0.  0.  0.5 0.5 1.  1.  1. ]
    >>> print(K.nknots)
    8
    >>> K.index(0.5)
    1
    >>> K.span(1.0)
    5
    >>> K.mult(0.5)
    2
    >>> K.mult(0.7)
    0
    >>> K[4],K[-1]
    (0.5, 1.0)
    >>> K[4:6]
    array([0.5, 1. ])

    """
    # This makes the KnotVector string format customizable.
    # The {v} field formats the value, {m} the multiplicity of the knot.
    _knot_format = "{v:.6g}*{m}"

    def __init__(self, data=None, val=None, mul=None):
        """Initialize a KnotVector"""
        if data is not None:
            data = at.checkArray(data, (-1,), 'f', 'i')
            val, inv = np.unique(data, return_inverse=True)
            mul, bins = at.multiplicity(inv)
        else:
            val = at.checkArray(val, (-1,), 'f', 'i')
            mul = at.checkArray(mul, val.shape, 'i')
        self.val = val.astype(np.float32)
        self.mul = mul
        self.csum = self.mul.cumsum() - 1


    @property
    def nknots(self):
        """Return the total number of knots"""
        return self.mul.sum()


#    def knots(self):
#        """Return the knots as tuples (value,multiplicity)"""
#        return zip(self.val,self.mul)


    def values(self):
        """Return the full list of knot values"""
        return np.concatenate([[v]*m for v, m in zip(self.val, self.mul)])


    def __str__(self):
        """Format the knot vector as a string."""
        return f"KnotVector({self.nknots}): " + ", ".join([
            KnotVector._knot_format.format(v=v, m=m)
            for v, m in zip(self.val, self.mul)])


    def index(self, u):
        """Find the index of knot value u.

        If the value does not exist, a ValueError is raised.
        """
        w = np.where(np.isclose(self.val, u))[0]
        if len(w) <= 0:
            raise ValueError(
                f"The value {u} does not appear in the KnotVector")
        return w[0]


    def vindex(self, j):
        """Find the index of knot value with index j.

        j should be in the range(0,self.nknots), else a ValueError is raised.
        This is equivalent to (but more efficient than)::

            self.index(self[j])
        """
        if j not in range(0, self.nknots):
            raise ValueError("j outside range(0, self.nknots)")
        return self.csum.searchsorted(j)


    def mult(self, u):
        """Return the multiplicity of knot value u.

        Returns
        -------
        int
            The multiplicity of the knot value u, or 0 if u is not in the
            KnotVector.
        """
        try:
            i = self.index(u)
            return self.mul[i]
        except Exception:
            return 0


    def span(self, u):
        """Find the (first) index of knot value u in the full knot values vector.

        If the value does not exist, a ValueError is raised.
        """
        i = self.index(u)
        return self.mul[:i].sum()


    def __getitem__(self, i):
        """Return knot i.

        Returns the knot with the index i, taking into account
        the multiplicity of the knots.
        """
        if isinstance(i, slice):
            i = np.arange(i.start, i.stop, i.step)
        i %= self.nknots
        ind = self.csum.searchsorted(i)
        return self.val[ind]


    def copy(self):
        """Return a copy of the KnotVector.

        Changing the copy will not change the original.
        """
        return KnotVector(val=self.val, mul=self.mul)


    def reverse(self):
        """Return the reverse knot vector.

        Examples
        --------
        >>> print(KnotVector([0,0,0,1,3,6,6,8,8,8]).reverse().values())
        [0. 0. 0. 2. 2. 5. 7. 8. 8. 8.]

        """
        val = self.val.min() + self.val.max() - self.val
        return KnotVector(val=val[::-1], mul=self.mul[::-1])



def genKnotVector(nctrl, degree, blended=True, closed=False):
    """Compute a sensible knot vector for a Nurbs curve.

    A knot vector is a sequence of non-decreasing parametric values. These
    values define the `knots`, i.e. the points where the analytical expression
    of the Nurbs curve may change. The knot values are only meaningful upon a
    multiplicative constant, and they are usually normalized to the range
    [0.0..1.0].

    A Nurbs curve with ``nctrl`` points and of given ``degree`` needs a knot
    vector with ``nknots = nctrl+degree+1`` values. A ``degree`` curve needs
    at least ``nctrl = degree+1`` control points, and thus at least
    ``nknots = 2*(degree+1)`` knot values.

    By default, the returned knot vector will produce a blended, clamped,
    open curve. A blended curve uses overlapping basis functions spanning
    multiple intervals of the knot vector. This gives the highest smoothness.
    An unblended (or decomposed) curve is like a chain of separate curves,
    each formed on a sequence of ``degree+1`` control points.

    A clamped (open) curve starts and ends exactly at the first and last
    control points. Unclamped curves are deprecated and therefore genKnotVector
    only produces knot vectors for clamped curves. To achieve this, the
    knot vector should have multiplicity ``degree+1`` for its end values.

    Thus, for an open blended curve, the policy is to set the knot values
    at the ends to 0.0, resp. 1.0, both with multiplicity ``degree+1``,
    and to spread the remaining ``nctrl-degree-1`` values equally over
    the interval.

    For an open unblended curve, all internal knots get multiplicity ``degree``.
    This results in a curve that is only one time continuously derivable at
    the knots, thus the curve is smooth between the knots, but can have crusts
    at the knots. There is an extra requirement in this case: ``nctrl`` should
    be a multiple  of ``degree`` plus 1.

    For a closed curve, we currently only produce blended curves. The knots are
    equally spread over the interval, all having a multiplicity 1 for maximum
    continuity of the curve.

    Parameters
    ----------
    nctrl: int
        The number of control points. This should be higher than the degree
        of the curve.
    degree: int
        The intended degree of the curve. Should be smaller than nctrl.

    Returns
    -------
    :class:`KnotVector`
        A KnotVector to create a NurbsCurve with the specified degree and
        number of control points.

    Examples
    --------
    >>> nctrl = 5
    >>> for i in range(1, nctrl): print(genKnotVector(nctrl, i))
    KnotVector(7): 0*2, 0.25*1, 0.5*1, 0.75*1, 1*2
    KnotVector(8): 0*3, 0.333333*1, 0.666667*1, 1*3
    KnotVector(9): 0*4, 0.5*1, 1*4
    KnotVector(10): 0*5, 1*5
    >>> print(genKnotVector(7,3))
    KnotVector(11): 0*4, 0.25*1, 0.5*1, 0.75*1, 1*4
    >>> print(genKnotVector(7,3,blended=False))
    KnotVector(11): 0*4, 1*3, 2*4
    >>> print(genKnotVector(3,2,closed=True))
    KnotVector(6): 0*1, 0.2*1, 0.4*1, 0.6*1, 0.8*1, 1*1
    """
    if degree >= nctrl:
        raise ValueError(
            f"Degree ({degree}) should be smaller than nctrl ({nctrl})")
    nknots = nctrl + degree + 1
    if closed or blended:
        nval = nknots
        if not closed:
            nval -= 2*degree
        val = at.uniformParamValues(nval-1)  # Returns nval values!
        mul = np.ones(nval, dtype=at.Int)
        if not closed:
            mul[0] = mul[-1] = degree+1
    else:
        nparts = (nctrl-1) // degree
        if nparts*degree+1 != nctrl:
            raise ValueError(
                "Discrete knot vectors can only be used if the number of "
                "control points is a multiple of the degree, plus one.")
        val = np.arange(nparts+1).astype(at.Float)
        mul = np.ones(nparts+1, dtype=at.Int) * degree
        mul[0] = mul[-1] = degree+1

    return KnotVector(val=val, mul=mul)


@utils.pzf_register
class NurbsCurve(Geometry4):
    """A NURBS curve.

    This class can represent a NURBS curve as well as its special case of a
    non-rational (or simple) B-spline curve. The difference sits only in the
    weights attributed to the control points: if they are constant, the
    interpolation functions are simple polynoms and the curve is a B-spline.
    If variable weights are attributed, the curve becomes a more general
    Non-Uniform Rational B-Spline or NURBS.

    A B-spline is defined by `nctrl` control points, a `degree` (>=1) and a
    sequence of `nknots = nctrl+degree+1` parametric values called
    `knots`. The knots divide the curve in parametric regions where the
    mathematical representation of the curve is constant.
    They form a non-descending sequence , but values may be repeated
    to model appropriate discontinuities. Given a set of control points and
    a knot vector, the degree of the curve is obviously
    `degree = nknots-nctrl-1`. In literature often the `order` of a NURBS
    is used. This is just `order = degree+1 = nknots-nctrl`. The order is
    also the minimum number of control points.

    To model a NURBS curve, we add a weight wi to each control point and use
    4-dimensional coordinates (xi*wi, yi*wi, zi*wi, wi) for each point i.
    Internally, the NurbsCurve class uses 4-dim points, with default weights
    set to 1. Before returning, the coordinates are divided
    At the endInput and output are always 3-dimensional points.

    Parameters
    ----------
    control: Coords-like (nctrl,3)
        The vertices of the control polygon.
    degree: int
        The degree of the Nurbs curve. If not specified, it is
        derived from the length of the knot vector (`knots`).
    wts: float array (nctrl)
        Weights to be attributed to the control
        points. Default is to attribute a weight 1.0 to all points. Using
        different weights allows for more versatile modeling (like perfect
        circles and arcs.)
    knots: KnotVector | list of floats
        The nknots knot values to be used. If a list, the values should be
        in ascending order. Identical values have to be repeated to
        their multiplicity.
        The values are only defined upon a multiplicative constant and will
        be normalized to set the last value to 1.
        If `degree` is specified, default values are constructed automatically
        by calling :func:`genKnotVector`.
        If no knots are given and no degree is specified, the degree is set to
        the nctrl-1 if the curve is blended. If not blended, the degree is not
        set larger than 3.
    closed: bool, optional
        Determines whether the curve is closed. Default is False.
        The functionality of closed NurbsCurves is currently limited.
    blended: bool, optional
        Determines that the curve is blended. Default is True.
        Set blended==False to define a nonblended curve.
        A nonblended curve is a chain of independent curves, Bezier
        curves if the weights are all ones. See also :meth:`decompose`.
        The number of control points should be a multiple of the degree,
        plus one. This parameter is only used if no knots are specified.

    """

    N_approx = 100
    #
    #    order (2,3,4,...) = degree+1 = min. number of control points
    #    ncontrol >= order
    #    nknots = order + ncontrol >= 2*order
    #
    #    convenient solutions:
    #    OPEN:
    #      nparts = (ncontrol-1) // degree
    #      nintern =
    #

    def __init__(self, control, degree=None, wts=None, knots=None,
                 blended=True, closed=False, wrap=True, norm_urange=True):
        Geometry4.__init__(self)
        #self.closed = closed
        nctrl = len(control)
        if knots is not None:
            if not isinstance(knots, KnotVector):
                knots = KnotVector(knots)
            nknots = knots.nknots

        if degree is None:
            if knots is None:
                degree = nctrl-1
                if not blended:
                    degree = min(degree, 3)
            else:
                if closed:
                    degree = nknots - nctrl - 1
                    if wrap:
                        if degree % 2 != 0:
                            raise ValueError("nknots - nctrl should be odd")
                        degree = degree // 2
                else:
                    degree = nknots - nctrl - 1
                    if degree <= 0:
                        raise ValueError(
                            f"Length of knot vector ({nknots}) must be at least"
                            f"number of control points ({nctrl}) plus 2")

        order = degree + 1
        control = Coords4(control)
        if wts is not None:
            wts = np.asarray(wts).ravel()
            control.deNormalize(wts.reshape(wts.shape[-1], 1))

        if closed and wrap:
            # We need to wrap nwrap control points
            nwrap = degree
            control = Coords4(np.concatenate([control, control[:nwrap]], axis=0))

        nctrl = control.shape[0]

        if nctrl < order:
            raise ValueError(f"For a degree {degree} curve you need "
                             f"at least {order} points, got only {nctrl}")

        if knots is None:
            knots = genKnotVector(nctrl, degree, blended=blended, closed=closed)
            nknots = knots.nknots

        if nknots != nctrl + order:
            raise ValueError(
                f"Length of knot vector ({nknots}) must be equal to number "
                f"of control points ({nctrl}) plus order ({order})")

        self.ctrl = control
        self.knotu = knots
        self.degree = degree
        self.closed = closed

        if norm_urange:
            umin, umax = self.urange()
            self.knotu.val -= umin
            self.knotu.val /= (umax-umin)


    @property
    def coords4(self):
        """The 4-dim coordinates"""
        return self.ctrl

    @property
    def coords(self):
        """The 3-dim coordinates"""
        return self.ctrl.toCoords()


    @property
    def knots(self):
        """Return the full list of knot values"""
        return self.knotu.values()

    @property
    def nctrl(self):
        """The number of control points"""
        return self.ctrl.shape[0]

    @property
    def nknots(self):
        """The number of knots"""
        return self.knotu.nknots

    @property
    def order(self):
        """The order of the Nurbs curve = nknots - nctrl = degree + 1"""
        return self.nknots - self.nctrl

    # @property
    # def degree(self):
    #     """The degree of the Nurbs curve = order + 1"""
    #     return self.order + 1

    def urange(self):
        """Return the parameter range on which the curve is defined.

        Returns a (2,) float array with the minimum and maximum parameter
        value for which the curve is defined.
        """
        p = self.degree
        # This is important for closed curves!
        return [self.knotu[p], self.knotu[-1-p]]
        #return self.knotu[0], self.knotu[-1]


    def isClamped(self):
        """Return True if the NurbsCurve uses a clamped knot vector.

        A clamped knot vector has a multiplicity p+1 for the first and
        last knot. All our generated knot vectors are clamped.
        """
        return self.knotu.mul[0] == self.knotu.mul[-1] == (self.degree + 1)


    def isUniform(self):
        """Return True if the NurbsCurve has a uniform knot vector.

        A uniform knot vector has a constant spacing between the knot values.
        """
        d = self.knotu.val[1:] - self.knotu.val[:-1]
        return np.isclose(d[1:], d[0]).all()


    def isRational(self):
        """Return True if the NurbsCurve is rational.

        The curve is rational if the weights are not constant.
        The curve is polynomial if the weights are constant.

        Returns True for a rational curve, False for a polynomial curve.
        """
        w = self.ctrl[:, 3]
        return not np.isclose(w[1:], w[0]).all()


    def isBlended(self):
        """Return True if the NurbsCurve is blended.

        An clamped NurbsCurve is unblended (or decomposed) if it consists
        of a chain of independent Bezier curves.
        Such a curve has multiplicity p for all internal knots and p+1
        for the end knots of an open curve.
        Any other NurbsCurve is blended.

        Returns True for a blended curve, False for an unblended one.

        Note: for testing whether an unclamped curve is blended or not,
        first clamp it.
        """
        return self.isClamped() and (self.knotu.mul[1:-1] == self.degree).all()


    def bbox(self):
        """Return the bounding box of the NURBS curve.

        """
        return self.ctrl.toCoords().bbox()


    def __str__(self):
        return (f"NURBS Curve, degree = {self.degree}, "
                f"nctrl = {len(self.ctrl)}, "
                f"nknots = {self.nknots}\n  "
                f"closed: {self.closed}; "
                f"clamped: {self.isClamped()}; "
                f"uniform: {self.isUniform()}; "
                f"rational: {self.isRational()}\n  "
                f"Control points:\n{self.ctrl}\n  "
                f"{self.knotu}\n  "
                f"urange: {self.urange()}")


    def copy(self):
        """Return a (deep) copy of self.

        Changing the copy will not change the original.
        """
        return NurbsCurve(control=self.ctrl.copy(), degree=self.degree,
                          knots=self.knotu.copy(), closed=self.closed)


    def pointsAt(self, u):
        """Return the points on the Nurbs curve at given parametric values.

        Parameters
        ----------
        u: float :term:`array_like` (nu,)
            The parametric values at which a point is to be placed.
            Note that valid points are only obtained for parameter values
            in the :meth:`range`.

        Returns
        -------
        Coords (nu, 3)
            The coordinates of nu points on the curve, at the specified
            parametric values.

        Examples
        --------
        >>> N = NurbsCurve(control=Coords('0121'), degree=3)
        >>> N.pointsAt([0.0, 0.5, 1.0])
        Coords([[0. , 0. , 0. ],
                [1. , 0.5, 0. ],
                [2. , 1. , 0. ]])
        >>> N.pointsAt(0.5)
        Coords([[1. , 0.5, 0. ]])
        """
        ctrl = self.ctrl.astype(np.double)
        knots = self.knots.astype(np.double)
        u = np.atleast_1d(u).astype(np.double)
        pts = lib.nurbs.curvePoints(ctrl, knots, u)
        if np.isnan(pts).any():
            print("We got a NaN")
            print('ctrl',ctrl)
            print('knots',knots)
            print('u',u)
            raise RuntimeError("Some error occurred during the evaluation "
                               "of the Nurbs curve")
        if pts.shape[-1] == 4:
            pts = Coords4(pts).toCoords()
        else:
            pts = Coords(pts)
        return pts


    def __call__(self, u):
        """Return the points on the Nurbs curve at given parametric values.

        This is like :meth:`pointsAt` but providing a scalar value returns
        a (3,) Coords array.

        Examples
        --------
        >>> N = NurbsCurve(control=Coords('0121'), degree=3)
        >>> N([0.0, 0.5, 1.0])
        Coords([[0. , 0. , 0. ],
                [1. , 0.5, 0. ],
                [2. , 1. , 0. ]])
        >>> N(0.5)
        Coords([1. , 0.5, 0. ])
        """
        P = self.pointsAt(u)
        if np.array(u).ndim == 0:
            P = P[0]
        return P

    def derivs(self, u, d=1):
        """Returns the points and derivatives up to d at parameter values u

        Parameters
        ----------
        u: float :term:`array_like` | int
            If a float array (nu,), these are the parameter values at
            which to compute points and derivatives.

            If an int, specifies the number of parameter values (nu)
            at which to evaluate the points and derivatives of the curve.
            The points are equally spaced in parameter space.

        d: int
            The highest derivative to compute.

        Returns
        -------
        float array (d+1,nu,3)
            The coordinates of the points and the derivates up to the
            order d at those points.

        Examples
        --------
        >>> N = NurbsCurve(control=Coords('0121'), degree=3)
        >>> N.derivs([0.0, 0.5, 1.0], 2)
        Coords([[[ 0. ,  0. ,  0. ],
                 [ 1. ,  0.5,  0. ],
                 [ 2. ,  1. ,  0. ]],
        <BLANKLINE>
                [[ 3. ,  0. ,  0. ],
                 [ 1.5,  1.5,  0. ],
                 [ 3. ,  0. ,  0. ]],
        <BLANKLINE>
                [[-6. ,  6. ,  0. ],
                 [ 0. ,  0. ,  0. ],
                 [ 6. , -6. ,  0. ]]])
        """
        if at.isInt(u):
            u = at.uniformParamValues(u, self.knotu.val[0], self.knotu.val[-1])
        else:
            u = at.checkArray(u, (-1,), 'f', 'i')

        # sanitize arguments for library call
        ctrl = self.ctrl.astype(np.double)
        knots = self.knots.astype(np.double)
        u = np.atleast_1d(u).astype(np.double)
        d = int(d)

        try:
            pts = lib.nurbs.curveDerivs(ctrl, knots, u, d)
            if np.isnan(pts).any():
                print("We got a NaN")
                print(pts)
                raise RuntimeError
        except Exception:
            raise RuntimeError("Some error occurred during the evaluation "
                               "of the Nurbs curve")

        if pts.shape[-1] == 4:
            pts = Coords4(pts)
            # When using no weights, ctrl points are Coords4 normalized points,
            # and the derivatives all have w=0: the points represent directions
            # We just strip off the w=0.
            # HOWEVER, if there are weights, not sure what to do.
            # Points themselves could be just normalized and returned.
            pts[0].normalize()
            pts = Coords(pts[..., :3])
        else:
            pts = Coords(pts)
        return pts


    def frenet(self, u):
        """Compute Frenet vectors, curvature and torsion at parameter values u

        Parameters
        ----------
        u: float :term:`array_like` | int
            If a float array (nu,), these are the parameter values at
            which to compute points and derivatives.

            If an int, specifies the number of parameter values (nu)
            at which to evaluate the points and derivatives of the curve.
            The points are equally spaced in parameter space.

        Returns
        -------
        T: float array(nu,3)
            Normalized tangent vectors (nu,3) at nu points.
        N: float array(nu,3)
            Normalized normal vectors (nu,3) at nu points.
        B: float array(nu,3)
            Normalized binormal vectors (nu,3) at nu points.
        k: float array(nu,3)
            Curvature of the curve (nu) at nu points.
        t: float array(nu,3)
            Torsion of the curve (nu) at nu points.
        """
        derivs = self.derivs(u, 3)
        return frenet(derivs[1], derivs[2], derivs[3])


    def curvature(self, u, torsion=False):
        """Compute curvature and torsion at parameter values u

        This is like :meth:`frenet` but only returns the curvature
        and optionally the torsion.
        """
        T, N, B, k, t = self.frenet(u)
        if torsion:
            return k, t
        else:
            return k


    def knotPoints(self, multiple=False):
        """Returns the points on the curve at the knot values.

        If multiple is True, points are returned with their multiplicity.
        The default is to return the points just once.

        Examples
        --------
        >>> N = NurbsCurve(Coords('012141'), degree=3)
        >>> print(N.knotu)
        KnotVector(10): 0*4, 0.333333*1, 0.666667*1, 1*4
        >>> N.knotPoints()
        Coords([[0.    , 0.    , 0.    ],
                [1.1667, 0.75  , 0.    ],
                [1.8333, 0.75  , 0.    ],
                [3.    , 0.    , 0.    ]])
        """
        if self.closed:
            p = self.degree
            val = np.unique(self.knots[p:-1-p])
        else:
            if multiple:
                val = self.knots
            else:
                val = self.knotu.val
        return self.pointsAt(val)


    def insertKnots(self, u):
        """Insert knots in the Nurbs curve.

        Parameters
        ----------
        u: float :term:`array_like` (nu,)
            A list of parameter values to be inserted into the
            curve's knot vector. The control points are adapted to keep
            the curve unchanged.

        Returns
        -------
        NurbsCurve
            A new curve equivalent with the original but with the specified
            knot values inserted in the knot vector, and the control
            points adapted.
        """
        if self.closed:
            raise ValueError("insertKnots currently does not work on "
                             "closed curves")
        # sanitize arguments for library call
        ctrl = self.ctrl.astype(np.double)
        knots = self.knots.astype(np.double)
        u = np.asarray(u).astype(np.double)
        umin, umax = self.urange()
        if (u < umin).any() or (u > umax).any():
            raise ValueError(
                f"All u values should be in the range {self.urange()}")
        newP, newU = lib.nurbs.curveKnotRefine(ctrl, knots, u)
        return NurbsCurve(newP, degree=self.degree, knots=newU,
                          closed=self.closed)


    def requireKnots(self, val, mul):
        """Insert knots until the required multiplicity is reached.

        Inserts knot values only if they are currently not there or their
        multiplicity is lower than the required one.

        Parameters
        ----------
        val: float :term:`array_like` (nval,)
            The list of knot values required in the knot vector.
        mul: int :term:`array_like` (nval,)
            The list of multiplicities required for the knot values.

        Returns
        -------
        NurbsCurve
            A curve equivalent with the original but where the knot vector
            is guaranteed to contain the values in `val` with at least the
            corresponding multiplicity in `mul`.
            If all requirements were already fulfilled at the beginning,
            returns self.
        """
        # get actual multiplicities
        m = np.array([self.knotu.mult(ui) for ui in val])
        # compute missing multiplicities
        mul = mul - m
        if (mul > 0).any():
            # list of knots to insert
            u = [[ui]*mi for ui, mi in zip(val, mul) if mi > 0]
            return self.insertKnots(np.concatenate(u))
        else:
            return self


    def removeKnot(self, u, m, tol=1.e-5):
        """Remove a knot from the knot vector of the Nurbs curve.

        Parameters
        ----------
        u: float
            The knot value to remove.
        m: int
            How many times to remove the knot `u`. If negative,
            remove maximally.
        tol: float
            Acceptable error (distance between old and new curve).

        Returns
        -------
        NurbsCurve
            A Nurbs curve equivalent (to the specified tolerance) with the
            original but with a knot vector where the value `u` has been
            removed `m` times, if possible, or else as many times as possible.
            The control points are adapted accordingly.
            Returns self if no value was removed.

        Notes
        -----
        removeKnot currently only works on open curves
        """
        if self.closed:
            raise ValueError("removeKnots currently does not work on "
                             "closed curves")

        i = self.knotu.index(u)

        if m < 0:
            m = self.knotu.mul[i]

        P = self.ctrl.astype(np.double)
        Uv = self.knotu.val.astype(np.double)
        Um = self.knotu.mul.astype(at.Int)
        t, newP, newU = lib.nurbs.curveKnotRemove(P, Uv, Um, i, m, tol)

        if t > 0:
            print(f"Removed the knot value {u} {t} times")
            return NurbsCurve(newP, degree=self.degree, knots=newU,
                              closed=self.closed)
        else:
            print(f"Can not remove the knot value {u}")
            return self


    def removeAllKnots(self, tol=1.e-5):
        """Remove all removable knots.

        Parameters
        ----------
        tol: float
            Acceptable error (distance between old and new curve).

        Returns
        -------
        NurbsCurve
            An equivalent (if tol is small) NurbsCurve with all
            extraneous knots removed.

        Notes
        -----
        :meth:`removeAllKnots` and :meth:`blend` are aliases.
        """
        N = self
        print(N)
        while True:
            print(N)
            for u in N.knotu.val:
                print(f"Removing {u}")
                NN = N.removeKnot(u, m=-1, tol=tol)
                if NN is N:
                    print("Can not remove")
                    continue
                else:
                    break
            if NN is N:
                print("Done")
                break
            else:
                print("Cycle")
                N = NN
        return N

    blend = removeAllKnots


    def decompose(self):
        """Decompose a curve in subsequent Bezier curves.

        Returns
        -------
        NurbsCurve
            An equivalent unblended NurbsCurve.

        See also
        --------
        toCurve: convert the NurbsCurve to a BezierSpline or PolyLine

        Notes
        -----
        :meth:`decompose` and :meth:`unblend` are aliases.
        """
        # sanitize arguments for library call
        ctrl = self.ctrl
        knots = self.knots.astype(np.double)
        X = lib.nurbs.curveDecompose(ctrl, knots)
        return NurbsCurve(X, degree=self.degree, blended=False)

    # For compatibility
    unblend = decompose


    def subCurve(self, u1, u2):
        """Extract the subcurve between parameter values u1 and u2

        Parameters
        ----------
        u1: float
            Parametric value of the start of the subcurve to extract.
            The value should be in :meth:`urange`.
        u2: float
            Parametric value of the end of the subcurve to extract.
            The value should be in :meth:`urange` and > `u1`.

        Returns
        -------
        NurbsCurve
            A NurbsCurve containing only the part between u1 and u2 of
            the original.
        """
        p = self.degree
        # Make sure we have the knots
        N = self.requireKnots([u1, u2], [p+1, p+1])
        j1 = N.knotu.index(u1)
        j2 = N.knotu.index(u2)
        knots = KnotVector(val=N.knotu.val[j1:j2+1], mul=N.knotu.mul[j1:j2+1])
        k1 = N.knotu.span(u1)
        nctrl = knots.nknots - p - 1
        ctrl = N.coords[k1:k1+nctrl]
        return NurbsCurve(control=ctrl, degree=p, knots=knots,
                          closed=self.closed)


    def clamp(self):
        """Clamp the knot vector of the curve.

        A clamped knot vector starts and ends with multiplicities p-1.
        See also :meth:`isClamped`.

        Returns
        -------
        NurbsCurve
           An equivalent curve with clamped knot vector, or self if the
           curve was already clamped.

        Notes
        -----
        The use of unclamped knot vectors is deprecated.
        This method is provided only as a convenient method to import
        curves from legacy systems using unclamped knot vectors.
        """
        if self.isClamped():
            return self
        else:
            p = self.degree
            u1, u2 = self.knotu.val[[p, -1-p]]
            return self.subCurve(u1, u2)


    def unclamp(self):
        """Unclamp the knot vector of the curve.

        Warning
        -------
        The use of unclamped knot vectors is deprecated.

        Returns
        -------
        NurbsCurve
           An equivalent curve with unclamped knot vector, or self if the
           curve was already unclamped.
        """
        if self.isClamped():
            from pyformex.lib.nurbs_e import curveUnclamp
            P, U = curveUnclamp(self.ctrl, self.knots)
            return NurbsCurve(control=P, degree=self.degree, knots=U,
                              closed=self.closed)
        else:
            return self


    def toCurve(self, force_Bezier=False):
        """Convert a (nonrational) NurbsCurve to a BezierSpline or PolyLine.

        This decomposes the curve in a chain of Bezier curves and converts
        the chain to a BezierSpline or PolyLine.

        This only works for nonrational NurbsCurves, as the
        BezierSpline and PolyLine classes do not allow homogeneous
        coordinates required for rational curves.

        Returns
        -------
        BezierSpline | PolyLine
            A BezierSpline (or PolyLine if degree is 1) that is equivalent
            with the NurbsCurve.

        See also
        --------
        unblend: decompose both rational and nonrational NurbsCurves

        """
        if self.isRational():
            raise ValueError("Can not convert a rational NURBS to BezierSpline")

        ctrl = self.ctrl
        knots = self.knots
        X = lib.nurbs.curveDecompose(ctrl, knots)
        X = Coords4(X).toCoords()
        if self.degree > 1 or force_Bezier:
            return curve.BezierSpline(control=X, degree=self.degree,
                                      closed=self.closed)
        else:
            return curve.PolyLine(X, closed=self.closed)


    def toBezier(self):
        """Convert a (nonrational) NurbsCurve to a BezierSpline.

        This is equivalent with toCurve(force_Bezier=True) and returns
        a BezierSpline in all cases.
        """
        return self.toCurve(force_Bezier=True)


    def elevateDegree(self, t=1):
        """Elevate the degree of the Nurbs curve.

        Parameters
        ----------
        t: int
            How much to elevate the degree of the curve

        Returns
        -------
        NurbsCurve
            A NurbsCurve equivalent with the original but of a higher degree.
        """
        if self.closed:
            raise ValueError("elevateDegree currently does not work on "
                             "closed curves")
        P = self.ctrl.astype(np.double)
        U = self.knotus.astype(np.double)
        newP, newU = lib.nurbs.curveDegreeElevate(P, U, t)
        return NurbsCurve(newP, degree=self.degree+t, knots=newU,
                          closed=self.closed)


    def reduceDegree(self, t=1, tol=np.inf):
        """Reduce the degree of the Nurbs curve.

        Parameters
        ----------
        t: int
            How much to reduce the degree (max. = degree-1)

        Returns
        -------
        NurbsCurve
            A NurbsCurve approximating the original but of a lower degree.
        """
        if self.closed:
            raise ValueError("reduceDegree currently does not work on "
                             "closed curves")

        if t >= self.degree:
            raise ValueError(
                f"This curve can maximally be reduced {self.degree-1} times")

        N = self
        while t > 0:
            from pyformex.lib import nurbs_e
            #newP, newU, maxerr = lib.nurbs.curveDegreeReduce(N.coords, N.knots)
            newP, newU, maxerr = nurbs_e.curveDegreeReduce(N.coords, N.knots, tol=tol)
            print(f"MAXERR = {maxerr}")
            N = NurbsCurve(newP, degree=self.degree-1, knots=newU,
                           closed=self.closed)
            t -= 1

        return N


    # TODO: This should be implemented in C for efficiency
    def projectPoint(self, P, *, u0=None, nseed=20,
                     eps1=1.e-5, eps2=1.e-5, maxit=50):
        """Project a given point on the Nurbs curve.

        This can also be used to determine the parameter value of a point
        lying on the curve.

        Parameters
        ----------
        P: :term:`coords_like` (3,)
            A set of npts points in space.
        u0: float, optional
            Start value for the parameter of the projected point. Providing
            a value close to the correct foot point will speed up the operation.
            If not provided, a number of values is tried and the one giving
            the closest point to P is chosen. See ``nseed``.
        nseed: int
            Number of intervals to divide the parameter range into for guessing
            a suitable initial value ``u0``. Only used if ``u0`` is not
            provided.

        Returns
        -------
        u: float
            Parameter value of the base point X of the projection
            of P on the NurbsCurve.
        P: Coords (3,)
            The coordinates of the base point of the projection of P
            on the NurbsCurve.
        d: float
            The distance of the point P from the NurbsCurve

        Notes
        -----
        Based on section 6.1 of The NurbsBook.
        """
        P = at.checkArray(P, (3,), 'f', 'i')
        umin, umax = self.knotu.val[[0, -1]]
        if u0 is None:
            # Determine start value from best match of nseed+1 points
            u = at.uniformParamValues(nseed+1, umin, umax)
            pts = self.pointsAt(u)
            d = pts.distanceFromPoint(P)
            i = d.argmin()
            u0, P0, d0 = u[i], pts[i], d[i]
            del pts
            del d
        else:
            P0 = self(u0)
            d0 = at.length(P-P0)

        if d0 == 0.:
            # Trivial case: the point is on the curve
            return u0, P0, d0

        # Apply Newton's method to minimize distance
        i = 0
        ui = u0
        while i < maxit:
            i += 1
            C = self.derivs([ui], 2)
            C0, C1, C2 = C[:, 0]
            CP = (C0-P)
            CPxCP = np.dot(CP, CP)
            C1xCP = np.dot(C1, CP)
            C1xC1 = np.dot(C1, C1)
            eps1sq = eps1*eps1
            eps2sq = eps2*eps2
            # Check convergence
            chk1 = CPxCP <= eps1sq
            if C1xC1 == 0. or CPxCP == 0.:
                chk2 = False
            else:
                chk2 = C1xCP / C1xC1 / CPxCP <= eps2sq

            uj = ui - np.dot(C1, CP) / (np.dot(C2, CP) + np.dot(C1, C1))
            # ensure that parameter stays in range
            if self.closed:
                while uj < umin:
                    uj += umax - umin
                while uj > umax:
                    uj -= umax - umin
            else:
                if uj < umin:
                    uj = umin
                if uj > umax:
                    uj = umax

            # Check convergence
            chk4 = (uj-ui)**2 * C1xC1 <= eps1sq
            P0 = self.pointsAt([uj])[0]

            if (chk1 or chk2) and chk4:
                # Converged!
                break
            else:
                # Prepare for next it
                ui = uj

        if i == maxit:
            print(f"Convergence not reached after {maxit} iterations")

        return u0, P0, at.length(P-P0)


    def projectPoints(self, P, **kargs):
        """Project multiple points"""
        return Coords.concatenate([self.projectPoint(Pi, **kargs)[1]
                                   for Pi in P])


    def distancePoints(self, P, **kargs):
        """Compute the distance of points P to the NurbsCurve"""
        return Coords.concatenate([self.projectPoint(Pi, **kargs)[2]
                                   for Pi in P])
        # return at.length(self.projectPoints(self, P, **kargs) - P)


    def approx(self, ndiv=None, nseg=None, **kargs):
        """Return a PolyLine approximation of the Nurbs curve

        If no `nseg` is given, the curve is approximated by a PolyLine
        through equidistant `ndiv+1` point in parameter space. These points
        may be far from equidistant in Cartesian space.

        If `nseg` is given, a second approximation is computed with `nseg`
        straight segments of nearly equal length. The lengths are computed
        based on the first approximation with `ndiv` segments.
        """
        if ndiv is None:
            ndiv = self.N_approx
        umin, umax = self.urange()
        u = at.uniformParamValues(ndiv, umin, umax)
        PL = curve.PolyLine(self.pointsAt(u))
        if nseg is not None:
            u = PL.atLength(nseg)
            PL = curve.PolyLine(PL.pointsAt(u))
        return PL


    def reverse(self):
        """Return the reversed Nurbs curve.

        The reversed curve is geometrically identical, but start and en point
        are interchanged and parameter values increase in the opposite direction.
        """
        return NurbsCurve(control=self.ctrl[::-1], knots=self.knotu.reverse(),
                          degree=self.degree, closed=self.closed)


    def actor(self, **kargs):
        """Graphical representation"""
        from pyformex.opengl.actors import Actor
        G = self.approx(ndiv=100).toMesh()
        G.attrib(**self.attrib)
        return Actor(G, **kargs)


    def pzf_dict(self):
        return {
            'control': self.ctrl,
            'knots': self.knotu.values(),
            f'degree:i__{self.degree}': None,
            f'closed:b__{self.closed}': None,
        }


#######################################################
## NURBS Surface ##

@utils.pzf_register
class NurbsSurface(Geometry4):

    """A NURBS surface

    The Nurbs surface is defined as a tensor product of NURBS curves in two
    parametrical directions u and v. The control points form a grid of
    (nctrlu,nctrlv) points. The other data are like those for a NURBS curve,
    but need to be specified as a tuple for the (u,v) directions.

    The knot values are only defined upon a multiplicative constant, equal to
    the largest value. Sensible default values are constructed automatically
    by a call to the :func:`genKnotVector` function.

    If no knots are given and no degree is specified, the degree is set to
    the number of control points - 1 if the curve is blended. If not blended,
    the degree is not set larger than 3.

    .. warning:: This is a class under development!

    """

    def __init__(self, control, degree=(None, None), wts=None,
                 knots=(None, None), closed=(False, False),
                 blended=(True, True)):
        """Initialize the NurbsSurface.

        """

        Geometry4.__init__(self)
        self.closed = closed

        control = Coords4(control)
        if wts is not None:
            control.deNormalize(wts.reshape(wts.shape[-1], 1))

        for d in range(2):
            nctrl = control.shape[1-d]  # BEWARE! the order of the nodes
            deg = degree[d]
            kn = knots[d]
            bl = blended[d]
            cl = closed[d]

            if deg is None:
                if kn is None:
                    deg = nctrl-1
                    if not bl:
                        deg = min(deg, 3)
                else:
                    deg = len(kn) - nctrl -1
                    if deg <= 0:
                        raise ValueError(
                            f"Length of knot vector ({len(knots)}) must be at"
                            f"least number of control points ({nctrl}) plus 2")
                # make degree changeable
                degree = list(degree)
                degree[d] = deg

            order = deg+1

            if nctrl < order:
                raise ValueError(
                    f"Number of control points ({nctrl}) must not be "
                    f"smaller than order ({order})")

            if kn is None:
                kn = genKnotVector(nctrl, deg, blended=bl, closed=cl).values()
            else:
                kn = np.asarray(kn).ravel()

            nknots = kn.shape[0]

            if nknots != nctrl+order:
                raise ValueError(
                    f"Length of knot vector ({nknots}) must be equal to "
                    f"number of control points ({nctrl}) plus order ({order})")

            if d == 0:
                self.knotu = kn
            else:
                self.knotv = kn

        self.ctrl = control
        self.degree = degree
        self.closed = closed


    def order(self):
        return (self.knotu.shape[0]-self.ctrl.shape[1],
                self.knotv.shape[0]-self.ctrl.shape[0])


    def urange(self):
        """Return the u-parameter range on which the curve is defined.

        Returns a (2,) float array with the minimum and maximum parameter
        value u for which the curve is defined.
        """
        p = self.degree[0]
        return [self.knotu[p], self.knotu[-1-p]]


    def vrange(self):
        """Return the v-parameter range on which the curve is defined.

        Returns a (2,) float array with the minimum and maximum parameter
        value v for which the curve is defined.
        """
        p = self.degree[1]
        return [self.knotv[p], self.knotv[-1-p]]


    def bbox(self):
        """Return the bounding box of the NURBS surface.

        """
        return self.ctrl.toCoords().bbox()


    def pointsAt(self, u):
        """Return the points on the Nurbs surface at given parametric values.

        Parameters:

        - `u`: (nu,2) shaped float array: `nu` parametric values (u,v) at which
          a point is to be placed.

        Returns (nu,3) shaped Coords with `nu` points at the specified
        parametric values.

        """
        ctrl = self.ctrl.astype(np.double)
        U = self.knotv.astype(np.double)
        V = self.knotu.astype(np.double)
        u = np.asarray(u).astype(np.double)

        try:
            pts = lib.nurbs.surfacePoints(ctrl, U, V, u)
            if np.isnan(pts).any():
                print("We got a NaN")
                raise RuntimeError
        except Exception:
            raise RuntimeError(
                "Some error occurred during the evaluation of the Nurbs "
                "surface.\nPerhaps you are not using the compiled library?")

        if pts.shape[-1] == 4:
            pts = Coords4(pts).toCoords()
        else:
            pts = Coords(pts)
        return pts


    def derivs(self, u, m):
        """Return points and derivatives at given parametric values.

        Parameters:

        - `u`: (nu,2) shaped float array: `nu` parametric values (u,v) at which
          the points and derivatives are evaluated.
        - `m`: tuple of two int values (mu,mv). The points and derivatives up
          to order mu in u direction and mv in v direction are returned.

        Returns:

        (nu+1,nv+1,nu,3) shaped Coords with `nu` points at the
        specified parametric values. The slice (0,0,:,:) contains the
        points.

        """
        # sanitize arguments for library call
        ctrl = self.ctrl.astype(np.double)
        U = self.knotv.astype(np.double)
        V = self.knotu.astype(np.double)
        u = np.asarray(u).astype(np.double)
        mu, mv = m
        mu = int(mu)
        mv = int(mv)

        try:
            pts = lib.nurbs.surfaceDerivs(ctrl, U, V, u, mu, mv)
            if np.isnan(pts).any():
                print("We got a NaN")
                raise RuntimeError
        except Exception:
            raise RuntimeError("Some error occurred during the evaluation "
                               "of the Nurbs surface")

        if pts.shape[-1] == 4:
            pts = Coords4(pts)
            pts[0][0].normalize()
            pts = Coords(pts[..., :3])
        else:
            pts = Coords(pts)
        return pts


    def approx(self, ndiv=None, **kargs):
        """Return a Quad4 Mesh approximation of the Nurbs surface

        Parameters:

        - `ndiv`: number of divisions of the parametric space.
        """
        if ndiv is None:
            ndiv = self.N_approx
        if at.isInt(ndiv):
            ndiv = (ndiv, ndiv)
        udiv, vdiv = ndiv
        umin, umax = self.urange()
        vmin, vmax = self.vrange()
        u = at.uniformParamValues(udiv, umin, umax)
        v = at.uniformParamValues(udiv, umin, umax)
        uv = np.ones((udiv+1, vdiv+1, 2))
        uv[:, :, 0] *= u
        uv[:, :, 1] *= v.reshape(-1, 1)
        coords = self.pointsAt(uv.reshape(-1, 2))
        elems = Quad4.els(udiv, vdiv)
        return Mesh(coords, elems, eltype='quad4')


    def actor(self, **kargs):
        """Graphical representation"""
        from pyformex.opengl.actors import Actor
        G = self.approx(ndiv=100)
        G.attrib(**self.attrib)
        return Actor(G, **kargs)


    def pzf_dict(self):
        return {
            'control': self.ctrl,
            'knotu': self.knotu.values(),
            'knotv': self.knotv.values(),
            'dict:r': {
                'degree': self.degree,
                'closed': self.closed,
            }
        }


################################################################


def besselTangents(Q, u):
    q = Q[1:] - Q[:-1]
    du = u[1:] - u[:-1]
    d = q / du[:,np.newaxis]
    alfa = du[:-1] / (du[:-1] + du[1:])
    alfa = alfa[:, np.newaxis]
    D = np.empty(Q.shape)
    D[1:-1] = (1-alfa) * d[:-1] + alfa * d[1:]
    D[0] = 2*d[0] - D[1]
    D[-1] = 2*d[-1] - D[-2]
    return D


def akimTangents(Q, corner=0.5, normalize=True):
    """Estimate tangents to a curve passing through given points.

    Parameters
    ----------
    Q: :term:`coords_like` (npts, 3)
        The points through which the curve should pass.
    corner: float
        A value in the range 0.0..1.0. A value 1.0 will set the tangent
        at a corner to that after the corner. A value sets it to that before.
        A value 0.5 gives an intermediate value.
    normalize: bool
        If True (default), normalized vectors are returned. If False,
        the vectors are not normalized and are good approximations for
        the derivative vectors of a curve interpolating/approximating
        the points.

    Returns
    -------
    array (npts, 3)
        The normalized tangent vectors at the points Q to a curve
        that interpolates those points.

    Notes
    -----
    Based on The NURBS Book (9.29) and (9.31).
    """
    n = len(Q)-1
    q = np.zeros((n+1, 3))  # k = -1..n+2  where Q is 0..n
    q[1:] = Q[1:] - Q[:-1]
    q[0] = 2*q[1] - q[2]
    qm1 = 2*q[0] - q[1]
    qn1 = 2*q[n] - q[n-1]
    qn2 = 2*qn1 - q[n]
    qq = np.zeros((n+4, 3))
    qq[1:-2] = q
    qq[0] = qm1
    qq[n+2] = qn1
    qq[n+3] = qn2
    cq = np.cross(qq[:-1], qq[1:])
    lcq = at.length(cq)
    denom = lcq[:-2] + lcq[2:]
    w = at.where_1d(denom!=0)
    alfa = np.full(lcq[:-2].shape, corner)
    alfa[w] = lcq[:-2][w] / denom[w]
    alfa = alfa[:, np.newaxis]
    V = (1-alfa) * qq[1:-2] + alfa * qq[2:-1]
    return at.normalize(V) if normalize else V


def _compute_alpha(P30, T03):
    """Nurbsbook (9.50)"""
    a = 16 - T03 @ T03
    b = 12 * P30 @ T03
    c = -36 * P30 @ P30
    r1, r2, k = at.quadraticEquation(a,b,c)
    assert (k!=2)
    return r2


def cubicInterpolate(Q, T=None, return_param=False):
    """Create a C1 cubic interpolation curve

    Parameters
    ----------
    Q: :term:`coords_like` (npts, 3)
        The points through which the curve should pass.
    T: :term:`coords_like` (npts, 3), optional
        The normalized tangent vectors at the points Q to a curve that
        interpolates those points. If not provided, they are computed
        with :func:`akimTangents`.
    return_param: bool
        If True, also returns also parameter values where the given points
        occur.

    Returns
    -------
    NurbsCurve:
        A cubic NurbsCurve interpolating the points Q and having
        tangents T at those points. The curve is
        guaranteed to have C1 continuity (including in the speed of the
        curve) and has a fairly uniform parametrization.
    u: float array (npts, )
        Only returned if return_param=True: the parametric values where
        the input points are found on the NurbsCurve. Thus, N.pointsAt(u)
        produces Q.

    Notes
    -----
    Based on The NURBS Book 9.3.4.
    """
    Q = at.checkArray(Q, (-1,3), 'f')
    d = curve.PolyLine(Q).lengths()
    if (d==0.0).any():
        raise ValueError("Double points in the data set are not allowed")
    if T is None:
        T = akimTangents(Q)
    else:
        T = at.checkArray(T, Q.shape, 'f')
        T = at.normalize(T)
    nQ = Q.shape[0]
    P = np.zeros((2*nQ, 3), dtype=Q.dtype)
    u = np.empty((nQ,), dtype=Q.dtype)
    u[0] = 0
    P[0] = Q[0]
    P[-1] = Q[-1]
    for i in range(1, nQ):
        alpha = _compute_alpha(Q[i]-Q[i-1], T[i-1]+T[i])
        P1 = Q[i-1] + alpha/3 * T[i-1]
        P2 = Q[i] - alpha/3 * T[i]
        P[2*i-1:2*i+1] = P1, P2
        u[i] = u[i-1] + 3*at.length(P1 - Q[i-1])
    u /= u[-1]
    U = np.empty((2*nQ+4,), dtype=Q.dtype)
    U[:4] = 0
    U[-4:] = 1
    U[4:-4:2] = u[1:-1]
    U[5:-4:2] = u[1:-1]
    N = NurbsCurve(P, knots=U, degree=3)
    if return_param:
        return N, u
    else:
        return N


# TODO: we could add a T0/T1 option
def cubicInterpolate(Q, T=None, return_param=False):
    """Create a C1 cubic interpolation curve

    Parameters
    ----------
    Q: :term:`coords_like` (npts, 3)
        The points through which the curve should pass.
    T: :term:`coords_like` (npts, 3), optional
        The normalized tangent vectors at the points Q to a curve that
        interpolates those points. If not provided, they are computed
        with :func:`akimTangents`.
    return_param: bool
        If True, also returns also parameter values where the given points
        occur.

    Returns
    -------
    NurbsCurve:
        A cubic NurbsCurve interpolating the points Q and having
        tangents T at those points. The curve is
        guaranteed to have C1 continuity (including in the speed of the
        curve) and has a fairly uniform parametrization.
    u: float array (npts, )
        Only returned if return_param=True: the parametric values where
        the input points are found on the NurbsCurve. Thus, N.pointsAt(u)
        produces Q.

    Notes
    -----
    Based on The NURBS Book 9.3.4.
    """
    Q = at.checkArray(Q, (-1,3), 'f')
    d = curve.PolyLine(Q).lengths()
    if (d==0.0).any():
        raise ValueError("Double points in the data set are not allowed")
    if T is None:
        T = akimTangents(Q)
    else:
        T = at.checkArray(T, Q.shape, 'f')
        T = at.normalize(T)
    nQ = Q.shape[0]
    P = np.zeros((2*nQ, 3), dtype=Q.dtype)
    u = np.empty((nQ,), dtype=Q.dtype)
    u[0] = 0
    P[0] = Q[0]
    P[-1] = Q[-1]
    for i in range(1, nQ):
        alpha = _compute_alpha(Q[i]-Q[i-1], T[i-1]+T[i])
        P1 = Q[i-1] + alpha/3 * T[i-1]
        P2 = Q[i] - alpha/3 * T[i]
        P[2*i-1:2*i+1] = P1, P2
        u[i] = u[i-1] + 3*at.length(P1 - Q[i-1])
    u /= u[-1]
    U = np.empty((2*nQ+4,), dtype=Q.dtype)
    U[:4] = 0
    U[-4:] = 1
    U[4:-4:2] = u[1:-1]
    U[5:-4:2] = u[1:-1]
    N = NurbsCurve(P, knots=U, degree=3)
    if return_param:
        return N, u
    else:
        return N


def quadraticInterpolate(Q, T=None, corners=False, reduce=True,
                         return_param=False):
    """Create a G1/C1 quadratic interpolation curve

    Parameters
    ----------
    Q: :term:`coords_like` (npts, 3)
        The points through which the curve should pass.
    T: :term:`coords_like` (npts, 3), optional
        The normalized tangent vectors at the points Q to a curve that
        interpolates those points. If not provided, they are computed
        with :func:`akimTangents`, with a corner value of 1.0 if corners
        is True, and 0.5 if not.
    corners: bool, optional
        If True, obvious corners will be retained in the result.
        The default (False) will round corners.
    reduce: bool, optional
        If True (default), the curve is reduced by removing the internal
        oncurve control points. If set False, the oncurve points are
        retained. Note that there may be more oncurve points than the
        originally specified set.
    return_param: bool
        If True, also returns also parameter values where the given points
        occur.

    Returns
    -------
    NurbsCurve:
        A quadratic NurbsCurve interpolating the given points and having
        tangents equal to the provided or computed ones. If not reduced,
        and corners is False, the curve has G1 (geometric) continuity and
        a fairly uniform parametrization. If reduced, it has C1 continuity
        (thus including the curve speed) and a smaller footprint, at the
        price of a less uniform parametrization. If corners is True, it
        has C0 continuity.

    Notes
    -----
    Based on The NURBS Book 9.3.2
    """
    Q = at.checkArray(Q, (-1,3), 'f', 'i')
    d = curve.PolyLine(Q).lengths()
    if (d==0.0).any():
        raise ValueError("Double points in the data set are not allowed")
    if T is None:
        akim = 1.0 if corners else 0.5
        T = akimTangents(Q, akim)
    else:
        T = at.checkArray(T, Q.shape, 'f')
    Q0, T0 = Q[:-1], T[:-1]
    Q1, T1 = Q[1:], T[1:]
    t0, t1 = gt.intersectLineWithLine(
        Q0, T0, Q1, T1, mode='pair', times=True)
    R = 0.5 * (Q0 + t0[:,np.newaxis]*T0 + Q1 + t1[:,np.newaxis]*T1)
    nc = len(Q)
    newQ = []
    newR = []
    for i in range(nc-1):
        newQ.append(Q[i])
        if ((t0[i] > 0.0 and t1[i] < 0.0)  # Normal segment
            or corners and (t0[i] == 0.0 or t1[i] == 0.0)):  # Corner
            newR.append(R[i])
        else:
            QQ = at.normalize(Q[i+1] - Q[i])  # chord length
            if np.allclose(T[i], T[i+1]) and np.allclose(T[i], QQ):
                R[i] = 0.5 * (Q[i] + Q[i+1])    # colinear 9.40
                newR.append(R[i])
            else:
                QQ = Q[i+1] - Q[i]
                if np.allclose(T[i], T[i+1]) or np.allclose(T[i], -T[i+1]):
                    # parallel or 180 turn
                    gamma = (0.5 * at.length(QQ), ) * 2   # 9.43
                else:
                    cos0 = at.projection(T[i], QQ)
                    cos1 = at.projection(T[i+1], QQ)
                    lQQ = at.length(QQ)
                    alfa = 2/3
                    c0 = (1-alfa) * cos0 + alfa * cos1
                    c1 = alfa * cos0 + (1-alfa) * cos1
                    gamma = (0.20 * lQQ / c0,
                             0.20 * lQQ / c1)  # 9.44
                    if np.isnan(gamma[0]) or np.isnan(gamma[1]):
                        gamma = (0.5 * at.length((Q[i+1] - Q[i])), ) * 2   # 9.43
                Rk = Q[i] + gamma[0] * T[i]       # 9.41
                Rk1 = Q[i+1] - gamma[1] * T[i+1]
                Qk = (gamma[0] * Rk1 + gamma[1] * Rk) / (gamma[0]+gamma[1])  # 9.42
                newR.append(Rk)
                newQ.append(Qk)
                newR.append(Rk1)

    newQ.append(Q[-1])
    nc = len(newQ)
    # parametric values of Q
    if reduce:
        # remove the internal oncurve control points
        Q = Coords.concatenate(newQ)
        R = Coords.concatenate(newR)
        u = np.empty(nc)
        u[:2] = 0, 1
        l1 = at.length(R - Q[:-1])
        l2 = at.length(Q[1:] - R)
        for k in range(2, nc):
            u[k] = u[k-1] + (u[k-1] - u[k-2]) * l1[k-1] / l2[k-2]
        u /= u[-1]
        U = np.concatenate([[0,0],u,[1,1]])
        Q = Coords.concatenate([Q[:1], R, Q[-1:]])
    else:
        # keep oncurve and intermediate points
        Q = at.interleave(Q, R)
        u = np.arange(nc) / (nc-1)
        U = np.empty(2*nc+2)
        U[0], U[-1] = 0, 1
        U[1:-1:2] = u
        U[2:-1:2] = u
    N = NurbsCurve(Q, knots=U, degree=2)
    if return_param:
        return N, u
    else:
        return N


def globalInterpolationParameters(Q, exp=1.0):
    """Compute parameters for a global interpolation curve

    The global interpolation algorithm computes the control points that
    produce a NurbsCurve with given points occurring at predefined
    parameter values. The curve shape depends on the choosen values.
    This function provides a way to set values that work well under
    mosr conditions/

    Parameters
    ----------
    Q: :term:`coords_like` (npts, 3)
        An ordered set of points through which the curve should pass.
        Two consecutive points should not coincide.
    exp: float
        The exponent to be used in the interpolation algorithm. See Notes.

    Returns
    -------
    u: float array (npts, )
        Only returned if return_param=True: the parametric values where
        the input points are found on the NurbsCurve. Thus, N.pointsAt(u)
        produces Q.

    Notes
    -----
    The algorithm to set these values uses a variable exponent.
    Different values produce (slighly) different curves.
    The smaller the value, the more the two spans get curved. Values
    above 1 will almost straighten the end spans, but intermediate spans
    become more curved.
    Typical values are:

    0.0: equally spaced (not recommended)
    0.5: centripetal (recommended when data set take sharp turns)
    0.7: our prefered default
    1.0: chord length (widely used)
    """
    # chord length
    d = curve.PolyLine(Q).lengths()
    if (d==0.0).any():
        utils.warn("warn_nurbs_gic")
        w = np.where(d!=0)[0]
        Q = np.concatenate([Q[w], Q[-1:]], axis=0)
        d = curve.PolyLine(Q).lengths()
        if (d==0.0).any():
            raise ValueError("Double points in the data set are not allowed")
    # apply exponent
    if exp != 1.:
        d = d ** exp
    d = d.cumsum()
    d /= d[-1]
    return np.concatenate([[0.], d])


# def globalInterpolationEndConditions(Q, t0, t1, alfa):
#     if t0 is not None:
#         t0 = at.checkArray(t0, (3,), 'f', 'i')
#     if t1 is not None:-1
#         t1 = at.checkArray(t1, (3,), 'f', 'i')
#     if alfa is None:
#         alfa = curve.PolyLine(Q).length()
#         t0 = at.normalize(t0)
#         t1 = at.normalize(t1)
#     if t0 is not None:
#         t0 = alfa*t0
#     if t1 is not None:
#         t1 = alfa*t1
#     return t0, t1


def cubicSpline(Q, D0, D1, *, u=None, exp=0.7, return_param=False):
    """Cubic spline interpolation.

    Computes a traditional C2 cubic spline through the points Q with
    given end tangents.

    Parameters
    ----------
    Q: :term:`coords_like` (npts, 3)
        An ordered set of points through which the curve should pass.
        Two consecutive points should not coincide.
    D0: :term:`coords_like` (3,)
        The derivative of the curve at the start point Q[0].
        The length of the vector is significant.
    D1: :term:`coords_like` (3,)
        The derivative of the curve at the end point Q[-1].
        The length of the vector is significant.
    u: float array (npts,), optional
        The parameter values where the points Q should be obtained on the
        curve. If not provided, a default set of parameter values is computed
        from :func:`globalInterpolationParameters` (Q, exp=exp)``.
    exp: float, optional
        The exponent to be used in computing the parameter values if no `u`
        was provided. The default value 0.7 will work well in most cases.
        See :func:`globalInterpolationParameters`.
    return_param: bool
        If True, also returns also parameter values where the given points
        occur.

    Returns
    -------
    N: NurbsCurve
        A NurbsCurve of the third degree that passes through the
        given point set Q and has tangents D0 and D1 at its ends.
        The number of control points of the curve is npts + 2.
        The parametric values of the input points Q can be got from
        ``N.knots[3:-3]``.
    u: float array (npts, )
        Only returned if return_param=True: the parametric values where
        the input points are found on the NurbsCurve. Thus, N.pointsAt(u)
        produces Q.

    See Also
    --------
    globalInterpolationCurve: global interpolation curve of any degree

    """
    # set the parameter values
    if u is None:
        u = globalInterpolationParameters(Q, exp=exp)
    else:
        u = at.checkArray(u, (npts,), 'f', 'i')
    # end conditions
    D0 = at.checkArray(D0, (3,), 'f', 'i')
    D1 = at.checkArray(D1, (3,), 'f', 'i')
    # Knots
    U = np.concatenate([[0]*3, u, [1]*3])
    # Control points
    P = lib.nurbs.cubicSplineInterpolation(Q, D0, D1, U)
    N = NurbsCurve(P, knots=U, degree=3)
    if return_param:
        return N, u
    else:
        return N


def globalInterpolationCurve(Q, degree=3, *, D=None, D0=None, D1=None,
                             u=None, exp=0.7, return_param=False):
    """Create a global interpolation NurbsCurve.

    An interpolation curve is a curve passing through all the given points.

    Parameters
    ----------
    Q: :term:`coords_like` (npts, 3)
        An ordered set of points through which the curve should pass.
        Two consecutive points should not coincide.
    degree: int
        The degree of the resulting curve. Usually 2 or 3 is used.
        For degree 1, the result is a PolyLine through the points Q.
        For degrees higher than 4, it is better to create a degree 3
        curve and then increase the degree.
    D: :term:`coords_like` (npts, 3)
        The derivatives of the curve at the points Q. The longer the
        derivative vectors, the further the curve will follow the tangent.
        If not provided, the interpolation is done without imposing
        tangent directions at the intermediate points.
    D0: :term:`coords_like` (3,)
        The derivative of the curve at the start point. Can only be used if
        D is not provided, and derivatives at one or both ends need to
        be imposed. The length of the vector is significant.
    D1: :term:`coords_like` (3,)
        The derivative of the curve at the end point. Can only be used if
        D is not provided, and derivatives at one or both ends need to
        be imposed. The length of the vector is significant.
    u: float :term:`array_like` (npts,), optional
        The parameter values where the points Q should be obtained on the
        curve. If not provided, a default set of parameter values is computed
        from ``globalInterpolationParameters(Q, exp=exp)``.
    exp: float, optional
        The exponent to be used in computing the parameter values if no `u`
        was provided. The default value 0.7 works well in most cases.
        See :func:`globalInterpolationParameters`.
    return_param: bool
        If True, also returns also parameter values where the given points
        occur.

    Returns
    -------
    N: NurbsCurve
        A NurbsCurve of the specified degree that passes through the
        given point set. The number of control points is equal to
        the number of input points plus one for every end tangent set.
    u: float array (npts, )
        Only returned if return_param=True: the parametric values where
        the input points are found on the NurbsCurve. Thus, N.pointsAt(u)
        produces Q.

    See Also
    --------
    cubicSpline: returns the classical C2 spline interpolate
    """
    p = degree
    Q = at.checkArray(Q, (-1,3), 'f')
    nQ = Q.shape[0]
    if D is not None:
        D = at.checkArray(D, Q.shape, 'f')
        D0 = D1 = None
    # set the parameter values
    if u is None:
        u = globalInterpolationParameters(Q, exp=exp)
    else:
        u = at.checkArray(u, (npts,), 'f', 'i')
    # compute system matrix
    if D is not None:
        print(f"Global, Q {Q.shape}, D {D.shape}, u {u.shape}, p {p}")
        from pyformex.lib import nurbs_e
        U, A, Q = nurbs_e.curveGlobalInterpolationMatrix2(Q, D, u, p)
        print(f"U {U.shape}, A {A.shape}, Q {Q.shape}")
    else:
        print(f"Global, Q {Q.shape}, D0 {D0}, D1 {D1}")
        # set the end conditions
        it0 = D0 is not None
        it1 = D1 is not None
        if it0:
            D0 = at.checkArray(D0, (3,), 'f', 'i')
        if it1:
            D1 = at.checkArray(D1, (3,), 'f', 'i')
        U, A = lib.nurbs.curveGlobalInterpolationMatrix(u, degree, it0, it1)
        # set right hand side (TODO: move this inside ^^^)
        if it0:
            D0 = Coords(D0).reshape(-1,3) * U[p+1] / p * 4
            Q = Coords.concatenate([Q[0:1], D0, Q[1:]])
        if it1:
            D1 = Coords(D1).reshape(-1,3) * (1-U[-(p+2)]) / p * 4
            Q = Coords.concatenate([Q[:-1], D1, Q[-1:]])
    P = np.linalg.solve(A, Q)
    N = NurbsCurve(P, knots=U, degree=degree)
    if return_param:
        return N, u
    else:
        return N


def lsqCurve(Q, p, nctrl, Wq=None, D=None, I=None, Wd=None, return_param=False):
    """Weighed and constrained least squares curve fit

    Creates a NurbsCurve of a given degree and with given number of
    control points, approximating a sequence of points. Points can be
    attributed weights to force the curve closer to specific points.
    Tangents can be specified at any point, and can be weighed to have
    better approximation at specific points. Specifying negative weights
    for specific points or tangents turns them into constraints to be
    met accurately.

    Parameters
    ----------
    Q: :term:`coords_like` (npts, 3)
        The points through which to fit a NurbsCurve
    p: int
        The degree of the target curve. A typical value is 3.
    nctrl: int
        The number of control points in the target curve. It should be higher
        than the degree ``p``, but smaller smaller than the number of points
        ``npts``. The higher the number, the closer the curve can come to all
        points, at the cost of higher oscillations though.
        A value of 2 with ``p=1`` fits a straight line throught the data.
    Wq: :term:`array_like` float (npts,), optional
        The weigths of the ``npts`` points, where the value is non-negative.
        Where negative, a point constraint is added to force the curve
        through the point. If not specified, all weights are set equal to 1.
    D: :term:`coords_like` (nder, 3), optional
        The derivatives at ``nder`` points. Note that the length of the vectors
        is significant. See Notes.
    I: :term:`array_like` int (nder,), optional
        The index of the points in Q for which the derivatives D are specified.
        Required if D is provided.
    Wd: :term:`array_like` float (nder,), optional
        The weight of the ``nder`` derivatives, where the value is non-negative.
        Where negative, a constraint is added to force the curve to have
        that derivative. If not specified, all weights are set equal to 1.
    return_param: bool
        If True, also returns also parameter values where the given points
        occur.

    Returns
    -------
    N: NurbsCurve
        A NurbsCurve of the specified degree and with the specified number
        of control points, passing as close as possible to the given
        (weighed) points and obeying any specified constraints.
    u: float array (npts, )
        Only returned if return_param=True: the parametric values where
        the input points are found on the NurbsCurve. Thus, N.pointsAt(u)
        produces points in the neighborhood of Q.

    Notes
    -----
    If derivatives or constraints are provided, the number of control points
    is further restricted. Let ``nc`` be the number of constraints points and
    derivatives and ``nu`` be the number of unconstrained points and derivatives,
    then ``nctrl`` should satisfy: ``nc-2 < nctrl < nu-nc+2``.

    The length of the derivatives has a significant influence on the resulting
    curve. The recommended length is the polygonal length of the point set.
    This can be achieved with::

        import pyformex.arraytools as at
        from pyformex.core import PolyLine
        D = at.normalize(D) * PolyLine(Q).length()

    This is algorithm A9.6 p.417 of the NurbsBook.

    This function requires scipy.
    """
    utils.Module.require('scipy')
    from pyformex.lib.nurbs_e import find_span, basis_funs, basis_derivs
    from scipy import linalg
    if p < 1 or p >= nctrl:
        raise ValueError(f"Degree p ({p}) should be >0 and <nctrl ({nctrl})")
    Q = at.checkArray(Q, ndim=2, kind='f')
    npts = Q.shape[0]
    if nctrl >= npts:
        raise ValueError(f"ctrl ({nctrl} should be <npts ({npts})")
    nd = Q.shape[1]
    if Wq is None:
        Wq = np.ones((npts,), dtype=at.Float)
    else:
        Wq = at.checkArray(Wq, (npts,), 'f')
    if D is None:
        nder = 0
    else:
        D = at.checkArray(D, (-1, nd), 'f')
        nder = D.shape[0]
    if nder > 0:
        I = at.checkArray(I, (nder,), 'i')
        if Wd is None:
            Wd = np.ones((nder,), dtype=at.Float)
        else:
            Wd = at.checkArray(Wd, (nder,), 'f')

    ru = -1 + (Wq >= 0.0).sum()
    rc = -1 + (Wq < 0.0).sum()
    if Wd is None:
        su = sc = -1
    else:
        su = -1 + (Wd >= 0.0).sum()
        sc = -1 + (Wd < 0.0).sum()
    mu = ru+su+1
    mc = rc+sc+1
    if nctrl < mc-1 or nctrl > mu-mc+2:
        print(f"nu={mu+1}, nc={mc+1}, nc-2={mc-1}, nu-nc+2={mu+1-(mc+1)+2}")
        raise ValueError(f"Invalid number of control points ({nctrl} for "
                         f"constraints: need {mc-1} <= nctrl <= {mu-mc+2}")

    # Parameters
    u = globalInterpolationParameters(Q)

    # Knots
    nknots = nctrl + p + 1
    U = np.zeros((nknots,))
    d = npts / (nctrl-p)  # NurbsBook 9.68
    for j in range(1, nctrl-p):
        jd = j * d
        i = int(jd)
        alfa = jd - i
        U[p+j] = (1-alfa)*u[i-1] + alfa*u[i]
    U[-(p+1):] = 1.0

    # Set up arrays
    W = np.zeros((mu+1,))
    S = np.zeros((mu+1, nd))
    N = np.zeros((mu+1, nctrl))
    T = np.zeros((mc+1, nd))
    A = np.zeros((mc+1,))
    M = np.zeros((mc+1, nctrl))
    j = 0  # current index into I
    mu2 = 0; mc2 = 0   # counters up to mu and mc
    for i in range(npts):
        span = find_span(U, u[i], p, nctrl-1)
        dflag = j < nder and i == I[j]
        if dflag:
            funs, derivs = basis_derivs(U, u[i], p, span, 1)
        else:
            funs = basis_funs(U, u[i], p, span)
        if Wq[i] >= 0.0:
            # Unconstrained point
            W[mu2] = Wq[i]
            S[mu2] = Wq[i] * Q[i]
            N[mu2, span-p:span+1] = funs
            mu2 += 1
        else:
            # Constrained point
            T[mc2] = Q[i]
            M[mc2, span-p:span+1] = funs
            mc2 += 1
        if dflag:
            # Derivatives at this point
            if Wd[j] >= 0.0:
                # Unconstrained derivative
                W[mu2] = Wd[j]
                S[mu2] = Wd[j] * D[j]
                N[mu2, span-p:span+1] = derivs
                mu2 += 1
            else:
                # Constrained derivative
                T[mc2] = D[j]
                M[mc2, span-p:span+1] = derivs
                mc2 += 1
            j += 1

    # Compute matrices
    NTW = N.T * W
    NTWN = NTW @ N
    NTWS = N.T @ S  # S already contains W !!
    del NTW
    lu, piv = linalg.lu_factor(NTWN)
    if mc < 0:
        # No constraints: direct solution
        P = linalg.lu_solve((lu,piv), NTWS)
    else:
        # inverse of NTWN
        NTWNI = linalg.lu_solve((lu,piv), np.identity(NTWN.shape[0]))
        # Solve for Lagrange multipliers: Nurbsbook  eq 9.75
        MI = M @ NTWNI
        MIMT = MI @ M.T
        MINWST = MI @ NTWS - T
        A = linalg.solve(MIMT, MINWST)
        # Solve for control points: Nurbsbook  eq 9.74
        P = NTWNI @ (NTWS - M.T @ A)

    N = NurbsCurve(P, knots=U, degree=p)
    if return_param:
        return N, u
    else:
        return N


def optLsqCurve(Q, p, dtol, nmin=None, nmax=None):
    """Compute an optimal lsqCurve

    Finds the lsqCurve with minimum number of control points that
    passes not further than dtol from any of the given points.

    Parameters
    ----------
    Q, p: see lsqCurve
    dtol: float
        Maximum distance from the curve allowed for any of the points Q.
        Note that specifying a very small value may lead to high
        oscillations in the curve.
    nmin: int
        Minimum number of control points in the curve. If not specified,
        it is set to p+1.
    nmax: int
        Minimum number of control points in the curve. If not specified,
        it is set to npts-1.

    Returns
    -------
    N: NurbsCurve
        The NurbsCurve obtained with lsqCurve with the minimum number of control
        points guaranteeing that no point is further than dtol from the curve.
    d: float
        The maximum distance of any point Q from the curve N.
    """
    def _one_step(Q, p, n):
        N, u = lsqCurve(Q, p, n, return_param=True)
        return N, at.length(Q-N(u)).max()

    npts = Q.shape[0]
    nmax = npts-1 if nmax is None else min(nmax, npts-1)
    nmin = p+1 if nmin is None else max(nmin, p+1)
    N, dmin = _one_step(Q,p,nmin)
    if dmin < dtol:
        return N, dmin
    Nmax, dmax = _one_step(Q,p,nmax)
    if dmax > dtol:
        raise ValueError(f"No solution with nmax={nmax} and dtol={dtol}; "
                         f"smallest dtol is {dmax}")
    col = 4
    it, maxit = 0, 100  # avoid endless loop
    while nmin < nmax-1 and it < maxit:
        nr = (nmin*(dtol-dmax) + nmax*(dmin-dtol)) / (dmin-dmax)
        n = int(round(nr))
        N, d = _one_step(Q,p,n)
        if d < dtol:
            if n == nmax:
                break
            Nmax, nmax, dmax = N, n, d
        elif d > dtol:
            if n == nmin:
                break
            nmin, dmin = n, d
        else:
            break
        col += 1
        it += 1
    return Nmax, dmax


def NurbsCircle(C=[0., 0., 0.], r=1.0, X=[1., 0., 0.], Y=[0., 1., 0.],
                ths=0., the=360.):
    """Create a NurbsCurve representing a perfect circle or arc.

    Parameters
    ----------
    C: float (3,)
        The center of the circle
    r: float
        The radius of the circle
    X: float (3,)
        A unit vector in the plane of the circle
    Y: float (3,)
        A unit vector in the plane of the circle and perpendicular to X
    ths: float
        Start angle (in degrees) of the arc, measured from the X axis,
        counterclockwise in X-Y plane
    the: float
        End angle (in degrees) of the arc, measured from the X axis,
        counterclockwise in X-Y plane

    Returns
    -------
    NurbsCurve
        A NurbsCurve that is a perfect circle or arc in the plane of the
        XY-axes.

    Notes
    -----
    NurbsBook algorithm A7.1
    """
    if the < ths:
        the += 360.
    theta = (the-ths)
    # Get the number of arcs
    narcs = int(np.ceil(theta/90.))
    n = 2*narcs   # n+1 control points
    C, X, Y = (at.checkArray(x, (3,), 'f', 'i') for x in (C, X, Y))
    dths = ths*at.DEG
    dtheta = theta*at.DEG/narcs
    w1 = np.cos(dtheta/2.)  # base angle
    # Initialize start values
    P0 = C + r*np.cos(dths)*X + r*np.sin(dths)*Y
    T0 = -np.sin(ths)*X + np.cos(ths)*Y
    Pw = np.zeros((n+1, 4), dtype=at.Float)
    Pw[0] = Coords4(P0)
    index = 0
    angle = ths*at.DEG
    # create narcs segments
    for i in range(1, narcs+1):
        angle += dtheta
        P2 = C + r*np.cos(angle)*X + r*np.sin(angle)*Y
        Pw[index+2] = Coords4(P2)
        T2 = -np.sin(angle)*X + np.cos(angle)*Y
        P1, P1b = gt.intersectLineWithLine(P0, T0, P2, T2)
        Pw[index+1] = Coords4(P1) * w1
        index += 2
        if i < narcs:
            P0, T0 = P2, T2
    # Load the knot vector
    j= 2*narcs+1
    U = np.zeros((j+3,), dtype=at.Float)
    for i in range(3):
        U[i] = 0.
        U[i+j] = 1.
    if narcs == 2:
        U[3] = U[4] = 0.5
    elif narcs == 3:
        U[3] = U[4] = 1./3.
        U[5] = U[6] = 2./3.
    elif narcs == 4:
        U[3] = U[4] = 0.25
        U[5] = U[6] = 0.5
        U[7] = U[8] = 0.75

    return NurbsCurve(control=Pw, degree=2, knots=U)


def toCoords4(x):
    """Convert cartesian coordinates to homogeneous

    `x`: :class:`Coords`
      Array with cartesian coordinates.

    Returns a Coords4 object corresponding to the input cartesian coordinates.
    """
    return Coords4(x)


Coords.toCoords4 = toCoords4


def pointsOnBezierCurve(P, u):
    """Compute points on a Bezier curve

    Parameters:

    P is an array with n+1 points defining a Bezier curve of degree n.
    u is a vector with nu parameter values between 0 and 1.

    Returns:

    An array with the nu points of the Bezier curve corresponding with the
    specified parametric values.
    ERROR: currently u is a single paramtric value!

    See also:
    examples BezierCurve, Casteljau
    """
    u = np.asarray(u).ravel()
    n = P.shape[0]-1
    return Coords.concatenate([
        (lib.nurbs.allBernstein(n, ui).reshape(1, -1, 1) * P).sum(axis=1)
        for ui in u], axis=0)


def frenet(d1, d2, d3=None):
    """Compute Frenet vectors, curvature and torsion.

    This function computes Frenet vectors, curvature and torsion
    from the provided first, second, and optional third derivatives
    of curve. The derivatives can be obtained from
    :func:`NurbsCurve.deriv`.
    Curvature is computed as `abs| d1 x d2 | / |d1|**3`

    Parameters
    ----------
    d1: float :term:`array_like` (npts,3)
        First derivative at `npts` points of a nurbs curve
    d2: float :term:`array_like` (npts,3)
        Second derivative at `npts` points of a nurbs curve
    d3: float :term:`array_like` (npts,3) , optional
        Third derivative at `npts` points of a nurbs curve

    Returns
    -------
    T: float array(npts,3)
        Normalized tangent vector to the curve at `npts` points.
    N: float array(npts,3)
        Normalized normal vector to the curve at `npts` points.
    B: float array(npts,3)
        Normalized binormal vector to the curve at `npts` points.
    k: float array(npts,3)
        Curvature of the curve at `npts` points.
    t: float array(npts,3), optional
        Torsion of the curve at `npts` points. This value is only returned
        if `d3` was provided.

    See Also
    --------
    NurbsCurve.frenet : the corresponding NurbsCurve method
    NurbsCurve.deriv : computation of the derivatives of a NurbsCurve
    """
    ld = at.length(d1)
    # What to do when ld is 0? same as with k?
    if ld.min() == 0.0:
        print(f"ld is zero at {np.where(ld==0.0)[0]}")
    e1 = d1 / ld.reshape(-1, 1)
    e2 = d2 - at.dotpr(d2, e1).reshape(-1, 1)*e1
    k = at.length(e2)
    if k.min() == 0.0:
        w = np.where(k==0.0)[0]
        print(f"k is zero at {w}")
    # where k = 0: set e2 to mean of previous and following
    e2 /= k.reshape(-1, 1)
    # e3 = normalize(ddd - dotpr(ddd,e1)*e1 - dotpr(ddd,e2)*e2)
    e3 = np.cross(e1, e2)
    # m = at.dotpr(np.cross(d1, d2), e3)
    # print "m",m
    m = np.cross(d1, d2)
    k = at.length(m) / ld**3
    if d3 is None:
        return e1, e2, e3, k
    # compute torsion
    t = at.dotpr(d1, np.cross(d2, d3)) / at.dotpr(d1, d2)
    return e1, e2, e3, k, t


### End
