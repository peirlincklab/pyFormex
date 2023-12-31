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

"""Mesh

This example illustrates some of the powerful methods provided by the
**Mesh** class. The example constructs a 2D or 3D (selectable by the user)
mesh by extruding a point into a line, the line into a surface, and in case
of a 3D structure, the surface into a volume.

In a sequence of steps, the example then draws the following geometries with
element numbers included:

- the extruded geometry,
- all the edges of all elements,
- the unique edges,
- all the faces of all elements,
- the unique faces,
- the border (in the 3D case, this is a set of faces, in the 2D case it is a
  set of lines.

At each step the number of elements is printed.

Remark
......
The script pauses at each step.
The user should click the **STEP** button to move the the next step, or the
**CONTINUE** button to move to the end of the script.

Script
......
Notice how the same script with the same methods is working for both the 2D
and the 3D cases.

Exercises
.........
1. Make this script also work for the 1D case.

"""


_level = 'beginner'
_topics = ['geometry', 'mesh']
_techniques = ['extrude', 'border', 'pause']

from pyformex.gui.draw import *


def run():
    clear()
    smoothwire()
    transparent()

    n = 3, 2, 5
    a = Formex(origin())

    res = ask("Choose the model:", ["None", "2D", "3D", "Help"])
    if res == "None":
        return
    if res == "Help":
        showDoc()
        return

    showInfo("At each step, press Play/Step to continue")

    ndim = int(res[0])

    if ndim == 2:
        view('front')
    else:
        view('iso')

    for i in range(ndim):
        a = a.extrude(n[i], i)

    draw(a)
    drawNumbers(a)

    clear()
    m = a.toMesh().setProp(1)
    export({'mesh': m})
    draw(m)
    drawNumbers(m)
    pause(msg="%s elements" % m.nelems())


    flat()
    e = Mesh(m.coords, m.getLowerEntities(1)).setProp(2)
    clear()
    draw(e)
    drawNumbers(e)
    pause(msg="%s edges" % e.nelems())

    e = Mesh(m.coords, m.edges).setProp(2)
    clear()
    draw(e)
    drawNumbers(e)
    pause(msg="%s unique edges" % e.nelems())

    smoothwire()
    e = Mesh(m.coords, m.getLowerEntities(2)).setProp(3)
    clear()
    draw(e)
    drawNumbers(e)
    pause(msg="%s faces" % e.nelems())

    e = Mesh(m.coords, m.faces).setProp(3)
    clear()
    draw(e)
    drawNumbers(e)
    pause(msg="%s unique faces" % e.nelems())

    e = Mesh(m.coords, m.getBorder()).setProp(4)
    export({'border': e})
    clear()
    draw(e)
    drawNumbers(e)
    pause(msg="%s border elements" % e.nelems())

    clear()
    m = m.setProp(np.arange(m.nelems()))
    draw(m)
    drawNumbers(m)
    pause(msg="mesh with properties")

    e = m.getBorderMesh()
    clear()
    draw(e)
    drawNumbers(e)
    print("border elements inherit the properties")

if __name__ == '__draw__':
    run()
# End
