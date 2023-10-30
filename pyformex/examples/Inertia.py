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
_techniques = ['color', 'axes']

from pyformex.gui.draw import *

def unitAxes():
    """Create a set of three axes."""
    Hx = Formex('l:1', 5).translate([-0.5, 0.0, 0.0])
    Hy = Hx.rotate(90)
    Hz = Hx.rotate(-90, 1)
    Hx.setProp(1)
    Hy.setProp(2)
    Hz.setProp(3)
    return Formex.concatenate([Hx, Hy, Hz])

def showPrincipal1(F):
    """Show the principal axes."""
    clear()
    I = F.coords.inertia()
    C = I.ctr
    print("Total mass: %s" % I.mass)
    print("Center: %s" % I.ctr)
    print("Inertia tensor: %s" % I.tensor)
    Iprin, Iaxes = I.principal()
    print("Principal Values: %s" % Iprin)
    print("Principal Directions:\n%s" % Iaxes)

    siz = F.dsize()
    H = unitAxes().scale(siz).affine(Iaxes, C)
    Ax, Ay, Az = Iaxes
    G = Formex([[C, C+Ax], [C, C+Ay], [C, C+Az]], 3)
    draw([F, G, H])


def run():
    reset()
    wireframe()
    view('front')
    setTriade()

    nx, ny, nz = 2, 3, 4
    dx, dy, dz = 2, 3, 4
    F = Formex([[[0, 0, 0]]]).replic(nx, dx, 0).replic(ny, dy, 1).replic(nz, dz, 2)

    Fr = F
    showPrincipal1(Fr)

    pause()
    Fr = F.rotate(30, 0).rotate(45, 1).rotate(60, 2)
    showPrincipal1(Fr)


if __name__ == '__draw__':
    run()
# End
