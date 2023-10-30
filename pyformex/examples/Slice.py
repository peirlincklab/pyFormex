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

"""Slice

This example illustrates the 'cutWithPlane' method applied on a
surface and the animation of the results.

A model of a horse is repeatedly cut by a plane and the cut-off parts
are rotated and translated.
"""


_level = 'advanced'
_topics = ['surface']
_techniques = ['color', 'widgets', 'animation']

from pyformex.gui.draw import *

def askSlices(bb):
    res = askItems([('Direction', 0),
                    ('# slices', 15),
                    ('total rot', 70.),
                   ], caption = 'Define the slicing planes')
    if res:
        axis = res['Direction']
        nslices = res['# slices']
        totalrot = res['total rot']
        xmin, xmax = bb[:, axis]
        dx =  (xmax-xmin) / nslices
        x = np.arange(nslices+1) * dx
        N = unitVector(axis)
        P = [bb[0]+N*s for s in x]
        return P, N, totalrot
    else:
        return None


def run():
    reset()
    smooth()
    lights(True)
    transparent(False)
    setView('horse', [20, 20, 0])
    S = TriSurface.read(getcfg('datadir') / 'horse.off')
    bb = S.bbox()

    t = -0.3
    bb[0] = (1.0-t)*bb[0] + t*bb[1]
    draw(S, bbox=bb, view='front')
    #return

    try:
        P, n, t = askSlices(S.bbox())
    except Exception:
        return

    a = t / len(P)

    F = S.toFormex()
    G = []
    setDrawOptions({'bbox': None})

    clear()
    A = None
    for i, p in enumerate(P):
        F1, F = F.cutWithPlane(p, -n)
        if F1.nelems() > 0:
            F1.setProp(i)
        G = [g.rot(a, around=p) for g in G]
        G.append(F1)
        B = draw([F, G])
        if A:
            undraw(A)
        A = B

    x = pf.canvas.width()//2
    y = pf.canvas.height() - 40
    T = drawText("No animals got hurt during the making of this movie!", (x, y), size=18, gravity='C')
    for i in range(8):
        sleep(0.3)
        undecorate(T)
        sleep(0.3)
        decorate(T)

if __name__ == '__draw__':
    run()
# End
