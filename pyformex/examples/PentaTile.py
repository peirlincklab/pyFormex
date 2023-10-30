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

"""PentaTile

This example shows the tiling of a plane with different kind of pentagons.

"""

_level = 'advanced'
_topics = ['geometry']
_techniques = ['formex']

from pyformex.gui.draw import *
from pyformex.plugins.polygon import Polygon
from pyformex.trisurface import fillBorder

nroll = 1

def pentagonMann():
    """Creates a single Mann pentagon

    See http://www.huffingtonpost.com/2015/08/18/historic-tile-discovery-gives-math-world-a-big-jolt_n_8010250.html?utm_hp_ref=world&ir=World

    """
    # lengths of the sides
    lengths = np.array([1., 0.5, 1./sqrt(2.)/(sqrt(3.)-1), 0.5, 0.5])
    # inner angles of the pentagons
    angles = np.array([60., 135., 105., 90., 150.])
    lengths = np.roll(lengths, nroll)
    angles = np.roll(angles, nroll)
    rotations = 180.-angles
    grotations = np.roll(rotations.cumsum(), 1)

    print("lengths: %s" % lengths)
    print("angles: %s" % angles)
    print("rotations: %s" % rotations)
    print("cumulative rotations: %s" % grotations)
    u = Coords([1., 0., 0.])
    X = Coords([u.scale(l).rotate(r) for l, r in zip(lengths, grotations)])
    #print(X)
    Y = X.cumsum(axis=0)
    print(Y)
    return fillBorder(Y, method='border')


def run():
    reset()
    smooth()
    clear()
    F = pentagonMann().setProp(1)
    draw(F)
    drawNumbers(F.coords)
    R = 0.5*(F.coords[nroll+1] + F.coords[nroll+2])
    draw(R)
    G = F.rotate(180, around=R)
    draw(G, color=magenta)



if __name__ == '__draw__':
    run()


# End
