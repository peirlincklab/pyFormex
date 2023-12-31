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

"""Projection

Projects a rectangule grid on a sphere and on a cylinder.
The result shows:

:black: the original rectangle
:red: the projection on a sphere
:blue: the projection on a cylinder
"""


_level = 'normal'
_topics = ['geometry', 'surface']
_techniques = ['projection']

from pyformex.gui.draw import *
from pyformex import simple

def run():
    reset()
    smoothwire()
    transparent()
    lights(True)

    nx, ny = 20, 10

    F = simple.rectangle(nx, ny)
    F = F.trl(-F.center()+[0., 0., nx/2])
    draw(F)

    G = F.projectOnSphere(ny)
    draw(G, color=red)

    H = F.rotate(30).projectOnCylinder(ny)
    draw(H, color=blue)

if __name__ == '__draw__':
    run()
# End
