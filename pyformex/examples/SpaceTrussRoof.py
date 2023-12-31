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
"""Double Layer Flat Space Truss Roof

"""


_level = 'normal'
_topics = ['geometry']
_techniques = ['dialog', 'animation', 'color', 'import', 'connect', 'interpolate']

from pyformex.gui.draw import *
from pyformex import simple

roof = None

def createRoof():
    global roof

    dx = 180  # Modular size (cm)
    ht = 150  # Deck height
    nx = 14  # number of bottom deck modules in x direction (should be even)
    ny = 14  # number of bottom deck modules in y direction (should be even)
    colht = 560  # Column height
    m = 2        # Column multiplicity: should be an integer divisor of nx and ny
    coldx = m * dx  # column distance (should be a multiple of dx)
    ncx = nx//m + 1  # number of columns in x-direction
    ncy = ny//m + 1  # and in y-direction


    bot = (Formex('l:1').replicm((nx, ny+1)) + Formex('l:2').replicm((nx+1, ny))).scale(dx)
    bot.setProp(3)
    top = (Formex('l:1').replicm((nx+1, ny+2)) + Formex('l:2').replicm((nx+2, ny+1))).scale(dx).translate([-dx/2, -dx/2, ht])
    top.setProp(0)
    T0 = Formex(4*[[[0, 0, 0]]])  # 4 times the corner of the bottom deck
    T4 = top.select([0, 1, nx+1, nx+2])  # 4 nodes of corner module of top deck
    dia = connect([T0, T4]).replicm((nx+1, ny+1), (dx, dx))
    dia.setProp(1)
    col = (Formex([[[0, 0, -colht], [0, 0, 0]]]).replicm((ncx, 2), (m, ny)) + Formex([[[0, m, -colht], [0, m, 0]]]).replicm((2, ncy-2), (nx, m))).scale([dx, dx, 1])
    col.setProp(2)

    roof = top+bot+dia+col


def run():
    reset()
    clear()
    linewidth(1)
    delay(1)

    if roof is None:
        createRoof()

    F = roof.rotate(-90, 0)  # put the structure upright
    draw(F)

    createView('myview1', (30., 0., 0.), True)
    view('myview1', True)


    setDrawOptions({'bbox': 'last'})
    for i in range(19):
        createView('myview2', (i*10., 20., 0.), True)
        view('myview2', True)
        delay(0.1)

    # fly tru
    if ack("Do you want to fly through the structure?"):
        totaltime = 10
        nsteps = 50
        # make sure bottom iz at y=0 and structure is centered in (x,z)
        F = F.centered()
        F = F.translate(1, -F.bbox()[0, 1])
        clear()
        linewidth(1)
        draw(F)
        bb = F.bbox()
        # create a bottom plate
        B = simple.rectangle(1, 1).swapAxes(1, 2).centered().scale(F.sizes()[0]*1.5)
        smooth()
        draw(B, color='slategrey')
        # Fly at reasonable height
        bb[0, 1] = bb[1, 1] = 170.
        ends = Formex([[bb[0]]]).interpolate(Formex([[bb[1]]]), [-0.5, 0.6])
        path = Formex(ends.coords.reshape(-1, 2, 3)).subdivide(nsteps)
        linewidth(2)
        draw(path)
        steptime = float(totaltime)/nsteps
        flyAlong(path, sleeptime=steptime)

if __name__ == '__draw__':
    run()
# End
