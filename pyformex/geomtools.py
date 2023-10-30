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
"""Basic geometrical operations.

This module defines some basic operations on simple geometrical entities
such as points, lines, planes, vectors, segments, triangles, circles.

The operations include intersection, projection, distance computing.

Many of the functions in this module are exported as methods on the
:class:`Coords` and the :class:`Geometry` derived classes.


Renamed functions::

    intersectionPointsLWL    -> intersectLineWithLine
    intersectionTimesLWL     -> intersectLineWithLine
    intersectionPointsLWP    -> intersectLineWithPlane
    intersectionTimesLWP     -> intersectLineWithPlane
    intersectionTimesSWP     -> intersectSegmentWithPlane
    intersectionSWP          -> intersectSegmentWithPlane
    intersectionPointsSWP    -> intersectSegmentWithPlane

    intersectionTimesPOP     -> projectPointOnPlane
    intersectionPointsPOP    -> projectPointOnPlane
    intersectionTimesPOL     -> projectPointOnLine
    intersectionPointsPOL    -> projectPointOnLine

    distancesPFL             -> distanceFromLine
    distancesPFS             -> distanceFromLine


Planned renaming of functions::

    lineIntersection         -> to be removed (or intersect2DLineWithLine)
    projectionVOV            -> projectVectorOnVector
    projectionVOP            -> projectVectorOnPlane

    pointsAtLines            -> pointOnLine
    pointsAtSegments         -> pointOnSegment
    intersectionTimesLWT     -> intersectLineWithTriangle
    intersectionPointsLWT    -> intersectLineWithTriangle
    intersectionTimesSWT     -> intersectSegmentWithTriangle
    intersectionPointsSWT    -> intersectSegmentWithTriangle
    intersectionPointsPWP    -> intersectThreePlanes
    intersectionLinesPWP     -> intersectTwoPlanes (or intersectPlaneWithPlane)
    intersectionSphereSphere -> intersectTwoSpheres (or intersectSphereWithSphere)

"""
import numpy as np

from pyformex import arraytools as at
from pyformex import utils
from pyformex import multi
from pyformex.coords import Coords
from pyformex.connectivity import Connectivity


class Lines():
    """A collection of lines, half-lines(rays) or segments.

    This class is intended as a common interface for a collection of
    lines, half-lines or segments. Many functions in the geomtools
    module operate on lines (or rays, or segments). Sometimes these
    are specified by two points, while in other case they need to be
    specified by one point and a vector.
    Also the user might store his line data in one of these two ways,
    and it is annoying and not effective to have to convert between
    these two multiple times.

    Then this class comes as a help. It is a lightweight class that
    can store lines, rays or segments. The class itself does not
    discriminate between these: the user is responsible for the
    interpretation. This is further complicated by the fact that the
    data structure of a vector is the same as that of a point.

    In what follows, a line can mean any of:

    - a full twosided infinite line,
    - a ray starting at some point and infinite in one direction,
    - a finite straight segment between two points.

    A Lines instance can be initialized by any of the following data:

    - a :term:`coords_like` object with shape (nlines, 2, 3),
      containing the coordinates of two points on each of the
      ``nlines`` lines. This is the natural way to specify segments,
      but it can be used for infinite lines and rays as well.
    - a tuple of two :term:`coords_like` objects, each with shape
      (nlines, 2, 3). The first contains a point on each of the lines,
      the second is a vector along the line. The vectors do not need
      to be unit length vectors. They typically will not be if this
      method is used to specify segments.
    - another Lines instance. In this case a shallow copy of the Lines
      is created, sharing its data with the input Lines.
      This is a convenience allowing the user to pass raw data as well
      as data already converted to a Lines instance in places where
      line data are expected.

    Parameters
    ----------
    data: :term:`coords_like` | tuple | Lines
        A :term:`coords_like` argument should have a shape (nlines,2,3)
        and defines ``nlines`` lines by the coordinates of two points
        on each of the lines.

        A tuple should contain two (nlines,3) shaped :term:`coords_like`
        structures. The first holds a point on the lines, the second
        a vector along the lines.

        If a Lines instance is specified as data, a shallow copy sharing
        the same data is created.


    A Lines instance has the following attributes (onbly the first two are
    actually stored):

    Attributes
    ----------
    p: array (nlines,3)
        The first point of the Lines.
    n: array (nlines,3)
        The vector from the first to the second point.
    coords: Coords (nlines, 2, 3)
        A :class:`~coords.Coords` containing both points on the lines.

    Examples
    --------
    Create Lines from two points.

    >>> L = Lines([[[2.,0.,0.],[2.,3.,0.]], [[0.,1.,0.],[1.,1.,0.]]])
    >>> print(L.p)
    [[2.  0.  0.]
     [0.  1.  0.]]
    >>> print(L.n)
    [[0.  3.  0.]
     [1.  0.  0.]]
    >>> L.coords
    Coords([[[2.,  0.,  0.],
             [2.,  3.,  0.]],
    <BLANKLINE>
            [[0.,  1.,  0.],
             [1.,  1.,  0.]]])

    Create the same Lines from one point and a vector.

    >>> M = Lines(([[2.,0.,0.],[0.,1.,0.]], [[0.,3.,0.],[1.,0.,0.]]))
    >>> print((M.p == L.p).all() and (M.n == L.n).all())
    True
    >>> print(id(M.p) == id(L.p) and id(M.n) == id(L.n))
    False

    Create a shallow copy.

    >>> M = Lines(L)
    >>> print((M.p == L.p).all() and (M.n == L.n).all())
    True
    >>> print(id(M.p) == id(L.p) and id(M.n) == id(L.n))
    True

    """

    _exclude_members_ = ['coords']

    def __init__(self, data):
        """Initialize the Lines instance."""
        if isinstance(data, Lines):
            self.p, self.n = data.p, data.n
        elif isinstance(data, tuple):
            p = at.checkArray(data[0], shape=(-1, 3))
            n = at.checkArray(data[1], shape=(p.shape[0], 3))
            self.p, self.n = p, n
        else:  # should have shape (nlines,2,3)
            P = at.checkArray(data, shape=(-1, 2, 3))
            self.p, self.n = P[:, 0], P[:, 1] - P[:, 0]

    @property
    def coords(self):
        """Return the start and end points."""
        return Coords(np.stack([self.p, self.p+self.n], axis=1))

    def toFormex(self):
        # This allows drawing the Lines (as segments)
        """Convert a Lines to a 2-plex Formex.

        Returns
        -------
        :Formex (nlines, 2, 3)
            A plex-2 Formex representing the Lines.

        Notes
        -----
        When drawn, the Lines will always be represented as straight line
        segments, even if they represent infinitely long lines.

        Examples
        --------
        >>> L = Lines([[[2.,0.,0.],[2.,3.,0.]], [[0.,1.,0.],[1.,1.,0.]]])
        >>> print(L.toFormex().asFormex())
        {[2.0,0.0,0.0; 2.0,3.0,0.0], [0.0,1.0,0.0; 1.0,1.0,0.0]}

        """
        from pyformex.formex import Formex
        return Formex(self.coords)


#################### low level functions ###############################

# TODO: Make these into Lines methods?

def pointsAtLines(q, m, t):
    """Return the points of lines (q,m) at parameter values t.

    Parameters
    ----------
    q: float array (..., 3)
        Array with (starting) points of a collection of lines.
    m: float array (..., 3)
        Array with vectors along the lines, broadcast compatible with q.
        The vectors do not need to have unit length.
    t: float array
        Array with parameter values, broadcast compatible with q[...]
        and m[...].
        Parametric value 0 is at point q, parametric value 1 is at q + m.

    Returns
    -------
    Coords:
        A Coords array with the points at parameter values t.

    """
    t = t[..., np.newaxis]
    with np.errstate(all='ignore'):
        x = q + t*m
    return Coords(x)


def pointsAtSegments(S, t):
    """Return the points of line segments S at parameter values t.

    Parameters
    ----------
    S: float array (..., 2, 3)
        A collection of line segments defined by two points.
    t: float array
        Array with parameter values, broadcast compatible with S[...].
        Parametric value 0 is at point 0, parametric value 1 is at point 1.

    Returns
    -------
    Coords:
        A Coords array with the points at parameter values t.

    """
    q0 = S[..., 0, :]
    q1 = S[..., 1, :]
    return pointsAtLines(q0, q1-q0, t)


################## intersection #######################

def intersectLineWithLine(q1, m1, q2, m2, mode='all', times=False):
    """Find the common perpendicular of lines (q1,m1) and lines (q2,m2).

    Return the intersection points of lines (q1,m1) and lines (q2,m2)
    with the perpendiculars between them. For intersecting lines, the
    corresponding points will coincide.

    Parameters
    ----------
    q1: float array (nq1, 3)
        Points on the first set of lines.
    m1: float array (nq1, 3)
        Direction vectors of the first set of lines.
    q2: float array (nq2, 3)
        Points on the second set of lines.
    m2: float array (nq2, 3)
        Direction vectors of the second set of lines.
    mode: 'all' | 'pair'
        If 'all', the intersection of all lines (q1,m1) with all lines
        (q2,m2) is computed; nq1 and nq2 can be different.
        If 'pair', nq1 and nq2 should be equal (or 1) and the
        intersection of pairs of lines is computed (using broadcasting
        for length 1 data).
    times: bool
        If True, return the parameter values of the intersection
        points instead of the coordinates (see Notes).

    Returns
    -------
    ar1: float array
        The intersection points of the common perpendiculars with the first
        set of lines. See Notes.
    ar2: float array
        The intersection points of the common perpendiculars with the second
        set of lines. See Notes.

    Notes
    -----
    By default (``times=False``) the returned arrays are the coordinates of
    the points, with shape (nq1,nq2,3) for mode 'all' and (nq1,3) for
    mode 'pair'.
    With ``times=True`` the return values are the parameter values of the
    intersection points, and the size opf the arrays is (nq1,nq2) for
    mode 'all' and (nq1,) for mode 'pair'.

    The coordinates of a point with parameter value t on a line (q,m)
    are given by ``q + t * m``.

    The intersection of two parallel lines results in NAN-values. These are
    not removed from the result. The user has to do it himself if needed.

    Examples
    --------
    >>> q,m = [[0,0,0],[0,0,1],[0,0,3]], [[1,0,0],[1,1,0],[0,1,0]]
    >>> p,n = [[2.,0.,0.],[0.,0.,0.]], [[0.,1.,0.],[0.,0.,1.]]
    >>> x1,x2 = intersectLineWithLine(q,m,p,n)
    >>> print(x1)
    [[[ 2.  0.  0.]
      [ 0.  0.  0.]]
    <BLANKLINE>
     [[ 2.  2.  1.]
      [ 0.  0.  1.]]
    <BLANKLINE>
     [[nan nan nan]
      [ 0.  0.  3.]]]
    >>> print(x2)
    [[[ 2.  0.  0.]
      [ 0.  0.  0.]]
    <BLANKLINE>
     [[ 2.  2.  0.]
      [ 0.  0.  1.]]
    <BLANKLINE>
     [[nan nan nan]
      [ 0.  0.  3.]]]

    >>> x1,x2 = intersectLineWithLine(q[:2],m[:2],p,n,mode='pair')
    >>> print(x1)
    [[2. 0. 0.]
     [0. 0. 1.]]
    >>> print(x2)
    [[2. 0. 0.]
     [0. 0. 1.]]

    >>> t1,t2 = intersectLineWithLine(q,m,p,n,times=True)
    >>> print(t1)
    [[ 2. -0.]
     [ 2. -0.]
     [nan -0.]]
    >>> print(t2)
    [[-0. -0.]
     [ 2.  1.]
     [nan  3.]]

    >>> t1,t2 = intersectLineWithLine(q[:2],m[:2],p,n,mode='pair',times=True)
    >>> print(t1)
    [ 2. -0.]
    >>> print(t2)
    [-0.  1.]

    """
    if mode == 'all':
        shape1 = (-1, 1, 3)
        shape2 = (1, -1, 3)
    else:
        shape1 = shape2 = (-1, 3)
    q1 = at.checkArray(q1, kind='f', allow='i').reshape(shape1)
    m1 = at.checkArray(m1, kind='f', allow='i').reshape(shape1)
    q2 = at.checkArray(q2, kind='f', allow='i').reshape(shape2)
    m2 = at.checkArray(m2, kind='f', allow='i').reshape(shape2)

    dot11 = at.dotpr(m1, m1)
    dot22 = at.dotpr(m2, m2)
    dot12 = at.dotpr(m1, m2)
    denom = (dot12**2-dot11*dot22)
    q12 = q2-q1
    dot11 = dot11[..., np.newaxis]
    dot22 = dot22[..., np.newaxis]
    dot12 = dot12[..., np.newaxis]
    with np.errstate(all='ignore'):
        t1 = at.dotpr(q12, m2*dot12-m1*dot22) / denom
        t2 = at.dotpr(q12, m2*dot11-m1*dot12) / denom
        if times:
            return t1, t2
        else:
            return pointsAtLines(q1, m1, t1), pointsAtLines(q2, m2, t2)


def intersectLineWithPlane(q, m, p, n, mode='all', times=False):
    """Find the intersection of lines (q,m) and planes (p,n).

    Parameters
    ----------
    q: float array (nq, 3)
        Points on the nq lines. A first dimension 1 will be broadcasted
        to size of ``m``.
    m: float array (nq, 3)
        Direction vectors of nq lines. A first dimension 1 will be
        broadcasted to size of ``q``.
    p: float array (np, 3)
        Points on the np planes. A first dimension 1 will be broadcasted
        to size of ``n``.
    n: float array (np, 3)
        Direction vectors of the np planes (i.e. perpendicular on the planes).
        A first dimension 1 will be broadcasted to size of ``p``.
    mode: 'all' | 'pair'
        If 'all', the intersection of all lines (q,m) with all planes
        (p,n) is computed; nq and np can be different.
        If 'pair', nq and np should be equal (or 1) and the
        pairwise intersection lines and planes is computed.
    times: bool
        If True, return the parameter values of the intersection
        points instead of the coordinates.

    Returns
    -------
    ar: float array
        If times is False (default) returns the intersection points of the
        lines and the planes. If mode=='all' (default), the shape is
        (nq,np,3), while for mode=='all' the shape is (nq,3) (with nq==np).

        If times is True, returns parameter values t, such that the
        intersection points are given by q+t*m. The shape of the array is
        (nq,np) for mode=='all' and (nq,) for mode='pair'.

    Notes
    -----
    The result will contain an INF value for lines that are
    parallel to the plane.

    Examples
    --------
    >>> q,m = [[0,0,0],[0,1,0],[0,0,3]], [[1,0,0],[0,1,0],[0,0,1]]
    >>> p,n = [[1.,1.,1.],[1.,1.,1.]], [[1.,1.,0.],[1.,1.,1.]]

    >>> t = intersectLineWithPlane(q,m,p,n,times=True)
    >>> print(t)
    [[ 2.  3.]
     [ 1.  2.]
     [inf  0.]]
    >>> x = intersectLineWithPlane(q,m,p,n)
    >>> print(x)
    [[[ 2.  0.  0.]
      [ 3.  0.  0.]]
    <BLANKLINE>
     [[ 0.  2.  0.]
      [ 0.  3.  0.]]
    <BLANKLINE>
     [[nan nan inf]
      [ 0.  0.  3.]]]
    >>> x = intersectLineWithPlane(q[:2],m[:2],p,n,mode='pair')
    >>> print(x)
    [[2. 0. 0.]
     [0. 3. 0.]]

    """
    q = at.checkArray(q, (-1, 3), 'f', 'i')
    m = at.checkArray(m, (-1, 3), 'f', 'i')
    p = at.checkArray(p, (-1, 3), 'f', 'i')
    n = at.checkArray(n, (-1, 3), 'f', 'i')

    with np.errstate(divide='ignore', invalid='ignore'):
        if mode == 'all':
            t = (at.dotpr(p, n) - np.inner(q, n)) / np.inner(m, n)
        elif mode == 'pair':
            t = at.dotpr(n, p-q) / at.dotpr(m, n)

    if times:
        return t
    else:
        if mode == 'all':
            q = q[:, np.newaxis]
            m = m[:, np.newaxis]
        return pointsAtLines(q, m, t)


def intersectSegmentWithPlane(s, p, n, mode='all', atol=0., returns='x'):
    """Find the intersection of line segments S with planes (p,n).

    Parameters
    ----------
    s: float array (ns, 2, 3)
        ns line segments each defined by two points.
    p: float array (np, 3)
        Points on the np planes. A first dimension 1 will be broadcasted
        to size of ``n``.
    n: float array (np, 3)
        Direction vectors of the np planes (i.e. perpendicular on the planes).
        A first dimension 1 will be broadcasted to size of ``p``.
    mode: 'all' | 'pair'
        If 'all', the intersection of all segments S with all planes
        (p,n) is computed; ns and np can be different.
        If 'pair', ns and np should be equal (or 1) and the
        pairwise intersection lines and planes is computed.
    atol: float
        A tolerance in the determination whether a point is inside a
        segment or not.
    returns: str
        A string defining what is to be returned. The string can contain
        the three characters 't', 'x' and 'i', which will return the
        following data:

        - 't': the parametric values of the intersection points along the
          segments
        - 'x': the coordinates of the intersection points
        - 'i': the indices of segments and planes corresponding with the
          intersection points and parameter values

        If the value contains an 'i', then only the actual intersection
        points are returned. If no 'i' is included, intersection values
        't' and 'x' are returned for all combinations of segments and planes
        (depending on the mode). The results will then include INF
        values where a plane does not cut a segment.

        A value ``returns='t'`` is equivalent with::

          intersectLineWithPlane(s[:,0], s[:,1]-s[:,0], p, n, mode, times=True)

    Returns
    -------
    t: float array
        The parameter values such that the intersection points are given
        by ``(1-t)*s[:,0] + t*s[:,1]``. The shape of the array is (ns,np)
        for mode=='all' and (ns,) for mode='pair'. Only returned if
        ``returns`` contains a 't'.
    x: float array (nx,3)
        The actual intersection points of the segments. Segments that are
        completely at one side of the plane do not intersect.
        Only returned if ``returns`` contains an 'x'.
    ind: int array
        Index array identifying the line segments and planes that gave rise
        to the intersection points x. For mode='all' the shape is (nx,2):
        the first column contains the line segment indices, the second column
        holds the plane indices. For mode='pair' the shape is (nx,) and the
        indices are the same for line and plane.
        Only returned if ``returns`` contains an 'i'.

    Examples
    --------
    Three line segments and three planes:

    >>> X = np.array([
    ...     [(0, 0, 0), (1., 0, 0)],
    ...     [(1, 0, 0), (1., 1, 0)],
    ...     [(1, 1, 0), (0., 0, 0)]])
    >>> P = np.array([(0.3,0,0), (0.5,0.5,0), (0.7,0,0)])
    >>> n = np.array([(1.0,0,0), (0,1.0,0), (1.0, -1.0,0)])

    Compute the intersection points of the three lines with the first
    two planes.

    >>> intersectSegmentWithPlane(X, P[:2], n[:2], returns='x')
    Coords([[0.3, 0. , 0. ],
            [1. , 0.5, 0. ],
            [0.3, 0.3, 0. ],
            [0.5, 0.5, 0. ]])

    Compute the intersection parameter values

    >>> intersectSegmentWithPlane(X, P[:2], n[:2], returns='t')
    array([[ 0.3,  inf],
           [-inf,  0.5],
           [ 0.7,  0.5]])

    Compute the intersection points and the indices:

    >>> x, ind = intersectSegmentWithPlane(X, P[:2], n[:2], returns='xi')
    >>> print(x)
    [[0.3  0.   0. ]
     [1.   0.5  0. ]
     [0.3  0.3  0. ]
     [0.5  0.5  0. ]]
    >>> print(ind)
    [[0 0]
     [1 1]
     [2 0]
     [2 1]]

    Compute the pairwise intersection for three lines and planes:

    >>> x, ind = intersectSegmentWithPlane(X, P, n, mode='pair', returns='xi')
    >>> print(x)
    [[0.3  0.   0. ]
     [1.   0.5  0. ]]
    >>> print(ind)
    [0 1]

    Computer the pairwise intersection with a single plane (uses broadcasting):

    >>> x, t = intersectSegmentWithPlane(X, P[0], n[0], mode='pair',
    ...     returns='xt')
    >>> print(x)
    [[ 0.3  0.   0. ]
     [ nan -inf  nan]
     [ 0.3  0.3  0. ]]
    >>> print(t)
    [ 0.3 -inf  0.7]
    """
    s = at.checkArray(s, (-1, 2, 3), 'f', 'i')
    p = np.reshape(p, (-1, 3))
    n = np.reshape(n, (-1, 3))
    q = s[..., 0, :]
    m = s[..., 1, :] - q
    t = intersectLineWithPlane(q, m, p, n, mode=mode, times=True)
    if returns == 't':
        return t

    # Find the actual intersections
    ok = (t >= 0.0-atol) * (t <= 1.0+atol)
    if 'i' in returns:
        # remember the indices
        if mode == 'all':
            i = np.column_stack(np.where(ok))
        elif mode == 'pair':
            s = s[ok]
            t = t[ok]
            i = np.where(ok)[0]
    if len(t) > 0:
        if mode == 'all':
            s = s[:, np.newaxis]
        x = pointsAtSegments(s, t)
        if x.ndim == 1:
            np.reshape(x, (1, 3))
        if mode == 'all':
            x = x[ok]
    else:
        # No intersection: return empty Coords
        x = Coords()

    # Prepare return value
    d = locals()  # Do not put locals() in the following statement!
    if len(returns) == 1:
        return d[returns]
    else:
        return tuple(d[c] for c in returns[:3])


def intersectLineWithTriangle(T, p, p1, method='line', atol=1.e-5):
    # TODO: add an optional argument return_index to return the index
    #       put index rows in order of intersection points
    #       change parameters p, p1 to single L (nlines,2,3) ???
    """Compute the intersection points with a set of lines.

    Parameters
    ----------
    T: :term:`coords_like` (ntri,3,3)
        The coordinates of the three vertices of ntri triangles.
    p: :term:`coords_like` (nlines,3)
        A first point for each of the lines to intersect.
    p1: :term:`coords_like` (nlines,3)
        The second point defining the lines to intersect.
    method: 'line' | 'segment' | ' ray'
        Define whether the points ``p`` and ``p1`` define an infinitely
        long line, a finite segment p-p1 or a half infinite ray (p->p1).
    atol: float
        Tolerance to be used in deciding whether an intersection point on
        a border edge is inside the surface or not.

    Returns
    -------
    X: Coords (nipts, 3)
        A fused set of intersection points
    ind: int array (nipts, 3)
        An array identifying the related intersection points, lines and
        triangle.

    Notes
    -----
    A line laying in the plane of a triangle does not generate
    intersections.

    This method is faster than the similar function
    :func:`intersectionPointsLWT`.

    Examples
    -------
    >>> from pyformex.formex import Formex
    >>> T = Formex('3:.12.34').coords
    >>> L = Coords([[[0.,0.,0.], [0.,0.,1.]],
    ...             [[0.5,0.5,0.5], [0.5,0.5,1.]],
    ...             [[0.2,0.7,0.5], [0.2,0.8,0.5]],
    ...             [[0.2,0.7,0.5], [0.2,0.7,0.2]],
    ...             ])
    >>> P, ind = intersectLineWithTriangle(T, L[:,0,:], L[:,1,:])
    >>> print(P)
    [[0.   0.   0. ]
     [0.5  0.5  0. ]
     [0.2  0.7  0. ]]
    >>> print(ind)
    [[0 0 0]
     [0 0 1]
     [1 1 0]
     [1 1 1]
     [2 3 1]]
    >>> P, ind = intersectLineWithTriangle(T, L[:,0,:], L[:,1,:],
    ...          method='ray')
    >>> print(P)
    [[0.   0.   0. ]
     [0.2  0.7  0. ]]
    >>> print(ind)
    [[0 0 0]
     [0 0 1]
     [1 3 1]]
    >>> P, ind = intersectLineWithTriangle(T, L[:,0,:], L[:,1,:],
    ...          method='segment')
    >>> print(P)
    [[0.  0.  0.]]
    >>> print(ind)
    [[0 0 0]
     [0 0 1]]

    """
    # line vectors
    m = p1-p
    # triangle bounding spheres
    r, C, n = triangleBoundingCircle(T)
    # detect candidate lines/triangles
    # For a line to intersect a triangle, the distance of the center
    # of the triangle to the line should not be more than the radius
    # This is a lengthy procedure, so use multiprocessing
    it = pointNearLine(C, p, m, r+atol, -1)
    il = np.concatenate([np.full_like(iti, i) for i, iti in enumerate(it)])
    it = np.concatenate(it)
    # intersect candidate lines/triangles
    P = intersectLineWithPlane(p[il], m[il], C[it], areaNormals(T)[1][it],
                               mode='pair')
    # remove nan/inf (lines parallel to triangles)
    i1 = np.where(~(np.isnan(P).any(axis=-1) + np.isinf(P).any(axis=-1)))[0]
    if len(i1)==0:
        return Coords(), []
    xt, xp, jl = T[it][i1], P[i1], il[i1]
    # remove intersections outside triangles
    i2 = insideTriangle(xt, xp[:, np.newaxis], atol=atol).reshape(-1)
    i = i1[i2]
    if method in ['ray', 'segment']:
        xp, jl = xp[i2], jl[i2]
        if method == 'ray':
            i3 = insideRay(p[jl], p1[jl] - p[jl], xp, atol)
        elif method == 'segment':
            i3 = insideSegment(p[jl], p1[jl], xp, atol)
        i = i[i3]
    P, j = P[i].fuse()
    return P, np.column_stack([j, il[i], it[i]])


def intersectionTimesLWT(q, m, F, mode='all'):
    """Return the intersection of lines (q,m) with triangles F.

    Parameters:

    - `q`,`m`: (nq,3) shaped arrays of points and vectors (`mode=all`)
      or broadcast compatible arrays (`mode=pair`), defining a single line
      or a set of lines.
    - `F`: (nF,3,3) shaped array (`mode=all`) or broadcast compatible array
      (`mode=pair`), defining a single triangle or a set of triangles.
    - `mode`: `all` to calculate the intersection of each line (q,m) with
      all triangles F or `pair` for pairwise intersections.

    Returns a (nq,nF) shaped (`mode=all`) array of parameter values t,
      such that the intersection points are given q+tm.

    """
    Fn = np.cross(F[..., 1, :]-F[..., 0, :], F[..., 2, :]-F[..., 1, :])
    return intersectLineWithPlane(q, m, F[..., 0, :], Fn, mode, times=True)


def intersectionPointsLWT(q, m, F, mode='all', return_all=False):
    """Return the intersection points of lines (q,m) with triangles F.

    Parameters:

    - `q`,`m`: (nq,3) shaped arrays of points and vectors, defining a single
      line or a set of lines.
    - `F`: (nF,3,3) shaped array, defining a single triangle or a set of
      triangles.
    - `mode`: `all` to calculate the intersection points of each line (q,m) with
      all triangles F or `pair` for pairwise intersections.
    - `return_all`: if True, all intersection points are returned. Default is
      to return only the points that lie inside the triangles.

    Returns:

      If `return_all==True`, a (nq,nF,3) shaped (`mode=all`) array of
      intersection points, else, a tuple of intersection points with shape (n,3)
      and line and plane indices with shape (n), where n <= nq*nF.

    """
    q = np.asanyarray(q).reshape(-1, 3)
    m = np.asanyarray(m).reshape(-1, 3)
    F = np.asanyarray(F).reshape(-1, 3, 3)
    if not return_all:
        # Find lines passing through the bounding spheres of the triangles
        r, c, n = triangleBoundingCircle(F)
        if mode == 'all':
            mode = 'pair'

            #
            # TODO: check if/why this is slower
            # If so, we should move this into distanceFromLine
            # this is much slower for large arrays
            # d = distanceFromLine(c,(q,m),mode).transpose()
            d = np.row_stack([distanceFromLine(c, ([q[i]], [m[i]]), mode)
                              for i in range(q.shape[0])])
            wl, wt = np.where(d<=r)
        elif mode == 'pair':
            d = distanceFromLine(c, (q, m), mode)
            wl = wt = np.where(d<=r)[0]
        if wl.size == 0:
            return np.empty((0, 3,), dtype=float), wl, wt
        q, m, F = q[wl], m[wl], F[wt]
    t = intersectionTimesLWT(q, m, F, mode)
    if mode == 'all':
        #
        # TODO:
        ## !!!!! CAN WE EVER GET HERE? only if return_all??
        #
        q = q[:, np.newaxis]
        m = m[:, np.newaxis]
    x = pointsAtLines(q, m, t)
    if not return_all:
        # Find points inside the faces
        ok = insideTriangle(F, x[np.newaxis]).reshape(-1)
        return x[ok], wl[ok], wt[ok]
    else:
        return x


def intersectionTimesSWT(S, F, mode='all'):
    """Return the intersection of lines segments S with triangles F.

    Parameters:

    - `S`: (nS,2,3) shaped array (`mode=all`) or broadcast compatible array
      (`mode=pair`), defining a single line segment or a set of line segments.
    - `F`: (nF,3,3) shaped array (`mode=all`) or broadcast compatible array
      (`mode=pair`), defining a single triangle or a set of triangles.
    - `mode`: `all` to calculate the intersection of each line segment S with
      all triangles F or `pair` for pairwise intersections.

    Returns a (nS,nF) shaped (`mode=all`) array of parameter values t,
    such that the intersection points are given by
    `(1-t)*S[...,0,:] + t*S[...,1,:]`.

    """
    Fn = np.cross(F[..., 1, :]-F[..., 0, :], F[..., 2, :]-F[..., 1, :])
    return intersectSegmentWithPlane(S, F[..., 0, :], Fn, mode, returns='t')


def intersectionPointsSWT(S, F, mode='all', return_all=False):
    """Return the intersection points of lines segments S with triangles F.

    Parameters:

    - `S`: (nS,2,3) shaped array, defining a single line segment or a set of
      line segments.
    - `F`: (nF,3,3) shaped array, defining a single triangle or a set of
      triangles.
    - `mode`: `all` to calculate the intersection points of each line segment S
      with all triangles F or `pair` for pairwise intersections.
    - `return_all`: if True, all intersection points are returned. Default is
      to return only the points that lie on the segments and inside the
      triangles.

    Returns:

      If `return_all==True`, a (nS,nF,3) shaped (`mode=all`) array of
      intersection points, else, a tuple of intersection points with shape (n,3)
      and line and plane indices with shape (n), where n <= nS*nF.

    """
    S = np.asanyarray(S).reshape(-1, 2, 3)
    F = np.asanyarray(F).reshape(-1, 3, 3)
    if not return_all:
        # Find lines passing through the bounding spheres of the triangles
        r, c, n = triangleBoundingCircle(F)
        if mode == 'all':
            #
            # this is much slower for large arrays
            # TODO: check why
            # d = distanceFromLine(c,S,mode).transpose()
            mode = 'pair'
            d = np.row_stack([distanceFromLine(c, S[i], mode)
                              for i in range(S.shape[0])])
            wl, wt = np.where(d<=r)
        elif mode == 'pair':
            d = distanceFromLine(c, S, mode)
            wl = wt = np.where(d<=r)[0]
        if wl.size == 0:
            return np.empty((0, 3,), dtype=float), wl, wt
        S, F = S[wl], F[wt]
    t = intersectionTimesSWT(S, F, mode)
    if mode == 'all':
        S = S[:, np.newaxis]
    x = pointsAtSegments(S, t)
    if not return_all:
        # Find points inside the segments and faces
        ok = (t >= 0.0) * (t <= 1.0) * insideTriangle(F, x[np.newaxis]).reshape(-1)
        return x[ok], wl[ok], wt[ok]
    else:
        return x


def intersectionPointsPWP(p1, n1, p2, n2, p3, n3, mode='all'):
    """Return the intersection points of planes (p1,n1), (p2,n2) and (p3,n3).

    Parameters:

    - `pi`,`ni` (i=1...3): (npi,3) shaped arrays of points and normals
      (`mode=all`)
      or broadcast compatible arrays (`mode=pair`), defining a single plane
      or a set of planes.
    - `mode`: `all` to calculate the intersection of each plane (p1,n1) with
      all planes (p2,n2) and (p3,n3) or `pair` for pairwise intersections.

    Returns a (np1,np2,np3,3) shaped (`mode=all`) array of intersection points.

    """
    if mode == 'all':
        p1 = np.asanyarray(p1).reshape(-1, 1, 1, 3)
        n1 = np.asanyarray(n1).reshape(-1, 1, 1, 3)
        p2 = np.asanyarray(p2).reshape(1, -1, 1, 3)
        n2 = np.asanyarray(n2).reshape(1, -1, 1, 3)
        p3 = np.asanyarray(p3).reshape(1, 1, -1, 3)
        n3 = np.asanyarray(n3).reshape(1, 1, -1, 3)
    dot1 = at.dotpr(p1, n1)[..., np.newaxis]
    dot2 = at.dotpr(p2, n2)[..., np.newaxis]
    dot3 = at.dotpr(p3, n3)[..., np.newaxis]
    cross23 = np.cross(n2, n3)
    cross31 = np.cross(n3, n1)
    cross12 = np.cross(n1, n2)
    denom = at.dotpr(n1, cross23)[..., np.newaxis]
    return (dot1*cross23+dot2*cross31+dot3*cross12)/denom


def intersectionLinesPWP(p1, n1, p2, n2, mode='all'):
    """Return the intersection lines of planes (p1,n1) and (p2,n2).

    Parameters:

    - `pi`,`ni` (i=1...2): (npi,3) shaped arrays of points and normals (`mode=all`)
      or broadcast compatible arrays (`mode=pair`), defining a single plane
      or a set of planes.
    - `mode`: `all` to calculate the intersection of each plane (p1,n1) with
      all planes (p2,n2) or `pair` for pairwise intersections.

    Returns a tuple of (np1,np2,3) shaped (`mode=all`) arrays of intersection
    points q and vectors m, such that the intersection lines are given by
    ``q+t*m``.

    """
    if mode == 'all':
        p1 = np.asanyarray(p1).reshape(-1, 1, 3)
        n1 = np.asanyarray(n1).reshape(-1, 1, 3)
        p2 = np.asanyarray(p2).reshape(1, -1, 3)
        n2 = np.asanyarray(n2).reshape(1, -1, 3)
    m = np.cross(n1, n2)
    q = intersectionPointsPWP(p1, n1, p2, n2, p1, m, mode='pair')
    return q, m


def intersectionSphereSphere(R, r, d):
    """Intersection of two spheres (or two circles in the x,y plane).

    Computes the intersection of two spheres with radii R, resp. r, having
    their centres at distance d <= R+r. The intersection is a circle with
    its center on the segment connecting the two sphere centers at a distance
    x from the first sphere, and having a radius y. The return value is a
    tuple x,y.

    """
    if d > R+r:
        raise ValueError(f"d ({d}) should not be larger than R+r ({R+r})")
    dd = R**2-r**2+d**2
    d2 = 2*d
    x = dd/d2
    y = np.sqrt(d2**2*R**2 - dd**2) / d2
    return x, y


########## projection #############################################


def projectPointOnPlane(X, p, n, mode='all'):
    """Return the projection of points X on planes (p,n).

    Parameters:

    - `X`: a (nx,3) shaped array of points.
    - `p`, `n`: (np,3) shaped arrays of points and normals defining `np` planes.
    - `mode`: 'all' or 'pair:

      - if 'all', the projection of all points on all planes is computed;
        `nx` and `np` can be different.
      - if 'pair': `nx` and `np` should be equal (or 1) and the projection
        of pairs of point and plane are computed (using broadcasting for
        length 1 data).

    Returns a float array of size (nx,np,3) for mode 'all', or size (nx,3)
    for mode 'pair'.

    Example:

    >>> X = Coords([[0.,1.,0.],[3.,0.,0.],[4.,3.,0.]])
    >>> p,n = [[2.,0.,0.],[0.,1.,0.]], [[1.,0.,0.],[0.,1.,0.]]
    >>> print(projectPointOnPlane(X,p,n))
    [[[2. 1. 0.]
      [0. 1. 0.]]
    <BLANKLINE>
     [[2. 0. 0.]
      [3. 1. 0.]]
    <BLANKLINE>
     [[2. 3. 0.]
      [4. 1. 0.]]]
    >>> print(projectPointOnPlane(X[:2],p,n,mode='pair'))
    [[2. 1. 0.]
     [3. 1. 0.]]

    """
    X = np.asarray(X).reshape(-1, 3)
    p = np.asarray(p).reshape(-1, 3)
    n = np.asarray(n).reshape(-1, 3)
    t = projectPointOnPlaneTimes(X, p, n, mode)
    if mode == 'all':
        X = X[:, np.newaxis]
    return pointsAtLines(X, n, t)


def projectPointOnPlaneTimes(X, p, n, mode='all'):
    """Return the projection of points X on planes (p,n).

    This is like :meth:`projectPointOnPlane` but instead of returning
    the projected points, returns the parametric values t along the
    lines (X,n), such that the projection points can be computed from
    X+t*n.

    Parameters: see :meth:`projectPointOnPlane`.

    Returns a float array of size (nx,np) for mode 'all', or size (nx,)
    for mode 'pair'.

    Example:

    >>> X = Coords([[0.,1.,0.],[3.,0.,0.],[4.,3.,0.]])
    >>> p,n = [[2.,0.,0.],[0.,1.,0.]], [[1.,0.,0.],[0.,1.,0.]]
    >>> print(projectPointOnPlaneTimes(X,p,n))
    [[ 2.  0.]
     [-1.  1.]
     [-2. -2.]]
    >>> print(projectPointOnPlaneTimes(X[:2],p,n,mode='pair'))
    [2. 1.]

    """
    if mode == 'all':
        return (at.dotpr(p, n) - np.inner(X, n)) / at.dotpr(n, n)
    elif mode == 'pair':
        return (at.dotpr(p, n) - at.dotpr(X, n)) / at.dotpr(n, n)


def projectPointOnLine(X, p, n, mode='all'):
    """Return the projection of points X on lines (p,n).

    Parameters:

    - `X`: a (nx,3) shaped array of points.
    - `p`, `n`: (np,3) shaped arrays of points and vectors defining `np` lines.
    - `mode`: 'all' or 'pair:

      - if 'all', the projection of all points on all lines is computed;
        `nx` and `np` can be different.
      - if 'pair': `nx` and `np` should be equal (or 1) and the projection
        of pairs of point and line are computed (using broadcasting for
        length 1 data).

    Returns a float array of size (nx,np,3) for mode 'all', or size (nx,3)
    for mode 'pair'.

    Example:

    >>> X = Coords([[0.,1.,0.],[3.,0.,0.],[4.,3.,0.]])
    >>> p,n = [[2.,0.,0.],[0.,1.,0.]], [[0.,2.,0.],[1.,0.,0.]]
    >>> print(projectPointOnLine(X,p,n))
    [[[2. 1. 0.]
      [0. 1. 0.]]
    <BLANKLINE>
     [[2. 0. 0.]
      [3. 1. 0.]]
    <BLANKLINE>
     [[2. 3. 0.]
      [4. 1. 0.]]]
    >>> print(projectPointOnLine(X[:2],p,n,mode='pair'))
    [[2. 1. 0.]
     [3. 1. 0.]]

    """
    X = np.asarray(X).reshape(-1, 3)
    p = np.asarray(p).reshape(-1, 3)
    n = np.asarray(n).reshape(-1, 3)
    t = projectPointOnLineTimes(X, p, n, mode)
    return pointsAtLines(p, n, t)


def projectPointOnLineTimes(X, p, n, mode='all'):
    """Return the projection of points X on lines (p,n).

    This is like :meth:`projectPointOnLine` but instead of returning
    the projected points, returns the parametric values t along the
    lines (X,n), such that the projection points can be computed from
    p+t*n.

    Parameters: see :meth:`projectPointOnLine`.

    Returns a float array of size (nx,np) for mode 'all', or size (nx,)
    for mode 'pair'.

    Example:

    >>> X = Coords([[0.,1.,0.],[3.,0.,0.],[4.,3.,0.]])
    >>> p,n = [[2.,0.,0.],[0.,1.,0.]], [[0.,1.,0.],[1.,0.,0.]]
    >>> print(projectPointOnLineTimes(X,p,n))
    [[1. 0.]
     [0. 3.]
     [3. 4.]]
    >>> print(projectPointOnLineTimes(X[:2],p,n,mode='pair'))
    [1. 3.]

    """
    if mode == 'all':
        return (np.inner(X, n) - at.dotpr(p, n)) / at.dotpr(n, n)
    elif mode == 'pair':
        return (at.dotpr(X, n) - at.dotpr(p, n)) / at.dotpr(n, n)


#################### distance ##############################


# TODO: we should extend the method of Coords.distanceFromLine
def distanceFromLine(X, lines, mode='all'):
    """Return the distance of points X from lines (p,n).

    Parameters
    ----------
    X: :term:`coords_like` (nx,3)
        A collection of points.
    lines: :term:`line_like`
        One of the following definitions of the line(s):

        - a tuple (p,n), where both p and n are (np,3) shaped arrays of
          respectively points and vectors defining `np` lines;
        - an (np,2,3) shaped array containing two points of each line.

    mode: 'all' or 'pair:
        If 'all', the distance of all points to all lines is computed;
        `nx` and `np` can be different.
        If 'pair': `nx` and `np` should be equal (or 1) and the distance
        of pairs of point and line are computed (using broadcasting for
        length 1 data).

    Returns
    -------
    float array
        A float array of size (nx,np) for mode 'all', or size (nx)
        for mode 'pair', with the distances between the points and
        the lines.

    Examples
    --------
    >>> X = Coords([[0.,1.,0.],[3.,0.,0.],[4.,3.,0.]])
    >>> L = Lines(([[2.,0.,0.],[0.,1.,0.]], [[0.,3.,0.],[1.,0.,0.]]))
    >>> print(distanceFromLine(X,L))
    [[2. 0.]
     [1. 1.]
     [2. 2.]]
    >>> print(distanceFromLine(X[:2],L,mode='pair'))
    [2. 1.]
    >>> L = Lines(([[[2.,0.,0.],[2.,2.,0.]], [[0.,1.,0.],[1.,1.,0.]]]))
    >>> print(distanceFromLine(X,L))
    [[2. 0.]
     [1. 1.]
     [2. 2.]]
    >>> print(distanceFromLine(X[:2],L,mode='pair'))
    [2. 1.]

    """
    lines = Lines(lines)
    if mode == 'all':
        return np.column_stack(X.distanceFromLine(p, n)
                               for p, n in zip(lines.p, lines.n))
    else:
        Y = projectPointOnLine(X, lines.p, lines.n, mode)
        return at.length(Y-X)


def pointNearLine(X, p, n, atol, nproc=1):
    """Find the points from X that are near to lines (p,n).

    Finds the points from X that are closer than atol to any of the lines (p,n).

    Parameters
    ----------
    X: :term:`coords_like` (npts,3)
        An array of points.
    p: :term:`coords_like` (nlines,3)
        An array of points which together with n define the lines.
    n: :term:`coords_like` (nlines,3)
        An array of direction vectors which together with p define the lines.
    atol: float or float array (npts,)
        A global or pointwise tolerance to be used in determining close points.

    Returns
    -------
    list of int arrays
        An index array for each of the lines, holding the indices of the points
        that are close to that line.

    Examples
    --------
    >>> X = Coords([[0.,1.,0.],[3.,0.,0.],[4.,3.,0.]])
    >>> p,n = [[2.,0.,0.],[0.,1.,0.]], [[0.,3.,0.],[1.,0.,0.]]
    >>> print(pointNearLine(X,p,n,1.5))
    [array([1]), array([0, 1])]
    >>> print(pointNearLine(X,p,n,1.5,2))
    [array([1]), array([0, 1])]

    """
    if at.isFloat(atol):
        atol = [atol]*len(X)
    atol = at.checkArray1D(atol, kind=None, allow=None, size=len(X))
    if nproc == 1:
        ip = [np.where(X.distanceFromLine(pi, ni) < atol)[0] for pi, ni in zip(p, n)]
        return ip
    args = multi.splitArgs((X, p, n, atol), mask=(0, 1, 1, 0), nproc=nproc)
    tasks = [(pointNearLine, a) for a in args]
    res = multi.multitask(tasks, nproc)
    from pyformex import olist
    return olist.concatenate(res)


def faceDistance(X, Fp, return_points=False):
    """Compute the closest perpendicular distance to a set of triangles.

    X is a (nX,3) shaped array of points.
    Fp is a (nF,3,3) shaped array of triangles.

    Note that some points may not have a normal with footpoint inside any
    of the facets.

    The return value is a tuple OKpid,OKdist,OKpoints where:

    - OKpid is an array with the point numbers having a normal distance;
    - OKdist is an array with the shortest distances for these points;
    - OKpoints is an array with the closest footpoints for these points
      and is only returned if return_points = True.

    """
    if not Fp.shape[1] == 3:
        raise ValueError("Currently this function only works for triangular faces.")
    # Compute normals on the faces
    Fn = np.cross(Fp[:, 1]-Fp[:, 0], Fp[:, 2]-Fp[:, 1])
    # Compute projection of points X on facets F
    Y = projectPointOnPlane(X, Fp[:, 0, :], Fn)
    # Find intersection points Y inside the facets
    inside = insideTriangle(Fp, Y.swapaxes(0, 1)).swapaxes(0, 1)
    pid = np.where(inside)[0]
    if pid.size == 0:
        if return_points:
            return [], [], []
        else:
            return [], []

    # Compute the distances
    X = X[pid]
    Y = Y[inside]
    dist = at.length(X-Y)
    # Get the shortest distances
    OKpid, OKpos = at.groupArgmin(dist, pid)
    OKdist = dist[OKpos]
    if return_points:
        # Get the closest footpoints matching OKpid
        OKpoints = Y[OKpos]
        return OKpid, OKdist, OKpoints
    return OKpid, OKdist


def edgeDistance(X, Ep, return_points=False):
    """Compute the closest perpendicular distance of points X to a set of edges.

    X is a (nX,3) shaped array of points.
    Ep is a (nE,2,3) shaped array of edge vertices.

    Note that some points may not have a normal with footpoint inside any
    of the edges.

    The return value is a tuple OKpid,OKdist,OKpoints where:

    - OKpid is an array with the point numbers having a normal distance;
    - OKdist is an array with the shortest distances for these points;
    - OKpoints is an array with the closest footpoints for these points
      and is only returned if return_points = True.

    """
    # Compute vectors along the edges
    En = Ep[:, 1] - Ep[:, 0]
    # Compute intersection points of perpendiculars from X on edges E
    t = projectPointOnLineTimes(X, Ep[:, 0], En)
    Y = pointsAtLines(Ep[:, 0], En, t)
    # Find intersection points Y inside the edges
    inside = (t >= 0.) * (t <= 1.)
    pid = np.where(inside)[0]
    if pid.size == 0:
        if return_points:
            return [], [], []
        else:
            return [], []

    # Compute the distances
    X = X[pid]
    Y = Y[inside]
    dist = at.length(X-Y)
    # Get the shortest distances
    OKpid, OKpos = at.groupArgmin(dist, pid)
    OKdist = dist[OKpos]
    if return_points:
        # Get the closest footpoints matching OKpid
        OKpoints = Y[OKpos]
        return OKpid, OKdist, OKpoints
    return OKpid, OKdist


def vertexDistance(X, Vp, return_points=False):
    """Compute the closest distance of points X to a set of vertices.

    X is a (nX,3) shaped array of points.
    Vp is a (nV,3) shaped array of vertices.

    The return value is a tuple OKdist,OKpoints where:

    - OKdist is an array with the shortest distances for the points;
    - OKpoints is an array with the closest vertices for the points
      and is only returned if return_points = True.

    """
    # Compute the distances
    dist = at.length(X[:, np.newaxis]-Vp)
    # Get the shortest distances
    OKdist = dist.min(-1)
    if return_points:
        # Get the closest points matching X
        minid = dist.argmin(-1)
        OKpoints = Vp[minid]
        return OKdist, OKpoints
    return OKdist,


################ other functions #################################

def areaNormals(x):
    """Compute the area and normal vectors of a collection of triangles.

    x is an (ntri,3,3) array with the coordinates of the vertices of ntri
    triangles.

    Returns a tuple (areas,normals) with the areas and the normals of the
    triangles. The area is always positive. The normal vectors are normalized.

    """
    x = x.reshape(-1, 3, 3)
    area, normals = at.vectorPairAreaNormals(x[:, 1]-x[:, 0], x[:, 2]-x[:, 1])
    area *= 0.5
    return area, normals


def degenerate(area, normals):
    """Return a list of the degenerate faces according to area and normals.

    area,normals are equal sized arrays with the areas and normals of a
    list of faces, such as the output of the :func:`areaNormals` function.

    A face is degenerate if its area is less or equal than zero or the
    normal has a nan (not-a-number) value.

    Returns a list of the degenerate element numbers as a sorted array.

    """
    return np.unique(np.concatenate([np.where(area<=0)[0],
                                     np.where(np.isnan(normals))[0]]))


def hexVolume(x):
    """Compute the volume of hexahedrons.

    Parameters:

    - `x`: float array (nelems,8,3)

    Returns a float array (nelems) withe the approximate volume of the
    hexahedrons formed by each 8-tuple of vertices. The volume is obained
    by dividing the hexahedron in 24 tetrahedrons and using the formulas
    from http://www.osti.gov/scitech/servlets/purl/632793

    Example:

    >>> from pyformex.elements import Hex8
    >>> X = Coords(Hex8.vertices).reshape(-1,8,3)
    >>> print(hexVolume(X))
    [1.]

    """
    x = at.checkArray(x, shape=(-1, 8, 3), kind='f')
    x71 = x[..., 6, :] - x[..., 1, :]
    x60 = x[..., 7, :] - x[..., 0, :]
    x72 = x[..., 6, :] - x[..., 3, :]
    x30 = x[..., 2, :] - x[..., 0, :]
    x50 = x[..., 5, :] - x[..., 0, :]
    x74 = x[..., 6, :] - x[..., 4, :]
    return (at.vectorTripleProduct(x71+x60, x72, x30)
            + at.vectorTripleProduct(x60, x72+x50, x74)
            + at.vectorTripleProduct(x71, x50, x74+x30)) / 12


def levelVolumes(x):
    """Compute the level volumes of a collection of elements.

    x is an (nelems,nplex,3) array with the coordinates of the nplex vertices
    of nelems elements, with nplex equal to 2, 3 or 4.

    If nplex == 2, returns the lengths of the straight line segments.
    If nplex == 3, returns the areas of the triangle elements.
    If nplex == 4, returns the signed volumes of the tetrahedron elements.
    Positive values result if vertex 3 is at the positive side of the plane
    defined by the vertices (0,1,2). Negative volumes are reported for
    tetrahedra having reversed vertex order.

    For any other value of nplex, raises an error.
    If successful, returns an (nelems,) shaped float array.

    """
    nplex = x.shape[1]
    if nplex == 2:
        return at.length(x[:, 1]-x[:, 0])
    elif nplex == 3:
        return at.vectorPairArea(x[:, 1]-x[:, 0], x[:, 2]-x[:, 1]) / 2
    elif nplex == 4:
        return at.vectorTripleProduct(x[:, 1]-x[:, 0], x[:, 2]-x[:, 1],
                                      x[:, 3]-x[:, 0]) / 6
    else:
        raise ValueError("Plexitude should be one of 2, 3 or 4; got {nplex}")


# TODO: move to Coords, rename to principalSizes(order=False)
def inertialDirections(x):
    """Return the directions and dimension of a Coords based of inertia.

    - `x`: a Coords-like array

    Returns a tuple of the principal direction vectors and the sizes along
    these directions, ordered from the smallest to the largest direction.

    """
    I = x.inertia()  # noqa: E741
    Iprin, Iaxes = I.principal()
    C = I.ctr
    X = x.trl(-C).rot(Iaxes.T)
    sizes = X.sizes()
    i = np.argsort(sizes)
    return Iaxes[i], sizes[i]


def smallestDirection(x, method='inertia', return_size=False):
    """Return the direction of the smallest dimension of a Coords.

    - `x`: a Coords-like array
    - `method`: one of 'inertia' or 'random'
    - return_size: if True and `method` is 'inertia', a tuple of a direction
      vector and the size  along that direction and the cross directions;
      else, only return the direction vector.

    """
    x = x.reshape(-1, 3)
    if method == 'inertia':
        # The idea is to take the smallest dimension in a coordinate
        # system aligned with the global axes.
        N, sizes=inertialDirections(x)
        if return_size:
            return N[0], sizes[0]
        else:
            return N[0]
    elif method == 'random':
        # Take the mean of the normals on randomly created triangles
        n = x.shape[0]
        m = 3 * (n // 3)
        e = np.arange(m)
        np.random.shuffle(e)
        if n > m:
            e = np.concatenate([e, [0, 1, n-1]])
        e = e.reshape(-1, 3)
        N = areaNormals(x[e])[1]
        ok = np.where(np.isnan(N).sum(axis=1) == 0)[0]
        N = N[ok]
        N = N*N
        N = N.mean(axis=0)
        N = np.sqrt(N)
        N = at.normalize(N)
        return N


def largestDirection(x, return_size=False):
    """Return the direction of the largest dimension of a Coords.

    - `x`: a Coords-like array
    - return_size: if True and `method` is 'inertia', a tuple of a direction
      vector and the size  along that direction and the cross directions;
      else, only return the direction vector.

    """
    x = x.reshape(-1, 3)
    N, sizes = inertialDirections(x)
    if return_size:
        return N[2], sizes[2]
    else:
        return N[2]


# TODO: add parameter mode = 'all' or 'pair'
def distance(X, Y):
    """Return the distance of all points of X to those of Y.

    Parameters:

    - `X`: (nX,3) shaped array of points.
    - `Y`: (nY,3) shaped array of points.

    Returns an (nX,nT) shaped array with the distances between all points of
    X and Y.

    """
    X = np.asarray(X).reshape(-1, 3)
    Y = np.asarray(Y).reshape(-1, 3)
    return at.length(X[:, np.newaxis]-Y)


def closest(X, Y=None, return_dist=False):
    """Find the point of Y closest to each of the points of X.

    Parameters:

    - `X`: (nX,3) shaped array of points
    - `Y`: (nY,3) shaped array of points. If None, Y is taken equal to X,
      allowing to search for the closest point in a single set. In the latter
      case, the point itself is excluded from the search (as otherwise
      that would obviously be the closest one).
    - `return_dist`: bool. If True, also returns the distances of the closest
      points.

    Returns:

    - `ind`: (nX,) int array with the index of the closest point in Y to the
      points of X
    - `dist`: (nX,) float array with the distance of the closest point. This
      is equal to length(X-Y[ind]). It is only returned if return_dist is True.

    """
    if Y is None:
        dist = distance(X, X)   # Compute all distances
        ar = np.arange(X.shape[0])
        dist[ar, ar] = dist.max()+1.
    else:
        dist = distance(X, Y)   # Compute all distances
    ind = dist.argmin(-1)       # Locate the smallest distances
    if return_dist:
        return ind, dist[np.arange(dist.shape[0]), ind]
    else:
        return ind


def closestPair(X, Y):
    """Find the closest pair of points from X and Y.

    Parameters:

    - `X`: (nX,3) shaped array of points
    - `Y`: (nY,3) shaped array of points

    Returns a tuple (i,j,d) where i,j are the indices in X,Y identifying
    the closest points, and d is the distance between them.

    """
    dist = distance(X, Y)   # Compute all distances
    ind = dist.argmin()     # Locate the smallest distances
    i, j = divmod(ind, Y.shape[0])
    return i, j, dist[i, j]


def projectedArea(x, dir):
    """Compute projected area inside a polygon.

    Parameters:

    - `x`: (npoints,3) Coords with the ordered vertices of a
      (possibly nonplanar) polygonal contour.
    - `dir`: either a global axis number (0, 1 or 2) or a direction vector
      consisting of 3 floats, specifying the projection direction.

    Returns a single float value with the area inside the polygon projected
    in the specified direction.

    Note that if the polygon is planar and the specified direction is that
    of the normal on its plane, the returned area is that of the planar
    figure inside the polygon. If the polygon is nonplanar however, the area
    inside the polygon is not defined. The projected area in a specified
    direction is, since the projected polygon is a planar one.

    """
    if x.shape[0] < 3:
        return 0.0
    if at.isInt(dir):
        dir = at.unitVector(dir)
    else:
        dir = at.normalize(dir)
    x1 = np.roll(x, -1, axis=0)
    area = at.vectorTripleProduct(Coords(dir), x, x1)
    return 0.5 * area.sum()


def polygonVectorPairs(x):
    """Compute vector pairs of the edges at each vertex of the polygons.

    Parameters
    ----------
    x: float :term:`array_like` (nel,nplex,3)
        Array with the coordinates of the vertices of nel polygons, each having
        nplex vertices.The polygons may be nonplanar.

    Returns
    -------
    vec1: float array (nel, nplex, 3)
        The vectors from each vertex to the previous vertex in the polygon.
    vec2: float array (nel, nplex, 3)
        The vectors from each vertex to the next vertex in the polygon.

    Examples
    --------
    >>> from pyformex.formex import Formex
    >>> F = Formex('3:164')
    >>> v1,v2 = polygonVectorPairs(F.coords)
    >>> print(v1)
    [[[ 1.  0.  0.]
      [-1.  1.  0.]
      [ 0. -1.  0.]]]
    >>> print(v2)
    [[[-1.  1.  0.]
      [ 0. -1.  0.]
      [ 1.  0.  0.]]]
    >>> F = Formex('l:1')
    >>> v1,v2 = polygonVectorPairs(F.coords)
    >>> print(v1)
    [[[-1.  0.  0.]
      [ 1.  0.  0.]]]
    >>> print(v2)
    [[[ 1.  0.  0.]
      [-1.  0.  0.]]]

    """
    ni = np.arange(x.shape[1])
    nj = np.roll(ni, 1)
    nk = np.roll(ni, -1)
    v1 = x-x[:, nj]
    v2 = x[:, nk]-x
    return v1, v2


def polygonNormals(x, return_angles=False):
    """Compute normals in all points of polygons in x.

    Parameters
    ----------
    x: float :term:`array_like` (nel,nplex,3)
        Array with the coordinates of the vertices of nel polygons, each having
        nplex vertices.The polygons may be nonplanar.
    return_angles: bool
        If True, also returns the angle at all vetices of the polygons.

    Returns
    -------
    normals: float array (nel,nplex,3)
        The unit normals on the two edges ending at each vertex.
    angles: float array (nel, nplex)
        Only returned if return_angles=True: the angles made by the
        two polygon edges at each vertex.

    See Also
    --------
    polygonAvgNormals: compute averaged normals at the nodes

    Examples
    --------
    >>> from pyformex.formex import Formex
    >>> F = Formex('3:164')
    >>> n, a = polygonNormals(F.coords, return_angles=True)
    >>> print(n)
    [[[ 0. -0.  1.]
      [ 0.  0.  1.]
      [-0.  0.  1.]]]
    >>> print(a)
    [[45. 45. 90.]]
    """
    if x.shape[1] < 3:
        normals = np.zeros_like(x)
        normals[:, :, 2] = -1.
        if return_angles:
            angles = np.zeros_like(x[..., 0])

    else:
        v1, v2 = polygonVectorPairs(x)
        normals = at.vectorPairNormals(v1.reshape(-1, 3),
                                       v2.reshape(-1, 3)).reshape(x.shape)
        if return_angles:
            angles = 180. - at.vectorPairAngle(v1, v2)

    if return_angles:
        return normals, angles
    else:
        return normals


def polygonAvgNormals(coords, elems, weights='angle',
                      atnodes=True, treshold=None):
    """Compute averaged normals at the nodes of a polygon Mesh.

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
    atnodes: bool, optional
        If True (default), unique averaged normals at the nodes are returned.
        If False, the averaged normals are returned for each node of each
        polygon. This is mainly intended for rendering purposes.
    treshold: float, optional
        Only used with ``atnodes=False``. If provided, element vertex normals
        making an angle with the averaged normal having a cosinus smaller than
        treshold, will be returned as the original normal. This allows for
        rendering feature edges.

    Returns
    -------
    normals: float array
        (ncoords, 3)
        The unit normals at the nodes, obtained by (weighted) averaging
        the normals on the polygons attached to that node. The default
        ``atnodes=True`` returns an array with shape (ncoords, 3). With
        ``atnodes=False``, an array with shape (nelems, nplex, 3) is
        returned.

    Examples
    --------
    This example is the surface of a unit cube. The square faces are divided
    into triangles by a single diagonal. Notice that the average normals
    come out nicely symmetric, despite the triangle layout not being
    symmetric: only node 0 and 6 have diagonals in all three planes.
    This is thanks to the use of weights equal to the angle between the
    facet edges.

    >>> from pyformex.simple import Cube
    >>> M = Cube().convert('tri3-u')
    >>> print(polygonAvgNormals(M.coords, M.elems))
    [[-0.5774 -0.5774 -0.5774]
     [ 0.5774 -0.5774 -0.5774]
     [ 0.5774  0.5774 -0.5774]
     [-0.5774  0.5774 -0.5774]
     [-0.5774 -0.5774  0.5774]
     [ 0.5774 -0.5774  0.5774]
     [ 0.5774  0.5774  0.5774]
     [-0.5774  0.5774  0.5774]]

    If we do not use any weights and simply average the normals on all
    facets at the node, the results are not so symmetric:

    >>> print(polygonAvgNormals(M.coords, M.elems, weights=None))
    [[-0.5774 -0.5774 -0.5774]
     [ 0.8165 -0.4082 -0.4082]
     [ 0.4082  0.4082 -0.8165]
     [-0.4082  0.8165 -0.4082]
     [-0.4082 -0.4082  0.8165]
     [ 0.4082 -0.8165  0.4082]
     [ 0.5774  0.5774  0.5774]
     [-0.8165  0.4082  0.4082]]
    """
    if weights=='angle':
        normals, weights = polygonNormals(coords[elems], return_angles=True)
    else:
        normals = polygonNormals(coords[elems])
    if not atnodes and treshold is not None:
        # save normals for comparison
        fnormals = normals
    if weights is not None:
        normals *= weights[..., np.newaxis]
    normals, cnt = at.nodalSum(normals, elems, coords.shape[0])
    # No need to take average, since we are going to normalize anyway
    normals = at.normalize(normals)
    if not atnodes:
        normals = normals[elems]
        if treshold is not None:
            fnormals = at.normalize(fnormals.reshape(-1, 3))
            normals = normals.reshape(-1, 3)
            cosa = at.vectorPairCosAngle(normals, fnormals)
            w = np.where(cosa<treshold)[0]
            normals[w, :] = fnormals[w, :]
            normals = normals.reshape(elems.shape[0], -1, 3)
    return normals


# TODO: remove after 2022-06; deprecated 2021-12
@utils.deprecated_by("geomtools.averageNormals", "geomtools.polygonAvgNormals")
def averageNormals(coords, elems, atNodes=False, treshold=None):
    return polygonAvgNormals(coords, elems, weights=None,
                             atnodes=atNodes, treshold=treshold)


# TODO: if there are internal angles ~180, we might split first
# at these vertices. Though we could use fillBorder for those cases.
def split_polygon(coords, faces):
    """Split polygons into two simpler ones.

    All input polygons should have the same plexitude. They are split
    along the shortest diagonal giving a maximal plexitude difference
    of 1.

    Parameters
    ----------
    coords: Coords
        The vertices of the polygons.
    faces: Connectivity
        Connectivity of the faces.

    Returns
    -------
    list of Connectivity
        Two Connectivity table with the two halves of the input
        polygons. If the input plexitude (nplex) is even, both
        have the same plexitude (nplex+2)/2; if nplex is uneven,
        the first will have a plexitude that is one higher than
        the second: (nplex+3)/2 and (nplex+1)/2.

    See Also
    --------
    splitPolygon: splits sets of polygons with different plexitude
    """
    from pyformex.mesh import Mesh
    if not isinstance(coords, Coords):
        coords = Coords(coords)
    if not isinstance(faces, Connectivity):
        faces = Connectivity(faces)
    nelems, nplex = faces.shape
    # nplus: the vertex difference of the diagonals considered
    # nplex1: the plexitude of the smallest element
    # nplex2: the plexitude of the largest element
    # ndiag: the number of diagonals to consider
    nplus = nplex // 2
    nplex1 = nplus + 1
    if nplex % 2 == 0:
        ndiag = nplex2 = nplex1
    else:
        nplex2 = nplex1 + 1
        ndiag = nplex
    # selector for the diagonals
    sel = np.array([(i, i+nplus) for i in range(ndiag)]) % nplex
    # vertex indices of the diagonals
    diags = faces[:, sel]
    # compute lengths of the diagonals
    diag = [Mesh(coords, diags[:, i, :], eltype='line2').lengths()
            for i in range(diags.shape[1])]
    diag = np.row_stack(diag)
    # find the shortest diagonal for each element
    diag = diag.argmin(axis=0).reshape(-1, 1)
    csel = np.arange(nelems).reshape(-1, 1)
    # first selector
    rsel = np.column_stack([(diag+i) % nplex for i in range(nplex1)])
    elems1 = faces[csel, rsel]
    # second selector
    rsel = np.column_stack([(diag+(nplus+i)) % nplex for i in range(nplex2)])
    elems2 = faces[csel, rsel]
    return elems1, elems2


# TODO: this can be replaced with Polygons.reduce
def splitPolygon(coords, faces, mplex=4):
    """Split sets of polygons into simpler ones with a maximum plexitude.

    Parameters
    ----------
    coords: Coords
        The vertices of the polygons.
    faces: dict | Connectivity
        A dictionary where the keys are the plexitudes of the polygons
        and the values are Connectivity tables defining all the polygons
        of that plexitude.

        A single Connectivity table may be specified instead of a dict.
    mplex: int
        The maximal plexitude of the output polygons. This should be
        at least 3 and smaller than the largest key in faces, or there
        is nothing to be split. A value of 4 will produce quads and
        triangles. A value 3 will produce only triangles.

    Returns
    -------
    dict
        The result is a dictionary like the input, but where all polygons
        with plexitude larger than mplex have been split into smaller ones.
        For example, with mplex=4, all 5-plex polygons are split into a
        quad and a triangle and 6-plex polygons into two quads.
        With mplex=3, 5-plex polygons would be split into three triangles
        and 6-plex polygons into four triangles.

    See Also
    --------
    split_polygon: split single plexitude polygons in two
    """
    def add_dict(d, elems):
        """Add a list of elems into the dict"""
        for e in elems:
            n = e.shape[-1]
            if n in d:
                d[n] = np.concatenate([d[n], e], axis=0)
            else:
                d[n] = e

    if isinstance(faces, dict):
        d = faces.copy()
    else:
        c = Connectivity(faces)
        d = {c.nplex(): c}
    while max(d) > mplex:
        add_dict(d, split_polygon(coords, d.pop(max(d))))
    return d


def triangleInCircle(x):
    """Compute the incircles of the triangles x.

    The incircle of a triangle is the largest circle that can be inscribed
    in the triangle.

    x is a Coords array with shape (ntri,3,3) representing ntri triangles.

    Returns a tuple r,C,n with the radii, Center and unit normals of the
    incircles.

    Examples
    --------
    >>> from pyformex.formex import Formex
    >>> X = Formex(Coords([1.,0.,0.])).rosette(3,120.)
    >>> print(X.asFormex())
    {[1.0,0.0,0.0], [-0.5,0.8660254,0.0], [-0.5,-0.8660254,0.0]}
    >>> radius, center, normal = triangleInCircle(X.coords.reshape(-1,3,3))
    >>> print(radius)
    [0.5]
    >>> print(center)
    [[0. 0. 0.]]

    """
    at.checkArray(x, shape=(-1, 3, 3))
    # Edge vectors
    v = np.roll(x, -1, axis=1) - x
    v = at.normalize(v)
    # create bisecting lines in x0 and x1
    b0 = v[:, 0]-v[:, 2]
    b1 = v[:, 1]-v[:, 0]
    # find intersection => center point of incircle
    center = intersectLineWithLine(x[:, 0], b0, x[:, 1], b1, mode='pair')[0]
    # find distance to any side => radius
    radius = distanceFromLine(center, (x[:, 0], v[:, 0]), mode='pair')
    # normals
    normal = np.cross(v[:, 0], v[:, 1])
    normal /= at.length(normal).reshape(-1, 1)
    return radius, center, normal


def triangleCircumCircle(x, bounding=False):
    """Compute the circumcircles of the triangles x.

    x is a Coords array with shape (ntri,3,3) representing ntri triangles.

    Returns a tuple r,C,n with the radii, Center and unit normals of the
    circles going through the vertices of each triangle.

    If bounding=True, this returns the triangle bounding circle.

    """
    at.checkArray(x, shape=(-1, 3, 3))
    # Edge vectors
    v = x - np.roll(x, -1, axis=1)
    vv = at.dotpr(v, v)
    # Edge lengths
    lv = np.sqrt(vv)
    n = np.cross(v[:, 0], v[:, 1])
    nn = at.dotpr(n, n)
    # Radius
    N = np.sqrt(nn)
    r = np.asarray(lv.prod(axis=-1) / N / 2)
    # Center
    w = -at.dotpr(np.roll(v, 1, axis=1), np.roll(v, 2, axis=1))
    a = w * vv
    C = a.reshape(-1, 3, 1) * np.roll(x, 1, axis=1)
    C = C.sum(axis=1) / nn.reshape(-1, 1) / 2
    # Unit normals
    n = n / N.reshape(-1, 1)
    # Bounding circle
    if bounding:
        # Modify for obtuse triangles
        for i, j, k in [[0, 1, 2], [1, 2, 0], [2, 0, 1]]:
            obt = vv[:, i] >= vv[:, j]+vv[:, k]
            r[obt] = 0.5 * lv[obt, i]
            C[obt] = 0.5 * (x[obt, i] + x[obt, j])

    return r, C, n


def triangleBoundingCircle(x):
    """Compute the bounding circles of the triangles x.

    The bounding circle is the smallest circle in the plane of the triangle
    such that all vertices of the triangle are on or inside the circle.
    If the triangle is acute, this is equivalent to the triangle's
    circumcircle. It the triangle is obtuse, the longest edge is the
    diameter of the bounding circle.

    x is a Coords array with shape (ntri,3,3) representing ntri triangles.

    Returns a tuple r,C,n with the radii, Center and unit normals of the
    bounding circles.

    """
    return triangleCircumCircle(x, bounding=True)


def triangleObtuse(x):
    """Check for obtuse triangles.

    x is a Coords array with shape (ntri,3,3) representing ntri triangles.

    Returns an (ntri) array of True/False values indicating whether the
    triangles are obtuse.

    """
    at.checkArray(x, shape=(-1, 3, 3))
    # Edge vectors
    v = x - np.roll(x, -1, axis=1)
    vv = at.dotpr(v, v)
    return ((vv[:, 0] > vv[:, 1]+vv[:, 2])
            + (vv[:, 1] > vv[:, 2]+vv[:, 0])
            + (vv[:, 2] > vv[:, 0]+vv[:, 1]))


@utils.deprecated_by('geomtools.lineIntersection', 'geomtools.intersectLineWithLine')
def lineIntersection(P0, N0, P1, N1):
    """Find the intersection of 2 (sets of) lines.

    This relies on the lines being pairwise coplanar.

    """
    Y0, Y1 = intersectLineWithLine(P0, N0, P1, N1, mode='pair')
    return Y0


def displaceLines(A, N, C, d):
    """Move all lines (A,N) over a distance a in the direction of point C.

    A,N are arrays with points and directions defining the lines.
    C is a point.
    d is a scalar or a list of scalars.
    All line elements of F are translated in the plane (line,C)
    over a distance d in the direction of the point C.
    Returns a new set of lines (A,N).

    """
    v = at.normalize(N)
    w = C - A
    vw = (v*w).sum(axis=-1).reshape((-1, 1))
    Y = A + vw*v
    v = at.normalize(C-Y)
    return A + d*v, N


def segmentOrientation(vertices, vertices2=None, point=None):
    """Determine the orientation of a set of line segments.

    vertices and vertices2 are matching sets of points.
    point is a single point.
    All arguments are Coords objects.

    Line segments run between corresponding points of vertices and vertices2.
    If vertices2 is None, it is obtained by rolling the vertices one position
    foreward, thus corresponding to a closed polygon through the vertices).
    If point is None, it is taken as the center of vertices.

    The orientation algorithm checks whether the line segments turn
    positively around the point.

    Returns an array with +1/-1 for positive/negative oriented segments.

    """
    if vertices2 is None:
        vertices2 = np.roll(vertices, -1, axis=0)
    if point is None:
        point = vertices.center()

    w = np.cross(vertices, vertices2)
    orient = np.sign(at.dotpr(point, w)).astype(at.Int)
    return orient


def rotationAngle(A, B, m=None, angle_spec=at.DEG):
    """Return rotation angles and vectors for rotations of A to B.

    A and B are (n,3) shaped arrays where each row represents a vector.
    This function computes the rotation from each vector of A to the
    corresponding vector of B.
    If m is None, the return value is a tuple of an (n,) shaped array with
    rotation angles (by default in degrees) and an (n,3) shaped array with
    unit vectors along the rotation axis.
    If m is a (n,3) shaped array with vectors along the rotation axis, the
    return value is a (n,) shaped array with rotation angles. The returned
    angle is then the angle between the planes formed by the axis and the
    vectors.
    Specify angle_spec=RAD to get the angles in radians.

    """
    A = np.asarray(A).reshape(-1, 3)
    B = np.asarray(B).reshape(-1, 3)
    if m is None:
        A = at.normalize(A)
        B = at.normalize(B)
        n = np.cross(A, B)  # vectors perpendicular to A and B
        t = at.length(n) == 0.
        if t.any():  # some vectors A and B are parallel
            if A.shape[0] >= B.shape[0]:
                temp = A[t]
            else:
                temp = B[t]
            n[t] = anyPerpendicularVector(temp)
        n = at.normalize(n)
        c = at.dotpr(A, B)
        angle = at.arccosd(c.clip(min=-1., max=1.), angle_spec)
        return angle, n
    else:
        m = np.asarray(m).reshape(-1, 3)
        # project vectors on plane
        A = projectionVOP(A, m)
        B = projectionVOP(B, m)
        angle, n = rotationAngle(A, B, angle_spec=angle_spec)
        # check sign of the angles
        m = at.normalize(m)
        inv = np.isclose(at.dotpr(n, m), [-1.])
        angle[inv] *= -1.
        return angle


def anyPerpendicularVector(A):
    """Return arbitrary vectors perpendicular to vectors of A.

    A is a (n,3) shaped array of vectors.
    The return value is a (n,3) shaped array of perpendicular vectors.

    The returned vector is always a vector in the x,y plane. If the original
    is the z-axis, the result is the x-axis.

    """
    A = np.asarray(A).reshape(-1, 3)
    x, y, z = np.hsplit(A, [1, 2])
    n = np.zeros(x.shape, dtype=at.Float)
    i = np.ones(x.shape, dtype=at.Float)
    t = (x==0.)*(y==0.)
    B = np.where(t, np.column_stack([i, n, n]), np.column_stack([-y, x, n]))
    return B


def perpendicularVector(A, B):
    """Return vectors perpendicular on both A and B."""
    return np.cross(A, B)


def projectionVOV(A, B):
    """Return the projection of vector of A on vector of B."""
    L = at.projection(A, B)
    B = at.normalize(B)
    shape = list(L.shape)
    shape.append(1)
    return L.reshape(shape)*B


def projectionVOP(A, n):
    """Return the projection of vector of A on a plane with normal n."""
    Aperp = projectionVOV(A, n)
    return A-Aperp


#################### barycentric coordinates ###############


def baryCoords(S, P):
    """Compute the barycentric coordinates of points wrt. simplexes.

    An n-simplex is a geometrical structure defined by n+1 vertices and
    bordered by the convex hull of those vertices. In practice it is
    either:

    - 1-simplex: line segment (nplex=2)
    - 2-simplex: triangle (nplex=3)
    - 3-simplex: tetrahedron (nplex=4)

    The barycentric coordinates of a 3d point with respect to a simplex
    of a lower order are the barycentric coordinates of the projection
    of that point on the simplex.

    Parameters
    ----------
    S: :term:`coords_like` (nel, nplex, 3)
        A set of nel n-simplexes (n=nplex-1).
    P: :term:`coords_like` (nel, npts, 3) or (1, npts, 3)
        A set of npts points (for each of the simplexes in S) for which
        the barycentric coordinates are to be computed. If the shape is
        (1,npts,3), the same points are used with each of the simplexes.

    Returns
    -------
    float array (nel, npts, nplex)
        The barycentric coordinates of the points with respect to the
        simplexes.

    See Also
    --------
    insideSimplex: test if a (projection) point falls within a simplex

    Examples
    --------
    >>> S = Coords('.1.6.4').reshape(3,2,3)
    >>> P = Coords([[[0,0,0],[0.2,0.2,0],[0.5,0.5,0],[0.5,0.7,0]]])
    >>> baryCoords(S,P)
    array([[[1. ,  0. ],
            [0.8,  0.2],
            [0.5,  0.5],
            [0.5,  0.5]],
    <BLANKLINE>
           [[0.5,  0.5],
            [0.5,  0.5],
            [0.5,  0.5],
            [0.4,  0.6]],
    <BLANKLINE>
           [[0. ,  1. ],
            [0.2,  0.8],
            [0.5,  0.5],
            [0.7,  0.3]]])
    >>> S1 = Coords('016').reshape(1,3,3)
    >>> baryCoords(S1,P)
    array([[[ 1. ,  0. ,  0. ],
            [ 0.6,  0.2,  0.2],
            [ 0. ,  0.5,  0.5],
            [-0.2,  0.5,  0.7]]])

    """
    S = at.checkArray(S, shape=(-1, -1, 3), kind='f', allow='i')
    P = at.checkArray(P, shape=(-1, -1, 3), kind='f', allow='i')
    if not (P.shape[0] == 1 or P.shape[0] == S.shape[0]):
        raise ValueError(
            "First dimension of P should 1 or equal to S.shape[0]")
    vs = S[:, 1:] - S[:, :1]
    vp = P - S[:, :1]
    A = at.dotpr(vs[:, :, np.newaxis], vs[:, np.newaxis])
    B = at.dotpr(vp[:, :, np.newaxis], vs[:, np.newaxis])
    # TODO: We could change axis order in solveMany to avoid transposing here
    t = at.solveMany(A, B.transpose(0, 2, 1)).transpose(0, 2, 1)
    t0 = (1. - t.sum(axis=-1))[:, :, np.newaxis]
    t = np.concatenate([t0, t], axis=-1)
    return t


def insideSimplex(S, P, atol=0.):
    """Check which points P are inside the simplexes S.

    An n-simplex is a geometrical structure defined by n+1 vertices and
    bordered by the convex hull of those vertices. In practice it is
    either:

    - 1-simplex: line segment (nplex=2)
    - 2-simplex: triangle (nplex=3)
    - 3-simplex: tetrahedron (nplex=4)

    A 3d point is 'inside' a simplex of a lower order if its projection
    on that simplex falls within the simplex. This is satisfied iff
    all the barycentric coordinates of the point with respect to the
    simplex are in the range [0.0, 1.0].

    Parameters
    ----------
    S: :term:`coords_like` (nel, nplex, 3)
        A set of nel n-simplexes (n=nplex-1).
    P: :term:`coords_like` (nel, npts, 3) or (1, npts, 3)
        A set of npts points that have to be tested against the nel
        simplexes. If the shape is (1,npts,3), the same points are
        tested against each of the simplexes. With a shape (nel, npts, 3)
        each simplex has its own set of points to be tested.
    atol: float, optional
        If provided, points which are falling outside the simplex within
        this tolerance (in parametric space), are also reported as inside.

    Returns
    -------
    bool array (nel, npts)
        The array holds True where the (projection of the) points fall
        inside the simplex, to the accuracy atol.

    See Also
    --------
    baryCoords: compute the barycentric coordiantes of the points

    Examples
    --------
    >>> S = Coords('.1.6.4').reshape(3,2,3)
    >>> P = Coords([[[0.2,0.2,0],[0.5,0.5,0],[0.5,0.7,0],[0.5,1.2,0]]])
    >>> insideSimplex(S,P)
    array([[ True,  True,  True,  True],
           [ True,  True,  True,  True],
           [ True,  True,  True, False]])
    >>> T = Coords('132.14').reshape(2,3,3)
    >>> insideSimplex(T,P)
    array([[ True,  True, False, False],
           [False,  True,  True, False]])

    """
    # If all bc are >= 0, they are also guaranteed to be all <= 1.0,
    # since their sum is 1.0
    return (baryCoords(S, P) >= -atol).all(axis=-1)


insideTriangle = insideSimplex


def insideSegment(Q, Q1, P, atol=0.):
    """Check if projections of points are inside line segments.

    Checks which projections of points P on the line segments Q-Q1
    are within the line segments.

    Parameters
    ----------
    Q: :term:`array_like` (nseg, 3)
        First point of ``nseg`` line segments.
    Q1: :term:`array_like` (nseg, 3)
        Second point of ``nseg`` line segments.
    P: :term:`array_like` (nseg, 3)
        The points to test against the segments. The testing is done
        by pair: one point for each segment. The test pertains to the
        projection of the point on the line containing the segment.
    atol: float, optional
        If provided, points which are falling outside the segment but within
        this tolerance are also reported as inside.

    Returns
    -------
    bool array (nseg)
        The array holds True where the (projection of the) point falls
        inside the corresponding segemnt, within the accuracy ``atol``.

    Notes
    -----
    On large data sets this is (slightly) more efficient than the
    equivalent::

        S = np.stack([Q, Q1], axis=1)
        P = P[:,np.newaxis]
        t = geomtools.insideSimplex(S,P).reshape(-1)

    See Also
    --------
    insideSimplex: a general test of (projection of) points inside simplexes
    insideRay: a similar test for points on a half-line (ray)

    Examples
    --------
    >>> nseg = 13
    >>> Q = Coords(np.random.rand(nseg,3))
    >>> Q1 = Coords(np.random.rand(nseg,3))
    >>> u = at.uniformParamValues(nseg-1, -0.1, 1.1).reshape(-1,1,1)
    >>> P = Q[:,np.newaxis] * (1.-u) + Q1[:, np.newaxis] * u
    >>> P = P.reshape(nseg,3)
    >>> insideSegment(Q, Q1, P, atol=1.e-5)
    array([False,  True,  True,  True,  True,  True,  True,  True,  True,
            True,  True,  True, False])
    >>> insideRay(Q, Q1-Q, P, atol=1.e-5)
    array([False,  True,  True,  True,  True,  True,  True,  True,  True,
            True,  True,  True,  True])

    """
    v = Q1-Q
    L = at.length(v)
    Lp = at.projection(P-Q, v)
    return (Lp >= -atol) * (Lp <= L + atol)


def insideRay(Q, v, P, atol=0.):
    """Check if projections of points are inside rays (half-lines).

    Checks which projections of points P on the line (Q,v)
    are within the positive half-lines (rays).

    Parameters
    ----------
    Q: :term:`array_like` (nlines, 3)
        Starting point of ``nlines`` rays (half-lines).
    v: :term:`array_like` (nlines, 3)
        Direction vectors of ``nlines`` rays (half-lines).
    P: :term:`array_like` (nlines, 3)
        The points to test against the rays. The testing is done
        by pair: one point for each segment. The test pertains to the
        projection of the point on the line containing the ray.
    atol: float, optional
        If provided, points which are falling outside the ray but within
        this tolerance are also reported as inside.

    Returns
    -------
    bool array (nseg)
        The array holds True where the (projection of the) point falls
        inside the corresponding ray, within the accuracy ``atol``.

    Notes
    -----
    On large data sets this is (slightly) more efficient than the
    equivalent::

        S = np.stack([Q, Q+v], axis=1)
        P = P[:,np.newaxis]
        B = geomtools.baryCoords(S,P).reshape(-1,2)
        t = np.where(B[:,1] >= atol)

    See Also
    --------
    insideSimplex: a general test of (projection of) points inside simplexes
    insideRay: a similar test for points on a half-line (ray)

    """
    Lp = at.projection(P-Q, v)
    return (Lp >= -atol)


# End
