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

"""ExtrudeBorder

This example illustrates some surface techniques. A closed surface is cut
with a number(3) of planes. Each cut leads to a hole, the border of which is
then extruded over a gioven length in the direction of the plane's positive
normal.
"""

_level = 'normal'
_topics = ['surface']
_techniques = ['extrude', 'borderfill', 'cut']

from pyformex.gui.draw import *

def cutBorderClose(S, P, N):
    """Cut a surface with a plane, and close it

    Return the border line and the closed surface.
    """
    S = S.cutWithPlane(P, N, side='-')
    B = S.border()[0]
    return B, S.close()


def run():
    smooth()
    linewidth(2)
    clear()
    S = simple.sphere()
    SA = draw(S)

    p = 0
    for P, N, L, div in [
        #
        # Each line contains a point, a normal, an extrusion length
        # and the number of elements along this length
        ((0.6, 0., 0.), (1., 0., 0.), 2.5, 5),
        ((-0.6, 0.6, 0.), (-1., 1., 0.), 4., (16, 1.0, 1.0)),
        ((-0.6, -0.6, 0.), (-1., -1., 0.), 3., 2),
        ]:
        B, S = cutBorderClose(S, P, N)
        draw(B)
        p += 1
        E = B.extrude(div, dir=at.normalize(N), length=L, eltype='tri3').setProp(p)
        draw(E)

    draw(S)
    undraw(SA)
    zoomAll()


if __name__ == '__draw__':
    run()
# End
