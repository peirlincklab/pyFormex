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
"""Predefined geometries with a simple shape.

This module contains some functions, data and classes for generating
Formex structures representing simple geometric shapes.
You need to import this module in your scripts to have access to its
contents.
"""
import numpy as np

from pyformex import utils
from pyformex import arraytools as at
from pyformex.coords import Coords
from pyformex.formex import Formex, connect

# A collection of Formex string input patterns to construct some simple
# geometrical shapes
Pattern = {
    'line':      'l:1',
    'angle':     'l:1+2',
    'square':    'l:1234',
    'plus':      'l:1+2+3+4',
    'cross':     'l:5+6+7+8',
    'diamond':   'l:/45678',
    'rtriangle': 'l:164',
    'cube':      'l:1234I/aI/bI/cI/41234',
    'star':      'l:1+2+3+4+5+6+7+8',
    'star3d':    'l:1+2+3+4+5+6+7+8+A+B+C+D+E+F+G+H+a+b+c+d+e+f+g+h',
    'triade':    '2:01020I',
}


def shape(name):
    """Return a Formex with one of the predefined named shapes.

    This is a convenience function returning a plex-2 Formex constructed
    from one of the patterns defined in the Pattern dictionary.
    Currently, the following pattern names are defined:
    'line', 'angle', 'square', 'plus', 'cross', 'diamond', 'rtriangle', 'cube',
    'star', 'star3d'.
    See the Pattern example.
    """
    return Formex(Pattern[name])


def randomPoints(n, bbox=[[0., 0., 0.], [1., 1., 1.]]):
    """Create n random points in a specified bbox.

    Examples
    --------
    >>> X = randomPoints(10)
    >>> X.shape
    (10, 3)
    >>> np.asarray(X >= 0.).all(), np.asarray(X <= 1.).all()
    (True, True)
    >>> X = randomPoints(15, bbox=[[1.,1.,1.],[2.,2.,2.]])
    >>> X.shape
    (15, 3)
    >>> np.asarray(X >= 1.).all(), np.asarray(X <= 2.).all()
    (True, True)
    """
    bbox = at.checkArray(bbox, (2, 3), 'f')
    return Coords(at.randomNoise((n, 3))).scale(bbox[1]-bbox[0]).trl(bbox[0])


def regularGrid(x0, x1, nx, swapaxes=None):
    """Create a regular grid of points between two points x0 and x1.

    Parameters:

    - `x0`: n-dimensional float (usually 1D, 2D or 3D).
    - `x1`: n-dimensional float with same dimension as `x0`.
    - `nx`: n-dimensional int   with same dimension as `x0` and `x1`.
      The space between `x0` and `x1` is subdivided in `nx[i]` equal parts
      along the axis i.
    - `swapaxes`: bool. If False(default), the points are number first in
      the direction of the 0 axis, then the next axis,...
      If True, numbering starts in the direction of the highest axis.
      This is the legacy behavior.

    Returns a rectangular grid of n-dimensional coordinates in an array with
    shape ( nx[0]+1, nx[1]+1, ..., ndim ).

    Example:

    >>> regularGrid(0.,1.,4)
    array([[0.  ],
           [0.25],
           [0.5 ],
           [0.75],
           [1.  ]])
    >>> regularGrid((0.,0.),(1.,1.),(3,2))
    array([[[0.    , 0.    ],
            [0.3333, 0.    ],
            [0.6667, 0.    ]],
    <BLANKLINE>
           [[1.    , 0.    ],
            [0.    , 0.5   ],
            [0.3333, 0.5   ]],
    <BLANKLINE>
           [[0.6667, 0.5   ],
            [1.    , 0.5   ],
            [0.    , 1.    ]],
    <BLANKLINE>
           [[0.3333, 1.    ],
            [0.6667, 1.    ],
            [1.    , 1.    ]]])
    """
    if swapaxes is None:
        # We do not use a decorator utils.warning, because
        # this function gets called during startup (initialization of elements)
        utils.warn("warn_regular_grid")
        swapaxes = False

    x0 = np.asarray(x0).ravel()
    x1 = np.asarray(x1).ravel()
    nx = np.asarray(nx).ravel()
    if x0.size != x1.size or nx.size != x0.size:
        raise ValueError("Expected equally sized 1D arrays x0,x1,nx")
    if any(nx < 0):
        raise ValueError("nx values should be >= 0")
    # First construct a grid with integer coordinates
    ndim = x0.size
    shape = np.append(tuple(nx + 1), ndim)
    if swapaxes:
        # we can just use numpy.indices
        ind = np.indices(nx + 1)
    else:
        # we need to reverse the axes for numpy.indices
        ind = np.indices(nx[::-1] + 1)[::-1]
    ind = ind.reshape((ndim, -1))
    # And a grid with the complementary indices
    nx[nx == 0] = 1
    jnd = nx.reshape((ndim, -1)) - ind
    ind = ind.transpose()
    jnd = jnd.transpose()
    return ((x0 * jnd + x1 * ind) / nx).reshape(shape)


def grid1(npts):
    """Return a 1-D grid of points along the x-axis

    Parameters
    ----------
    npts: int
        Number of points

    Returns
    -------
    Coords
        A Coords with shape (npts, 3) containing npts points along
        the x-axis at equal distance 1. The first point is at the
        origin, the last point is at x=npts-1.
    """
    return Coords(np.arange(npts).reshape(-1,1))


def point(x=0., y=0., z=0.):
    """Return a Formex which is a point, by default at the origin.

    Each of the coordinates can be specified and is zero by default.
    """
    return Formex([[[x, y, z]]])


def line(p1=[0., 0., 0.], p2=[1., 0., 0.], n=1):
    """Return a Formex which is a line between two specified points.

    p1: first point, p2: second point
    The line is split up in n segments.
    """
    return Formex([[p1, p2]]).subdivide(n)


def rect(p1=[0., 0., 0.], p2=[1., 0., 0.], nx=1, ny=1):
    """Return a Formex which is a the circumference of a rectangle.

    p1 and p2 are two opposite corner points of the rectangle.
    The edges of the rectangle are in planes parallel to the z-axis.
    There will always be two opposite edges that are parallel with the x-axis.
    The other two will only be parallel with the y-axis if both points
    have the same z-value, but in any case they will be parallel with the
    y-z plane.

    The edges parallel with the x-axis are divide in nx parts, the other
    ones in ny parts.
    """
    p1 = Coords(p1)
    p2 = Coords(p2)
    p12 = Coords([p2[0], p1[1], p1[2]])
    p21 = Coords([p1[0], p2[1], p2[2]])
    return Formex.concatenate([
        line(p1, p12, nx),
        line(p12, p2, ny),
        line(p2, p21, nx),
        line(p21, p1, ny)
    ])


def rectangle(nx=1, ny=1, b=None, h=None, bias=0., diag=None):
    """Return a Formex representing a rectangular surface.

    The rectangle has a size(b,h) divided into (nx,ny) cells.

    The default b/h values are equal to nx/ny, resulting in a modular grid.
    The rectangle lies in the (x,y) plane, with one corner at [0,0,0].
    By default, the elements are quads. By setting diag='u','d' of 'x',
    diagonals are added in /, resp. \\ and both directions, to form triangles.
    """
    if isinstance(diag, str):
        diag = diag[:1]
    if diag == 'x':
        base = Formex(
            [[[0.0, 0.0, 0.0], [1.0, -1.0, 0.0], [1.0, 1.0, 0.0]]]
        ).rosette(4, 90.).translate([-1.0, -1.0, 0.0]).scale(0.5)
    else:
        base = Formex({'u': '3:012934', 'd': '3:016823'}.get(diag, '4:0123'))
    if b is None:
        sx = 1.
    else:
        sx = float(b) / nx
    if h is None:
        sy = 1.
    else:
        sy = float(h) / ny
    return base.replic2(nx, ny, bias=bias).scale([sx, sy, 0.])


def Cube(level=2):
    """Create a cube

    Parameters
    ----------
    level: int
        The geometric level (0..3) of the cube: 3 for volume, 2 for surfaces,
        1 for edges, 0 for points.

    Returns
    -------
    Mesh
        A Mesh with the representation of a unit cube, either as a volume,
        as its 6 faces, as its 12 edges or as its 8 vertices.
    """
    from pyformex.elements import Hex8
    if level not in range(4):
        level = 2
    M = Hex8.toMesh(level)
    return M


def circle(a1=2., a2=0., a3=360., r=None, n=None, c=None, eltype='line2',
           angle_spec=at.DEG):
    """A polygonal approximation of a circle or arc.

    All points generated by this function lie on a circle with unit radius at
    the origin in the x-y-plane.

    - `a1`: the angle enclosed between the start and end points of each line
      segment (dash angle).
    - `a2`: the angle enclosed between the start points of two subsequent line
      segments (module angle). If ``a2==0.0``, `a2` will be taken equal to `a1`.
    - `a3`: the total angle enclosed between the first point of the first
      segment and the end point of the last segment (arc angle).

    All angles are given in degrees and are measured in the direction from
    x- to y-axis. The first point of the first segment is always on the x-axis.

    The default values produce a full circle (approximately).
    If $a3 < 360$, the result is an arc.
    Large values of `a1` and `a2` result in polygons. Thus
    `circle(120.)` is an equilateral triangle and `circle(60.)`
    is regular hexagon.

    Remark that the default a2 == a1 produces a continuous line,
    while a2 > a1 results in a dashed line.

    Three optional arguments can be added to scale and position the circle
    in 3D space:

    - `r`: the radius of the circle
    - `n`: the normal on the plane of the circle
    - `c`: the center of the circle

    Examples
    --------
    >>> circle(90., 90.).coords
    Coords([[[ 1.,  0.,  0.],
             [ 0.,  1.,  0.]],
    <BLANKLINE>
            [[ 0.,  1.,  0.],
             [-1.,  0.,  0.]],
    <BLANKLINE>
            [[-1.,  0.,  0.],
             [-0., -1.,  0.]],
    <BLANKLINE>
            [[-0., -1.,  0.],
             [ 1., -0.,  0.]]])
    >>> circle(90., 45.).coords
    Coords([[[ 1.    ,  0.    ,  0.    ],
             [ 0.    ,  1.    ,  0.    ]],
    <BLANKLINE>
            [[ 0.7071,  0.7071,  0.    ],
             [-0.7071,  0.7071,  0.    ]],
    <BLANKLINE>
            [[ 0.    ,  1.    ,  0.    ],
             [-1.    ,  0.    ,  0.    ]],
    <BLANKLINE>
            [[-0.7071,  0.7071,  0.    ],
             [-0.7071, -0.7071,  0.    ]],
    <BLANKLINE>
            [[-1.    ,  0.    ,  0.    ],
             [-0.    , -1.    ,  0.    ]],
    <BLANKLINE>
            [[-0.7071, -0.7071,  0.    ],
             [ 0.7071, -0.7071,  0.    ]],
    <BLANKLINE>
            [[-0.    , -1.    ,  0.    ],
             [ 1.    , -0.    ,  0.    ]],
    <BLANKLINE>
            [[ 0.7071, -0.7071,  0.    ],
             [ 0.7071,  0.7071,  0.    ]]])
    """
    a1 = a1 * angle_spec
    a2 = a1 if a2 == 0.0 else a2 * angle_spec
    a3 = a3 * angle_spec
    ns = int(round(a3/a2))
    if eltype=='line2':
        F = Formex([[[1., 0., 0.],
                     [np.cos(a1), np.sin(a1), 0.]]])

    elif eltype=='line3':
        F = Formex([[[1., 0., 0.],
                     [np.cos(a1/2.), np.sin(a1/2.), 0.],
                     [np.cos(a1), np.sin(a1), 0.]]], eltype=eltype)
    F = F.rosette(ns, a2, axis=2, around=[0., 0., 0.], angle_spec=at.RAD)
    if r is not None:
        F = F.scale(r)
    if n is not None:
        F = F.rotate(at.rotMatrix2([0., 0., 1.], n))
    if c is not None:
        F = F.trl(c)
    return F


def polygon(n):
    """A regular polygon with n sides.

    Creates the circumference of a regular polygon with $n$ sides,
    inscribed in a circle with radius 1 and center at the origin.
    The first point lies on the axis 0. All points are in the (0,1) plane.
    The return value is a plex-2 Formex.
    This function is equivalent to circle(360./n).
    """
    return circle(360. / n)


def polygonSector(n):
    """Create one sector of a regular polygon with n sides"""
    if n < 3:
        raise ValueError("n should be at least 3")
    P0 = Coords([0., 0., 0.])
    P1 = Coords([1., 0., 0.])
    P2 = P1.rotate(360./n)
    return Formex([[P0, P1, P2]])


def triangle():
    """An equilateral triangle with base [0,1] on axis 0.

    Returns an equilateral triangle with side length 1.
    The first point is the origin, the second points is on the axis 0.
    The return value is a plex-3 Formex.
    """
    return Formex([[[0., 0., 0.], [1., 0., 0.], [0.5, 0.5 * np.sqrt(3.), 0.]]])


def quadraticCurve(x=None, n=8):
    """Create a collection of curves.

    x is a (3,3) shaped array of coordinates, specifying 3 points.

    Return an array with 2*n+1 points lying on the quadratic curve through
    the points x. Each of the intervals [x0,x1] and [x1,x2] will be divided
    in n segments.
    """
    x = at.checkArray(x, (3, 3), kind='f')
    # Interpolation functions in normalized coordinates (-1..1)
    h = [lambda x: x*(x-1)/2, lambda x: (1+x)*(1-x), lambda x: x*(1+x)/2]
    t = np.arange(-n, n+1) / float(n)
    H = np.column_stack([hi(t) for hi in h])
    return np.dot(H, x)


def sphere(ndiv=6, base='icosa', radius=1.0, equiv='R'):
    """Create a triangulated surface approximating a sphere.

    The approximation of a spherical surface is constructed as follows.
    First a simple base triangulated surface is created. Its triangular
    facets are subdivided into identical smaller triangles by dividing
    all edges in `ndiv` parts. The resulting mesh is then projected on a
    sphere with the specified radius.

    Parameters
    ----------
    ndiv: int
        Number of divisions along the edges of the base surface. The higher
        `ndiv` is taken, the better the approximation. With ``ndiv<=1``,
        the base surface is returned.
    base: str
        The type of base surface to be used. Currently available:

        - 'icosa': icosahedron (20 faces): this offers the highest
          quality with triangles of almost same size and shape.
        - 'octa': octahedron (8 faces): this model will have the same
          mesh on each of the quadrants of the global axes.
          The coordinate planes do not cut any triangle. This model is
          this fit to be split along coordinate planes.
    radius: float, optional
        The radius of the sphere. Default is 1.0.
    equiv: 'R' | 'A' | 'V'
        The quantity that should be equivalent with the perfect sphere.
        The default ('R') places the points exactly at the specified radius.
        The computed area and volume will obviously be less than
        those of the perfect sphere. With 'A' or 'V', the radius is
        increased in such way that the triangular surface has the same
        area, respectively volume, as the perfect sphere.

    Returns
    -------
    TriSurface
        A TriSurface representing a triangulated approximation of a
        spherical surface with specified radius and center at the origin.

    Notes
    -----
    The number of elements is equal to 20*ndiv**2 for 'icosa' and
    8*ndiv**2 for 'octa'.

    Examples
    --------
    This computes the relative area and volume of the triangulated
    surface with respect to the perfect sphere

    >>> for ndiv in range(1,9):
    ...     S = sphere(ndiv)
    ...     A = S.area() / (4*at.pi)
    ...     V = S.volume() / (4/3*at.pi)
    ...     np, nf = S.ncoords(), S.nelems()
    ...     print(f"ndiv: {ndiv}; npoints: {np:3}; nfaces: {nf:4}; "
    ...           f"area: {A:.4f}; volume: {V:.4f}")
    ndiv: 1; npoints:  12; nfaces:   20; area: 0.7619; volume: 0.6055
    ndiv: 2; npoints:  42; nfaces:   80; area: 0.9283; volume: 0.8735
    ndiv: 3; npoints:  92; nfaces:  180; area: 0.9669; volume: 0.9409
    ndiv: 4; npoints: 162; nfaces:  320; area: 0.9811; volume: 0.9662
    ndiv: 5; npoints: 252; nfaces:  500; area: 0.9878; volume: 0.9781
    ndiv: 6; npoints: 362; nfaces:  720; area: 0.9915; volume: 0.9848
    ndiv: 7; npoints: 492; nfaces:  980; area: 0.9938; volume: 0.9888
    ndiv: 8; npoints: 642; nfaces: 1280; area: 0.9952; volume: 0.9914

    Here is a comparison of the radius, area and volume equivalent surfaces
    for ``ndiv=4``.

    >>> for equiv in ['R', 'A', 'V']:
    ...     S = sphere(4, equiv=equiv)
    ...     R = S.coords.distanceFromPoint([0.,0.,0.]).mean()
    ...     A = S.area() / (4*at.pi)
    ...     V = S.volume() / (4/3*at.pi)
    ...     print(f"radius: {R:.4f}; area: {A:.4f}; volume: {V:.4f}")
    radius: 1.0000; area: 0.9811; volume: 0.9662
    radius: 1.0096; area: 1.0000; volume: 0.9942
    radius: 1.0115; area: 1.0039; volume: 1.0000
    """
    from pyformex.elements import ElementType
    from pyformex.trisurface import TriSurface

    base = ElementType.get(base)
    S = TriSurface(base.vertices, base.faces)
    if ndiv > 1:
        S = S.subdivide(ndiv).fuse()
    S = S.projectOnSphere()
    if equiv == 'A':
        radius /= (S.area() / (4*at.pi)) ** 0.5
    elif equiv == 'V':
        radius /= (S.volume() / (4/3*at.pi)) ** (1/3)
    if radius != 1.0:
        S = S.scale(radius)
    return S


def MoebiusRing(nturns=1, nw=2, nl=30):
    """Create a model of a Möbius ring.

    A Möbius ring is a strip where one end is turned over a number of times
    and then glued to the other end.

    Parameters
    ----------
    nturns: int
        The number of turns to give to one end of the strip.
    nl: int
        The number of cells over the length of the strip.
    nw: int
        The number of cells over the width of the strip.
    If uneven, the resulting surface
        is not orientable: it has only one side. If even the surface
        has two sides and is orientable.

    Returns
    -------
    Mesh
        A quad4 Mesh representing a Möbius ring
    """
    cell = Formex('4:0123')
    strip = cell.replicm((nl, nw)).translate(1, -0.5*nw)
    a = nturns*180./nl
    torded = strip.map(lambda x, y, z: [x, y*at.cosd(x*a), y*at.sind(x*a)])
    ring = torded.trl(2, nl/at.pi)\
                 .scale([360./nl, 1., 1.])\
                 .trl(0, -90)\
                 .cylindrical(dir=[2, 0, 1])
    return ring.toMesh()


def sphere3(nx, ny, r=1, bot=-90., top=90.):
    """Return a sphere consisting of surface triangles

    A sphere with radius r is modeled by the triangles formed by a regular
    grid of nx longitude circles, ny latitude circles and their diagonals.

    The two sets of triangles can be distinguished by their property number:
    1: horizontal at the bottom, 2: horizontal at the top.

    The sphere caps can be cut off by specifying top and bottom latitude
    angles (measured in degrees from 0 at north pole to 180 at south pole.
    """
    base = Formex([[[0, 0, 0], [1, 0, 0], [1, 1, 0]],
                   [[1, 1, 0], [0, 1, 0], [0, 0, 0]]],
                  [1, 2])
    grid = base.replicm((nx, ny), (1., 1.))
    s = float(top - bot) / ny
    return grid.translate([0, bot / s, 1]).spherical(scale=[360. / nx, s, r])


def sphere2(nx, ny, r=1, bot=-90, top=90):
    """Return a sphere consisting of line elements.

    A sphere with radius r is modeled by a regular grid of nx
    longitude circles, ny latitude circles and their diagonals.

    The 3 sets of lines can be distinguished by their property number:
    1: diagonals, 2: meridionals, 3: horizontals.

    The sphere caps can be cut off by specifying top and bottom latitude
    angles (measured in degrees from 0 at north pole to 180 at south pole.
    """
    base = Formex('l:543', [1, 2, 3])           # single cell
    d = base.select([0]).replicm((nx, ny))      # all diagonals
    m = base.select([1]).replicm((nx, ny))      # all meridionals
    h = base.select([2]).replicm((nx, ny + 1))  # all horizontals
    grid = m + d + h
    s = float(top - bot) / ny
    return grid.translate([0, bot / s, 1]).spherical(scale=[360. / nx, s, r])


@utils.deprecated_by('simple.connectCurves', 'Mesh.connect')
def connectCurves(curve1, curve2, n):
    """Connect two curves to form a surface.

    curve1, curve2 are plex-2 Formices with the same number of elements.
    The two curves are connected by a surface of quadrilaterals, with n
    elements in the direction between the curves.

    See Also
    --------
    Mesh.connect
    """
    return curve1.toMesh().connect(curve2.toMesh(), n).toFormex()


def sector(r, t, nr, nt, h=0., diag=None):
    """Constructs a Formex which is a sector of a circle/cone.

    A sector with radius r and angle t is modeled by dividing the
    radius in nr parts and the angle in nt parts and then creating
    straight line segments.
    If a nonzero value of h is given, a conical surface results with its
    top at the origin and the base circle of the cone at z=h.
    The default is for all points to be in the (x,y) plane.


    By default, a plex-4 Formex results. The central quads will collapse
    into triangles.
    If diag='up' or diag = 'down', all quads are divided by an up directed
    diagonal and a plex-3 Formex results.
    """
    r = float(r)
    t = float(t)
    p = Formex(regularGrid([0., 0., 0.], [r, 0., 0.], [nr, 0, 0],
                           swapaxes=True).reshape(-1, 3))
    if h != 0.:
        p = p.shear(2, 0, h / r)
    q = p.rotate(t / nt)
    if isinstance(diag, str):
        diag = diag[0]
    if diag == 'u':
        F = connect([p, p, q], bias=[0, 1, 1]) + \
            connect([p, q, q], bias=[1, 2, 1])
    elif diag == 'd':
        F = connect([q, p, q], bias=[0, 1, 1]) + \
            connect([p, p, q], bias=[1, 2, 1])
    else:
        F = connect([p, p, q, q], bias=[0, 1, 1, 0])

    F = Formex.concatenate([F.rotate(i * t / nt) for i in range(nt)])
    return F


def cylinder(D, L, nt, nl, D1=None, angle=360., bias=0., diag=None):
    """Create a cylindrical, conical or truncated conical surface.

    Returns a Formex representing (an approximation of) a cylindrical or
    (possibly truncated) conical surface with its axis along the z-axis.
    The resulting surface is actually a prism or pyramid, and only becomes
    a good approximation of a cylinder or cone for high values of `nt`.

    Parameters:

    - `D`: base diameter (at z=0) of the cylinder/cone,
    - `L`: length (along z-axis) of the cylinder/cone,
    - `nt`: number of elements along the circumference,
    - `nl`: number of elements along the length,
    - `D1`: diameter at the top (z=L) of the cylinder/cone: if unspecified,
      it is taken equal to `D` and a cylinder results.
      Setting either `D1` or `D` to zero results in a cone,
      other values will create a truncated cone.
    - `diag`: by default, the elements are quads. Setting `diag` to 'u' or 'd'
      will put in an 'up' or 'down' diagonal to create triangles.
    """
    C = rectangle(nl, nt, L, angle, bias=bias, diag=diag).trl(2, D / 2.)
    if D1 is not None and D1 != D:
        C = C.shear(2, 0, (D1 - D) / L / 2)
    return C.cylindrical(dir=[2, 1, 0])


def boxes(x):
    """Create a set of cuboid boxes.

    `x`: Coords with shape (nelems,2,3), usually with x[:,0,:] < x[:,1,:]

    Returns a Formex with shape (nelems,8,3) and of type 'hex8',
    where each element is the cuboid box which has x[:,0,:]
    as its minimum coordinates and x[:,1,:] as the maximum ones.
    Note that the elements may be degenerate or reverted if the minimum
    coordinates are not smaller than the maximum ones.

    This function can be used to visualize the bboxes() of a geometry.
    """
    x = Coords(x).reshape(-1, 2, 3)
    i = [[0, 0, 0],
         [1, 0, 0],
         [1, 1, 0],
         [0, 1, 0],
         [0, 0, 1],
         [1, 0, 1],
         [1, 1, 1],
         [0, 1, 1]]

    j = [0, 1, 2]

    return Formex(x[:, i, j], eltype='hex8')


def boxes2d(x):
    """Create a set of rectangular boxes.

    Parameters:

    - `x`: Coords with shape (nelems,2,3), usually with x[:,0,:] < x[:,1,:]
      and x[:,:,2] == 0.

    Returns a Formex with shape (nelems,4,3) and of type 'quad4',
    where each element is the rectangular box which has x[:,0,:]
    as its minimum coordinates and x[:,1,:] as the maximum ones.
    Note that the elements may be degenerate or reverted if the minimum
    coordinates are not smaller than the maximum ones.

    This function is a 2D version of :meth:`bboxes`.
    """
    x = Coords(x).reshape(-1, 2, 3)
    i = [[0, 0, 0],
         [1, 0, 0],
         [1, 1, 0],
         [0, 1, 0]]

    j = [0, 1, 2]

    return Formex(x[:, i, j], eltype='quad4')


def cuboid(xmin=[0., 0., 0.], xmax=[1., 1., 1.], cs=None):
    """Create a rectangular prism.

    Create a rectangular prism from two opposite corners. The vertices
    are specified in the global or a given coordinate system. The faces
    are parallel to the coordinate planes.

    Parameters:

    - `xmin`: float(3): minimum coordinates
    - `xmax`: float(3): maximum coordinates
    - `cs`: CoordSys: if specified, the cuboid is constructed in this
      coordinate system, and then transformed back to global axes.

    Returns a single element Formex with eltype 'hex8'.
    """
    F = boxes([xmin, xmax])
    if cs:
        F = F.fromCS(cs)
    return F


def cuboid2d(xmin=[0., 0., 0.], xmax=[1., 1., 0.]):
    """Create a rectangle.

    Creates a rectangle with sides parallel to the global y-axis
    and global xz-plane, and having the points xmin and xmax as
    opposite corner points.

    Returns a single element Formex with eltype 'quad4'.
    """
    return boxes2d([xmin, xmax])


def boundingBox(obj, cs=None):
    """Returns a cuboid that is the bounding box of some geometry

    The boundingBox is computed in the specified coordinate system.
    The default is the global axes.

    Returns a single hexahedral Formex object.
    """
    if cs:
        obj = obj.toCS(cs)
    xmin, xmax = obj.bbox()
    return cuboid(xmin, xmax, cs)


def principalBbox(obj):
    return boundingBox(obj, cs=obj.principalCS())


# End
