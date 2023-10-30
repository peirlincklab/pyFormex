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

"""Texture

Shows how to draw with textures and how to set a background image.
"""

_level = 'normal'
_topics = ['Image', 'Geometry']
_techniques = ['texture']

from pyformex.gui.draw import *
from pyformex import simple

def run():
    clear()
    smooth()

    image = pf.cfg['pyformexdir'] / 'data' / 'butterfly.png'

    F = simple.cuboid().centered().toMesh().getBorderMesh()
    F.attrib(color=white)
    G = Formex('4:0123')
    H = G.replicm((3, 2)).toMesh().setProp(np.arange(1, 7)).centered()
    K = G.scale(200).toMesh()
    K.attrib(color=yellow, rendertype=2, texture=image)
    draw([F, H, K], texture=image)
    drawText(image, (200, 20), size=20)

    view('iso')
    zoomAll()
    zoom(0.5)

    bgcolor(color=[white, yellow, yellow, white], image=image)

if __name__ == '__draw__':
    run()
# End
