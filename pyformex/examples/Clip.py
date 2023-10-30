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

"""Clip

"""

_level = 'beginner'
_topics = ['geometry']
_techniques = ['color']

from pyformex.gui.draw import *
from pyformex import simple


def run():
    resetAll()
    smoothwire()
    setDrawOptions({'clear': True, 'shrink': True})
    delay(1)


    # A square domain of triangles
    n = 16
    F = simple.rectangle(n, n, diag='d')

    # Novation (Spots)
    m = 4
    h = 0.15*n
    r = n//m
    s = n//r
    a = [[r*i, r*j, h]  for j in range(1, s) for i in range(1, s)]

    for p in a:
        F = F.bump(2, p, lambda x: np.exp(-0.75*x), [0, 1])


    # Define a plane
    plane_p = (n/2, n/2, 0.0)
    plane_n = (2.0, 1.0, 0.0)

    # Define a line by a point and direction
    line_p = (0.0, 0.0, 0.0)
    line_n = (1., 1., 0.25)
    d = F.distanceFromLine(line_p, line_n)
    # compute number of nodes closer that 2.2 to line
    close = (d < 2.2).sum(-1)

    sel = [F.test(nodes=0, dir=0, min=1.5, max=3.5),
            F.test(nodes=[0, 1], dir=0, min=1.5, max=3.5),
            F.test(nodes=[0, 1, 2], dir=0, min=1.5, max=3.5),
            F.test(nodes='any', dir=1, min=1.5, max=3.5),
            F.test(nodes='all', dir=1, min=1.5, max=3.5),
            F.test(nodes='none', dir=1, min=1.5),
            F.testPlane(plane_p, plane_n)[1],
            close == 3,
            ]

    txt = ['First node has x between 1.5 and 3.5',
            'First two nodes have x between 1.5 and 3.5',
            'First 3 nodes have x between 1.5 and 3.5',
            'Any node has y between 1.5 and 3.5',
            'All nodes have y between 1.5 and 3.5',
            'No node has y larger than 1.5',
            f'Cut by the plane P = {plane_p}, n = {plane_n}',
            f'3 nodes closer than 2.2 from line ({line_p}, {line_n})',
            ]

    draw(F)

    color = getcfg('canvas/colormap')
    prop = np.zeros(F.nelems(), dtype=at.Int)
    i = 0
    for s, t in zip(sel, txt):
        prop[s] = i
        F.setProp(prop)
        print('%s (%s): %s' % (color[i], sum(s), t))
        draw(F,mode='flat')
        i += 1

    delay(2)
    print('Clip Formex to last selection')
    draw(F.clip(s), view=None)

    print('Clip complement')
    draw(F.cclip(s))

if __name__ == '__draw__':
    run()
# End
