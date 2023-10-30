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
"""Horseslice

This example illustrates working with triangulated surfaces in pyFormex.
A triangulated surface (TriSurface) is read from the file 'horse.off'
in the pyformex data directory. The surface is drawn.

Next the surface is intersected with a series of parallel plan. A dialog
dialog pops up where the user can set the parameters to define this planes.
Finally, the intersection curves are drawn on the surface. The 'ontop' option
will draw the curves fully visible (like if the surface were transparent).
The 'remove surface' option removes the surface, leaving only the curves.
"""


_level = 'advanced'
_topics = ['geometry', 'surface', 'mesh']
_techniques = ['intersection', 'dialog']

from pyformex.gui.draw import *

def run():
    reset()
    smooth()
    lights(True)

    S = TriSurface.read(getcfg('datadir') / 'horse.off')
    SA = draw(S)

    res = askItems([
        _I('direction', [1., 0., 0.]),
        _I('number of sections', 20),
        _I('color', 'red'),
        _I('ontop', False),
        _I('remove surface', False),
        ])
    if not res:
        return

    d = res['direction']
    n = res['number of sections']
    c = res['color']

    slices = S.slice(dir=d, nplanes=n)
    linewidth(2)
    draw(slices, color=c, view=None, bbox='last', nolight=True, ontop=res['ontop'])
    export({'_HorseSlice_slices': slices})

    if res['remove surface']:
        undraw(SA)

    zoomAll()


if __name__ == '__draw__':
    run()
# End
