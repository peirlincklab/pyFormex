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
"""Remesh

This example illustrates remeshing a TriSurface
"""

_level = 'normal'
_topics = ['surface']
_techniques = ['remesh']

from pyformex.gui.draw import *

def run():
    global S, T
    infile = pf.cfg['datadir'] / 'horse.off'
    S = TriSurface.read(infile)
    T = S.remesh(npoints=2000, ndiv=3).removeNonManifold().fixNormals('internal')
    print(T)
    out = [S, T]
    if software.External.has('instant-meshes'):
        global U, V
        U = S.remesh(method='instant', nplex=3, vertices=2000)
        print(U)
        V = S.remesh(method='instant', nplex=4, vertices=500)
        print(V)
        out.extend([U, V])
    layout(len(out), 2)
    i = 0
    for M in out:
        viewport(i)
        i += 1
        clear()
        smoothwire()
        view('xy')
        draw(M)

if __name__ == '__draw__':
    run()
# End
