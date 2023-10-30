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
#
"""FieldDraw

This example demonstrates how to use field variables and how to render them.
"""

_level = 'advanced'
_topics = ['mesh', 'postprocess']
_techniques = ['field', 'color']

from pyformex.gui.draw import *


def run():

    clear()
    view('front')
    smoothwire()
    layout(4,2)

    F = simple.rectangle(4, 3)
    M = F.toMesh()
    #M.attrib(color=yellow)

    # add some fields

    # 1. distance from point 7, defined at nodes

    data = at.length(M.coords - M.coords[7])
    M.addField('node', data, 'dist')


    # 2. convert to field defined at element nodes
    M.convertField('dist', 'elemn', 'distn')

    # 3. convert to field constant over elements
    M.convertField('distn', 'elemc', 'distc')

    # 4. convert back to node field
    fld = M.getField('distc').convert('node')

    print(M.fieldReport())

    # draw the fields
    viewport(0)
    drawField(M.getField('dist'))
    zoomAll()
    viewport(1)
    drawField(M.getField('distn'))
    zoomAll()
    viewport(2)
    drawField(M.getField('distc'))
    zoomAll()
    viewport(3)
    drawField(fld)
    zoomAll()


if __name__ == '__draw__':
    run()
# End
