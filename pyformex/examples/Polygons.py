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
"""Polygons

Example of using the Polygons class.

"""

_level = 'normal'
_topics = ['geometry', 'polygons']
_techniques = ['polygons']

from pyformex.gui.draw import *
from pyformex.polygons import Polygons

def run():
    smoothwire()
    clear()
    # Create a grid of 10x3 points
    X = Formex([0,0,0]).replic2(10,3).coords.reshape(-1,3)
    draw(X)
    drawNumbers(X)
    # Create Polygons
    PS = Polygons(X, [
        [2, 3, 13, 12],
        [0, 1, 10],
        [10, 12, 22, 21],
        [1, 2, 12, 10],
        ]).setProp('range')
    # and another one
    PS1 = Polygons(X, [[4, 5, 6, 17, 26, 25, 24, 13]]).setProp(14)
    # add it to the first
    PS += PS1
    # draw
    draw(PS)
    print(PS.elems)


if __name__ == '__draw__':
    run()
# End
