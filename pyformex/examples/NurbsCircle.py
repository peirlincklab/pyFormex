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

"""NurbsCircle

Draws a number of Nurbs curves that were generated
from the same set of 8 control points (shown in black, numbered 0..7)
placed on the circumference of a square with side length 2.

The following curves are closed (and blended) Nurbs curves of different degree:

  :black: degree 1: linear
  :red: degree 2: quadratic
  :green: degree 3: cubic

The next four curves are unclosed, unblended Nurbs of degree 2, with non-unity
weight factors for the corner points. Allthough these curves are not blended,
they still have continuous derivatives (except for the one with weight 0.)
because of the appropriate position of the control points.

  :blue: weight = sqrt(2)
  :cyan: weight = sqrt(2)/2
  :magenta: weight = 0.25
  :white: weight = 0.

Finally, The dotted yellow curve is created with simple.circle and shows 180
line segments approximately on the circumference of a circle with unit radius.

Notice that the curve with weigths equal to sqrt(2)/2 exactly represents a
circle.

"""

_level = 'advanced'
_topics = ['geometry', 'curve']
_techniques = ['nurbs', 'border']

from pyformex.gui.draw import *
from pyformex import simple
from pyformex.plugins.nurbs import *

def drawThePoints(N, n, color=None):
    umin = N.knots[N.degree]
    umax = N.knots[-N.degree-1]
    u = umin + np.arange(n+1) * (umax-umin) / float(n)
    P = N.pointsAt(u)
    draw(P, color=color, marksize=5)

def run():
    clear()
    linewidth(2)
    flat()

    F = Formex([[[1., 0., 0.]], [[1., 1., 0.]]]).rosette(4, 90.)
    draw(F)
    drawNumbers(F)
    zoomAll()
    setDrawOptions(bbox=None)
    showDoc()

    pts = F.coords.reshape(-1, 3)

    draw(simple.circle(2, 4), color=yellow, linewidth=4)

    for degree, c in zip(list(range(1, 4)), [black, red, green]):
        N = NurbsCurve(pts, degree=degree, closed=True)
        draw(N, color=c)
        drawThePoints(N, 16, color=c)

    for w, c in zip([sqrt(2.), sqrt(2.)/2., 0.25, 0.], [blue, cyan, magenta, white]):
        wts = np.array([1., w] * 4).reshape(8, 1)
        pts4 = Coords4(pts)
        pts4.deNormalize(wts)
        pts4 = Coords4(np.concatenate([pts4, pts4[:1]], axis=0))
        N = NurbsCurve(pts4, degree=2, closed=False, blended=False)
        draw(N, color=c)
        drawThePoints(N, 16, color=c)


if __name__ == '__draw__':
    run()
# End
