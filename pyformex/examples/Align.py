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
"""Align

Create some objects and align them.
"""

_level = 'beginner'
_topics = ['drawing']
_techniques = ['align', 'attrib', 'Formex']

from pyformex.gui.draw import *

def run():

    X = Formex('4:0123')
    X.attrib(color=red)
    Y = X.rotate(30)
    Y.attrib(color=green)
    Z = X.replic2(2, 2)
    Z.attrib(color=blue)

    clear()
    L = [X, Y, Z]
    draw(L)

    pause()
    clear()
    L1 = align(L, '|0-')
    draw(L1)

    pause()
    clear()
    L1 = align(L, '|--')
    draw(L1)

    pause()
    clear()
    L1 = align(L, '|--', offset=(0.2, 0., 0.))
    draw(L1)

    pause()
    clear()
    L1 = align(L, '|--', offset=(0.2, 1., -2.))
    draw(L1)

if __name__ == '__draw__':
    run()
# End
