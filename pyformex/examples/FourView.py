##
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
"""FourView.py

Demonstrate multiple views of same contents. It display a model of a man,
with front, right, top and isometric views. The first three feature a
camera with locked viewing direction, but zooming is possible. The last
viewport has a completely free camera.

Note: This is a feature under development. Currently you need to construct
the scene first and then set/lock the layout.
"""

_level = 'advanced'
_topics = ['surface']
_techniques = ['viewport', 'frontview', 'camera']

from pyformex.gui.draw import *

def fourview():
    layout(4)
    for i in range(1,4):
        pf.GUI.viewports.linkScene(i,0)
    viewport(0)
    view('front')
    pf.canvas.update()
    pf.canvas.camera.lockview()
    viewport(1)
    view('right')
    pf.canvas.camera.lockview()
    viewport(2)
    view('top')
    pf.canvas.camera.lockview()
    viewport(3)
    view('iso0')
    for i in range(1,4):
        pf.GUI.viewports[i].redrawAll()
        pf.GUI.viewports[i].zoomAll()

def run():
    resetAll()
    frontview('xz')
    setTriade()
    S = Formex.read(pf.cfg['datadir'] / 'man.pgf')
    draw(S)
    fourview()


if __name__ == '__draw__':
    run()
# End
