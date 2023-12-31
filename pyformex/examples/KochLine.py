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
"""Koch line

This example illustrates the use of the 'lima' plugin to create subsequent
generations of a Koch line. The Koch line is a line with fractal properties.
Six generations of the Koch line are created. They are drawn in one of three
ways:

- all on top of each other
- in a series one above the other
- as radii of an n-pointed star

The actual draw method is choosen randomly. Execute again to see another one.
"""


_level = 'beginner'
_topics = ['illustration']
_techniques = ['color', 'lime']

from pyformex.gui.draw import *
from pyformex.plugins.lima import lima

def run():
    clear()
    wireframe()
    view('front')
    linewidth(2)
    n = 6  # number of generations

    # We use the lima module to create six generations of the Koch line
    F = [Formex(lima("F", {"F": "F*F//F*F"}, i,
                      {'F': 'fd();', '*': 'ro(60);', '/': 'ro(-60);'}), i)
          for i in range(n)]

    # scale each Formex individually to obtain same length
    sc = [3**(-i) for i in range(n)]
    sz = sc[0]/3.
    F = [F[i].scale(sc[i]) for i in range(n)]

    # display all lines in one (randomly choosen) of three ways
    mode = np.random.randint(3)
    if mode == 0:
        # all on top of each other
        draw([F[i].translate([0, sz*(i-1), 0]) for i in range(n)])

    elif mode == 1:
        # one above the other
        draw([F[i].translate([0, sz*n, 0]) for i in range(n)])

    else:
        # as radii of an n-pointed star
        draw([F[i].rotate(360.*i/n) for i in range(n)])

    zoomAll()

if __name__ == '__draw__':
    run()
# End
