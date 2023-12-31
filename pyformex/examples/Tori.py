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
#
"""Torus variants

"""

_level = 'normal'
_topics = ['geometry']
_techniques = ['programming', 'widgets', 'globals']


from pyformex.gui.draw import *

def torus(m, n, surface=True):
    """Create a torus with m cells along big circle and n cells along small."""
    if surface:
        C = Formex('3:016823', [1, 3])
    else:
        C = Formex('l:164', [1, 2, 3])
    F = C.replicm((m, n))
    G = F.translate(2, 1).cylindrical([2, 1, 0], [1., 360./n, 1.])
    H = G.translate(0, 5).cylindrical([0, 2, 1], [1., 360./m, 1.])
    return H


def series():
    view='iso'
    for n in [3, 4, 6, 8, 12]:
        for m in [3, 4, 6, 12, 36]:
            clear()
            draw(torus(m, n), view)
            view=None

def drawTorus(m, n):
    clear()
    draw(torus(m, n), view=None)


def drawit():
    global dialog
    if dialog.validate():
        drawTorus(**dialog.results)

def close():
    global dialog
    dialog.close()

def run():
    global dialog
    m = 20
    n = 10
    dialog = Dialog([
        _I('m', m, itemtype='slider',
           text='Number of elements along large circle', min=3, max=72),
        _I('n', n, itemtype='slider',
           text='Number of elements along small circle', min=3, max=36)
    ], actions=[('Close', close), ('Draw', drawit)])
    dialog.show()


if __name__ == '__draw__':
    run()
# End
