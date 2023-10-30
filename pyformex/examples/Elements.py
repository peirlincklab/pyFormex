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

"""Elements

This example is intended for testing the drawing functions for each of the
implemented element types.
"""
_level = 'normal'
_topics = ['geometry', 'mesh']
_techniques = ['dialog', 'elements']
_name = 'Elements'
_data = _name+'_data'

from pyformex.gui.draw import *

from pyformex.elements import ElementType
from pyformex.mesh import Mesh
from pyformex import utils

eltypes = ElementType.list()
notype = '-----'
colors = [black, blue, yellow, red]


def nextEltype(eltype):
    try:
        ind = eltypes.index(eltype)
        if ind < len(eltypes)-1:
            ind += 1
        else:
            ind = 0
    except:
        ind = 0
    return eltypes[ind]


def showElement(eltype, options):
    clear()
    M = Mesh(eltype=eltype)
    msg = f"Element type: {eltype}"

    if options['Show report']:
        print(M.report())

    ndim = M.level()

    if ndim == 3:
        view('iso')
        #smoothwire()
    else:
        view('front')
        #smoothwire()

    if options['Reverse']:
        M = M.reverse()
        msg += f"\nReversed"

    i = 'xyz'.find(options['Mirror'])
    if i >= 0:
        M = M.trl(i, 0.2)
        M = M + M.reflect(i)
        msg += f"\nMirrored {i}"

    if options['Deform']:
        M.coords = M.coords.addNoise(rsize=0.2)
        # if options['Force dimensionality']:
        #     if ndim < 3:
        #         M.coords[..., 2] = 0.0
        #     if ndim < 2:
        #         M.coords[..., 1:] = 0.0
        msg += f"\nDeformed"

    if options['Subdivide'] != 'No' and ndim > 0:
        if options['Subdivide'] == 'Uniform':
            ndiv = options['Subdivide_uni']
        else:
            ndiv = options['Subdivide_nonuni']
            #print(ndiv)
        ndiv = (ndiv,) * ndim
        #draw(M, color=yellow)
        M = M.subdivide(*ndiv, fuse=False)
        msg += f"\nSubdivided {ndiv}"

    totype = options['Convert to']
    if totype != notype:
        M = M.convert(totype)
        msg += f"\nConverted to {totype}"

    drawText(msg, (10, pf.canvas.height()-20), size=18, color=black)

    M.setProp([5, 6])

    if options['Show nodes']:
        draw(M.coords, marksize=8)
        drawNumbers(M.coords, gravity='NE')
        if M.level() == 1:
            brd = M.borderNodes()
            draw(M.coords[brd], marksize=10)

    if options['Draw as'] == 'Formex':
        M = M.toFormex()
    elif options['Draw as'] == 'Border' and ndim > 0:
        M = M.getBorderMesh()

    if options['Color setting'] == 'prop':
        draw(M)
    else:
        draw(M, color=red, bkcolor=blue)
    zoom(1.2)

def showRes(res):
    eltype = res.pop('Element Type')
    if eltype == 'All':
        for el in eltypes:
            showElement(el, res)
    else:
        showElement(eltype, res)

def close():
    global dialog
    if dialog:
        dialog.close()
        dialog = None
    # Release script lock
    scriptRelease(__file__)

def show():
    if dialog.validate():
        showRes(dialog.results)

def showNext():
    if dialog.validate():
        res = dialog.results
        eltype = nextEltype(res['Element Type'])
        dialog.updateData({'Element Type': eltype})
        res['Element Type'] = eltype
        showRes(res)

def timeOut():
    show()
    wait()
    close()

def change_eltype(item):
    eltype = item.value()
    dialog = item.dialog()
    if dialog:
        convert = dialog['Convert to']
        conversions = list(ElementType.get(eltype).conversions)
        convert.setChoices([notype] + conversions)
        convert.setValue(notype)

def run():
    global dialog
    dialog = Dialog(caption=_name, store=_data, items=[
        _I('Element Type', choices=['All', ]+eltypes, func=change_eltype),
        _C('',[_I('Reverse', False, itemtype='bool'),]),
        _C('',[_I('Deform', False, itemtype='bool'),]),
        _I('Mirror', itemtype='radio', choices=['No', 'x', 'y', 'z']),
        _I('Subdivide', choices=['No', 'Uniform', 'Non-uniform']),
        _I('Subdivide_uni', 1, min=1),
        _I('Subdivide_nonuni', [0.0, 0.2, 0.5, 1.0]),
        _I('Convert to', choices=[notype] + eltypes),
        _I('Draw as', itemtype='radio', choices=['Mesh', 'Formex', 'Border']),
        _I('Show nodes', True),
        _I('Color setting', itemtype='radio', choices=['direct', 'prop']),
        _I('Show report', False, itemtype='bool'),
    ], enablers = [
        ('Subdivide', 'Uniform', 'Subdivide_uni'),
        ('Subdivide', 'Non-uniform', 'Subdivide_nonuni'),
    ], actions=[
        ('Close', close),
        ('Next', showNext),
        ('Show', show)],
    )
    dialog.show(timeoutfunc=timeOut)


if __name__ == '__draw__':
    run()

# End
