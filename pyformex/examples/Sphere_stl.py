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
"""Sphere_stl

"""


_level = 'normal'
_topics = ['geometry', 'surface']
_techniques = ['connect', 'spherical', 'dialog', 'persistence', 'color']

from pyformex.gui.draw import *

def run():
    clear()
    top = 0.
    bot = -90.
    r = 1.
    n = 8
    m = 12  # initial divisions

    # Create points
    dy = float(top-bot) / n
    F = [Formex(np.zeros((m+1, 1, 3)))]
    for i in range(n):
        dx = 360./(m+i)
        f = Formex([[[j*dx, (i+1)*dy, 0]] for j in range(m+i+1)])
        F.append(f)
        draw(F)

    # Create Lines
    if ack("Create Line model?"):
        G = [[], [], []]
        for i, f in enumerate(F[1:]):
            G[0].append(connect([f, f], bias=[0, 1]))
            G[1].append(connect([F[i], f], bias=[0, 0]))
            if i > 0:
                G[2].append(connect([F[i], f], bias=[0, 1]))
        G = [Formex.concatenate(Gi) for Gi in G]
        for i, f in enumerate(G):
            f.setProp(i)
        G = Formex.concatenate(G)

        clear()
        draw(G)
        print(G.bbox())
        L = G.translate([0, bot, r]).spherical()
        clear()
        draw(L)

    # Create Triangles
    if ack("Create Surface model?"):
        G = [[], []]
        for i, f in enumerate(F[1:]):
           G[0].append(connect([F[i], f, f], bias=[0, 1, 0]))
           if i > 0:
               G[1].append(connect([F[i], F[i], f], bias=[0, 1, 1]))
        G = [Formex.concatenate(Gi) for Gi in G]
        for i, f in enumerate(G):
           f.setProp(i+1)
        G = Formex.concatenate(G)

        clear()
        draw(G)

        smoothwire()
        #pf.canvas.update()
        T = G.translate([0, bot, r]).spherical()
        clear()
        draw(T)

        T += T.reflect(dir=2)
        clear()
        draw(T)

        if ack('Export this model in STL format?', default='No'):
            fn = askNewFilename(getcfg('workdir'), "Stl files (*.stl)")
            if fn:
                from pyformex.filewrite import writeSTL
                writeSTL(fn, T.coords)


if __name__ == '__draw__':
    run()
# End
