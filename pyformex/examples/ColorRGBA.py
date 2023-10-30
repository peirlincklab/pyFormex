##  You should have received a copy of the GNU General Public License
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
"""ColorRGBA

This example demonstrates the use of RGBA color model in drawing
operations.

"""


_level = 'normal'
_topics = ['drawing']
_techniques = ['color', 'rgba', 'transparency']

from pyformex.gui.draw import *

def run():
    reset()
    clear()
    transparent(False)
    flat()
    nx, ny = 1, 1
    F = Formex('4:0123').replicm((nx, ny)).centered()
    G = F.scale((0.99, 0.6, 0))
    F1 = F.trl(0, 1.2)
    G1 = G.trl(0, 1.2)
    F.attrib(color = [[(1., 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1)]])
    F1.attrib(color = [[(1, 0, 0, 0.0), (0, 1, 0, 1.0), (0, 0, 1, 1.0), (1, 0, 1, 0)]])
    FA = draw(F, ontop=True)
    FB = draw(F1, ontop=True)
    draw(G)
    draw(G1)
    print("Colors of the left square:")
    print(FA.color)
    print("Colors of the right square:")
    print(FB.color)
    showInfo("""..

These two colored squares were drawn with RGBA color mode. The RGB
components are the same for both squares. The squares hide a black
rectangle.

For the left square only RGB components were given, without A value:
the default 0.5 is then used for all points, making the transparency
uniform over the square.
For the right square the value of A was set to 0.0 at the left corners
and to 1.0 at the right corners, making the transparency
range horizontally over the square from fully transparent to opaque.

To see the effect, click the 'Toggle Transparent Mode' button.
""", caption='Example info')


if __name__ == '__draw__':
    run()

# End
