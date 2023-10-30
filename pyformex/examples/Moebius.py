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
"""Moebius Ring

This example dynamically illustrates the creation of a Möbius ring.
See also :func:`simple.Moebius' for the final result.
"""

_level = 'advanced'
_topics = ['geometry', 'surface']
_techniques = ['dialog', 'animation', 'color']

from pyformex.gui.draw import *
from pyformex.opengl.textext import *

def run():
    reset()
    smooth()

    res = askItems([
        _I('w', 3, text='width', tooltip='Number of unit squares along the width'),
        _I('l', 30, text='length', tooltip='Number of unit squares along the length'),
        _I('n', 1, text='number of turns', tooltip='Number of 180 degree turns to apply'),
        _I('tosurface', False, text='Export as TriSurface'),
        ])
    if not res:
        return

    globals().update(res)

    ft = FontTexture.default()
    text = ' pyFormex ' * int(np.ceil(l*w/10.))
    text = text[0:w*l]
    tc = FontTexture.default().texCoords(text)
    #print("%s * %s = %s = %s" % (l,w,l*w,len(text)))
    cell = Formex('4:0123')
    strip = cell.replicm((l, w)).translate(1, -0.5*w)
    TA = draw(strip, color='orange', bkcolor='red', texture=ft, texcoords=tc, texmode=2)


    sleep(1)

    nsteps = 40
    step = n*180./nsteps/l
    for i in np.arange(nsteps+1):
        a = i*step
        torded = strip.map(lambda x, y, z: [x, y*at.cosd(x*a), y*at.sind(x*a)])
        TB = draw(torded, color='orange', bkcolor='red', texture=ft, texcoords=tc, texmode=2)
        undraw(TA)
        TA = TB

    sleep(1)
    #TA = None
    nsteps = 80
    step = 360./nsteps
    for i in np.arange(1, nsteps+1):
        ring = torded.trl(2, l*nsteps/pi/i).scale([i*step/l, 1., 1.]).trl(0, -90).cylindrical(dir=[2, 0, 1])
        TB = draw(ring, color='orange', bkcolor='red', texture=ft, texcoords=tc, texmode=2)
        undraw(TA)
        TA = TB

    if tosurface:
        export({'Möbius':ring.toSurface()})

    sleep(1)
    nsteps = 80
    step = 720./nsteps
    for i in np.arange(1, nsteps+1):
        moebius = ring.rotate(i*step, 1)
        TB = draw(moebius, name='Möbius', color='orange', bkcolor='red', texture=ft, texcoords=tc, texmode=2, bbox='last')
        undraw(TA)
        TA = TB


if __name__ == '__draw__':
    run()
# End
