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

"""BezierSpline

This example shows a collection of Bezier Spline curves through a number of
points. The points used are the corners and midside points of a unit square.
The user is asked for a number of points to use.
The image shows open (left) and closed (right) BezierSpline curves of
degrees 1(red), 2(magenta) and 3(blue).

"""

_level = 'normal'
_topics = ['geometry', 'curve']
_techniques = ['spline', 'dialog']

from pyformex.gui.draw import *

# Predefined set of points
_pts = Coords([
    [1., 0., 0.],
    [1., 1., 0.],
    [0., 1., 0.],
    [-1., 1., 0.],
    [-1., 0., 0.],
    [-1., -1., 0.],
    [0., -1., 0.],
    [1., -1., 0.],
    [1., 0., 0.],
    ])

# Number of points to actually use
npts = 5

def run():
    global npts  # makes this value persistent
    resetAll()
    clear()
    linewidth(2)

    # Ask the user how many points he wants to use
    res = askItems([_I('npts', npts, text='How many points to use (2..%s)' % len(_pts))])
    if not res:
        return

    # Keep only the requested number of points
    npts = res['npts']
    pts = _pts[:npts]

    # Show open and closed Bezier Splines, for degrees 1,2,3
    degrees = [1, 2, 3]
    colors = [red, green, blue]
    collection = {}
    for closed in [False, True]:
        draw(pts)
        drawNumbers(pts)
        for d, c in zip(degrees, colors):
            print("Degree %s, %s" % (d, closed))
            B = BezierSpline(pts, closed=closed, degree=d)
            collection["BezierSpline-degree:%s-closed:%s" % (d, closed)] = B
            draw(B, color=c)

            t = np.arange(2*B.nparts)*0.5
            ipts = B.pointsAt(t)
            draw(ipts, color=c, marksize=10)
            idir = B.directionsAt(t)
            drawVectors(ipts, 0.2*idir)
        # Translate the points to the right
        pts = pts.trl(0, 2.5)  # [:-1]

    zoomAll()
    export(collection)


if __name__ == '__draw__':
    run()
# End
