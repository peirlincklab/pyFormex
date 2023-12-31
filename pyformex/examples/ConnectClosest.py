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

"""ConnectClosest

This example connects each point in a set with the closest other point.
"""


_level = 'beginner'
_topics = ['formex', 'mesh']
_techniques = ['connect', 'closest', 'regularGrid', 'addNoise']

from pyformex.gui.draw import *

from pyformex import geomtools
from pyformex.simple import regularGrid

def run():
    clear()
    # Create a grid of points with
    X = Coords(regularGrid([0., 0., 0.], [1., 1., 0.], [3, 3, 0]).reshape(-1, 3))
    X = X.addNoise(rsize=0.05, asize=0.0)
    draw(X)
    drawNumbers(X)
    ind = geomtools.closest(X)
    M = connect([X, X[ind]]).toMesh().removeDuplicate()
    # Hint: the connect() function transforms all items in the first
    # argument to Formices. Thus it also works directly with Coords objects.
    draw(M)
    drawNumbers(M, color='red')

if __name__ == '__draw__':
    run()
# End
