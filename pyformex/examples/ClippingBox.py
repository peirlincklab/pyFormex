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
"""ClippingBox

Clips a mesh with sheared box without using VTK.
"""

_level = 'normal'
_topics = ['surface']
_techniques = ['boolean', 'partition']

from pyformex.gui.draw import *
from pyformex.simple import sphere, cuboid
from pyformex.plugins.gts_itf import gtsset


def run():
    clear()
    smooth()

    # Create two surfaces
    S1 = sphere(10).setProp(1)
    S2 = cuboid(*S1.bbox()).toMesh().scale([0.8, 0.8, 1]).rot(30, 1).rot(20, 0).shear(2, 1, 0.3).toSurface().setProp(6)
    draw(S1,alpha=1)
    draw(S2)

    # Create all the set operations
    S = S1.gts_set(S2, 'a', prop=[1,1,6,6], verbose=True)

    # Collect everything in a nice dialog to present
    result = dict(zip(
        ['s1 && s2', 's1', 's2', 's1 in s2', 's1 out s2', 's2 in s1',
         's2 out s1', 's1 + s2', 's1 * s2', 's1 - s2', 's2 - s1', 'symdiff'],
        [S1 + S2, S1, S2] + S))

    def show(item):
        key = item.value()
        clear()
        if key in result:
            draw(result[key])

    dialog = Dialog(caption="ClippingBox", items=[
        _I('info', "Which surface to display?", itemtype='label', text=''),
        _I('key', choices=list(result.keys()), itemtype='hpush', func=show,
           text=''),
    ], actions=[('Cancel',)])
    dialog.show()


if __name__ == '__draw__':
    run()
