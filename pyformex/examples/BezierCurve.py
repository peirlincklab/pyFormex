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

"""BezierCurve

level = 'normal'
topics = ['geometry', 'curve']
techniques = []

.. Description

BezierCurve
===========
This example illustrates the use of Bernstein polynomials to evaluate points
on a Bezier curve.
"""


_level = 'normal'
_topics = ['geometry', 'curve']
_techniques = []

from pyformex.gui.draw import *
from pyformex.plugins.nurbs import pointsOnBezierCurve

def run():
    predefined = ['514', '1234', '51414336', 'custom']

    res = askItems([
        dict(name='pattern', choices=predefined),
        dict(name='custom', value=''),
        ])

    if not res:
        return

    s = res['pattern']
    if s == 'custom':
        s = res['custom']

    if not s.startswith('l:'):
        s = 'l:' + s
    C = Formex(s).toCurve()

    clear()
    linewidth(2)
    flat()

    draw(C, bbox='auto', view='front')
    draw(C.coords)
    drawNumbers(C.coords)

    setDrawOptions({'bbox': None})
    n = 100
    u = np.arange(n+1)*1.0/n
    P = pointsOnBezierCurve(C.coords, u)
    draw(P)



if __name__ == '__draw__':
    run()
# End
