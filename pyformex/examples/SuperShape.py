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
"""Super Shape

This example illustrates the power of the superspherical transformation.
It is also a nice example of dedicated GUI construction and of the use
of files to store data.

The example creates sphere-like structures by applying a superspherical
transformation to a planar grid. The parameters defining the grid and the
transformation can be set from a modeless GUI. The grid as well as the
resulting structure can be shown. The parameters can also be saved to a
file. Finally, the GUi also allows to replay the whole set of saved
structures.
"""


_level = 'advanced'
_topic = ['geometry']
_techniques = ['dialog', 'persistence']

from pyformex.gui.draw import *
from pyformex.simple import rectangle
from pyformex.utils import NameSequence
from pyformex.plugins.imagearray import *

dialog = None
savefile = None
tol = 1.e-4

gname = NameSequence('Grid-0')
sname = NameSequence('Shape-0')

color = None
bkcolor = None
colormap = None


def createGrid():
    """Create the grid from global parameters"""
    global B
    nx, ny = grid_size
    b, h = x_range[1]-x_range[0], y_range[1]-y_range[0]
    if grid_base.startswith('tri'):
        diag = grid_base[-1]
    else:
        diag = ''
    B = rectangle(nx, ny, b, h, diag=diag, bias=grid_bias).translate([x_range[0], y_range[0], 1.])
    if grid_skewness != 0.0:
        B = B.shear(0, 1, grid_skewness*b*ny/(h*nx))
    if x_clip:
        B = B.clip(B.test('any', dir=0, min=x_clip[0]+tol*b, max=x_clip[1]-tol*b))
    if y_clip:
        B = B.clip(B.test('any', dir=1, min=y_clip[0]+tol*h, max=y_clip[1]-tol*h))
    export({grid_name: B})


def createSuperShape():
    """Create a super shape from global parameters"""
    global F
    B = pf.PF[grid_name]
    F = B.superSpherical(n=north_south, e=east_west, k=eggness)
    if scale == [1.0, 1.0, 1.0]:
        pass
    else:
        F = F.scale(scale)
    if post:
        print("Post transformation")
        F = eval(post)
    export({name: F})


def drawGrid():
    """Show the last created grid"""
    clear()
    wireframe()
    view('front')
    draw(B, color=grid_color)


def drawSuperShape():
    """Show the last created super shape"""
    global color, colormap
    clear()
    smoothwire()
    if isinstance(color, str) and color.startswith('file:'):
        print("trying to convert color")
        im = QImage('Elevation-800.jpg')
        print(im)
        print(im.isNull())
        nx, ny = grid_size
        color, colormap = qimage2glcolor(im.scaled(nx, ny))[0]
        print(color.shape)

    draw(F, color=color, colormap=colormap, bkcolor=bkcolor)


def acceptData():
    if dialog.validate():
        pf.PF['_SuperShape_data_'] = dialog.results
        globals().update(dialog.results)
        return True
    return False

##########################
# Button Functions

def showGrid():
    """Accept data, create and show grid."""
    if acceptData():
        createGrid()
        drawGrid()

def replayShape():
    """Create and show grid from current data."""
    createGrid()
    createSuperShape()
    drawSuperShape()

def show():
    """Accept data, create and show shape."""
    if acceptData():
        replayShape()


def close():
    global dialog, savefile
    if dialog:
        dialog.close()
        dialog = None
    if savefile:
        savefile.close()
        savefile = None
    scriptRelease(__file__)



def save():
    global savefile
    show()
    if savefile is None:
        filename = askNewFilename(filter="Text files (*.txt)")
        if filename:
            savefile = open(filename, 'a')
    if savefile:
        print("Saving to file")
        savefile.write('%s\n' % str(dialog.results))
        savefile.flush()
        globals().update({'grid_name': next(gname), 'name': next(sname), })
        if dialog:
           dialog['grid_name'].setValue(grid_name)
           dialog['name'].setValue(name)


def replay():
    global savefile
    if savefile:
        filename = savefile.name
        savefile.close()
    else:
        filename = getcfg('datadir') / 'supershape.txt'
        filename = askFilename(cur=filename, filter="Text files (*.txt)")
    if filename:
        savefile = open(filename, 'r')
        for line in savefile:
            print(line)
            globals().update(eval(line))
            replayShape()
        savefile = open(filename, 'a')


################# Dialog

dialog_items = [
    _G('Grid data', [
        _I('grid_size', [24, 12],),
        _I('x_range', (-180., 180.),),
        _I('y_range', (-90., 90.),),
        _I('grid_base', 'quad', itemtype='radio', choices=['quad', 'tri-u', 'tri-d', 'tri-x']),
        _I('grid_bias', 0.0,),
        _I('grid_skewness', 0.0,),
        _I('x_clip', (-360., 360.),),
        _I('y_clip', (-90., 90.),),
        _I('grid_name', gname.peek(),),
        _I('grid_color', 'blue',),
        ]),
    _G('Shape data', [
        _I('north_south', 1.0,),
        _I('east_west', 1.0,),
        _I('eggness', 0.0,),
        _I('scale', [1., 1., 1.],),
        _I('post', '',),
        _I('name', sname.peek(),),
        _I('color', 'red',),
        _I('bkcolor', 'yellow',),
#        _I('texture','None',),
        ]),
    ]

dialog_actions = [
    ('Close', close),
    ('Reset', reset),
    ('Replay', replay),
    ('Save', save),
    ('Grid', showGrid),
    ('Show', show)
    ]

dialog_default = 'Show'


def timeOut():
    try:
        show()
    finally:
        close()


def createDialog():
    global dialog

    # Create the dialog
    dialog = Dialog(
        caption = 'SuperShape parameters',
        items = dialog_items,
        actions = dialog_actions,
        default = dialog_default
        )

    # Update its data from stored values
    if '_SuperShape_data_' in pf.PF:
        dialog.updateData(pf.PF['_SuperShape_data_'])


def run():
    """Show the dialog"""
    resetAll()
    clear()
    smoothwire()
    lights(True)
    transparent(False)
    createDialog()
    setView('eggview', (0., -30., 0.))
    view('eggview')
    dialog.show(timeoutfunc=timeOut)
    scriptLock(__file__)

if __name__ == '__draw__':
    run()
# End
