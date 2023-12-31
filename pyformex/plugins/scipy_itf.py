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

"""Interface with SciPy.

This module provides an interface with some functions of the SciPy library.
Documentation for Scipy can be found on http://scipy.org/scipylib/index.html.

Note that while NumPy (also a Scipy project) is required for pyFormex, the full
SciPy package is not. There are however some functions of the SciPy library that
can be made to good use. If you have SciPy installed, you will have these
extended functionalities.
On Debian/Ubuntu-likes install package 'python3-scipy'.
"""

from pyformex import utils
utils.Module.require('scipy')

from pyformex.connectivity import Connectivity
import pyformex.arraytools as at


def convexHull(points):
    """Return the convex hull of a set of points.

    Parameters
    ----------
    points: float array (npoints, 2|3)
        A set of 2D or 3D point coordinates.

    Returns
    -------
    :class:`Connectivity`
        A Connectivity table with the indices of the points that constitute the
        convex hull of the given point set. The convex hull is the minimal set
        of simplices enclosing all the points.
        For a 3D convex hull, the Connectivity will have plexitude 3 and an
        eltype 'tri3', while for 2D convex hulls, the Connectivity has
        plexitude 2 and eltype 'line2'.

    Notes
    -----
    This requires SciPy version 0.12.0 or higher.

    If :func:`scipy.spatial.ConvexHull raises an error, an empty Connectivity
    is returned. This happens if all the points of a 3D set are in a plane or
    all the points of a 2D set are on a line.

    """
    utils.Module.require('scipy', '>=0.12.0')
    from scipy.spatial import ConvexHull

    points = at.checkArray(points, ndim=2, kind='f')
    ndim = points.shape[1]
    if ndim not in [2, 3]:
        raise ValueError('Expected 2D or 3D coordinate array')

    try:
        hull = ConvexHull(points).simplices
    except Exception:
        hull = []

    return Connectivity(hull, nplex=ndim, eltype='tri3' if ndim==3 else 'line2')

# End
