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
"""Curves

Examples showing the use of the 'curve' plugin

"""
_level = 'normal'
_topics = ['geometry', 'curve']
_techniques = ['widgets', 'persistence', 'import', 'spline', 'frenet']

from pyformex.gui.draw import *

def run():

    clear()

    X = pattern('0214412214')
    print(X)

    def drawCurveWithPoints(C, color=black, linewidth=1):
        draw(C, color=color, linewidth=linewidth)
        draw(C.coords, color=color)
        drawNumbers(C.coords, color=color)

    C = BezierSpline(control=X)
    drawCurveWithPoints(C)

    if ack('Split?'):

        CL = C.splitAt([0.3, 1.7, 2.5])
        for i, c in  enumerate(CL):
            drawCurveWithPoints(c, color=i+1, linewidth=3)
            print("======= PART %s ========" % i)
            print(c.coords)

    else:

        D = C.insertPointsAt([0.3, 1.7, 2.5])
        drawCurveWithPoints(D, color=red, linewidth=3)
        print(D.coords)




if __name__ == '__draw__':
    run()
# End
