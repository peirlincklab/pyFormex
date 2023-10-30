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
"""PixelCount

Count the pixels from a snapshot of the pyFormex canvas
"""
_level = 'normal'
_topics = ['draw', 'camera', 'image']
_techniques = ['image', 'delay', 'boolean']

from pyformex.gui.draw import *
import pyformex as pf
from pyformex.simple import cylinder
from pyformex.plugins.imagearray import image2array

def run():

    clear()
    perspective(True)
    bgcolor('white')
    flat()
    view('-zy')

    delay(2)
    F = cylinder(L=8., D=2., nt=36, nl=20, diag='u').centered().toSurface()
    F = F.close(method='planar').fuse().compact().fixNormals('internal')
    draw(F, color=red)
    #create the geometry
    G = F.rotate(57., 0).rotate(12., 1).trl([1., 0., 2.])
    draw(G, color=green)
    I = F.boolean(G, '-')
    p = I.partitionByAngle(35)
    I.setProp(p+1)
    clear()
    draw(I)

    #set the camera focus to the center of the cut and the eye set in the z direction with distance D
    focus = I.selectProp(2).compact().center()
    D = 4
    dir = np.array([1, 0, 0, ])
    pf.canvas.camera.lookAt(focus=focus, eye=focus+dir*D)
    #ensure that the object is between the camera clipping planes
    pf.canvas.camera.setClip(D*1e-5, D*10000)
    wait()
    pf.canvas.update()

    # Get the canvas as rgb array
    perspective(False)
    img = pf.canvas.rgb()
    npixels = img.shape[0] * img.shape[1]
    uniq, ind = at.uniqueRowsIndex(img.reshape(-1, 3))
    pal = img.reshape(-1, 3)[uniq]
    cnt = np.bincount(ind)
    for col, npx in zip(pal, cnt):
        print ('The image has color RGB %s in %d pixels (%2.0f%%)' % (col, npx, 100*npx/npixels))
    delay(0)


if __name__ == '__draw__':
    run()
    perspective(True)
