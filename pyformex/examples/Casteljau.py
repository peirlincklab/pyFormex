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

"""Casteljau

This example illustrates the de Casteljau algorithm for constructing a point
on a  Bezier curve.

User input:

:pattern: a string defining a set of points (see 'pattern' function).
  It can be selected from a number of predefined values, or be set as
  a custom value.
:custom: a custom string to be used instead of one of the predefined values.
:value: a parametric value between 0.0 and 1.0.

The pattern string defines a set of N points, where N is the length of the
string. These N points define a Bezier Spline of degree N-1.

The application first draws a PolyLine through the N points. Then it draws
the subsequent steps of de Casteljau's algorithm to construct the point of
the Bezier Spline for the given parametric value.

Finally it also draws a whole set of points on the Bezier Spline. These points
are computed from Bernstein polynomials, just like in example BezierCurve.
"""


_level = 'normal'
_topics = ['geometry', 'curve']
_techniques = ['pattern', 'delay']

from pyformex.gui.draw import *
from pyformex import curve
from pyformex.plugins import nurbs

# Some strings defining line patterns
predefined = [
    '2584',
    '58',
    '214',
    '184',
    '514',
    '1234',
    '51414336',
    '5858585858',
    '12345678',
    'custom']

# Default values
pattern = None    # The chosen pattern
custom = ''       # The custom pattern
value = 0.5   # Parametric value of the point to construct

def run():

    res = askItems([
        dict(name='pattern', value=pattern, choices=predefined),
        dict(name='custom', value=custom),
        dict(name='value', value=value),
        ], enablers=[('pattern', 'custom', 'custom')])

    if not res:
        return

    globals().update(res)
    if pattern == 'custom':
        pat = custom
    else:
        pat = pattern

    if not pat.startswith('l:'):
        pat = 'l:' + pat

    clear()
    linewidth(2)
    flat()
    delay(0)

    # Construct and show a polyline through the points
    C = Formex(pat).toCurve()
    draw(C, bbox='auto', view='front')
    draw(C.coords)
    drawNumbers(C.coords)

    setDrawOptions({'bbox': None})

    # Compute and show the deCasteljau construction
    Q = curve.deCasteljau(C.coords, value)
    delay(1)
    wait()
    for q in Q[1:-1]:
        draw(PolyLine(q), color=red)
    draw(Q[-1], marksize=10)

    # Compute and show many points on the Bezier
    delay(0)
    n = 100
    u = np.arange(n+1)*1.0/n
    P = nurbs.pointsOnBezierCurve(C.coords, u)
    draw(Coords(P))

if __name__ == '__draw__':
    run()
# End
