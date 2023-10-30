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
"""Interpolate

This examples illustrates the working of the 'interpolate' method.

First, two lines are created, each one consisting of two line segments.
Then new lines are created by interpolating between the two.
Next, an interpolation is created with the element order swapped.
Finally, the lines are subdivided in smaller segments.
"""


_level = 'beginner'
_topics = ['geometry']
_techniques = ['color', 'interpolate', 'subdivide']

from pyformex.gui.draw import *

def run():
    clear()
    flat()

    a = Formex([[[0, 0, 0], [1, 0, 0]], [[1, 0, 0], [2, 0, 0]]]).setProp([1, 2])
    b = Formex([[[0, 1, 0], [1, 1, 0]], [[1, 1, 0], [2, 1, 0]]]).setProp([3, 4])
    print("Two lines")
    draw([a, b])
    drawNumbers(a)
    drawNumbers(b)

    n = 5

    pause()
    c = a.interpolate(b, n)
    print("Interpolate between the two")
    clear()
    draw(c)
    drawNumbers(c)

    pause()
    d = a.interpolate(b, n, swap=True)
    clear()
    print("Interpolate again with swapped order")
    draw(d)
    drawNumbers(d)
    #return

    pause()
    f = c.subdivide(n)
    f.setProp((1, 3))
    clear()
    print("Subdivide the set of lines")
    draw(f)
    drawNumbers(f)


if __name__ == '__draw__':
    run()
# End
