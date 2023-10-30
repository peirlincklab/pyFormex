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
"""Layers

Subdivide a cylindrical mesh in different (radial) layers.
To every layer a different property is assigned.
"""

_level = 'normal'
_topics = ['surface', 'cylinder']
_techniques = ['surface', 'subdivide', 'frontwalk', 'layers', 'partitioning']

from pyformex.gui.draw import *
from pyformex.simple import cylinder

def run():
    clear()
    cyl = cylinder(L=8., D=2., nt=36, nl=20, diag='').centered().toMesh()
    cyl = cyl.connect(cyl.scale([1.2, 1.2, 1]))
    cyl = cyl.subdivide(1, 1, [0, 0.1, 0.3, 0.6, 1])
    # drawing the border mesh for hex Meshes gives nicer graphics
    draw(cyl.getBorderMesh(), color=red)
    pause()
    clear()

    cylbrd = cyl.getBorderMesh()
    cyledgs = cyl.getFreeEntitiesMesh(level=1)
    pcyl = cylbrd.partitionByCurve(cyledgs)

    cylbrd = cylbrd.setProp(pcyl)

    innds = cyl.matchCoords(cylbrd.selectProp(1, compact=True))
    inelems = cyl.connectedTo(innds)

    play = cyl.frontWalk(startat=inelems)
    cyl = cyl.setProp(play)
    draw(cyl.getBorderMesh(), color='prop')


if __name__ == '__draw__':
    run()
# End
