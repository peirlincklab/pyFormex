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
"""HorseTorse

Torsing a horse is like horsing a torse.
"""


_level = 'advanced'
_topics = ['geometry', 'surface']
_techniques = ['animation', 'color']

from pyformex.gui.draw import *

def drawSurf(F, surface=False, **kargs):
    """Draw a Formex as surface or not."""
    if surface:
        F = TriSurface(F)
    return draw(F, **kargs)


def run():
    reset()
    smooth()
    lights(True)

    surf=True
    F = Formex.read(getcfg('datadir') / 'horse.pgf')
    F = F.translate(-F.center())
    xmin, xmax = F.bbox()

    F = F.scale(1./(xmax[0]-xmin[0]))
    FA = drawSurf(F, surf)

    angle = 360.
    n = 120
    da = angle*at.DEG/n

    F.setProp(1)
    for i in range(n+1):
        a = i*da
        torse = lambda x, y, z: [x, cos(a*x)*y-sin(a*x)*z, cos(a*x)*z+sin(a*x)*y]
        G = F.map(torse)
        GA = drawSurf(G, surf)
        undraw(FA)
        FA = GA


    elong = 2.0
    nx = 50
    dx = elong/nx

    for i in range(nx+1):
        s = 1.0+i*dx
        H = G.scale([s, 1., 1.])
        GA = drawSurf(H, surf, bbox=None)
        undraw(FA)
        FA = GA

if __name__ == '__draw__':
    run()
# End
