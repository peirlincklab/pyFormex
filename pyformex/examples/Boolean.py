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
"""Boolean

Perform boolean operations on surfaces
"""

_level = 'normal'
_topics = ['surface', 'gts']
_techniques = ['boolean', 'intersection']

from pyformex.gui.draw import *
from pyformex.simple import cylinder
from pyformex.trisurface import fillBorder


def drawResults(**res):
    op = res['op'].split()[0]
    verbose = res['verbose']
    scale = res['scale 2']
    rot = res['rot 2']
    trl = res['trl 2']
    # Compute result of operation
    G = F.scale(scale).rotate(rot, 0).trl(0, trl).setProp(1)

    if op == 'I':
        R = F.intersection(G, verbose=verbose)
    else:
        R = F.gts_set(G, op, prop=[2,2,1,1], verbose=verbose)
    clear()
    draw(R)

    if op == 'I':
        if ack('Create a surface inside the curve ?'):
            R = R.toMesh()
            e = R.elems.chained()
            R = Mesh(R.coords, R.elems.chained()[0])
            clear()
            draw(R, color=red, linewidth=3)
            S = fillBorder(R, method='planar')
            draw(S)

def close():
    global dialog
    if dialog:
        dialog.close()
        dialog = None
    # Release script lock
    scriptRelease(__file__)

def show():
    if dialog.validate():
        drawResults(**dialog.results)

def timeOut():
    show()
    wait()
    close()

def run():
    global dialog, F, G
    clear()
    smooth()
    view('iso')
    F = cylinder(L=8., D=2., nt=36, nl=20, diag='u').centered()
    F = TriSurface(F).close(method='planar').fuse().compact().fixNormals('internal')
    F = F.setProp(2)
    G = F.rotate(90., 0).trl(0, 1.).setProp(1)
    export({'F': F, 'G': G})
    draw([F, G])
    _items =\
        [_I('op', text='Operation', choices=[
            '- (Difference 1-2)',
            '* (Intersection)',
            '+ (Union)',
            '2- (Difference 2-1)',
            '^ (Symmetric difference)',
            'I (Intersection curve)',
            ]),
         _I('verbose', False, text='Verbose'),
         _I('scale 2', 1.0),
         _I('rot 2', 90.),
         _I('trl 2', 1.),
        ]
    dialog = Dialog(
        items=_items,
        actions=[('Close', close), ('Show', show)],
        default='Show')
    dialog.show(timeoutfunc=timeOut)


if __name__ == '__draw__':
    run()
# End
