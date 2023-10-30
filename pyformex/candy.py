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

"""Predefined geometries for a special purpose.

This module contains some predefined special purpose geometries functions.
You need to import this module in your scripts/apps to have access to its
contents.

Contents
--------

:class:`Axes`
    A geometrical representation of a coordinate system.

:func:`Horse`
    A surface model of a horse.

"""
import pyformex as pf
from pyformex.mesh import Mesh
from pyformex.trisurface import TriSurface
from pyformex.coordsys import CoordSys
from pyformex.olist import List


class Axes(List):

    """A geometry representing the three axes of a coordinate system.

    This class is a subclass of :class:`List` and contains two :class:`Mesh`
    instances: the lines along the axes and the triangles in the coordinate
    planes.

    The default geometry consists of three colored lines of unit length
    along the positive directions of the axes of the coordinate system,
    and three colored triangles representing the coordinate planes.
    The triangles extend from the origin to half the length of the
    unit vectors. Default colors for the axes is red, green, blue.

    Parameters
    ----------
    cs: :class:`coordsys.CoordSys`
        If provided, the Axes will represent the specified CoordSys. Else,
        The axes are aligned along the global axes.
    size: float
        A scale factor for the unit vectors.
    psize: float
        Relative scale factor for the coordinate plane triangles.
        If 0, no triangles will be drawn.
    reverse: bool
        If True, also the negative unit axes are included, with
        colors 4..6.
    color: 3 or 6 colors
        A set of three or six colors to use for x,y,z axes.
        If `reverse` is True or psize > 0.0, the color set should have 6 colors,
        else 3 will suffice.
    **kargs: keyword arguments
        Any extra keyword arguments will be added as attributes
        to the geometry.
    """

    def __init__(
        self,
        cs=None,
        size=1.0,
        psize=0.5,
        reverse=True,
        color=['red', 'green', 'blue', 'cyan', 'magenta', 'yellow'],
        linewidth=2,
        alpha=0.5,
        **kargs
    ):
        """Initialize the AxesGeom"""

        if cs is None:
            cs = CoordSys()
        if not isinstance(cs, CoordSys):
            raise ValueError("cs should be a CoordSys")
        coords = cs.points().reshape(4, 3)

        # Axes
        lines = [[3, 0], [3, 1], [3, 2]]
        M = Mesh(coords.scale(size, center=coords[3]), lines)
        col = color[:3]
        if reverse:
            # Add negative axes
            M = Mesh.concatenate([M, M.reflect(dir=[0, 1, 2], pos=coords[3])])
            col = color[:6]
        M.attrib(
            color=col, lighting=False, opak=True, linewidth=linewidth, **kargs
        )
        L = [M]

        # Coord planes
        if psize > 0.0:
            planes = [[3, 1, 2], [3, 2, 0], [3, 0, 1]]
            M = Mesh(coords.scale(size * psize, center=coords[3]), planes)
            col = color[:3]
            bkcol = color[3:6] if reverse else col
            M.attrib(
                color=col, bkcolor=bkcol, lighting=False, alpha=alpha, **kargs
            )
            L.append(M)

        List.__init__(self, L)


def Horse():
    """A surface model of a horse.

    Returns
    -------
    TriSurface
        A surface model of a horse. The model is loaded from a file.
    """
    return TriSurface.read(pf.cfg['datadir'] / 'horse.off')


# End
