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
"""Handling curves in pyFormex

This module defines classes and functions specialized for handling curves
(one-dimensional geometrical objects) in pyFormex. They can be straight lines,
polylines, higher order curves and collections thereof. In general,
the curves are 3D, but special cases may be created for handling plane curves.

The most important curve type classes defined in this module are:

- :class:`Curve`: a virtual base class for all curve type classes.
  It can not be instantiated itself: always use one of the derived classes.
- :class:`BezierSpline`: curves consisting of a concatenation of Bezier
  polynomes of degree 1 to 3.
- :class:`PolyLine`: curves consisting of a concatenation of straight segments.
- :class:`Arc`: circles and arcs

Another important curve type, :class:`~plugins.nurbs.NurbsCurve`, is defined
in the :mod:`plugins.nurbs` module.
"""
import math
import functools

import numpy as np

import pyformex as pf
from pyformex import arraytools as at
from pyformex import utils
from pyformex.coords import Coords
from pyformex.coordsys import CoordSys
from pyformex.geometry import Geometry
from pyformex.formex import Formex, connect
from pyformex.mesh import Mesh
from pyformex import geomtools as gt
from pyformex.varray import Varray

# TODO: remove this when we make 3.9 the minimum version
import sys
cache = functools.cache if sys.hexversion >= 0x03090000 else functools.lru_cache

_numpy_printoptions_ = {'precision':3}

###########################################################################
##
##   class Curve
##
#########################

class Curve(Geometry):
    """Base class for curve type classes.

    This is a virtual class that can not be instantiated. It defines the common
    definitions for all curve type subclasses. The subclasses define at least
    the following attributes:

    Attributes
    ----------
    coords: :class:`~coords.Coords`
        The coordinates of all the points needed to define the curve. These
        are not necessarily points on the curve.
    nparts: int
        The number of parts comprising the curve. Subsequent parts of a curve
        (e.g. straight segments of a polyline), have a local parameter with
        values in the range 0..1. Any point on the curve can thus be identified
        by a float number, where the integer part is the curve number and the
        fractional part is the parameter value. See :meth:`localParam`.
    closed: bool
        Whether the curve is closed or not. A closed curve has coinciding
        begin and end points, making it a closed loop. An open curve with
        coinciding end points may look like a closed curve, but technically
        it is still open, and its behavior may be different from that of a
        closed curve.
    """
    _exclude_members_ = ['nelems', '_select']

    # Required implementation of abstract Geometry methods
    # Keep undocumented as they are not relevant
    def nelems(self):
        return 1
    def _select(self, sel, compact=False):
        return self

    # DEVS:
    # Curve subclasses should override the following methods if the default
    # is not suitable:
    #
    # - `sub_points(t,j)`: returns points at parameter value t,j
    # - `sub_directions(t,j)`: returns direction at parameter value t,j
    # - `pointsOn()`: the defining points placed on the curve
    # - `parts(j,k)`:


    def __init__(self):
        if self.__class__ == Curve:
            raise ValueError("Curve can not be instantiated, use a subclass")
        super().__init__()
        self.prop = None


    @property
    def ctype(self):
        """Return the curve type

        Returns
        -------
        str
            A oneline string with the class name and important parameters.

        See Also
        --------
        report: return a full report about the curve

        Examples
        --------
        >>> C = PolyLine(Coords('012'))
        >>> print(C.ctype)
        PolyLine: nparts=2, ncoords=3, open
        >>> C = BezierSpline('012')
        >>> print(C.ctype)
        BezierSpline: degree=3, nparts=2, ncoords=7, open
        >>> C = Arc(center=[0.,0.,0.], radius=1., angles=(-90., 90.))
        >>> print(C.ctype)
        Arc: nparts=1, ncoords=3, open
        """
        s = f"{self.__class__.__name__}: "
        if hasattr(self, 'degree') and not isinstance(self, PolyLine):
            s += f"degree={self.degree}, "
        s += f"nparts={self.nparts}, ncoords={self.coords.shape[0]}, "
        s += 'closed' if self.closed else 'open'
        return s


    def report(self):
        """Return a report of the curve.

        Returns
        -------
        str
            A multiline string with the :meth:`ctype` and the full set
            of control points. This is also what is printed by the
            print statement.

        See Also
        --------
        ctype: return a one-line string with the curve type

        """
        return self.ctype + f"\n  Control points:\n{self.coords}"


    __str__ = report


    # Methods to be defined in subclasses
    def sub_points(self, t, j):
        """Return the points at parameter values t in part j

        Parameters
        ----------
        t: float or float array
            One or more parameter values at which to evaluate the point
            coordinates. Values are usually between 0.0 and 1.0.
        j: int
            Curve part index for which to find points.

        Returns
        -------
        Coords:
            The coordinates of the points on curve part `j` at parameter
            values `t`.
        """
        raise NotImplementedError

    def sub_directions(self, t, j):
        """Return the directions at parameter values t in part j

        Parameters
        ----------
        t: float or float array
            One or more parameter values at which to evaluate the curve's
            direction vector. Values are usually between 0.0 and 1.0.
        j: int
            Curve part index for which to find directions.

        Returns
        -------
        Coords:
            The direction vector(s) at parameter values `t` in curve part `j`.
        """
        raise NotImplementedError

    def parts(self, i, j):
        raise NotImplementedError

    def lengths(self, t=(0., 1.), j=None):
        raise NotImplementedError


    # Other methods
    def pointsOn(self):
        """Return the control points that are on the curve.

        Returns
        -------
        Coords
        """
        return self.coords


    def pointsOff(self):
        """Return the control points that are off the curve.

        Returns
        -------
        Coords
        """
        return Coords()


    def ncoords(self):
        """Return the total number of control points.

        Returns
        -------
        int
        """
        return self.coords.shape[0]


    def endPoints(self):
        """Return start and end points of an open curve.

        Returns
        -------
        Coords:
            A Coords with two points (the begin and end of the open curve)
            or None if the curve is closed.
        """
        if self.closed:
            return None
        else:
            return self.coords[[0, -1]]


    def charLength(self):
        """Return a characteristic length of the curve.

        This value is used in some methods to make input tolerances
        dimensionless.

        Returns
        -------
        float
            The characteristic length of the curve. If the curve defines
            a :meth:`lengths` method returning the lengths of its parts,
            this is the mean part length.
            Else, it is the :meth:`~coords.Coords.dsize` of the curve's
            :meth:`~coords.Coords.bbox`.

        Examples
        --------
        >>> PolyLine([[0.,0.,0.], [1.,0.,0.], [1.5,0.,0.]]).charLength()
        0.75
        """
        try:
            return self.lengths().mean()
        except Exception:
            return self.bbox().dsize()


    def localParam(self, u, disc=False):
        """Split global parameter value in part number and local parameter

        Each point along a Curve can be identified by a single float value
        varying from 0 at the begin point to `nparts` at the end point, where
        `nparts` is the number of parts in the curve. The integer part of
        the parameter is the part number, and the decimal part is the local
        parameter for that part, varying from 0 to 1. Input values outside
        the range [0..nparts] are allowed. Values < 0 return a negative local
        parameter on part 0, values above nparts return a value > 1 on the
        last part (nparts-1).

        Parameters
        ----------
        u: float :term:`array_like`
            One or more global parameter values, usually in the range
            0..nparts.
        disc: bool
            If True, values input values which are (very nearly) integers
            will be reported twice: once in the previous part with local
            parameter value 1., and once with the next part with local
            parameter 0. This allows processing of discontinuities at
            the part boundaries.

        Returns
        -------
        j: int array
            Array of the same length as u with the part numbers corresponding
            to the parameters t. Values are in the range 0 to nparts-1.
        t: float array
            Array of the same length as u with the local parameter value in part
            i corresponding to global parameter u. Values are in the range
            [0.0, 1.0] if input was inside 0..nparts. It is however legal to
            extend parameters before the start and after the end of the curve.

        Examples
        --------
        >>> PL = PolyLine(Coords('012'))
        >>> PL.nparts
        2
        >>> PL.localParam([0.0, 0.5, 1.0, 1.5, 2.0])
        (array([0, 0, 1, 1, 1]), array([0. , 0.5, 0. , 0.5, 1. ]))
        >>> PL.localParam([0.0, 0.5, 1.0, 1.5, 2.0], disc=True)
        (array([0, 0, 0, 1, 1, 1]), array([0. , 0.5, 1. , 0. , 0.5, 1. ]))
        >>> PL.localParam([-0.1, 1.000001, 1.999999, 2.1])
        (array([0, 1, 1, 1]), array([-0.1,  0. ,  1. ,  1.1]))
        >>> PL.localParam([-0.1, 1.000001, 1.999999, 2.1], disc=True)
        (array([0, 0, 1, 1, 1]), array([-0.1,  1. ,  0. ,  1. ,  1.1]))
        """
        # Do not use np.asarray here! We change it, so need a copy!
        t = np.array(u).astype(at.Float).ravel()
        ti = np.floor(t).clip(min=0, max=self.nparts-1)
        t -= ti
        j = ti.astype(int)
        if disc:
            atol = 1.e-5
            d = at.where_1d((t < atol) * (j > 0))
            d1 = at.where_1d(((1.0-t) < atol) * (j < self.nparts-1))
            l, l1 = len(d), len(d1)
            if l > 0:
                vj = j[d] - 1
                tj = [1.] * l
            else:
                vj = tj = []
            if l1 > 0:
                vj1 = j[d1] + 1
                tj1 = [0.] * l1
            else:
                vj1 = tj1 = []
            if l + l1 > 0:
                d = np.concatenate([d, d1])
                vj = np.concatenate([vj, vj1])
                tj = np.concatenate([tj, tj1])
                t = np.insert(t, d, tj)
                j = np.insert(j, d, vj)

        return j, t


    def pointsAt(self, u, return_position=False):
        """Return the points at parameter values t.

        Parameters
        ----------
        u: float :term:`array_like`
            One or more global parameter values, usually in the range
            0..nparts (see :meth:`localParam`)
        return_position: bool, optional
            If True, also returns the values of :meth:`localParam` for the
            given `u`.

        Returns
        -------
        coords: Coords
            The coordinates of the points on the curve corresponding with the
            parameter values u.
        j, t:
            The return values of :meth:`localParam` for the given u.
            Only returned if return_position is True.

        Examples
        --------
        >>> PL = PolyLine(Coords('012'))
        >>> PL.pointsAt([0.5, 1.5])
        Coords([[0.5, 0. , 0. ],
                [1. , 0.5, 0. ]])
        """
        j, t = self.localParam(u)
        X = Coords.concatenate([self.sub_points(ti, ji)
                                for ti, ji in zip(t, j)])
        if return_position:
            return X, j, t
        else:
            return X


    def directionsAt(self, u):
        """Return the directions at parameter values t.

        Parameters
        ----------
        u: float :term:`array_like`
            One or more global parameter values, usually in the range
            0..nparts (see :meth:`localParam`)

        Returns
        -------
        :Coords
            The unit tangent vectors to the curve at the points with
            parameter values u.

        Examples
        --------
        >>> PL = PolyLine(Coords('012'))
        >>> PL.directionsAt([0.5, 1.5])
        Coords([[1., 0., 0.],
                [0., 1., 0.]])
        """
        i, t = self.localParam(u)
        return Coords.concatenate([self.sub_directions(tj, ij)
                                   for tj, ij in zip(t, i)])


    def approx(self, nseg=None, *, ndiv=None, chordal=0.01,
               equidistant=False, npre=None, atl=None):
        """Approximate a Curve with a PolyLine

        There are three strategies to define the positions of the PolyLine
        approximation:

        - `nseg`: specify the total number of segments along the curve,
        - `ndiv`: specify the number of segments over each part of the curve,
        - `chordal`: use an adaptive method limiting the chordal distance of
          the curve to the PolyLine segments.

        Parameters
        ----------
        nseg: int
            Total number of segments of the resulting PolyLine. The number
            of returned parameter values is `nseg` if the curve is closed,
            else `nseg+1`. If provided, the `nseg` method will be used and
            `ndiv` and `chordal` are ignored.
        ndiv: int
            A single integer or a list of :attr:`nparts` integers.
            If a single integer, each part of the curve is divided in
            ndiv segments and the total number of segments is
            ``ndiv * self.nparts``. A list of integers specifies the number
            of segments for each part, and the total is the sum of the list.
            If provided (and `nseg` is not), `chordal` is ignored.
        chordal: float
            Maximum chordal error when using the chordal method
            (i.e. neither nseg nor ndiv are provided).
            The chordal error is the maximum chord to curve distance,
            relative to the curve's :meth:`charLength`.
        equidistant: bool
            Only used with the `nseg` method: if True, the nseg points are
            spread at (almost) equal distances along the curve, instead of
            at equal parameter distances.
        npre: int:
            Only used if the `chordal` method is used or if `nseg` is used
            and `equidistant` is True: the number of segments per part of
            the curve (like `ndiv`) used in a pre-approximation.
            If not provided, the default value is set to the degree of the
            curve in case of the `chordal` method, and to 100 for the
            equidistant `nseg` method (which uses the pre-approximation
            to compute accurate curve lengths).
        atl: float :term:`array_like`
            Only used with the `chordal` method: a list of parameter values
            that need to be included in the result. The list should contain
            increasing values in the curve's parameter range. It will be used
            as a start for the adaptive refining. If not provided, a default
            is used assuring that the curve is properly approximated. If you
            specify this yourself, you may end up with bad approximations due
            to bad choice of the initial values.

        Returns
        -------
        PolyLine

        See Also
        --------
        atApprox: return the parameter values yielding the PolyLine points

        Examples
        --------
        >>> C = BezierSpline([[1,0,0], [0,1,0], [-1,0,0]], degree=2)
        >>> print(C.approx(4))
        PolyLine: nparts=4, ncoords=5, open
          Control points:
        [[ 1.    0.    0.  ]
         [ 0.5   0.75  0.  ]
         [ 0.    1.    0.  ]
         [-0.5   0.75  0.  ]
         [-1.    0.    0.  ]]
        >>> print(C.approx(ndiv=2))
        PolyLine: nparts=4, ncoords=5, open
          Control points:
        [[ 1.    0.    0.  ]
         [ 0.5   0.75  0.  ]
         [ 0.    1.    0.  ]
         [-0.5   0.75  0.  ]
         [-1.    0.    0.  ]]
        >>> print(C.approx(chordal=0.2))
        PolyLine: nparts=4, ncoords=5, open
          Control points:
        [[ 1.    0.    0.  ]
         [ 0.5   0.75  0.  ]
         [ 0.    1.    0.  ]
         [-0.5   0.75  0.  ]
         [-1.    0.    0.  ]]

        """
        atl = self.atApprox(nseg, ndiv, chordal, equidistant, npre, atl)
        return self.approxAt(atl)


    def _at_approx(self, nseg=None, ndiv=None, equidistant=False, npre=None):
        """Implementation of nseg and ndiv methods for atApprox."""
        if ndiv is not None:
            if at.isInt(ndiv):
                nseg = ndiv * self.nparts
                ndiv = None
            equidistant = False
        if equidistant:
            if npre is None:
                npre = 100
            S = self.approx(ndiv=npre)
            atl = S.atLength(nseg) / npre
        elif ndiv is not None:
            atl = np.concatenate([[0.]] + [i + at.unitDivisor(n)[1:]
                                           for i, n in enumerate(ndiv)])
        else:
            if nseg is None:
                nseg = self.nparts
            atl = np.arange(nseg+1) * float(self.nparts) / nseg
        return atl


    def _at_chordal(self, chordal, atl=None):
        """Implementation of chordal method for atApprox."""
        # Create first approximation
        if atl is None:
            if hasattr(self, 'degree'):
                ndiv = self.degree
            else:
                ndiv = 1
            atl = self._at_approx(nseg=ndiv*self.nparts)
        charlen = self.approxAt(atl).charLength()
        # Split in handled and to-be-handled
        atl, bt = list(atl[:1]), list(atl[1:])
        # Handle segment by segment
        #
        # TODO: THIS SHOULD BE CHANGED:
        #    insert NO points of degree 1 (always correct)
        #    insert 1 point at 1/2 for degree 2  (current implementation)
        #    insert 2 points at 1/3 and 2/3 for degree 3
        #    etc...
        #
        while len(bt) > 0:
            c0, c2 = atl[-1], bt[0]
            if c2 > c0:
                c1 = 0.5*(c0+c2)
                X = self.pointsAt([c0, c1, c2])
                XM = 0.5*(X[0]+X[2])
                d = at.length(X[1]-XM) / charlen

                if d >= chordal:
                    # need refinement: put new point in front of todo list
                    bt = [c1] + bt
                    continue
            # move on
            atl.append(bt.pop(0))
        return atl


    def atApprox(self, nseg=None, ndiv=None, chordal=0.02,
                 equidistant=False, npre=None, atl=None):
        """Return parameter values for approximating a Curve with a PolyLine.

        The parameters are the same as for :meth:`approx`

        Returns
        -------
        array
            A list of parameter values that define the positions of
            the point of the PolyLine approximation of the curve
            using the same parameter values.

        See Also
        --------
        approx: return a PolyLine approximation of a Curve.

        Examples
        --------
        >>> PL = PolyLine([[0,0,0],[1,0,0],[1,1,0]])
        >>> print(PL.atApprox(nseg=6))
        [0.    0.333 0.667 1.    1.333 1.667 2.   ]
        >>> print(PL.atApprox(ndiv=3))
        [0.    0.333 0.667 1.    1.333 1.667 2.   ]
        >>> print(PL.atApprox(ndiv=(2,4)))
        [0.   0.5  1.   1.25 1.5  1.75 2.  ]
        >>> print(PL.atApprox(ndiv=(2,)))
        [0.  0.5 1. ]
        """
        if nseg or ndiv:
            atl = self._at_approx(nseg, ndiv, equidistant, npre)
        else:
            atl = self._at_chordal(chordal, atl)
        if self.closed and atl[0] == 0. and atl[-1] == float(self.nparts):
            # Avoid having the endpoint twice
            atl = atl[:-1]
        return atl


    def approxAt(self, u):
        """Create a PolyLine approximation with specified parameter values.

        Parameters
        ----------
        u: :term:`array_like`
            A list of global parameter values for the curve, usually in the
            curve's parameter range. Values outside the range will extend the
            curve.

        Returns
        -------
        PolyLine
            A PolyLine connecting the points on the curve at the specified
            parameter values.

        See Also
        --------
        atApprox: convenient methods to compute the parameter values
        approx: PolyLine approximation with parameter values from atApprox

        Examples
        --------
        >>> C = BezierSpline([[1,0,0], [0,1,0], [-1,0,0]], degree=2)
        >>> PL = C.approxAt([0.0, 1.0, 2.0])
        >>> print(PL)
        PolyLine: nparts=2, ncoords=3, open
          Control points:
        [[ 1.  0.  0.]
         [ 0.  1.  0.]
         [-1.  0.  0.]]
        >>> C.approxAt([0.0, 0.5, 1.0]).coords
        Coords([[1.  , 0.  , 0.  ],
                [0.5 , 0.75, 0.  ],
                [0.  , 1.  , 0.  ]])
        """
        X = self.pointsAt(u)
        PL = PolyLine(X, closed=self.closed)
        return PL.setProp(self.prop)


    def length(self, u0=None, u1=None):
        """Return the length of the curve between two parameter values.

        Parameters
        ----------
        u0: float
            Global parameter value from where to measure length. If not
            provided, it is set to the start of the curve (0.).
        u1: float
            Global parameter value until where to measure length. If not
            provided, it is set to the end of the curve (self.nparts).

        Returns
        -------
        float
            The length of the curve between the specified parameter values.
            Without parameters, the full length of the curve.

        Notes
        -----
        This is only available for curves that implement the 'lengths'
        method.

        Examples
        --------
        >>> C = BezierSpline('1234', degree=2)
        >>> C.length()
        3.23...
        >>> C.length(u1=1.5)
        1.61...
        >>> C.length(0.5, 2.5)
        1.95...
        """
        if u0 is None and u1 is None:
            return self.lengths().sum()
        if u0 is None:
            u0 = 0.
        if u1 is None:
            u1 = self.nparts
        if u1 < u0:
            return 0.
        i, r = self.localParam(u0)
        j, s = self.localParam(u1)
        l0 = self.lengths(t=(r, 1.), j=i)
        l1 = self.lengths(j=np.arange(i+1, j))
        l2 = self.lengths(t=(0., s), j=j)
        return np.concatenate([l0, l1, l2]).sum()


    # TODO: compute correct results and add an algorithm to fix
    #       disc, nans, flips
    def frenet(self, ndiv=None, nseg=None, chordal=0.01, upvector=None,
               avgdir=True, compensate=False):
        """Return points and Frenet frame along the curve.

        First, a PolyLine approximation for the curve is constructed, using the
        :meth:`Curve.approx()` method with the arguments `ndiv`, `nseg`
        and `chordal`.
        Then Frenet frames are constructed with :meth:`PolyLine._movingFrenet`
        using the remaining arguments.
        The resulting PolyLine points and Frenet frames are returned.
        The PolyLine polygon approximation,limits the accuracy. More accurate
        results can be obtained by converting the Curve to a :class:`NurbsCurve`
        and using its :meth:`plugins.nurbs.NurbsCurve.frenet` method.
        That one however has currently no discontinuity smoothing
        (discontinuous tangents at sharp corners, undetermined normals at zero
        curvature, binormal flips).

        Parameters
        ----------
        upvector: float (3,) vector
            A vector normal to the (tangent,normal) plane at the first point
            of the curve. It defines the binormal at the first point.
            If not provided it is set to the shortest distance through
            the set of 10 first points.
        avgdir: bool | array.
            If True (default), the tangential vector is set to
            the average direction of the two segments ending at a node.
            If False, the tangent vectors will be those of the line segment
            starting at the points.
            The tangential vector can also be set by the user by specifying
            an array with the matching number of vectors.
        compensate: bool
            If True, adds a compensation algorithm if the curve is closed.
            For a closed curve the moving Frenet algorithm can be continued
            back to the first point. If the resulting binormal does not
            coincide with the starting one, some torsion is added to the end
            portions of the curve to make the two binormals coincide.

            This feature is off by default because it is currently experimental
            and is likely to change in future.
            It may also form the base for setting the starting as well as the
            ending binormal.

        Returns
        -------
        X: :class:`Coords` (npts,3)
            The coordinates of `npts` points on the curve.
        T: :class:`Coords` (npts,3)
            The normalized tangent vectors to the curve at the points `X`.
        N: :class:`Coords` (npts,3)
            The normalized normal vectors to the curve at the points `X`.
        B: :class:`Coords` (npts,3)
            The normalized binormal vector to the curve at the points `X`.

        Notes
        -----

        """
        PL = self.approx(ndiv=ndiv, nseg=nseg, chordal=chordal)
        X = PL.coords
        T, N, B = PL._movingFrenet(upvector=upvector, avgdir=avgdir,
                                   compensate=compensate)
        return X, T, N, B


    # TODO: This should use more accurate frenet when it has smoothing
    def position(self, geom, csys=None):
        """ Position a Geometry object along a path.

        Creates copies of geom along a curve, orienting it according to
        the :meth:`frenet` frame.

        Parameters
        ----------
        geom: :class:`Geometry` | :class:`Coords`
            The geometry to position
        csys: :class:`CoordSys`
            The coordinate system that will be positioned along the
            frenet axes. If not provided, the global axes are used.

        Returns
        -------
        list
            A list of Geometry/Coords objects properly positioned and
            oriented along the curve.
        """
        X, T, N, B = self.frenet()
        if csys:
            geom = geom.fromCS(csys)
        return [geom.fromCS(CoordSys(rot=np.row_stack([t, n, b]), trl=x))
                for x, t, n, b in zip(X, T, N, B)]


    # TODO: This should be removed in favor of a Mesh.sweep using position
    def sweep(self, mesh, eltype=None, csys=None):
        """Sweep a mesh along the curve, creating an extrusion.

        Copies of the input mesh are :meth:`position` -ed along the curve
        and then :meth:`~mesh.Mesh.connect` -ing them into an extrusion.

        Parameters
        ----------
        mesh: :class:`Mesh`
            The (usually planar) mesh that is to be swept along the curve.
            It should be a Mesh or an object having a `toMesh` method to
            transform it into a Mesh.
        eltype: str
            The name of the target element type of the returned Mesh.
            If not provided, it is determined from extruding the `mesh`
            eltype.
        csys: :class:`CoordSys`
            The coordinate system that will be positioned along the
            :meth:`frenet` axes. If not provided, the global axes are used.

        Returns
        -------
        Mesh
            The Mesh obtained by sweeping the input mesh along the curve.
            This involves :meth:`position` -ing copies of the input Mesh
            along the curve,

            The returned Mesh has double plexitude of the original.
            If `path` is a closed Curve connect back to the first.

        .. note:: Sweeping nonplanar objects and/or sweeping along very curly
           curves may result in physically impossible geometries.

        See Also
        --------
        sweep2
        """
        loop = self.closed
        mesh = mesh.toMesh()
        seq = self.position(mesh.coords, csys)
        return mesh.connect(seq, eltype=eltype, loop=loop)


    # TODO: This should be merged with position if it is to be kept
    # Better however to use frenet positioning
    def position2(self, objects, normal=0, upvector=2, avgdir=True,
                  enddir=None):
        """ Position a sequence of Coords objects along a path.

        At each point of the curve, a copy of the Coords object is created, with
        its origin in the curve's point, and its normal along the curve's direction.
        In case of a PolyLine, directions are pointing to the next point by default.
        If avgdir==True, average directions are taken at the intermediate points
        avgdir can also be an array like sequence of shape (N,3) to explicitely set
        the directions for ALL the points of the path

        Missing end directions can explicitely be set by enddir, and are by default
        taken along the last segment.
        enddir is a list of 2 array like values of shape (3). one of the two can
        also be an empty list.
        If the curve is closed, endpoints are treated as any intermediate point,
        and the user should normally not specify enddir.

        The return value is a sequence of the repositioned Coords objects.
        """
        points = self.coords
        if isinstance(avgdir, bool):
            if avgdir:
                directions = self.avgDirections()
            else:
                directions = self.directions()
        else:
            directions = np.asarray(avgdir).reshape(len(avgdir), -1)

        missing = points.shape[0] - directions.shape[0]
        if missing == 1:
            lastdir = (points[-1] - points[-2]).reshape(1, 3)
            directions = np.concatenate([directions, lastdir], axis=0)
        elif missing == 2:
            lastdir = (points[-1] - points[-2]).reshape(1, 3)
            firstdir = (points[1] - points[0]).reshape(1, 3)
            directions = np.concatenate([firstdir, directions, lastdir], axis=0)

        if enddir:
            for i, j in enumerate([0, -1]):
                if enddir[i]:
                    directions[j] = Coords(enddir[i])

        directions = at.normalize(directions)

        if at.isInt(normal):
            normal = Coords(at.unitVector(normal))

        if at.isInt(upvector):
            upvector = Coords(at.unitVector(upvector))

        sequence = [x.rotate(at.rotMatrix2(normal, d, upvector)).translate(p)
                    for x, d, p in zip(objects, directions, points)]

        return sequence


    # TODO: this should be merged into position2.
    def sweep2(self, coords, origin=(0., 0., 0.), scale=None, **kargs):
        """ Sweep a Coords object along a curve, returning a series of copies.

        At each point of the curve a copy of the coords is created,
        possibly scaled, and rotated to keep same orientation with
        respect to the curve.

        Parameters
        ----------
        coords: Coords object
            The Coords object to be copied, possibly scaled and positioned
            at each point of the curve.
        origin: float :term:`array_like` (3,)
            The local origin in the Coords. This is the point that will
            be positioned at the curve's points. It is also the center of
            scaling if `scale` is provided.
        scale: float :term:`array_like`, optional
            If provided, it should have the shape (npts,3). For each point
            of the curve, it specifies the three scaling factors to be used
            in the three coordinate directions on the `coords` for the copy
            that is to be plavced at that point.
        **kargs: optional keyword arguments
            Extra keyword arguments that are passed to :meth:`position2`.

        Returns
        -------
        A sequence of the transformed Coords objects.

        See Also
        --------
        sweep

        """
        if scale is not None:
            scale = at.checkArray(scale, shape=(self.ncoords(), 3),
                                  kind='f', allow='i')
        # translate input coords to origin
        base = coords.translate(-Coords(origin))
        # create the scaled copies
        if scale is not None:
            sequence = (base.scale(*sc) for sc in scale)
        else:
            sequence = (base, ) * self.ncoords()
        # position the copies at the curve's points
        sequence = self.position2(sequence, **kargs)
        return sequence


    # DEVS: we have an actor to draw curves with a higher accuracy
    #       than the default toMesh() would have
    #       (until we have better line3/line4 drawing
    def actor(self, **kargs):
        """Create an actor to draw the Curve."""
        G = self.approx().toMesh()
        G.attrib(**self.attrib)
        return G.actor(**kargs)


    def toNurbs(self):
        """Convert a curve to a NurbsCurve.

        Returns
        -------
        NurbsCurve
            A :class:`plugins.nurbs.nurbscurve` equivalent with the
            input Curve. This is currently only implemented for
            BezierSpline and PolyLine.
        """
        from pyformex.plugins.nurbs import NurbsCurve
        if isinstance(self, (BezierSpline, PolyLine)):
            return NurbsCurve(self.coords, degree=self.degree,
                              closed=self.closed, blended=False)
        else:
            raise ValueError(f"A curve of type {self.__class__.__name__}"
                             " can not (yet) be converted to NurbsCurve")


    def setProp(self, prop=None):
        """Create or destroy the property number for the Curve.

        A curve can have a single integer as property number.
        If it is set, derived curves and approximations will inherit it.
        Use this method to set or remove the property.

        Parameters
        ----------
        prop: int
            The int value to set as the curve's prop number. If None,
            the prop is removed from the Curve.

        Returns
        -------
        self
            The curve itself with the property set or removed.
        """
        try:
            self.prop = int(prop)
        except Exception:
            self.prop = None
        return self


    # TODO: remove in 3.3
    # Deprecated 2022-09-28. Kept for compatibility/convenience
    utils.deprecated_by('Curve.totalLength', 'Curve.length')
    def totalLength(self, t0, t1):
        return self.length(u0=t0, u1=t1)

    # TODO: remove in 3.3
    # Deprecated 2022-09-08. Kept for compatibility/convenience
    utils.deprecated_by('Curve.approximate', 'Curve.approx')
    def approximate(self, *args, **kargs):
        return self.approx(*args, **kargs)

    # TODO: remove in 3.3
    # Deprecated 2022-09-08.
    # Kept for extend parameter, until Curve.extend is implemented
    utils.deprecated_by('Curve.subPoints', 'Curve.pointsAt(Curve.atApprox)')
    def subPoints(self, div=10, extend=[0., 0.]):
        C = self.extend(*extend)
        return C.pointsAt(C.atApprox(ndiv=div))


##############################################################################
#
#  BezierSpline
#
##############################################################################


@utils.pzf_register
class BezierSpline(Curve):
    """A class representing a Bezier spline curve of degree 1, 2, 3 or higher.

    A BezierSpline of degree `d` is a continuous curve consisting of `nparts`
    successive Bezier curves of the same degree. Successive means that the
    end point of one curve is also the starting point of the next curve.

    A Bezier curve of degree d is determined by d+1 control points,
    of which the first and the last are on the curve (the endpoints),
    and the intermediate d-1 points are not.
    Since the end point of one part is the starting point of the next part,
    a BezierSpline is described by ``ncontrol = d * nparts + 1`` control
    points. The number of points on the curve is ``npoints = nparts + 1``.

    The above holds for open curves. The BezierSpline class however
    distinguishes between open and closed curves. In a closed curve,
    the last point coincides with the first, and is not stored. If the
    last point is needed, it is obtained by wrapping around back to the
    first point. An open curve however may also have a last point coinciding
    with the first, so that the curve looks closed, but technically it remains
    an open curve.

    The BezierSpline class provides ways to create a full set of
    control points. Often the off-curve control points can be
    generated automatically. The default degree (3) generates them from
    the requirement that the curve should be smooth, i.e. have a
    continuous tangent vector when moving from one part to the next.

    Therefore there are basically two ways to create a BezierSpline:
    by specifying all control points, or by specifying only the points
    through which the curve should pass (and possibly the tangents at
    those points). The difference is made clear by using either the
    ``control`` or the ``coords`` parameter. Because in most quick
    application cases the use of the ``coords`` option is the likely
    choice, that parameter is made the (only) positional one.
    The ``coords`` and ``control`` parameters are mutually exclusive, but
    at least one of them must be used.
    Historically, there was an option to use both ``coords`` and ``control``
    parameters, with the latter then only specifying the off-curve points,
    but this use case is now prohibited. See Notes for how to work around it.

    Parameters
    ----------
    coords: :term:`coords_like` (npoints, 3), optional
        A set of points through which the curve should pass. The number
        of points should at least be 2. An interpolation BezierSpline
        of the requested degree is then constructed. The result can be
        tuned by other parameters (``tangents``, ``curl``).
        This is the only parameter that is allowed as a positional parameter
        It can not be combined with the ``control`` parameter. It can also
        not be used for degrees > 3 (which are seldomly used).
    control: :term:`coords_like` (ntrl, 3)
        The complete set of control points that define the BezierSpline.
        The number of points (nctrl) should be a multiple of degree, plus 1.
        This parameter can not be used if ``coords`` was provided.
    degree: int
        The polynomial degree of the curve. The default value is 3.
        For curves of degree 1, the specialized :class:`PolyLine` subclass
        may be more appropriate. For curves of degree 4 or higher the use of a
        :class:`~plugins.nurbs.NurbsCurve` may be prefered.
    closed: bool
        If True, a closed curve is created. If the distance from
        the last point to the first is less than ``tol``, the last point
        is removed and the last segment is created between the penultimate
        point and the first point. Else, a segment is created between the
        last point and the first.
    tol: float, optional
        Tolerance used in testing for end point coincidence when creating
        a closed curve. Only used if `closed=True`. If the distance
        between the end points is less than `tol`, they are considered
        coincident. Else, an extra curve segment is created between the
        last and the first point. A value `0.0` will force the creation
        of a extra segment. A value `np.inf` will never create an extra
        segment. If not provided, a default value
        ``1.e-5 * coords.dsize()`` is used. This value ensures expected
        behavior in most use cases.
    tangents: :term:`coords_like` (npts, 3) or (2, 3), optional
        The imposed tangent vectors to the curve at the specified points
        ``coords``. Can only be used with degree 2 or 3.
        The number of tangents should be equal to the number of points
        (after possibly removing one point for a closed curve).
        As a convenience, the tangents array may contain just two vectors
        if only the end tangents need to be specified.
        The provided vectors will get normalized, so their length is irrelevant.
        If not provided, ``tangents`` is set equal to
        ``PolyLine(coords).avgDirections()``.
        The tangents array can contain np.nan values for points were the
        user does not want to prescribe a tangent direction. These will also
        be filled in with values from ``PolyLine(coords).avgDirections()``
    curl: float, optional
        The curl parameter can be set to influence the curliness of the curve
        between two subsequent curve endpoints. A value curl=0.0 results in
        straight segments. The higher the value, the more the curve becomes
        curled. Can only be used with degree 3.
    kargs: deprecated keyword arguments
        For compatibility of legacy code, the 'tangents' parameter may
        also be called 'deriv'.

    Returns
    -------
    BezierSpline
        A BezierSpline of the requested degree, passing through all points
        ``coords``. If the degree is 3, or the degree is 2 and all points
        are lying in the same plane, the curve will have the provided (or
        computed) tangents at the given points. If the degree is 2 and the
        points are not coplanar, the curve may have discontinuities in the
        tangent at the points.

    See Also
    --------
    :class:`PolyLine`: a BezierSpline of degree 1 with more specialized methods
    :class:`~plugins.nurbs.NurbsCurve`: Industry standard curves with a finer
        control of smoothness.

    Notes
    -----
    The combined use of coords and control is no longer permitted.
    For such cases one can use the arraytools.interleave function to combine
    them into a single full set of control points. Thus, instead of::

        BezierSpline(coords=Q, control=R, degree=2)
        BezierSpline(coords=Q, control=R, degree=3)

    use::

        BezierSpline(control=at.interleave(Q, R[:,0]), degree=2)
        BezierSpline(control=at.interleave(Q, R[:,0], R[:,1]), degree=3)

    Examples
    --------
    >>> B = BezierSpline('0123')
    >>> print(B)
    BezierSpline: degree=3, nparts=3, ncoords=10, open
      Control points:
    [[ 0.     0.     0.   ]
     [ 0.316 -0.105  0.   ]
     [ 0.764 -0.236  0.   ]
     [ 1.     0.     0.   ]
     [ 1.236  0.236  0.   ]
     [ 1.236  0.764  0.   ]
     [ 1.     1.     0.   ]
     [ 0.764  1.236  0.   ]
     [ 0.316  1.105  0.   ]
     [ 0.     1.     0.   ]]
    >>> print(B.pointsOn())
    [[0. 0. 0.]
     [1. 0. 0.]
     [1. 1. 0.]
     [0. 1. 0.]]
    >>> print(B.pointsOff())
    [[[ 0.316 -0.105  0.   ]
      [ 0.764 -0.236  0.   ]]
    <BLANKLINE>
     [[ 1.236  0.236  0.   ]
      [ 1.236  0.764  0.   ]]
    <BLANKLINE>
     [[ 0.764  1.236  0.   ]
      [ 0.316  1.105  0.   ]]]
    >>> print(B.points(1))
    [[1.    0.    0.   ]
     [1.236 0.236 0.   ]
     [1.236 0.764 0.   ]
     [1.    1.    0.   ]]
    >>> B = BezierSpline('0123', degree=1)
    >>> print(B)
    BezierSpline: degree=1, nparts=3, ncoords=4, open
      Control points:
    [[0. 0. 0.]
     [1. 0. 0.]
     [1. 1. 0.]
     [0. 1. 0.]]
    >>> B = BezierSpline('0123', degree=1, closed=True)
    >>> print(B.ctype)
    BezierSpline: degree=1, nparts=4, ncoords=4, closed
    """
    def __init__(self, coords=None, *, control=None, degree=3, closed=False,
                 tol=None, tangents=None, curl=1/3, **kargs):
        """Create a BezierSpline curve."""
        super().__init__()

        if degree <= 0:
            raise ValueError("Degree of BezierSpline should be > 0!")

        if coords is None:
            # control points are specified
            control = Coords(control)
            if control.ndim != 2:
                raise ValueError("The control parameter should be a 2-dim array")
            # TODO: check number of control points
            # TODO: if the interpolate functions work with the extra point,
            #       we could move this below.
            if closed:
                if tol is None:
                    tol = 1.e-5 * control.dsize()
                if at.length(control[0] - control[-1]) < tol:
                    control = control[:-1]
        else:
            # interpolate: control points are to be computed
            coords = Coords(coords)
            if coords.ndim != 2:
                raise ValueError("Coords(npts,3) required.")
            ncoords = coords.shape[0]
            if ncoords < 2:
                raise ValueError("Need at least two points to create a curve")
            if closed:
                if tol is None:
                    tol = 1.e-5 * coords.dsize()
                if at.length(coords[0] - coords[-1]) < tol:
                    coords = coords[:-1]
            if 'deriv' in kargs:
                # Deprecated deriv but still accepting
                utils.warn('depr_bezierspline_deriv')
                tangents = kargs.pop('deriv')
            if kargs:
                raise ValueError(f"Unknown parameter(s): {list(kargs.keys())}")
            if degree == 1:
                control = coords
            elif degree == 2:
                control = _quadratic_bezier_interpolate(
                    coords, tangents, closed=closed)
            elif degree == 3:
                control = _cubic_bezier_interpolate(
                    coords, tangents, closed=closed, curl=curl)
            else:
                raise ValueError(
                    "The coords parameter can only be used with degree <=3")
        self.degree = degree
        self.coeffs = bezierPowerMatrix(degree)
        self.coords = control
        self.closed = closed


    @property
    def nparts(self):
        """The number of parts in the BezierSpline"""
        n = self.coords.shape[0]
        if self.closed or self.degree > 1:
            return n // self.degree
        else:
            return n - 1


    @property
    def npoints(self):
        """The number of oncurve points in the BezierSpline

        This is equal to the number of parts if the curve is closed;
        else, it is one more.
        """
        n = self.nparts
        return n if self.closed else n + 1


    def pointsOn(self):
        """Return the control points that are on the curve.

        Returns
        -------
        :class:`~coords.Coords` (nparts+1, 3):
            The coordinates of the nparts+1 points on the curve.
            For a closed curve, the last point will be equal to the first.
        """
        return self.coords[::self.degree]


    def pointsOff(self):
        """Return the control points that are off the curve.

        Returns
        -------
        :class:`~coords.Coords` (nparts, degree-1, 3):
            The coordinates of the intermediary control points for the
            nparts in dividual Bezier curves. For degree=1, an empty Coords
            is returned.
        """
        if self.degree > 1:
            return self.coords[:-1].reshape(-1, self.degree, 3)[:, 1:]
        else:
            return Coords()


    def points(self, j=None, k=None):
        """Return the point sequence defining parts j to k of the curve.

        The returned points sequence can be used to create a curve
        identical to the parts j:k of the curve.

        Parameters
        ----------
        j: int
            The first (or only) part to return. The value should be in
            the range 0..nparts. If not provided, all points are returned.
        k: int, optional
            One more than the last part to return. Its value should be in
            the range 1..nparts+1. For an open curve, k should be > j. For
            a closed curve, k <= j is allowed to take a points spanning
            the first/last point.
            If not provided, k is set to j+1, resulting in the points for
            a single part.

        Returns
        -------
        :class:`~coords.Coords` ((k-j)*degree+1, 3)
            The sequence of points from self.coords that define parts j to k
            of the curve.

        See Also
        --------
        part_points: return an array of single part points
        parts: return a curve identical to parts j:k

        Examples
        --------
        >>> C = BezierSpline('1234', degree=2)
        >>> print(C.coords)
        [[ 1.    0.    0.  ]
         [ 1.25  0.75  0.  ]
         [ 1.    1.    0.  ]
         [ 0.5   1.5   0.  ]
         [ 0.    1.    0.  ]
         [-0.25  0.75  0.  ]
         [ 0.    0.    0.  ]]
        >>> print(C.points(0))
        [[1.   0.   0.  ]
         [1.25 0.75 0.  ]
         [1.   1.   0.  ]]
        >>> print(C.points(1,3))
        [[ 1.    1.    0.  ]
         [ 0.5   1.5   0.  ]
         [ 0.    1.    0.  ]
         [-0.25  0.75  0.  ]
         [ 0.    0.    0.  ]]

        Notice the difference with :meth:`part_points`:

        >>> print(C.part_points([1,2]))
        [[[ 1.    1.    0.  ]
          [ 0.5   1.5   0.  ]
          [ 0.    1.    0.  ]]
        <BLANKLINE>
         [[ 0.    1.    0.  ]
          [-0.25  0.75  0.  ]
          [ 0.    0.    0.  ]]]

        Closed curve example:

        >>> C = BezierSpline('1234', degree=2, closed=True)
        >>> print(C.coords)
        [[ 1.   0.   0. ]
         [ 1.5  0.5  0. ]
         [ 1.   1.   0. ]
         [ 0.5  1.5  0. ]
         [ 0.   1.   0. ]
         [-0.5  0.5  0. ]
         [ 0.   0.   0. ]
         [ 0.5 -0.5  0. ]]
        >>> print(C.points(0))
        [[1.  0.  0. ]
         [1.5 0.5 0. ]
         [1.  1.  0. ]]
        >>> print(C.points(3,1))
        [[ 0.   0.   0. ]
         [ 0.5 -0.5  0. ]
         [ 1.   0.   0. ]
         [ 1.5  0.5  0. ]
         [ 1.   1.   0. ]]
        """
        if j is None:
            return self.coords
        if k is None:
            k = j + 1
        if j < 0 or k < 0 or j > self.nparts or k > self.nparts:
            raise ValueError(
                f"j, k-1 should be in range(0,nparts) with nparts={self.nparts}")
        degree = self.degree
        start = degree * j
        end = degree * k + 1
        if self.closed:
            npoints = self.ncoords()
            if end > npoints:
                end %= npoints
            if k <= j or end == 1:
                # this works whether the last point of a closed curve
                # is stored or not.
                # Note: this is faster than a roll + single take
                end1 = degree * self.nparts
                coords = Coords.concatenate([
                    self.coords[start:end1], self.coords[:end]])
            else:
                coords = self.coords[start:end]
        else:
            if k <= j:
                raise ValueError("Open curves require k > j.")
            coords = self.coords[start:end]
        return coords


    def split(self, split=None):
        """Split a curve into a list of partial curves

        Parameters
        ----------
        split: list(int)
            A list of integer values specifying the point numbers
            where the curve is to be split. As a convenience, a single int may
            be given if the curve is to be split only at a single point,
            or None, to split at all nodes.

        Returns
        -------
        list
            A list of open curves of the same type as the original. Together,
            the curves cover the original curve.

        Notes
        -----
        Only multipart curves can be split.
        Splitting a closed curve at a single point creates a single open curve
        with begin/end at the split point.

        Examples
        --------
        >>> PL = PolyLine(Coords('0123'))
        >>> for PLi in PL.split(): print(PLi)
        PolyLine: nparts=1, ncoords=2, open
          Control points:
        [[0. 0. 0.]
         [1. 0. 0.]]
        PolyLine: nparts=1, ncoords=2, open
          Control points:
        [[1. 0. 0.]
         [1. 1. 0.]]
        PolyLine: nparts=1, ncoords=2, open
          Control points:
        [[1. 1. 0.]
         [0. 1. 0.]]
        """
        if not hasattr(self, 'parts'):
            raise ValueError(
                f"Curves of type {self.__class__.__name__} can not be split")

        if split is None:
            split = np.arange(1, self.nparts)
        else:
            if at.isInt(split):
                split = [split]
            split = np.unique(split)
        if len(split) == 0:
            return [self.copy()]
        if self.closed:
            if split[-1] != split[0]+self.nparts:
                split = np.concatenate([split, [split[0]]])
        else:
            if split[0] != 0:
                split = np.concatenate([[0], split])
            if split[-1] != self.nparts:
                split = np.concatenate([split, [self.nparts]])
        return [self.parts(j, k) for j, k in zip(split[:-1], split[1:])]


    def parts(self, j, k):
        """Return a curve containing only parts j to k.

        Parameters
        ----------
        j: int
            The first part to include in the new curve. The value should be in
            range(0,nparts).
        k: int
            One more than the last part to include.

        Returns
        -------
        BezierSpline
            An open BezierSpline of the same degree as the input curve,
            containing only the parts j..k of it.

        Examples
        --------
        >>> PL = PolyLine(Coords('0123'))
        >>> print(PL.ctype)
        PolyLine: nparts=3, ncoords=4, open
        >>> print(PL.parts(1,3))
        PolyLine: nparts=2, ncoords=3, open
          Control points:
        [[1. 0. 0.]
         [1. 1. 0.]
         [0. 1. 0.]]
        >>> PLC = PL.close()
        >>> print(PLC)
        PolyLine: nparts=4, ncoords=4, closed
          Control points:
        [[0. 0. 0.]
         [1. 0. 0.]
         [1. 1. 0.]
         [0. 1. 0.]]
        >>> print(PLC.ctype)
        PolyLine: nparts=4, ncoords=4, closed
        >>> print(PLC.parts(3,1))
        PolyLine: nparts=2, ncoords=3, open
          Control points:
        [[0. 1. 0.]
         [0. 0. 0.]
         [1. 0. 0.]]
        >>> print(PLC.parts(0,1))
        PolyLine: nparts=1, ncoords=2, open
          Control points:
        [[0. 0. 0.]
         [1. 0. 0.]]

        """
        return self.__class__(control=self.points(j, k), degree=self.degree)


    def part_points(self, j=None):
        """Return the defining points for parts j.

        Parameters
        ----------
        j: int | int :term:`array_like`
            The part number(s)for which to return the defining points.
            If not provided, all parts are returned.

        Returns
        -------
        :class:`~coords.Coords`
            The coordinates of the points defining each of the parts j
            of the curve. If j is a single int, the shape of the Coords
            (degree+1, 3), else it is (len(j), degree+1, 3).

        See Also
        --------
        points: return a single sequence of points for parts j to k

        Examples
        --------
        >>> C = BezierSpline('1234', degree=2)
        >>> print(C.coords)
        [[ 1.    0.    0.  ]
         [ 1.25  0.75  0.  ]
         [ 1.    1.    0.  ]
         [ 0.5   1.5   0.  ]
         [ 0.    1.    0.  ]
         [-0.25  0.75  0.  ]
         [ 0.    0.    0.  ]]
        >>> print(C.part_points(0))
        [[1.   0.   0.  ]
         [1.25 0.75 0.  ]
         [1.   1.   0.  ]]
        >>> print(C.part_points([2,0]))
        [[[ 0.    1.    0.  ]
          [-0.25  0.75  0.  ]
          [ 0.    0.    0.  ]]
        <BLANKLINE>
         [[ 1.    0.    0.  ]
          [ 1.25  0.75  0.  ]
          [ 1.    1.    0.  ]]]
        """
        if j is None:
            j = np.arange(self.nparts)
        if np.isscalar(j):
            return self.points(j)
        else:
            j = np.asarray(j).reshape(-1)  # force a 1-d array
            return np.stack([self.points(i) for i in j])


    def sub_points(self, t, j=None):
        """Return points on the curve at parameter values t in part(s) j.

        Parameters
        ----------
        t: float :term:`array_like`
            Local parameter values (usually in the range 0.0..1.0) of
            the points to return.
        j: int or int :term:`array_like`
            The part number(s)for which to return points.
            If not provided, points on all parts are returned.

        Returns
        -------
        :class:`~coords.Coords`
            The coordinates of the points on the curve at local parameter
            values t of the parts j. The shape of the Coords is (len(t), 3)
            if j is a single int, else the shape is (len(j), len(t), 3).

        Examples
        --------
        >>> C = BezierSpline('1234', degree=2)
        >>> C.sub_points([0.0, 0.2, 0.5])
        Coords([[[ 1.   ,  0.   ,  0.   ],
                 [ 1.08 ,  0.28 ,  0.   ],
                 [ 1.125,  0.625,  0.   ]],
        <BLANKLINE>
                [[ 1.   ,  1.   ,  0.   ],
                 [ 0.8  ,  1.16 ,  0.   ],
                 [ 0.5  ,  1.25 ,  0.   ]],
        <BLANKLINE>
                [[ 0.   ,  1.   ,  0.   ],
                 [-0.08 ,  0.88 ,  0.   ],
                 [-0.125,  0.625,  0.   ]]])
        >>> C.sub_points([0.0, 0.2, 0.5], 1)
        Coords([[1.  , 1.  , 0.  ],
                [0.8 , 1.16, 0.  ],
                [0.5 , 1.25, 0.  ]])
        >>> C.sub_points([0.0, 0.2, 0.5], [1, 0])
        Coords([[[1.   , 1.   , 0.   ],
                 [0.8  , 1.16 , 0.   ],
                 [0.5  , 1.25 , 0.   ]],
        <BLANKLINE>
                [[1.   , 0.   , 0.   ],
                 [1.08 , 0.28 , 0.   ],
                 [1.125, 0.625, 0.   ]]])
        """
        t = np.asarray(t).reshape(-1)
        P = self.part_points(j)
        C = np.dot(self.coeffs, P)
        if C.ndim > 2:
            C = C.transpose(1, 0, 2)
        U = [t**d for d in range(0, self.degree+1)]
        U = np.column_stack(U)
        X = np.dot(U, C)
        if X.ndim > 2:
            X = X.transpose(1, 0, 2)
        return Coords(X)


    def sub_directions(self, t, j=None):
        """Return the unit direction vectors at values t in part j.

        Parameters
        ----------
        t: float :term:`array_like`
            Local parameter values (usually in the range 0.0..1.0) of
            the points at which to find the direction vector.
        j: int or int :term:`array_like`
            The part number(s) for which to return directions.
            If not provided, directions for t on all parts are returned.

        Returns
        -------
        :class:`array`
            The unit direction vectors of the curve at the points with local
            parameter values t on the parts j. The shape of the array is
            (len(t), 3) if j is a single int, else it is (len(j), len(t), 3).

        Examples
        --------
        >>> C = BezierSpline('1234', degree=2)
        >>> C.sub_directions([0.0, 0.5, 1.0], 1)
        array([[-0.707,  0.707,  0.   ],
               [-1.   ,  0.   ,  0.   ],
               [-0.707, -0.707,  0.   ]])
        >>> C.sub_directions([0.0, 0.5, 1.0])
        array([[[ 0.316,  0.949,  0.   ],
                [ 0.   ,  1.   ,  0.   ],
                [-0.707,  0.707,  0.   ]],
        <BLANKLINE>
               [[-0.707,  0.707,  0.   ],
                [-1.   ,  0.   ,  0.   ],
                [-0.707, -0.707,  0.   ]],
        <BLANKLINE>
               [[-0.707, -0.707,  0.   ],
                [ 0.   , -1.   ,  0.   ],
                [ 0.316, -0.949,  0.   ]]])
        """
        t = np.asarray(t).reshape(-1)
        P = self.part_points(j)
        C = np.dot(self.coeffs, P)
        if C.ndim > 2:
            C = C.transpose(1, 0, 2)
        U = [d*(t**(d-1)) if d >= 1 else np.zeros_like(t)
             for d in range(0, self.degree+1)]
        U = np.column_stack(U)
        T = np.dot(U, C)
        if T.ndim > 2:
            T = T.transpose(1, 0, 2)
        T = at.normalize(T)
        return T


    # TODO: This is nowhere used. Create an example?
    # TODO: to be replaced with general frenet method
    def sub_curvature(self, t, j=None):
        """Return the curvature at values t in part j.

        Parameters
        ----------
        t: float :term:`array_like`
            Local parameter values (usually in the range 0.0..1.0) of
            the points at which to find the curvature.
        j: int or int :term:`array_like`
            The part number(s) for which to return curvatures.
            If not provided, curvatures for all parts are returned.

        Returns
        -------
        :class:`array`
            The curvature of the curve at the points with local
            parameter values t on the parts j. The shape of the return array is
            (len(t),) if j is a single int, else it is (len(j), len(t)).

        Examples
        --------
        >>> C = BezierSpline('1234', degree=2)
        >>> C.sub_curvature([0.0, 0.5, 1.0], 0)
        array([0.253, 1.   , 2.828])
        >>> C.sub_curvature([0.0, 0.5, 1.0], 1)
        array([0.707, 2.   , 0.707])
        >>> C.sub_curvature([0.0, 0.5, 1.0])
        array([[0.253, 1.   , 2.828],
               [0.707, 2.   , 0.707],
               [2.828, 1.   , 0.253]])
        """
        t = np.asarray(t).reshape(-1)
        P = self.part_points(j)
        C = np.dot(self.coeffs, P)
        if C.ndim > 2:
            C = C.transpose(1, 0, 2)
        U1 = [d*(t**(d-1)) if d >= 1 else np.zeros_like(t)
              for d in range(0, self.degree+1)]
        U1 = np.column_stack(U1)
        T1 = np.dot(U1, C)
        U2 = [d*(d-1)*(t**(d-2)) if d >=2 else np.zeros_like(t)
              for d in range(0, self.degree+1)]
        U2 = np.column_stack(U2)
        T2 = np.dot(U2, C)
        K = at.length(np.cross(T1, T2))/(at.length(T1)**3)
        if T1.ndim > 2:
            K = K.transpose(1, 0)
        return K


    def directions(self):
        """Return the direction vectors at the points on the curve"""
        return self.directionsAt(np.arange(self.npoints))


    def _length_intgrnd(self, t, j):
        P = self.points(j)
        C = np.dot(self.coeffs, P)
        U = [d*(t**(d-1)) if d >= 1 else 0. for d in range(0, self.degree+1)]
        U = np.asarray(U)
        T = np.dot(U, C).reshape(3)
        return at.length(T)


    def lengths(self, t=(0., 1.), j=None):
        """Return the length of the parts of the curve.

        Parameters
        ----------
        t: tuple of float
            The range of parameter values over which to integrate the length.
            Default is 0.0..1.0, to obtaind the full part length.
        j: int or int :term:`array_like`
            The part number(s) for which to return lengths.
            If not provided, lengths for all parts are returned.

        Returns
        -------
        :class:`array`
            The lengths of the parts j of the curve between parameter values t.

        Examples
        --------
        >>> C = BezierSpline('1234', degree=2)
        >>> C.lengths()
        array([1.046, 1.148, 1.046])
        >>> C.lengths((0.0, 0.5), [0,1])
        array([0.64 , 0.574])
        """
        try:
            from scipy import integrate
        except ImportError:
            pf.warning("""..

**The **lengths** function is not available.
Most likely because 'python-scipy' is not installed on your system.""")
            return
        if j is None:
            j = np.arange(self.nparts)
        else:
            j = np.asarray(j).reshape(-1)
        L = [integrate.quad(self._length_intgrnd, t[0], t[1], args=(i,))[0]
             for i in j]
        return np.array(L)


    def atLength(self, l, approx=20):
        """Return the parameter values at given relative curve length.

        Parameters
        ----------
        l: :term:`array_like`
            The list of relative curve lengths (ranging from 0.0 to 1.0
            over the full length of the curve).
            As a convenience, a single integer value may be specified,
            in which case the relative curve lengths are found by dividing
            the interval [0.0,1.0] in the specified number of subintervals.
        approx: int or None.
            If not None, an approximate result is returned obtained by
            approximating the curve first by a PolyLine with `approx`
            number of line segments per curve segment.
            This is currently the only implemented method, and specifying
            None will fail.

        Returns
        -------
        list
            A list with the parameter values for the points at the specified
            relative lengths.

        Examples
        --------
        >>> C = BezierSpline('1234', degree=2)
        >>> C.atLength([0.0, 1/3, 0.5, 0.75, 1.0])
        array([0.   , 1.025, 1.5  , 2.314, 3.   ])
        """
        if at.isInt(approx) and approx > 0:
            P = self.approx(ndiv=approx)
            return P.atLength(l) / approx  # this is not recursive
        else:
            raise ValueError("approx should be int and > 0")


    def insertPointsAt(self, t, return_indices=False):
        """Insert new points on the curve at parameter values t.

        Parameters
        ----------
        t: float :term:`array_like`
            A list of global parameter values where the new points will be
            inserted.
            ** Currently there is a maximum of one new point per segment. **
        return_indices: bool
            If True, returns the indices of the new points in the BezierSpline.

        Returns
        -------
        BezierSpline
            The BezierSpline with extra points inserted at the specified
            parameter values.
        indices: int array
            The indices in the new curve's :meth:`pointsOn` of the inserted
            oncurve points. Only returned if `return_indices` is True.

        See Also
        --------
        PolyLine.insertPointsAt: allows multiple insertions on same segment

        Examples
        --------
        >>> C = BezierSpline('012', degree=2)
        >>> print(C)
        BezierSpline: degree=2, nparts=2, ncoords=5, open
          Control points:
        [[ 0.    0.    0.  ]
         [ 0.75 -0.25  0.  ]
         [ 1.    0.    0.  ]
         [ 1.25  0.25  0.  ]
         [ 1.    1.    0.  ]]
        >>> C1 = C.insertPointsAt([0.5, 1.5])
        >>> print(C1)
        BezierSpline: degree=2, nparts=4, ncoords=9, open
          Control points:
        [[ 0.     0.     0.   ]
         [ 0.375 -0.125  0.   ]
         [ 0.625 -0.125  0.   ]
         [ 0.875 -0.125  0.   ]
         [ 1.     0.     0.   ]
         [ 1.125  0.125  0.   ]
         [ 1.125  0.375  0.   ]
         [ 1.125  0.625  0.   ]
         [ 1.     1.     0.   ]]
        >>> C1 = C.insertPointsAt([-0.5])
        >>> print(C1)
        BezierSpline: degree=2, nparts=3, ncoords=7, open
          Control points:
        [[-0.875  0.375  0.   ]
         [-0.375  0.125  0.   ]
         [ 0.     0.     0.   ]
         [ 0.75  -0.25   0.   ]
         [ 1.     0.     0.   ]
         [ 1.25   0.25   0.   ]
         [ 1.     1.     0.   ]]
        """
        t = np.asarray(t).ravel()
        t.sort()
        X = []
        points = []  # points of left over parts
        if return_indices:
            ind = -np.ones(self.npoints, dtype=at.Int)
        # Loop in descending order to avoid recomputing parameters
        n = len(t)
        all_j, all_u = self.localParam(t[::-1])  # reverse order!
        k = self.nparts  # last part
        for j, u in zip(all_j, all_u):
            P = self.points(j)
            if j==k:
                raise ValueError(
                    "Currently there is max. one split point per curve part")
            # Push the tail beyond current part
            if k > j+1:
                points[0:1] = self.points(j+1, k).tolist()
            L, R = splitBezier(P, u)
            if u < 0.:
                L, R = L[::-1], P
            elif u > 1.:
                L, R = P, R[::-1]
            # Push the right part
            points[0:1] = R.tolist()
            # Save the new segment
            X.insert(0, Coords.concatenate(points))
            if return_indices:
                n -= 1
                if u < 0.:
                    ind = np.concatenate([[n], ind])
                elif u > 1.:
                    ind = np.concatenate([ind, [n]])
                else:
                    ind = np.concatenate([ind[:j+1], [n], ind[j+1:]])
            # Save left part
            points = L.tolist()
            k = j
        if k > 0:
            points = self.points(0, k).tolist()[:-1]+points
        X.insert(0, Coords.concatenate(points))
        X = Coords.concatenate([X[0]] + [xi[1:] for xi in X[1:]])
        C = self.__class__(control=X, degree=self.degree, closed=self.closed)

        if return_indices:
            ind = ind.tolist()
            ind = [ind.index(i) for i in np.arange(len(t))]
            return C, ind
        else:
            return C


    def splitAt(self, t):
        """Split a BezierSpline at parameter values.

        Parameters
        ----------
        t: float :term:`array_like`
            A list of global parameter values where the curve will be split.
            For a BezierSpline there is currently a maximum of one split point
            per segment. The PolyLine subclass however allows multiple split
            points per segment.

        Returns
        -------
        list(BezierSpline)
            A list of len(t)+1 open BezierSplines of the same degree
            as the input.

        Examples
        --------
        >>> C = BezierSpline('012', degree=2)
        >>> CL = C.splitAt([0.5, 1.5])
        >>> for Ci in CL: print(Ci)
        BezierSpline: degree=2, nparts=1, ncoords=3, open
          Control points:
        [[ 0.     0.     0.   ]
         [ 0.375 -0.125  0.   ]
         [ 0.625 -0.125  0.   ]]
        BezierSpline: degree=2, nparts=2, ncoords=5, open
          Control points:
        [[ 0.625 -0.125  0.   ]
         [ 0.875 -0.125  0.   ]
         [ 1.     0.     0.   ]
         [ 1.125  0.125  0.   ]
         [ 1.125  0.375  0.   ]]
        BezierSpline: degree=2, nparts=1, ncoords=3, open
          Control points:
        [[1.125 0.375 0.   ]
         [1.125 0.625 0.   ]
         [1.    1.    0.   ]]
        """
        C, t = self.insertPointsAt(t, return_indices=True)
        return C.split(t)


    def splitAtLength(self, L):
        """Split a BezierSpline at relative lenghts L.

        This is a convenient shorthand for::

           self.splitAt(self.atLength(L))

        See Also
        --------
        splitAt: split a PolyLine at given parameter values
        atLength: compute parameter values at given curve length
        """
        return self.splitAt(self.atLength(L))


    def extend(self, start=None, end=None):
        """Extend the curve beyond its endpoints.

        Uses de Casteljau's algorithm to add an extra curve part before
        the first and/or after the last part of the :class:`BezierSpline`.

        Parameters
        ----------
        start: float
            Parameter values to extend the :class:`BezierSpline` at
            the start. Values start with zero at the start of the curve and
            run in the direction opposite to that of segment 0. The new
            start point of the curve will thus become the point that would
            be inserted by ``self.insertPointsAt([-start])``.
        end: float
            Parameter value to extend :class:`BezierSpline` at
            the end. Values start with zero at the end of the curve and
            run beyond thet point along the last segment. The new
            start point of the curve will thus become the point that would
            be inserted by ``self.insertPointsAt([self.nparts + end])``.

        Returns
        -------
        BezierSpline
            A Curve of same type and degree as the input, extended at
            the start and/or the end.

        Notes
        -----
        Only open curves can be extended.

        See Also
        --------
        PolyLine.extend: allows a list of values for start/end

        Examples
        --------
        >>> PL = PolyLine(Coords('012'))
        >>> PL.extend(0.4, 0.5).coords
        Coords([[-0.4,  0. ,  0. ],
                [ 0. ,  0. ,  0. ],
                [ 1. ,  0. ,  0. ],
                [ 1. ,  1. ,  0. ],
                [ 1. ,  1.5,  0. ]])
        >>> C = BezierSpline('012', degree=1)
        >>> C.extend(0.4, 0.5).coords
        Coords([[-0.4,  0. ,  0. ],
                [ 0. ,  0. ,  0. ],
                [ 1. ,  0. ,  0. ],
                [ 1. ,  1. ,  0. ],
                [ 1. ,  1.5,  0. ]])
        """
        t = []
        if start is not None:
            t.append(-start)
        if end is not None:
            t.append(self.nparts + end)
        return self.insertPointsAt(t)


    def close(self, tangents=False, tol=None):
        """Close a Curve

        Creates a closed curve throught the oncurve points of the current,
        and possibly with the same tangents.

        Parameters
        ----------
        tangents: bool
            If True, the returned curve will have the same tangents
            at all internal points.
        tol: float
            Tolerance for testing end point coincidence when creating
            closed curves. This parameter is passed to :meth:`ipol`.

        Returns
        -------
        BezierSpline | PolyLine
            A closed variant of the input curve. If that is already closed,
            just returns self.
        """
        if self.closed:
            return self
        kargs = {
            'coords': self.pointsOn(),
            'degree': self.degree,
            'closed': True,
            'tol': tol,
        }
        if self.  degree > 1 and tangents:
            T = self.directions()
            T[0] = T[-1] = at.normalize(0.5 * (T[0] + T[-1]))
            kargs['tangents'] = T
        return self.__class__(**kargs)


    def reverse(self):
        """Return the same curve with the parameter direction reversed."""
        control = at.reverseAxis(self.coords, axis=0)
        return self.__class__(control=control, degree=self.degree,
                              closed=self.closed)


    def roll(self, n):
        """Roll the parts of a closed curve.

        This rolls the start vertex of the curve n positions further.

        Parameters
        ----------
        n: int
            The number of vertex positions to roll over: part 0
            then becomes part n.

        Returns
        -------
        BezierSpline | PolyLine
            The same curve as the input, but with the vertex numbers
            rolled over n positions.

        Notes
        -----
        This only works for a closed curve.

        Examples
        --------
        >>> C = BezierSpline('012', degree=2, closed=True)
        >>> print(C.coords)
        [[ 0.     0.     0.   ]
         [ 0.293 -0.707  0.   ]
         [ 1.     0.     0.   ]
         [ 1.707  0.707  0.   ]
         [ 1.     1.     0.   ]
         [-0.707  1.707  0.   ]]
        >>> print(C.roll(1).coords)
        [[ 1.     1.     0.   ]
         [-0.707  1.707  0.   ]
         [ 0.     0.     0.   ]
         [ 0.293 -0.707  0.   ]
         [ 1.     0.     0.   ]
         [ 1.707  0.707  0.   ]]
        """
        if not self.closed:
            raise ValueError("""Can only roll a closed curve""")
        return self.__class__(
            control=np.roll(self.coords, n*self.degree, axis=0),
            degree=self.degree, closed=True)


    def toMesh(self):
        """Convert a BezierSpline to a Mesh.

        Returns
        -------
        Mesh
            A Mesh of eltype 'line2', 'line3' or 'line4', where each element
            corresponds with a part of the BezierSpline. This gives an exact
            representation of a BezierSpline of degree 1, 2, or 3 or a
            PolyLine.

        Notes
        -----
        Currently, only BezierSplines of degree <= 3 can be converted to a Mesh.
        For higher degrees, create an approximation of degree <= 3 first.

        Examples
        --------
        >>> M = PolyLine('0123').toMesh()
        >>> print(M.coords)
        [[0. 0. 0.]
         [1. 0. 0.]
         [1. 1. 0.]
         [0. 1. 0.]]
        >>> print(M.elems)
        [[0 1]
         [1 2]
         [2 3]]
        >>> M = BezierSpline('0123',degree=2,closed=True).toMesh()
        >>> print(M.coords)
        [[ 0.    0.    0.  ]
         [ 0.5  -0.25  0.  ]
         [ 1.    0.    0.  ]
         [ 1.25  0.5   0.  ]
         [ 1.    1.    0.  ]
         [ 0.5   1.25  0.  ]
         [ 0.    1.    0.  ]
         [-0.25  0.5   0.  ]]
        >>> print(M.elems)
        [[0 1 2]
         [2 3 4]
         [4 5 6]
         [6 7 0]]
        """
        if self.degree > 3:
            raise ValueError(
                "BezierSpline of degree > 3 can not be converted to Mesh")

        if self.degree == 1:
            X = self.coords
        else:
            t = {2: (0., 0.5), 3: (0., 1/3, 2/3)}[self.degree]
            X = [self.sub_points(t, j) for j in range(self.nparts)]
            if not self.closed:
                X.append(self.coords[-1:])
            X = Coords.concatenate(X)

        nplex = self.degree + 1
        c1 = np.arange(0, self.degree*self.nparts, self.degree)
        e = np.column_stack([c1+i for i in range(nplex)])
        if self.closed:
            e[-1,-1] = e[0,0]
        return Mesh(X, e, eltype=f"line{nplex}", prop=self.prop)


    def toFormex(self):
        """Convert the BezierSpline to a Formex.

        This is notational convenience for::
          self.toMesh().toFormex()
        """
        return self.toMesh().toFormex()


    ###################
    ## PZF interface ##

    def pzf_dict(self):
        kargs = super().pzf_dict()
        kargs['control'] = kargs.pop('coords')
        kargs[f'degree:i__{self.degree}'] = None
        kargs[f'closed:b__{self.closed}'] = None
        return kargs


###########################################################################
# Functions constructing BezierSpline interpolates
#

def _cubic_bezier_interpolate(Q, T=None, closed=False, curl=1/3):
    """Create a cubic BezierSpline passing through given points.

    coords: Coords(npts, 3)
    tangents: Coords(npts, 3) or (2,3)
    closed: bool
    curl:
    """
    P = PolyLine(control=Q, closed=closed)
    ncoords = P.coords.shape[0]
    ampl = P.lengths().reshape(-1, 1)
    if T is None:
        T = P.avgDirections()
    else:
        deriv = at.checkArray(T, (-1,3), 'f', 'i')
        nderiv = deriv.shape[0]
        if not (nderiv == ncoords or nderiv == 2):
            raise ValueError(
                f"Expected either all or the start and end tangents, "
                f"but got {nderiv}")
            if nderiv == ncoords:
                T = deriv
            else:
                T = np.full(Q.shape, np.nan, dtype=at.Float)
                T[0], T[-1] = deriv

    undefined = np.isnan(T).any(axis=-1)
    if undefined.any():
        T[undefined] = P.avgDirections()[undefined]
    if closed:
        R1 = Q + T*curl*ampl
        R2 = Q - T*curl*np.roll(ampl, 1, axis=0)
        R2 = np.roll(R2, -1, axis=0)
        segments = np.stack([Q, R1, R2], axis=1).reshape(-1,3)
    else:
        R1 = Q[:-1] + T[:-1]*curl*ampl
        R2 = Q[1:] - T[1:]*curl*ampl
        segments = np.stack([Q[:-1], R1, R2], axis=1)
        segments = Coords(segments.reshape(-1,3))
        segments = Coords.concatenate([segments, Q[-1]])
    return segments
    # return BezierSpline(control=segments, degree=3, closed=closed)


def _quadratic_bezier_interpolate(Q, T=None, *, closed=False):
    """Create a quadratic BezierSpline interpolating given points.

    Parameters
    ----------
    Q: :term:`coords_like` (npts, 3)
        The points through which the quadratic BezierSpline should pass.
    T: :term:`coords_like` (npts, 3), optional
        The tangents to the curve at the points Q. The length of the
        vectors is irrelevant. If not provided, it is set equal to
        ``PolyLine(Q).avgDirections()``.

    Returns
    -------
    BezierSpline
        A BezierSpline of the second degree, passing through all points Q,
        and with tangents (approximately) equal to the tangents T.

    Notes
    -----
        If the points Q are coplanar, a planar curve results, the tangents
        are exactly T and the curve is geometrically smooth.
        A nonplanar curve however may contain discontinuities in the tangent
        directions. A :func:`cubicBezierInterpolate` on the other hand
        guarantees smoothness even for nonplanar curves.
    """

    def handle_special(Q0, Q1, T0, T1, t0, t1):
        QQ = at.normalize(Q1 - Q0)
        if np.allclose(T0, QQ) and np.allclose(T1, QQ):
            # straight segment
            return [0.5 * (Q0 + Q1)]
        elif np.allclose(T0, T1):
            # parallel tangents: inflection point in the middle
            Qm = 0.5 * (Q0 + Q1)
            Tm = 2*(Q1-Q0) - T1
            P0, P1 = gt.intersectLineWithLine(Q0, T0, Qm, Tm, mode='pair')
            R0 = 0.5 * (P0+P1)
            P0, P1 = gt.intersectLineWithLine(Q1, T1, Qm, Tm, mode='pair')
            R1 = 0.5 * (P0+P1)
            return [R0, Qm, R1]
        else:
            gamma = 0.25 * at.length(Q1-Q0)
            R0 = Q0 + gamma * T0
            R1 = Q1 - gamma * T1
            Qm = 0.5 * (R0 + R1)
            return [R0, Qm, R1]

    Q = at.checkArray(Q, (-1,3), 'f', 'i')
    ncoords = Q.shape[0]
    if ncoords < 2:
        raise ValueError("Need at least two points to create a curve")
    if T is None:
        T = PolyLine(Q, closed=closed).avgDirections()
    else:
        T = at.checkArray(T, Q.shape, 'f', 'i')
    if closed:
        Q0, T0 = Q, T
        Q1, T1 = np.roll(Q, -1, axis=0), np.roll(T, -1, axis=0)
    else:
        Q0, T0 = Q[:-1], T[:-1]
        Q1, T1 = Q[1:], T[1:]
    t0, t1 = gt.intersectLineWithLine(Q0, T0, Q1, T1, mode='pair', times=True)
    R = 0.5 * (Q0 + t0[:,np.newaxis]*T0 + Q1 + t1[:,np.newaxis]*T1)
    ok = (t0 > 0.0) * (t1 < 0.0)
    segments = []
    n = Q.shape[0]
    for i in range(n if closed else n-1):
        segments.append(Q[i])
        if ok[i]:
            segments.append(R[i])
        else:
            j = i+1 if i+1 < n else 0
            extra = handle_special(Q[i], Q[j], T[i], T[j], t0[i], t1[i])
            segments.extend(extra)
    if not closed:
        segments.append(Q[-1])
    segments = Coords.concatenate(segments)
    return segments
    # return BezierSpline(control=segments, degree=2, closed=closed)


##############################################################################
#
#  PolyLine
#
##############################################################################

@utils.pzf_register
class PolyLine(BezierSpline):
    """A Curve consisting of a sequence of straight line segments.

    This is implemented as a :class:`BezierSpline` of degree 1, and in many
    cases one can just use that super class. The PolyLine class however
    provides a lot of extra functionality, which is only available for
    curves of degree 1.

    Parameters
    ----------
    coords: :term:`coords_like`
        An (npts,3) shaped array with the coordinates of the subsequent
        vertices of the PolyLine, or any other data accepted by the
        :class:`Coords` initialization.
        Each vertex is connected to the next to form a PolyLine segment.
        For compatibility with the :class:`BezierSpline` class, this
        argument can also be named `control`, and takes precedent if both
        are used.
    closed: bool, optional
        If True, the PolyLine is closed by connecting the last vertex back
        to the first. The closed PolyLine thus has `npts` segments.
        The default (False) leaves the curve open with `npts-1` segments.
    control: optional
        This is an alias for the coords parameter. It exists only for
        symmetry with the :class:`BezierSpline` class.
        If specified, `control` overrides the value of `coords`.

    Examples
    --------
    >>> P = PolyLine('0123')
    >>> print(P)
    PolyLine: nparts=3, ncoords=4, open
      Control points:
    [[0. 0. 0.]
     [1. 0. 0.]
     [1. 1. 0.]
     [0. 1. 0.]]
    >>> P.nparts
    3
    >>> P = PolyLine(P.coords, closed=True).nparts
    >>> print(P)
    4
    """
    def __init__(self, control=None, *, closed=False, tol=None, **kargs):
        """Initialize a PolyLine"""
        control = Coords(kargs.get('coords', control))
        super().__init__(control=control, closed=closed, tol=tol, degree=1)


    def vectors(self):
        """Return the vectors from each point to the next one.

        Returns
        -------
        Coords (nparts,3)
            A Coords array holding the vectors from each point of the
            PolyLine to the next one. The number of vectors is equal to
            :attr:`nparts`.

        Examples
        --------
        >>> PolyLine('0123').vectors()
        Coords([[ 1.,  0.,  0.],
                [ 0.,  1.,  0.],
                [-1.,  0.,  0.]])
        """
        x = self.coords
        if self.closed:
            x = Coords.concatenate([x, x[0]])
        return x[1:] - x[:-1]


    def directions(self, return_doubles=False):
        """Returns unit vectors in the direction of the next point.

        Parameters
        ----------
        return_doubles: bool
            If True, also returns an index of coincident points.

        Returns
        -------
        dirs: array(npoints,3)
           The unit vectors at all points in the direction of the next
           point. If two subsequent points are identical, the first one gets
           the direction of the previous segment. If more than two subsequent
           points are equal, an invalid direction (NaN) is returned.
           If the curve is not closed, the last direction is set equal to the
           penultimate.
        doubles: array
           The indices of the points that coincide with their follower.
           Only returned if return_doubles is True.

        See Also
        --------
        avgDirections: the average direction of the segments ending at the point

        Examples
        --------
        >>> PolyLine('0123').directions()
        array([[ 1.,  0.,  0.],
               [ 0.,  1.,  0.],
               [-1.,  0.,  0.],
               [-1.,  0.,  0.]])
        >>> P = PolyLine('01.2')
        >>> print(P)
        PolyLine: nparts=3, ncoords=4, open
          Control points:
        [[0. 0. 0.]
         [1. 0. 0.]
         [1. 0. 0.]
         [1. 1. 0.]]
        >>> P.directions(return_doubles=True)
        (array([[1., 0., 0.],
               [1., 0., 0.],
               [0., 1., 0.],
               [0., 1., 0.]]), array([1]))
        """
        d = at.normalize(self.vectors())
        w = at.where_1d(np.isnan(d).any(axis=1))
        d[w] = d[w-1]
        if not self.closed:
            d = np.concatenate([d, d[-1:]], axis=0)
        if return_doubles:
            return d, w
        else:
            return d


    def avgDirections(self, return_indices=False):
        """Returns the average directions at points.

        Parameters
        ----------
        return_indices: bool
            If True, also returns an index of the points where an
            average was computed. This excludes the endpoints and
            subsequent conincident points, where the returned direction
            is the same as that from :meth:`directions`.

        Returns
        -------
        dirs: array(npoints,3)
            The average direction at all points. The returned direction is
            the average of the direction from the preceding point to the
            current, and the direction from the current to the next point.
            If the curve is open, the end directions are set to mimic
            a natural free end: the angle with the chord is half the angle
            at the other end of the segment, and in opposite direction.
            Where two subsequent points coincide, the average directions
            are set equal to those of the segment ending in the first point
            and the segment starting from the last point.
        doubles: array
           The indices of the points that coincide with their follower.
           Only returned if return_doubles is True.

        See Also
        --------
        directions: the direction from the point to the next point

        Examples
        --------
        >>> PolyLine('0123').avgDirections()
        array([[ 0.949, -0.316,  0.   ],
               [ 0.707,  0.707,  0.   ],
               [-0.707,  0.707,  0.   ],
               [-0.949, -0.316,  0.   ]])
        >>> P = PolyLine('012.3')
        >>> print(P)
        PolyLine: nparts=4, ncoords=5, open
          Control points:
        [[0. 0. 0.]
         [1. 0. 0.]
         [1. 1. 0.]
         [1. 1. 0.]
         [0. 1. 0.]]
        >>> P.avgDirections(return_indices=True)
        (array([[ 0.949, -0.316,  0.   ],
               [ 0.707,  0.707,  0.   ],
               [ 0.   ,  1.   ,  0.   ],
               [-1.   ,  0.   ,  0.   ],
               [-1.   ,  0.   ,  0.   ]]), array([1]))
        """
        d, w = self.directions(True)
        w = np.concatenate([w, w+1])
        if not self.closed:
            w = np.concatenate([[0, self.nparts], w])
        w = np.setdiff1d(np.arange(self.nparts), w)
        d[w] = 0.5 * (d[w] + np.roll(d, 1, axis=0)[w])
        if not self.closed:
            # set free end condition
            d[0] = 2 * d[0] - d[1]
            d[-1] = 2 * d[-1] - d[-2]
        d = at.normalize(d)  # need to renormalize!
        if return_indices:
            return d, w
        else:
            return d


    def lengths(self, t=(0., 1.), j=None):
        """Return the length of the parts of the PolyLine.

        This is like :meth:`BezierSpline.lengths` but implemented
        more efficiently for PolyLine

        Examples
        --------
        >>> PolyLine([[0., 0., 0.], [0.4, 0., 0.], [0.4, 0.9, 0.]]).lengths()
        array([0.4, 0.9])
        """
        lens = at.length(self.vectors()) * (t[1]-t[0])
        if j is not None:
            lens = lens[j]
        return lens


    # TODO: this can be done for BezierSpline
    def cumLengths(self):
        """Return the cumulative length of the curve for all vertices."""
        return np.concatenate([[0.], self.lengths().cumsum()])


    # TODO: this can be done for BezierSpline
    def relLengths(self):
        """Return the relative length of the curve for all vertices."""
        cumlen = self.cumLengths()
        return cumlen / cumlen[-1]


    def atLength(self, div):
        """Return the parameter values at given relative curve length.

        Parameters
        ----------
        div: :term:`array_like`
            The list of relative curve lengths (ranging from 0.0 to 1.0
            over the full length of the curve).
            As a convenience, a single integer value may be specified,
            in which case the relative curve lengths are found by dividing
            the interval [0.0,1.0] in the specified number of subintervals.

        Returns
        -------
        list
            A list with the parameter values for the points at the specified
            relative lengths.

        Examples
        --------
        >>> P = PolyLine([[0., 0., 0.], [0.4, 0., 0.], [0.4, 0.9, 0.]])
        >>> P.atLength([0., 0.25, 0.5, 0.75, 1.0])
        array([0.   , 0.812, 1.278, 1.639, 2.   ])
        """
        rlen = self.relLengths()
        if at.isInt(div):
            div = np.arange(div+1) / float(div)
        else:
            div = np.asarray(div)
        z = rlen.searchsorted(div)
        # we need interpolation
        wi = np.where(z>0)[0]
        zw = z[wi]
        L0 = rlen[zw-1]
        L1 = rlen[zw]
        ai = zw + (div[wi] - L1) / (L1-L0)
        atl = np.zeros(len(div))
        atl[wi] = ai
        return atl


    def cosAngles(self):
        """Return the cosinus of the angles between subsequent segments.

        Returns
        -------
        array
            An array of floats in the range [-1.0..1.0]. The value
            at index i is the cosinus of the angle between the segment i and
            the segment i-1. The number of floats is always equal to the number
            of points.

            If the curve is open, the first value is the cosinus of the
            angle between the last and the first segment, while the last value
            is always equal to 1.0.
            Where a curve has two subsequent coincident points, the value for the
            the first point is 1.0. Where a curve has more than two
            subsequent coincident points, NAN values will result.

        Examples
        --------
        >>> C1 = PolyLine('01567')
        >>> C2 = PolyLine('01567',closed=True)
        >>> C3 = PolyLine('015674')
        >>> print(C1.cosAngles())
        [-0.707  0.707  0.     0.     1.   ]
        >>> print(C2.cosAngles())
        [0.    0.707 0.    0.    0.707]
        >>> print(C3.cosAngles())
        [0.    0.707 0.    0.    0.707 1.   ]
        """
        d = self.directions()
        return at.vectorPairCosAngle(np.roll(d, 1, axis=0), d)


    # TODO: add a subdivide(ndiv) method, identical to self.approx(ndiv=ndiv)
    def subdivide(self, ndiv):
        return self.approx(ndiv=ndiv)


    def insertPointsAt(self, t, return_indices=False):
        """Insert new points at parameter values t

        Parameters
        ----------
        t: float :term:`array_like`
            A list of global parameter values where the new points will be
            inserted. The values can be in any order, but will be sorted
            before processing.
            Usually values are in the range 0..nparts. However, for open
            PolyLines values < 0. will result in points inserted
            before the first point, and values > nparts are will result
            in points beyond the end of the PolyLine. This is a convenient
            way to extend a PolyLine in the direction of its end segments.
        return_indices: bool
            If True, returns the indices of the new points in the PolyLine.

        Returns
        -------
        PolyLine
            A PolyLine with the new points inserted. Note that the
            parameter values of the existing points will have changed.
        indices: int array
            Only returned if `return_indices` is True: the indices of the
            inserted points in the returned PolyLine.

        Notes
        -----
        This is like :meth:`BezierSpline.insertPointsAt` but allows multiple
        values on the same segment.

        Examples
        --------
        >>> PL = PolyLine(Coords('012'))
        >>> PL.insertPointsAt([-0.5, 1.5, 2.5, 3.5]).coords
        Coords([[-0.5,  0. ,  0. ],
                [ 0. ,  0. ,  0. ],
                [ 1. ,  0. ,  0. ],
                [ 1. ,  0.5,  0. ],
                [ 1. ,  1. ,  0. ],
                [ 1. ,  1.5,  0. ],
                [ 1. ,  2.5,  0. ]])
        """
        t = np.sort(t)
        if self.closed:
            if (t<0.).any() or (t>self.nparts).any():
                raise ValueError("For a closed curve all parameter values"
                                 "should be in the range 0..nparts")
        X, i, t = self.pointsAt(t, return_position=True)
        Xc = self.coords.copy()
        if return_indices:
            ind = -np.ones(len(Xc), dtype=at.Int)
        # Loop in descending order to avoid recomputing parameters
        for j in range(len(i))[::-1]:
            Xi, ii, ti = X[j].reshape(-1, 3), i[j]+1, t[j]
            if ti < 0.:
                ii -= 1
            elif ti > 1.:
                ii += 1
            Xc = Coords.concatenate([Xc[:ii], Xi, Xc[ii:]])
            if return_indices:
                ind = np.concatenate([ind[:ii], [j], ind[ii:]])
        PL = PolyLine(Xc, closed=self.closed)
        if return_indices:
            ind = ind.tolist()
            ind = [ind.index(i) for i in np.arange(len(i))]
            return PL, ind
        else:
            return PL


    def extend(self, start=[], end=[]):
        """Extend and open PolyLine beyond its endpoints.

        Parameters
        ----------
        start: float or float :term:`array_like`
            One or more parameter values to extend the PolyLine at
            the start. Parameter values start at point 0 and run in
            the direction opposite to that of segment 0, with a value
            1.0 being obtained at a distance equal to the length of
            the first segment.
        end: float or float :term:`array_like`
            One or more parameter values to extend the PolyLine at
            the end. Parameter values start at point :attr:`nparts` and run in
            the direction opposite to that of the last segment , with a value
            1.0 being obtained at a distance equal to the length of
            the last segment.


        Notes
        -----
        This is equivalent with using :meth:`insertPointsAt` with t
        values given by `- start` and `self.nparts + end`.
        Only open curves can be extended.
        This is like :meth:`BezierSpline.extend` but allows multiple
        values for start and/or end.

        Examples
        --------
        >>> PL = PolyLine(Coords('012'))
        >>> PL.extend(0.4, [0.3, 0.5]).coords
        Coords([[-0.4,  0. ,  0. ],
                [ 0. ,  0. ,  0. ],
                [ 1. ,  0. ,  0. ],
                [ 1. ,  1. ,  0. ],
                [ 1. ,  1.3,  0. ],
                [ 1. ,  1.5,  0. ]])
        """
        if self.closed:
            raise ValueError("Can not extend a closed curve")
        start = np.atleast_1d(start)
        end = np.atleast_1d(end)
        t = np.concatenate([-start.ravel(), self.nparts + end.ravel()])
        return self.insertPointsAt(t)


    def toFormex(self):
        """Return the PolyLine as a Formex."""
        x = self.coords
        F = connect([x, x], bias=[0, 1], loop=self.closed)
        return F.setProp(self.prop)


    def splitByAngle(self, cosangle=0.0, angle=None, angle_spec=at.DEG):
        """Split a PolyLine at points with high change of direction.

        Parameters
        ----------
        cosangle: float
            Threshold value for the cosinus of the angle between subsequent
            segment vectors. The curve is split at all points where the
            value of :meth:`cosAngles` is (algebraicallly) lower than or equal
            to this threshold value. The default value splits the curve
            where the direction changes with more than 90
            degrees. A value 1.0 will split the curve at all points. A value
            of -1.0 will only split where the curve direction exactly reverses.
        angle: float, optional
            If provided, `cosangle` is computed from
            ``at.cosd(angle,angle_spec)```
        angle_spec: float, optional
            Units used for the `angle` parameter. This is the number of
            radians for 1 unit.

        Returns
        -------
        list
            A list of PolyLine objects, where each PolyLine has a limited
            change of direction at its vertices.
        """
        if at.isFloat(angle):
            cosangle = at.cosd(angle, angle_spec)
        w = np.where(self.cosAngles() <= cosangle)[0]
        return self.split(w)


    def _compensate(self, end=0, cosangle=0.5):
        """_Compensate an end discontinuity over a piece of curve.

        An end discontinuity in the curve is smeared out over a part of
        the curve where no sharp angle occur with cosangle < 0.5
        """
        cosa = self.cosAngles()
        print("COSA", cosa)
        L = self.lengths()
        if end < 0:
            L = L[::-1]
            cosa = np.roll(cosa, -1)[::-1]
        print(len(L), L)
        for i in range(1, len(L)):
            if cosa[i] <= cosangle:
                break
        print(f"HOLDING AT i={i}")
        L = L[:i]
        print(len(L), L)
        L = L[::-1].cumsum()
        comp = L / L[-1]
        comp = comp[::-1]
        print("COMP", comp)
        return comp


    def _movingFrenet(self, upvector=None, avgdir=True, compensate=False):
        """Return a Frenet frame along the curve.

        ..note : The recommended way to use this method is through the
                 :meth:`frenet` method.

        The Frenet frame consists of a system of three orthogonal vectors:
        the tangent (T), the normal (N) and the binormal (B).
        These vectors define a coordinate system that re-orients while walking
        along the polyline.
        The _movingFrenet method tries to minimize the twist angle.

        Parameters:

        - `upvector`: (3,) vector: a vector normal to the (tangent,normal)
          plane at the first point of the curve. It defines the binormal at
          the first point. If not specified it is set to the shorted distance
          through the set of 10 first points.
        - `avgdir`: bool or array.
          If True (default), the tangential vector is set to
          the average direction of the two segments ending at a node.
          If False, the tangent vectors will be those of the line segment
          starting at the points.
          The tangential vector can also be set by the user by specifying
          an array with the matching number of vectors.
        - `compensate`: bool: If True, adds a compensation algorithm if the
          curve is closed. For a closed curve the moving Frenet
          algorithm can be continued back to the first point. If the resulting
          binormial does not coincide with the starting one, some torsion is
          added to the end portions of the curve to make the two binormals
          coincide.

          This feature is off by default because it is currently experimental
          and is likely to change in future.
          It may also form the base for setting the starting as well as the
          ending binormal.

        Returns:

        - `T`: normalized tangent vector to the curve at `npts` points
        - `N`: normalized normal vector to the curve at `npts` points
        - `B`: normalized binormal vector to the curve at `npts` points
        """
        if isinstance(avgdir, np.ndarray):
            T = at.checkArray(avgdir, (self.ncoords(), 3), 'f')
        elif avgdir:
            T = self.avgDirections()
        else:
            T = self.directions()
        B = np.zeros(T.shape)
        if upvector is None:
            upvector = gt.smallestDirection(self.coords[:10])

        B[-1] = at.normalize(upvector)
        for i, t in enumerate(T):
            B[i] = np.cross(t, np.cross(B[i-1], t))
            if np.isnan(B[i]).any():
                # if we can not compute binormal, keep previous
                B[i] = B[i-1]

        T = at.normalize(T)
        B = at.normalize(B)

        if self.closed and compensate:
            from pyformex.gui.draw import drawVectors
            print(len(T))
            print(T[0], B[0])
            print(T[-1], B[-1])
            P0 = self.coords[0]
            if avgdir:
                T0 = T[0]
            else:
                T0 = T[-1]
            B0 = np.cross(T0, np.cross(B[-1], T0))
            N0 = np.cross(B0, T0)
            drawVectors(P0, T0, size=2., nolight=True, color='magenta')
            drawVectors(P0, N0, size=2., nolight=True, color='yellow')
            drawVectors(P0, B0, size=2., nolight=True, color='cyan')
            print("DIFF", B[0], B0)
            if at.length(np.cross(B[0], B0)) < 1.e-5:
                print("NO NEED FOR COMPENSATION")
            else:
                PM, BM = gt.intersectionLinesPWP(P0, T[0], P0, T0, mode='pair')
                PM = PM[0]
                BM = BM[0]
                if at.length(BM) < 1.e-5:
                    print("NORMAL PLANES COINCIDE")
                    BM = (B0 + B[0])/2

                print(f"COMPENSATED B0: {BM}")
                print("Compensate at start")
                print(BM, B[0])
                a = at.vectorPairAngle(B[0], BM)
                print(f"ANGLE to compensate: {a}")
                sa = np.sign(at.projection(np.cross(B[0], BM), T[0]))
                print(f"Sign of angle: {sa}")
                a *= sa
                torsion = a * self._compensate(0)
                print("COMPENSATION ANGLE", torsion)
                for i in range(len(torsion)):
                    B[i] = Coords(B[i]).rotate(torsion[i], axis=T[i])

                print("Compensate at end")
                print(BM, B0)
                a = at.vectorPairAngle(B0, BM)
                print(f"ANGLE to compensate: {a}")
                sa = np.sign(at.projection(np.cross(BM, B0), T[-1]))
                print(f"Sign of angle: {sa}")
                a *= sa
                torsion = a * self._compensate(-1)
                print("COMPENSATION ANGLE", torsion)
                for i in range(len(torsion)):
                    B[-i] = Coords(B[-i]).rotate(torsion[i], axis=T[-i])

        N = np.cross(B, T)
        return T, N, B


    def cutWithPlane(self, p, n, side=''):
        """Return the parts of the PolyLine at one or both sides of a plane.

        Cuts a PolyLine with a plane and returns the resulting polylines at
        either side of the plane or both.

        Parameters
        ----------
        p: :term:`array_like` (3,)
            A point in the cutting plane.
        n: :term:`array_like` (3,)
            The normal vector to the cutting plane.
        side: str ('' | '+' | '-')
            Specifies which side of the plane should be returned.
            If an empty string (default), both sides are returned.
            If '+' or '-', only the part at the positive, resp. negative
            side of the plane (as defined by its normal `n`) is returned.

        Returns
        -------
        PLpos: list of PolyLine
            A list of the resulting polylines at the positive side of the plane.
            Not returned if side=='-'.
        PLneg: list of PolyLine
            A list of the resulting polylines at the negative side of the plane.
            Not returned if side=='+'.
        """
        n = np.asarray(n)
        p = np.asarray(p)
        d = self.coords.distanceFromPlane(p, n)
        t = d > 0.0
        cut = t != np.roll(t, -1)
        if not self.closed:
            cut = cut[:-1]
        w = np.where(cut)[0]   # segments where side switches

        res = [[], []]
        i = 0        # first point to include in next part
        if t[0]:
            sid = 0  # start at '+' side
        else:
            sid = 1  # start at '-' side
        Q = Coords()  # new point from previous cutting (None at start)

        for j in w:
            pts = self.coords.take(range(j, j+2), axis=0, mode='wrap')
            P = gt.intersectSegmentWithPlane(pts, p, n, mode='pair')
            x = Coords.concatenate([Q, self.coords[i:j+1], P])
            res[sid].append(PolyLine(x))
            sid = 1-sid
            i = j+1
            Q = P

        # Remaining points
        x = Coords.concatenate([Q, self.coords[i:]])
        if not self.closed:
            # append the remainder as an extra PolyLine
            res[sid].append(PolyLine(x))
        else:
            # append remaining points to the first
            if len(res[sid]) > 0:
                x = Coords.concatenate([x, res[sid][0].coords])
                res[sid][0] = PolyLine(x)
            else:
                res[sid].append(PolyLine(x))
            if len(res[sid]) == 1 and len(res[1-sid]) == 0:
                res[sid][0].closed = True

        # Do not use side in '+-', because '' in '+-' returns True
        if side in ['+', '-']:
            return res['+-'.index(side)]
        else:
            return res


    def append(self, PL, fuse=True, smart=False, **kargs):
        """Concatenate two open PolyLines.

        This combines two open PolyLines into a single one. Closed PolyLines
        cannot be concatenated.

        Parameters
        ----------
        PL: PolyLine
            An open PolyLine, to be appended at the end of the current.
        fuse: bool
            If True (default), the last point of `self` and the first point
            of `PL` will be fused to a single point if they are close. Extra
            parameters may be added to tune the fuse operation. See the
            :meth:`Coords.fuse` method. The `ppb` parameter is not allowed.
        smart: bool
            If True, `PL` will be connected to `self` by the
            endpoint that is closest to the last point of self, thus possibly
            reverting the sense of PL.

        Returns
        -------
        PolyLine
            The concatenation of the polylines self and PL.

        Notes
        -----
        The same result (with the default parameter values) can also be
        achieved using operator syntax: ``PolyLine1 + PolyLine2``.

        See Also
        --------
        concatenate: concatenate a list of PolyLine's
        """
        if self.closed or PL.closed:
            raise RuntimeError("Closed PolyLines cannot be concatenated.")
        if smart:
            d = PL.coords[[0, -1]].distanceFromPoint(self.coords[-1])
            if d[1] < d[0]:
                PL = PL.reverse()
        X = PL.coords
        if fuse:
            x = Coords.concatenate([self.coords[-1], X[0]])
            x, e = x.fuse(ppb=3)  # !!! YES ! > 2 !!!
            if e[0] == e[1]:
                X = X[1:]
        return PolyLine(Coords.concatenate([self.coords, X]))


    # allow syntax PL1 + PL2
    __add__ = append


    @staticmethod
    def concatenate(PLlist, **kargs):
        """Concatenate a list of :class:`PolyLine` objects.

        Parameters
        ----------
        PLlist: list of PolyLine.
            The list of PolyLine's to concatenate
        **kargs:
            Other keyword arguments like in :meth:`append`.

        Returns
        -------
        PolyLine
            The concatenation of all the polylines in `PLlist`.
        """
        PL = PLlist[0]
        for pl in PLlist[1:]:
            PL = PL.append(pl, **kargs)
        return PL


    def refine(self, maxlen):
        """Insert extra points in the PolyLine to reduce the segment length.

        Parameters
        ----------
        maxlen: float
            The maximum length of the segments. The value is
            relative to the total curve :meth:`length`.

        Returns
        -------
        PolyLine
            A PolyLine which is geometrically equivalent to the
            input PolyLine but has no segment longer than `maxlen`
            times the total curve :meth:`length`.
        """
        maxlen *= self.length()
        ndiv = np.ceil(self.lengths() / maxlen).astype(at.Int)
        return self.approx(ndiv=ndiv)


    def vertexReductionDP(self, tol, maxlen=None, keep=[0, -1]):
        """Douglas-Peucker vertex reduction.

        Finds out which points of the PolyLine can be removed while
        keeping a required accuracy.

        Parameters
        ----------
        tol: float
            Required accuracy of the result. For any subpart of the PolyLine,
            if the distance of all its vertices to the line connecting its
            endpoints is smaller than `tol`, the internal points are removed.

        Returns
        -------
        bool array
            A bool array flagging the vertices to be kept in the reduced form.

        See Also
        --------
        coarsen: returns the reduced PolyLine
        """
        x = self.coords
        n = len(x)
        _keep = np.zeros(n, dtype=bool)
        _keep[keep] = 1

        def decimate(i, j):
            """Recursive vertex decimation.

            This will remove all the vertices in the segment i-j that
            are closer than tol to any chord.
            """
            # Find point farthest from line through endpoints
            d = x[i+1:j].distanceFromLine(x[i], x[j]-x[i])
            k = np.argmax(d)
            dmax = d[k]
            k += i+1
            if dmax > tol:
                # Keep the farthest vertex, split the polyline at that vertex
                # and recursively decimate the two parts
                _keep[k] = 1
                if k > i+1:
                    decimate(i, k)
                if k < j-1:
                    decimate(k, j)

        def reanimate(i, j):
            """Recursive vertex reanimation.

            This will revive vertices in the segment i-j if the
            segment is longer than maxlen.
            """
            if j > i+1 and at.length(x[i]-x[j]) > maxlen:
                # too long: revive a point
                d = at.length(x[i+1:j]-x[i])
                w = np.where(d>maxlen)[0]
                if len(w) > 0:
                    k = w[0] + i+1
                    _keep[k] = 1
                    reanimate(k+1, j)


        # Compute vertices to keep
        decimate(0, n-1)

        # Reanimate some vertices if maxlen specified
        if maxlen is not None:
            w = np.where(_keep)[0]
            for i, j in zip(w[:-1], w[1:]):
                reanimate(i, j)

        return _keep


    def coarsen(self, tol=0.01, maxlen=None, keep=[0, -1]):
        """ Reduce the number of points of the PolyLine.

        Parameters
        ----------
        tol: float
            Maximum relative distance from the chord of the segment for
            vertices to be removed. The value is relative to the total curve
            length.
        keep: int :term:`array_like`
            List of vertices to keep during the coarsening process.
            (Not implemented yet !! NEED TO CHECK THIS).

        Returns
        -------
        Polyline
            A coarsened version of the PolyLine.
        """
        atol = tol*self.length()
        if maxlen:
            maxlen *= self.length()
        keep = self.vertexReductionDP(tol=atol, maxlen=maxlen, keep=keep)
        return PolyLine(self.coords[keep], closed=self.closed)


    ###################
    ## PZF interface ##

    def pzf_dict(self):
        """Return the data to save in PZF format."""
        kargs = super().pzf_dict()
        kargs.pop('degree:i__1', None)   # no need to store the degree
        return kargs


##############################################################################
#
#
class Line(PolyLine):
    """A Line is a straight segment between two points.

    Line is implemented as a :class:PolyLine with exactly two points.

    Parameters
    ----------
    coords: :term:`array_like` (2,3)
        The coordinates of begin and end point of the line.

    Examples
    --------
    >>> L = Line([[0.,0.,0.], [0.,1.,0.]])
    >>> print(L)
    Line: nparts=1, ncoords=2, open
      Control points:
    [[0. 0. 0.]
     [0. 1. 0.]]
    """
    def __init__(self, coords):
        """Initialize the Line."""
        super().__init__(coords)
        if self.coords.shape[0] != 2:
            raise ValueError(
                f"Expected exactly two points, got {coords.shape[0]}")


##############################################################################

class Contour(Curve):
    """A class for storing a contour.

    The Contour class stores a continuous (often closed, 2D) curve which
    consists of a sequence of strokes, each stroke being a Bezier curve.
    Generally the degree of the Bezier curves is in the range 1..3, but
    higher degrees are accepted. Each stroke is thus defined by 2, 3 or 4
    (or more) points. Each strokes starts at the endpoint of the previous
    stroke. If the last point of the last stroke and the first point of the
    first stroke are the same point, the Contour is closed.

    The Contour is defined by a list of points and a Varray of element
    connectivity. This format is well suited to store contours of scalable
    fonts (the contours are the normally 2D curves).

    Parameters
    ----------
    coords: :term:`coords_like` (npoints, 3)
        The coordinates of all points used in the definitions of the strokes.
    elems: :term:`varray_like`
        A Varray defining the strokes as a list of point indices. Each row
        should start with the same point that ended the previous stroke.

    Examples
    --------
    >>> X = Coords('0123')
    >>> C = Contour(X, [(0,1), (1,2,3,0)])
    >>> print(C)
    Contour: nparts=2, ncoords=4, closed
    Control points:
    [[0. 0. 0.]
     [1. 0. 0.]
     [1. 1. 0.]
     [0. 1. 0.]]
    Strokes: Varray (nrows=2, width=2..4)
      [0 1]
      [1 2 3 0]
    >>> print(C.elems)
    Varray (nrows=2, width=2..4)
      [0 1]
      [1 2 3 0]
    >>> print(C.nparts)
    2
    >>> print(C.stroke(1))
    BezierSpline: degree=3, nparts=1, ncoords=4, open
      Control points:
    [[1. 0. 0.]
     [1. 1. 0.]
     [0. 1. 0.]
     [0. 0. 0.]]
    >>> print(C.parts(1,2))
    Contour: nparts=1, ncoords=4, open
      Control points:
    [[0. 0. 0.]
     [1. 0. 0.]
     [1. 1. 0.]
     [0. 1. 0.]]
      Strokes: Varray (nrows=1, width=4..4)
      [1 2 3 0]
    """
    def __init__(self, coords, elems):
        super().__init__()
        self.prop = None
        self.coords = Coords(at.checkArray(coords, (-1, 3), 'f'))
        self.elems = Varray(elems)
        wmin, wmax = self.elems.width
        if wmin < 2 or wmax > 4:
            raise ValueError(f"Contour: row length of elems should be"
                             f" in the range [2..4], got [{wmin}..{wmax}]")
        first = self.elems.col(0)
        last = self.elems.col(-1)
        if (first[1:] != last[:-1]).any():
            raise ValueError("elems do not form a continuous contour")
        self.nparts = self.elems.shape[0]
        self.closed = self.elems[0][0] == self.elems[-1][-1]


    def __str__(self):
        return super().__str__() + f"\n  Strokes: {self.elems}"


    def pointsOn(self):
        ind = self.elems.col(0)
        if not self.closed:
            ind = np.concatenate([ind, [self.elems[-1][-1]]])
        return self.coords[ind]

    def pointsOff(self):
        ind = np.unique(np.concatenate([r[1:-1] for r in self.elems]))
        return self.coords[ind]

    def ncoords(self):
        return self.coords.shape[0]

    def endPoints(self):
        """Return start and end points of the curve.

        Returns a Coords with two points, or None if the curve is closed.
        """
        if self.closed:
            return None
        else:
            return self.coords[[0, -1]]

    def points(self, i):
        """Returns the points defining part j of the curve."""
        return self.coords[self.elems[i]]

    def compact(self):
        """Compact the data, removing unused points"""
        pass  # TODO: needs to be implemented

    def parts(self, j, k):
        """Return a Contour only containing parts j to k"""
        # TODO: this should compact the data
        return Contour(self.coords, self.elems.select(range(j, k)))


    def stroke(self, i):
        """Return curve for part i"""
        X = self.points(i)
        degree = len(X) - 1
        if len(X) == 1:
            return PolyLine(X)
        else:
            return BezierSpline(control=X, degree=degree)


    def split(self):
        return [self.stroke(i) for i in range(self.nparts)]


    def sub_points(self, t, j):
        """Return the points at values t in part j

        t can be an array of parameter values, j is a single segment number.
        """
        j = int(j)
        t = np.asarray(t).reshape(-1, 1)
        return self.stroke(j).sub_points(t, 0)


    def sub_directions(self, t, j):
        """Return the directions at values t in part j

        t can be an array of parameter values, j is a single segment number.
        """
        j = int(j)
        t = np.asarray(t).reshape(-1, 1)
        return self.stroke(j).sub_points(t, 0)


    def lengths(self):
        return [self.stroke(i).length() for i in range(self.nparts)]


    def atChordal(self, chordal=0.01, atl=None):
        # Define specialized preapproximation
        if at is None:
            atl = self.atApprox(ndiv=self.elems.lengths)
        return Curve.atChordal(self, chordal, atl)


    def toMesh(self):
        """Convert the Contour to a Mesh."""
        return [self.stroke(i).toMesh() for i in range(self.nparts)]


###########################################################################

# DEPRECATED 2022-08-24

class CardinalSpline(BezierSpline):
    def __init__(self, coords, tension=0.0, closed=False, **kargs):
        utils.warn('depr_cardinalspline')
        super().__init__(coords, curl=(1.-tension)/3., closed=closed)

##############################################################################

# DEPRECATED 2022-11-08

class NaturalSpline(Curve):
    """A class representing a natural spline.

    The use of this class is deprecated. For a closed curve or an open curve
    with endzerocurv=True, BezierSpline gives a good approximation.
    For an open curve with endzerocurv=False, a NurbsCurve obtained with
    nurbs.globalInterpolationCurve will do fine.
    """

    def __init__(self, coords, closed=False, endzerocurv=False):
        """Create a natural spline through the given points.

        coords specifies the coordinates of a set of points. A natural spline
        is constructed through this points.

        closed specifies whether the curve is closed or not.

        endzerocurv specifies the end conditions for an open curve.
        If True, the end curvature will forced to be zero. The default is
        to use maximal continuity (up to the third derivative) between
        the first two splines. The value may be set to a tuple of two
        values to specify different end conditions for both ends.
        This argument is ignored for a closed curve.
        """
        utils.warn('depr_naturlspline')
        super().__init__()
        coords = Coords(coords)
        if closed:
            coords = Coords.concatenate([coords, coords[:1]])
        self.nparts = coords.shape[0] - 1
        self.closed = closed
        if not closed:
            if endzerocurv in [False, True]:
                self.endzerocurv = (endzerocurv, endzerocurv)
            else:
                self.endzerocurv = endzerocurv
        self.coords = coords
        self.compute_coefficients()


    def _set_coords(self, coords):
        C = self.copy()
        C._set_coords_inplace(coords)
        C.compute_coefficients()
        return C


    def compute_coefficients(self):
        n = self.nparts
        M = np.zeros([4*n, 4*n])
        B = np.zeros([4*n, 3])

        # constant submatrix
        m = np.array([[0., 0., 0., 1., 0., 0., 0., 0.],
                      [1., 1., 1., 1., 0., 0., 0., 0.],
                      [3., 2., 1., 0., 0., 0., -1., 0.],
                      [6., 2., 0., 0., 0., -2., 0., 0.]])

        for i in range(n-1):
            f = 4*i
            M[f:f+4, f:f+8] = m
            B[f:f+2] = self.coords[i:i+2]

        # the last spline passes through the last 2 points
        f = 4*(n-1)
        M[f:f+2, f:f+4] = m[:2, :4]
        B[f:f+2] = self.coords[-2:]

        # add the appropriate end constrains
        if self.closed:
            # first and second derivatives at starting and last point
            # (that are actually the same point) are the same
            M[f+2, f:f+4] = m[2, :4]
            M[f+2, 0:4] = m[2, 4:]
            M[f+3, f:f+4] = m[3, :4]
            M[f+3, 0:4] = m[3, 4:]

        else:
            if self.endzerocurv[0]:
                # second derivatives at start is zero
                M[f+2, 0:4] = m[3, 4:]
            else:
                # third derivative is the same between the first 2 splines
                M[f+2, [0, 4]] = np.array([6., -6.])

            if self.endzerocurv[1]:
                # second derivatives at end is zero
                M[f+3, f:f+4] = m[3, :4]
            else:
                # third derivative is the same between the last 2 splines
                M[f+3, [f-4, f]] = np.array([6., -6.])

        # calculate the coefficients
        C = np.linalg.solve(M, B)
        self.coeffs = np.array(C).reshape(-1, 4, 3)


    def sub_points(self, t, j):
        C = self.coeffs[j]
        U = np.column_stack([t**3., t**2., t, np.ones_like(t)])
        X = np.dot(U, C)
        return X

##############################################################################
## circles and arcs

def circle():
    """Create a BezierSpline approximation of a circle.

    Returns
    -------
    BezierSpline
        A closed BezierSpline through 8 points lying on a circle x,y plane,
        with its center at (0,0,0) and having a radius 1.

    Notes
    -----
    The result can easily be scaled, translated or rotated to create other
    circles. It is adequate for drawing circles, though it doesn't exactly
    represent a circle.

    See Also
    --------
    Arc: create exact representation of circles and arcs.
    """
    pts = Formex([1.0, 0.0, 0.0]).rosette(8, 45.).coords.reshape(-1, 3)
    return BezierSpline(pts, curl=0.375058, closed=True)


class Arc(Curve):
    """A class representing a circular arc.

    The arc can be specified in one of three ways:

    - by specifying 3 points on the arc: the begin point,
      an intermediate point and the end point. Use the p3 argument to use
      this method.
    - by specifying the center and the begin and end points: use the cbe
      argument.
    - by the general method specifying the center, radius, normal, and
      begin and end angles of the arc.

    Parameters
    ----------
    p3: :term:`coords_like` (3,3)
        The coordinates of three subsequent points on the arc: the begin
        point, an intermediate point and the end point. The three points
        should obviously not be colinear, with one exception: if the begin
        and end points coincide, a full circle is created, and the `normal`
        argument is used to help with orienting the circle's plane.
        If `p3` is provided, all other arguments but `normal` are disregarded.
    cbe: :term:`coords_like` (3,3)
        The coordinates of the center and the begin and end points of the arc.
        The three points should not be colinear. Even then, the problem has
        always two solutions, depending on the choice of the positive normal
        on the plane of the three points. Those two solutions form a full
        circle. The chosen solution is the  one that corresponds with a positive
        normal pointing to the same side of the plane as the specified `normal`
        vector. If `cbe` method is used (and no `p3` is provided), all other
        arguments but `normal` are disregarded.
    center: :term:`coords_like` (3,)
        The center point of the arc.
    radius: float
        The radius of the arc.
    normal: :term:`coords_like` (3,)
        The normal on the plane of the arc. The arc is constructed in the
        x,y plane and then the z-axis is rotated to the specified normal
        direction.
    angles: (float, float)
        The start and end angles of the arc, by default in degrees.
    angle_spec: float
        A multiplier that turns the angles into radians. The default
        expects the angles to be degrees.

    Examples
    --------
    Three ways to construct a full unit circle in the x,y plane:

    >>> A = Arc(center=[0.,0.,0.], radius=1., angles=(0., 360.))
    >>> B = Arc(cbe=[[0.,0.,0.], [1.,0.,0.], [1.,0.,0.]])
    >>> C = Arc(p3=[[1.,0.,0.], [-1.,0.,0.], [1.,0.,0.]])
    >>> print(A,B,C)
    Arc
      Center [0. 0. 0.], Radius 1., Normal [0. 0. 1.]
      Angles=(0.0, 360.0)
      P0=[1. 0. 0.]; P1=[-1.  0.  0.]; P2=[ 1. -0.  0.]
    Arc
      Center [0. 0. 0.], Radius 1., Normal [0. 0. 1.]
      Angles=(0.0, 360.0)
      P0=[1. 0. 0.]; P1=[-1.  0.  0.]; P2=[1. 0. 0.]
    Arc
      Center [0. 0. 0.], Radius 1., Normal [0. 0. 1.]
      Angles=(0.0, 360.0)
      P0=[1. 0. 0.]; P1=[-1.  0.  0.]; P2=[1. 0. 0.]

    Three ways to constructing the right half of that circle:

    >>> A = Arc(center=[0.,0.,0.], radius=1., angles=(-90., 90.))
    >>> B = Arc(cbe=[[0.,0.,0.], [0.,-1.,0.], [0.,1.,0.]])
    >>> C = Arc(p3=[[0.,-1.,0.], [1.,0.,0.], [0.,1.,0.]])
    >>> print(A,B,C)
    Arc
      Center [0. 0. 0.], Radius 1., Normal [0. 0. 1.]
      Angles=(270.0, 450.0)
      P0=[-0. -1.  0.]; P1=[ 1. -0.  0.]; P2=[0. 1. 0.]
    Arc
      Center [0. 0. 0.], Radius 1., Normal [0. 0. 1.]
      Angles=(270.0, 450.0)
      P0=[ 0. -1.  0.]; P1=[ 1. -0.  0.]; P2=[0. 1. 0.]
    Arc
      Center [0. 0. 0.], Radius 1., Normal [0. 0. 1.]
      Angles=(270.0, 450.0)
      P0=[ 0. -1.  0.]; P1=[1. 0. 0.]; P2=[0. 1. 0.]
    """
    def __init__(self, *, p3=None, cbe=None, center=(0., 0., 0.), radius=1.,
                 normal=(0., 0., 1.), angles=(0., 360.), angle_spec=at.DEG):
        """Initialize the arc."""
        super().__init__()
        self.nparts = 1
        self.closed = False  # TODO: derive from angles
        if p3 is not None:
            # 3 points on the arc
            points = Coords(p3)
            if points.shape != (3, 3):
                raise ValueError("Expected 3 points for p3")
            if np.allclose(points[0], points[2]):
                # first and last point are coincident
                # we have a full circle with normal given by argument
                radius = at.length(points[1] - points[0]) / 2
                center = (points[0] + points[1]) / 2
            else:
                r, c, n = gt.triangleCircumCircle(points.reshape(1, 3, 3))
                if np.isnan(r).any():
                    raise ValueError(
                        "The three points are colinear and the first "
                        "and last point do not coincide")
                radius, center, normal = r[0], c[0], n[0]
            angles = gt.rotationAngle(
                Coords([1., 0., 0.]).rotate(at.rotMatrix2([0., 0., 1.], normal)),
                points[[0, 2]], normal, angle_spec)
        elif cbe is not None:
            # center, begin, end
            points = Coords(cbe)
            if points.shape != (3, 3):
                raise ValueError("Expected 3 points for cbe")
            center = points[0].copy()
            v = points[1:] - center
            radius = at.length(v[0])
            n = at.normalize(np.cross(v[0], v[1]))
            if np.isnan(n).any():
                # cbe points are colinear: try to use normal
                n = at.orthog(normal, v[0])
                if np.isnan(n).any():
                    n = at.any_perp(v[0])
            else:
                if normal is not None:
                    normal = at.checkArray(normal, shape=(3,))
                    if n @ normal < 0.:
                        # flip the normal
                        n = -n
            normal = n
            angles = gt.rotationAngle(
                Coords([1., 0., 0.]).rotate(
                    at.rotMatrix2([0., 0., 1.], normal)), v, normal, angle_spec)
            points[0] = points[1]  # move beginpoint to first position
        else:
            # general method
            center = np.asarray(center).reshape(3)
            radius = float(radius)
            normal = np.asarray(normal).reshape(3)
            angles = (float(angles[0]), float(angles[1]))

        self.center = center
        self.radius = radius
        self.normal = at.normalize(normal)
        self.angles = _fix_angles(*angles)
        if p3 is not None:
            pass
        elif cbe is not None:
            points[1] = self.sub_points(np.array([0.5]), 0)[0]
        else:
            points = self.sub_points(np.array([0.0, 0.5, 1.0]), 0)
        self.coords = points


    @property
    def points(self, j=None, k=None):
        return self.coords

    def __repr__(self):
        return f"Arc(p3={self.coords.tolist()})"

    def __str__(self):
        return f"""\
Arc
  Center {self.center}, Radius {_g(self.radius)}, Normal {self.normal}
  Angles={self.angles}
  P0={self.points[0]}; P1={self.points[1]}; P2={self.points[2]}
"""

    def sub_points(self, t, j):
        a = t*(self.angles[-1]-self.angles[0])
        X = Coords(np.column_stack([at.cosd(a), at.sind(a), np.zeros_like(a)]))
        X = X.scale(self.radius).rotate(self.angles[0]).rotate(
            at.rotMatrix2([0., 0., 1.], self.normal)).translate(self.center)
        return X


    def sub_directions(self, t, j):
        a = t*(self.angles[-1]-self.angles[0])
        X = Coords(np.column_stack([-at.sind(a), at.cosd(a), np.zeros_like(a)]))
        X = X.rotate(self.angles[0]).rotate(
            at.rotMatrix2([0., 0., 1.], self.normal))
        return X


    def approx(self, ndiv=None, chordal=0.001):
        """Return a PolyLine approximation of the Arc.

        Approximates the Arc by a sequence of inscribed straight line
        segments.

        If `ndiv` is specified, the arc is divided in precisely `ndiv`
        segments.

        If `ndiv` is not given, the number of segments is determined
        from the chordal distance tolerance. It will guarantee that the
        distance of any point of the arc to the chordal approximation
        is less or equal than `chordal` times the radius of the arc.
        """
        if ndiv is None:
            phi = 2. * np.arccos(1.-chordal)
            rng = abs(self.angles[1] - self.angles[0]) * at.DEG
            ndiv = int(np.ceil(rng/phi))
            # print(ndiv)
        return Curve.approx(self, ndiv=ndiv)


def arc2points(x0, x1, R, pos='-'):
    """Create an arc between two points

    Given two points x0 and x1, this constructs an arc with radius R
    through these points. The two points should have the same z-value.
    The arc will be in a plane parallel with the x-y plane and wind
    positively around the z-axis when moving along the arc from x0 to x1.

    If pos == '-', the center of the arc will be at the left when going
    along the chord from x0 to x1, creating an arc smaller than a half-circle.
    If pos == '+', the center of the arc will be at the right when going
    along the chord from x0 to x1, creating an arc larger than a half-circle.

    If R is too small, an exception is raised.
    """
    if x0[2] != x1[2]:
        raise ValueError("The points should b in a plane // xy plane")
    xm = (x0+x1) / 2  # center of points
    xd = (x0-x1) / 2  # half length vector
    do = at.normalize([xd[1], -xd[0], 0])  # direction of center
    xl = np.dot(xd, xd)    # square length
    if R**2 < xl:
        raise ValueError(f"The radius should at least be {np.sqrt(xl)}")
    dd = np.sqrt(R**2 - xl)   # distance of center to xm
    if pos == '+':
        xc = xm - dd * do  # Center is to the left when going from x0 to x1
    else:
        xc = xm + dd * do

    xx = [1., 0., 0.]
    xz = [0., 0., 1.]
    angles = gt.rotationAngle([xx, xx], [x0-xc, x1-xc], m=[xz, xz])
    if dir == '-':
        angles = reversed(angles)
    xc[2] = x0[2]
    return Arc(center=xc, radius=R, angles=angles)


# TODO: implement this
# class Spiral(Curve):
#     """A class representing a spiral curve."""

#     def __init__(self, turns=2.0, nparts=100, rfunc=None):
#         Curve.__init__(self)
#         # TODO: implement the rfunc
#         if rfunc is None:
#             rfunc = lambda x: x
#         self.coords = Coords([0., 0., 0.]).replic(npoints+1).hypercylindrical()
#         self.nparts = nparts
#         self.closed = False


##############################################################################
# Other functions


def _g(value, precision=None):
    """Format a float in g format but add a trailing dot if None

    >>> print(f"{1.27:g} {1.00:g}")
    1.27 1
    >>> print(f"{_g(1.27)} {_g(1.00)}")
    1.27 1.
    """
    s = f"{value:g}"
    if '.' not in s:
        s += '.'
    return s


def _fix_angles(angle0, angle1):
    """Sanitize angles

    Given two angles in degrees, this makes sure that
    - angle1 > angle0
    - angle0 in range [0, 360]
    - angle1 in range ]0, 720]

    Returns
    -------
    angle0: float
        The first angle, in the range [0, 360[
    angle1: float
        The second angle, in the range ]0, 720[ and > angle0.

    Examples
    --------
    >>> _fix_angles(360,720)
    (0.0, 360.0)
    >>> _fix_angles(750,10)
    (30.0, 370.0)
    >>> _fix_angles(-30,-100)
    (330.0, 620.0)
    """
    angle0 %= 360.
    angle1 %= 360.
    if angle1 <= angle0:
        angle1 += 360
    return angle0, angle1


# Keep binomial as an alias for compatibilty
binomial = math.comb

@cache
def binomialCoeffs(p):
    """Compute all binomial coefficients for a given degree p.

    Parameters
    ----------
    p: int
        Degree of the binomial

    Returns
    -------
    array:
        An array of p+1 float values.

    Notes
    -----
    The results of this function are cached to allow multiple calls without
    the need for recomputing.

    Examples
    --------
    >>> print(binomialCoeffs(4))
    [1 4 6 4 1]
    """
    return np.array([binomial(p, i) for i in range(p+1)])


@cache
def bezierPowerMatrix(p):
    """Compute the Bezier to power curve transformation matrix for degree p.

    Bezier curve representations can be converted to power curve representations
    using the coefficients in this matrix.

    Returns a (p+1,p+1) shaped array with a zero upper triangular part.

    For efficiency reasons, the computed values are stored in the module,
    in a dict with p as key. This allows easy and fast lookup of already
    computed values.

    Notes
    -----
    The results of this function are cached to allow multiple calls without
    the need for recomputing.

    Examples
    --------
    >>> print(bezierPowerMatrix(3))
    [[ 1.  0.  0.  0.]
     [-3.  3.  0.  0.]
     [ 3. -6.  3.  0.]
     [-1.  3. -3.  1.]]
    """
    M = np.zeros((p+1, p+1))
    # Set corner elements
    M[0, 0] = M[p, p] = 1.0
    M[p, 0] = -1.0 if p % 2 else 1.0
    # Compute first column, last row and diagonal
    sign = -1.0
    for i in range(1, p):
        M[i, i] = binomialCoeffs(p)[i]
        M[i, 0] = M[p, p-i] = sign*M[i, i]
        sign = -sign
    # Compute remaining elements
    k1 = (p+1)//2
    pk = p-1
    for k in range(1, k1):
        sign = -1.0
        for j in range(k+1, pk+1):
            M[j, k] = M[pk, p-j] = \
                sign * binomialCoeffs(p)[k] * binomialCoeffs(p-k)[j-k]
            sign = -sign
        pk -= 1
    return M


def deCasteljau(P, u):
    """Compute points on a Bezier curve using deCasteljau algorithm

    Parameters:

    P is an array with n+1 points defining a Bezier curve of degree n.
    u is a single parameter value between 0 and 1.

    Returns:

    A list with point sets obtained in the subsequent deCasteljau
    approximations. The first one is the set of control points, the last one
    is the point on the Bezier curve.

    This function works with Coords as well as Coords4 points.
    """
    n = P.shape[0]-1
    C = [P]
    for k in range(n):
        Q = C[-1]
        Q = (1.-u) * Q[:-1] + u * Q[1:]
        C.append(Q)
    return C


def splitBezier(P, u):
    """Split a Bezier curve at parametric values

    Parameters:

    P is an array with n+1 points defining a Bezier curve of degree n.
    u is a single parameter value between 0 and 1.

    Returns two arrays of n+1 points, defining the Bezier curves of degree n
    obtained by splitting the input curve at parametric value u. These results
    can be used with the control argument of BezierSpline to create the
    corresponding curve.

    This works for u < 0 and u > 1, to extend the curve.
    If u < 0, the left part is returned reverse, if u

    """
    C = deCasteljau(P, u)
    L = np.stack([x[0] for x in C])
    R = np.stack([x[-1] for x in C[::-1]])
    return L, R

# End
