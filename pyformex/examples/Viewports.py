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
"""Viewports.py

Demonstrate multiple viewports.
"""

_level = 'advanced'
_topics = ['surface']
_techniques = ['viewport', 'color']

from pyformex.gui.draw import *
def atExit():
    print("EXITING")
    layout(1)
    reset()

def run():
    reset()
    smoothwire()

    nsl = 0
    F = Formex.read(getcfg('datadir') / 'horse.pgf')

    layout(1)
    FA = draw(F, view='front')
    drawText('Viewport 0', (20, 20), size=20)

    pause(msg='NEXT: Create Empty Viewport 1')
    layout(2)
    smooth()
    FA = draw(F, view='front')
    drawText('Viewport 1', (20, 20), size=20)
    pf.GUI.viewports.updateAll()
    pause()
    return

    pause(msg='NEXT: Create Viewport 2 and draw in green')
    layout(3)
    draw(F, color='green')

    pause(msg='NEXT: Link Viewport 2 to Viewport 0')

    linkViewport(2, 0)
    pf.GUI.viewports.updateAll()

    pause(msg='NEXT: Create 4 Viewports all linked to Viewport 0')

    layout(4, 2)
    viewport(0)
    for i in range(1, 4):
        linkViewport(i, 0)

    pause(msg='NEXT: Change background colors in the viewports')

    colors=['indianred', 'olive', 'coral', 'yellow']

    for i, v in enumerate(['front', 'right', 'top', 'iso']):
        viewport(i)
        view(v)
        bgcolor(colors[i])

    pause(msg='NEXT: Cut the horse in viewport 3, notice results visible in all')

    viewport(3)
    G = F.cutWithPlane([0., 0., 0.], [-1., 0., 0.], side='+')
    clear()
    draw(G)  # this draws in the 4 viewports !
    pf.GUI.viewports.updateAll()

    pause(msg='NEXT: DONE')


if __name__ == '__draw__':
    run()
# End
