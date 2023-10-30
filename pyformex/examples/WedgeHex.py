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

"""WedgeHex

This example illustrates the creation of geometry by a revolution around
an axis and the automatic reduction of the resulting degenerate elements
to lower plexitude.

First a 2D rectangular quad mesh is created. It is then revolved around an axis
cutting the rectangle. The result is a fan shaped volume of hexahedrons,
of which some elements are degenerate (those touching the axis). The
splitDegenerate method is then used to split the mesh in nondegenerat meshes
of Wedge6 (magenta) and Hex8 (cyan) type.
"""


_level = 'normal'
_topics = ['mesh']
_techniques = ['revolve', 'degenerate']

from pyformex.gui.draw import *
from pyformex import simple

delay(1)

def run():
    clear()
    smoothwire()
    view('iso')

    # create a 2D xy mesh
    nx, ny = 6, 2
    G = simple.rectangle(1, 1, 1., 1.).replicm((nx, ny)).setProp(np.arange(nx))
    M = G.toMesh()
    draw(M)

    # create a 3D axial-symmetric mesh by REVOLVING
    n, a = 8, 45.
    R = M.revolve(n, angle=a, axis=1, around=[1., 0., 0.])
    draw(R)

    # reduce the degenerate elements to WEDGE6
    clear()
    ML = R.fuse().splitDegenerate()
    # keep only the non-empty meshes
    ML = [m for m in ML if m.nelems() > 0]
    print("After splitting: %s meshes:" % len(ML))
    for m in ML:
        print("  %s elements of type %s" % (m.nelems(), m.elName()))
    draw(ML)

    # show wedge elements in other color
    ML = [Mi.setProp(i+4) for i, Mi in enumerate(ML)]
    clear()
    draw(ML)

if __name__ == '__draw__':
    run()
# End
