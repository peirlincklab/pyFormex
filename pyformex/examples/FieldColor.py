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
"""FieldColor

This examples shows how to interactively change the colors displayed
on an object.
"""

_level = 'normal'
_topics = ['image']
_techniques = ['color', 'field', 'field color', 'slider']

from pyformex.gui.draw import *
from pyformex.plugins.imagearray import *


def changeColorDirect(i):
    """Change the displayed color by directly changing color attribute."""
    global FA, model
    F = FA.object
    color = F.getField('color_%s' % i)
    if model == 'Quads':
        color = color.convert('elemn')
    color = color.data
    print("Color shape = %s" % str(color.shape))
    #print("Drawables: %s:" % len(FA.drawable))
    for dr in FA.drawable[:2]:
        dr.changeVertexColor(color)
    pf.canvas.update()


def setFrame(item):
    changeColorDirect(item.value())


def run():
    global width, height, FA, dialog, dotsize, model
    clear()
    smooth()
    lights(False)
    view('front')

    # read an image from pyFormex data
    filename = getcfg('datadir') / 'butterfly'
    print(filename)
    im = QImage(filename)
    if im.isNull():
        warning("Could not load image '%s'" % fn)
        return
    nx, ny = im.width(), im.height()
    print("Image size: %s x %s" % (nx, ny))
    ntot = nx*ny
    print("Total cells = %s" % ntot)

    # Create a 2D grid of nx*ny elements
    res = askItems([_I('model', itemtype='hradio', choices=['Dots', 'Quads'])])
    if not res:
        return

    model = res['model']
    dotsize = 3
    if model == 'Dots':
        base = '1:0'
    else:
        base = '4:0123'
    F = Formex(base).replicm((nx, ny)).toMesh()


    # Draw the image
    color, colormap = qimage2glcolor(im)
    if colormap is not None:
        print("This image is not fit for our purposes.")
        return

    # Currently, Field Color changes will only work with VertexColor.
    # Therefore, when using Quads, multiplex the color to vertexcolor.
#    if model == 'Quads':
#        color = multiplex(color,4,axis=-2)

    print("Color shape = %s" % str(color.shape))
    FA = draw(F, color=color, colormap=None, marksize=dotsize, name='image')

    # Create some color fields
    # The color fields consist of the original image with one of
    # the standard colors mixed in.
    nframes = 10
    mix = [0.7, 0.3]
    for i in range(nframes):
        fld = mix[0] * color + mix[1] * pf.canvas.settings.colormap[i]
        #fldtype = 'node' if model == 'Dots' else 'elemc'
        fldtype = 'elemc'
        F.addField(fldtype, fld, 'color_%s' % i)

    frame = 0
    dialog = Dialog([
        _I('frame', frame, itemtype='slider', min=0, max=nframes-1, ticks=1,
           func=setFrame, tooltip="Move the slider to see one of the color"
           "fields displayed on the original Actor"),
        ])
    dialog.setMinimumWidth(500)
    dialog.show()


if __name__ == '__draw__':
    run()

# End
