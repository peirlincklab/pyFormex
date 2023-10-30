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
"""Torus

"""


_level = 'beginner'
_topics = ['geometry']
_techniques = ['color']

from pyformex.gui.draw import *

def run():
    m = 36  # number of cells along torus big circle
    n = 36  # number of cells along torus small circle
    print("Create a triangle with three colored members")
    F = Formex('l:164', [1, 2, 3])
    clear(); draw(F); pause()
    print("Replicate it into a rectangular pattern")
    F = F.replicm((m, n))
    clear(); draw(F); pause()
    print("Fold the rectangle into a tube")
    G = F.translate(2, 1).cylindrical([2, 1, 0], [1., 360./n, 1.])
    clear(); draw(G, view='right'); pause()
    print("Bend the tube into a torus with mean radius 5")
    H = G.translate(0, 5).cylindrical([0, 2, 1], [1., 360./m, 1.])
    clear(); draw(H, view='iso'); pause()
    print("Cut a part from the torus")

    K = H.cutWithPlane([0., 2., 0.], [1., 1., 1.], side='-')
    clear()
    draw(K)

if __name__ == '__draw__':
    run()
# End
