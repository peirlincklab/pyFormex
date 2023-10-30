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
"""Inertia

"""


_level = 'beginner'
_topics = ['geometry']
_techniques = ['inertia']

from pyformex.gui.draw import *
from pyformex.simple import sphere, Cube
from pyformex import inertia

def run():
    smoothwire()

    print("======================")
    print("A cube with side = 1.0")
    F = Cube(3).convert('tet4').toFormex()
    clear()
    draw(F.toMesh().getBorderMesh())
    print("Number of tetrahedrons: %s" % F.shape[0])
    print("Bounding box: %s" % F.bbox())
    V, M, C, I = inertia.tetrahedral_inertia(F.coords)
    # Analytical
    Va = 1.
    Ma = Va
    Ca = [0.5, 0.5, 0.5]
    Ia = [1./6, 1./6, 1./6, 0., 0., 0.]
    print("Volume = %s (corr. %s)" % (V, Va))
    print("Mass = %s (corr. %s)" % (M, Ma))
    print("Center of mass = %s (corr. %s)" % (C, Ca))
    print("Inertia tensor = %s (corr. %s)" % (I, Ia))

    pause()
    print("======================")
    print("A sphere with radius = 1.0")
    # Increase the quality to better approximate the sphere
    quality = 4
    if not utils.External.has('tetgen'):
        warning("Skipping the remainder because 'tetgen' is missing")
        return

    F = sphere(quality).tetgen().toFormex()
    clear()
    draw(F.toMesh().getBorderMesh())
    print("Number of tetrahedrons: %s" % F.shape[0])
    print("Bounding box: %s" % F.bbox())
    V, M, C, I = inertia.tetrahedral_inertia(F.coords)
    # Analytical
    Va = 4*pi/3
    Ma = Va
    Ca = [0., 0., 0.]
    ia = 8*pi/15
    Ia = [ia, ia, ia, 0., 0., 0.]
    print("Volume = %s (corr. %s)" % (V, Va))
    print("Mass = %s (corr. %s)" % (M, Ma))
    print("Center of mass = %s (corr. %s)" % (C, Ca))
    print("Inertia tensor = %s (corr. %s)" % (I, Ia))

if __name__ == '__draw__':
    run()

# End
