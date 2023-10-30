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
"""Circulize

This example illustrates the 'circulize' transformation.

This creates a triangular sector from a regular n-sided polygon and
subdivides it with m parts along each edge. The sector is then
transformex into a circular sector. The circular sector is finally
rotationally repeated to create a full circle.

"""


_level = 'beginner'
_topics = ['geometry']
_techniques = ['circulize', 'rosette']

from pyformex.gui.draw import *

def do_example(n, m, nc, nr, s=None):
    """Show one example. """
    T = simple.polygonSector(n).toMesh().subdivide(m)
    G = T.circulize(nc)
    R = G.toFormex().rosette(nr, 360./nr)
    clear()
    draw(coords.align([T, G, R], '|+-', offset=(1., 0., 0.)), color=red)
    if s is None:
        s = "npolygon = %s, ncirculize=%s" % (n, nc)
    drawText(s, (100, 100), size=24)
    pause()


def run():
    clear()
    smoothwire()

    m = 8
    for n in range(3, 9):
        do_example(n, m, n, n)

    clear()

    # Examples with different n for polygonSector en circulize
    do_example(4, 8, 8, 4)
    do_example(8, 8, 4, 4)

    # And an extra with quads
    T = Formex('4:0123').replic2(18, 18).centered().rotate(45)
    G = T.circulize(4)
    clear()
    draw(coords.align([T, G], '|--', offset=(1., 0., 0.)), color=red)
    drawText("quads", (100, 100), size=22)


if __name__ == '__draw__':
    run()
# End
