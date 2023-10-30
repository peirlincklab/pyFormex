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
"""Cube

Show (the faces of) a cube with different colors.
The user is presented a dialog where he can choose whether the faces
of the cube are drawn as triangles or as quadrilaterals, and what color
scheme is to be used: no color (black), a single color, a single color per
face, or a color gradient over the faces.
"""
_name = 'Cube'
_level = 'normal'
_topics = ['geometry', 'surface']
_techniques = ['color', 'elements', 'reverse']

from pyformex.gui.draw import *
#from pyformex.elements import Hex8
#from pyformex import simple


def cube_quad(color):
    """Create a cube with colored quad faces"""
    cube = simple.Cube(2)
    if color == 'Single':
        color = 'red'
    elif color == 'Face':
        color = [4, 1, 5, 2, 6, 3]
    elif color == 'Full':
        color = np.array([7, 6, 4, 5, 3, 2, 0, 1])[cube.elems]
    cube.attrib(color=color)
    return cube


def cube_tri(color=None):
    """Create a cube with triangles."""
    cube = simple.Cube(2).convert('tri3')
    if color == 'Single':
        color = 'blue'
    elif color == 'Face':
        color = np.arange(1, 7).repeat(2)
    elif color == 'Full':
        color = np.array([[4, 5, 7], [7, 6, 4], [7, 3, 2], [2, 6, 7], [7, 5, 1], [1, 3, 7],
                       [3, 1, 0], [0, 2, 3], [0, 1, 5], [5, 4, 0], [0, 4, 6], [6, 2, 0]])
    cube.attrib(color=color)
    return cube


def showCube(base, color):
    if base == 'Triangle':
        cube = cube_tri(color)
    else:
        cube = cube_quad(color)
    draw(cube, clear=True)
    export({f'Cube_{base}_{color}': cube})
#    zoomAll()


def show():
    """Show a single Cube"""
    if dialog.validate():
        res = dialog.results
        showCube(res['Base'], res['Color'])


def showAll():
    """Show all Cubes"""
    for base in baseshape:
        for color in colormode:
            showCube(base, color)
            sleep(1)


def timeout():
    showAll()
    dialog.close()


baseshape = ['Quad', 'Triangle']
colormode = ['None', 'Single', 'Face', 'Full']

def run():
    """Show the dialog"""
    global dialog

    clear()
    reset()
    smooth()
    view('iso')

    dialog = Dialog(caption=_name, store=_name+'_data', items=[
        _I('Base', 'Quad', choices=baseshape),
        _I('Color', 'Full', choices=colormode),
    ], actions=[('Close', None), ('ShowAll', showAll), ('Show', show)])
    dialog.show(timeoutfunc=timeout)


if __name__ == '__draw__':
    run()
# End
