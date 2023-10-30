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

"""BorderExtension

This example shows how to create extension tubes on the borders of a
surface techniques.
"""


_level = 'normal'
_topics = ['surface']
_techniques = ['extrude', 'borderfill', 'cut']

from pyformex.gui.draw import *
from pyformex import geomtools

def run():
    reset()
    clear()
    # read and draw the surface
    chdir(getcfg('datadir'))
    S = TriSurface.read('bifurcation.off.gz').smooth()
    draw(S)
    # Get the center point and the border curves
    CS = S.center()
    border = S.border()

    # B0 = border[0]
    # clear()
    # draw(B0, color=red)
    # print(B0)
    # drawNumbers(B0)
    # drawNumbers(B0.nodes)
    # return


    BL = []
    for B in border:
        draw(B, color=red, linewidth=2)
        # find the smallest direction of the curve
        d, s = geomtools.smallestDirection(B.coords, return_size=True)
        # Find outbound direction of extension
        CB = B.center()
        p = np.sign(at.projection((CB-CS), d))
        # Flatten the border curve and translate it outwards
        B1 = B.projectOnPlane(d, CB).trl(d, s*8*p)
        draw(B1, color=green)
        # create a surface between border curve and translated flat curve
        M = B.connect(B1)
        draw(M, color=blue, bkcolor=yellow)
        BL.append(M)

    zoomAll()

    if ack("Convert extensions to 'tri3' and add to surface?"):
        # convert extensions to 'tri3'
        BL = [B.setProp(i+1).convert('tri3') for i, B in enumerate(BL)]

        clear()
        draw(BL, color=yellow, bkcolor=green)
        export(dict((f'BE-{i}', B) for i, B in enumerate(BL)))

        T = TriSurface.concatenate([S]+BL).fuse().compact().fixNormals('internal')
        clear()
        draw(T)
        export({'T': T})


if __name__ == '__draw__':
    run()

# End
