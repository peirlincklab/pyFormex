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

"""ObjectDialog

This example illustrates the interactive modification of object rendering.

The example creates the same geometry as the WebGL example, and then pops up
a dialog to allow the user to interactively change the rendering of the
objects. Attributes that can be changed include color, opacity, visibility,

"""

_level = 'normal'
_topics = ['export']
_techniques = ['webgl']

from pyformex.gui.draw import *

from pyformex.simple import sphere, sector, cylinder
from pyformex.mydict import Dict
from pyformex.plugins.webgl import WebGL
from pyformex.opengl.objectdialog import objectDialog
from pyformex.examples.WebGL import createGeometry


def run():
    reset()
    clear()
    smooth()
    transparent()
    bgcolor(white)
    view('right')

    # Create some geometrical objects
    objects = createGeometry()

    # make them available in the GUI
    export([(obj.attrib.name, obj) for obj in objects])

    # draw the objects
    drawn_objects = draw(objects)
    zoomAll()

    # create an object dialog
    dialog = objectDialog(drawn_objects)
    if dialog:
        dialog.show()


if __name__ == '__draw__':
    run()

# End
