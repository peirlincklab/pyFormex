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

"""ConnectMesh

"""


_level = 'normal'
_topics = ['mesh']
_techniques = ['connect', 'color']

from pyformex.gui.draw import *

from pyformex import simple

def run():
    clear()
    smoothwire()

    nx = 4
    ny = 3
    nz = 7

    delay(2)

    # A rectangular mesh
    M1 = simple.rectangle(nx, ny).toMesh().setProp(1)
    # Same mesh, rotated and translated
    M2 = M1.rotate(45, 0).translate([1., -1., nz]).setProp(3)
    draw([M1, M2])

    # Leave out the first and the last two elements
    sel = np.arange(M1.nelems())[1:-2]
    m1 = M1.select(sel)
    m2 = M2.select(sel)
    clear()
    draw([m1, m2], view=None)

    # Connect both meshes to a hexaeder mesh
    m = m1.connect(m2, nz)
    clear()
    draw(m, color=red, view=None)

if __name__ == '__draw__':
    run()
# End
