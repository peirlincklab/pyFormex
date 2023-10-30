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
"""Spirals

This example shows how to create a spiral curve and how to spread points
evenly along a curve.

See also the Sweep example for a more sophisticated application of spirals.
"""
_level = 'normal'
_topics = ['geometry', 'curve']
_techniques = ['transform', 'spiral']

from pyformex.gui.draw import *

def createLine(nseg, turns):
    """Create a line along x-as with nseg segments and length nturns*360"""
    return PolyLine(simple.grid1(nseg+1).scale(turns*2*pi/nseg))

def createSpiral(nseg=100, turns=1., phi=30., alpha=70., c=0.):
    X = simple.grid1(nseg+1).scale(turns*2*pi/nseg)
    a = at.tand(phi)
    b = at.tand(phi) / at.tand(alpha)
    zf = lambda x: c * np.exp(b*x)
    rf = lambda x: a * np.exp(b*x)
    Y = X.spiral((1,0,2), rfunc=rf, zfunc=zf, angle_spec=at.RAD)
    return PolyLine(Y)

def run():
    linewidth(2)
    clear()
    flat()
    view('front')
    turns = 1.   # Number of turns of the spiral
    nseg = 36    # number of segments over one turn
    L = createLine(nseg, turns)
    S = createSpiral(nseg, turns)
    draw(L.coords, color=blue)
    drawNumbers(L.coords, color=blue, gravity='se')
    draw(S, color=red)
    draw(S.coords, color=red)
    drawNumbers(S.coords, color=red, gravity='ne')
    zoomAll()

if __name__ == '__draw__':
    run()
# End
