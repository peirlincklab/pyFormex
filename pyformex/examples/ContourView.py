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
"""ContourView

Saves the contour of an object as shown in the viewport.

"""
_level = 'normal'
_topics = ['geometry', 'rendering']
_techniques = ['outline', 'contour']

from pyformex.gui.draw import *
import pyformex as pf
from pyformex.candy import Horse


def outlineBox(F, axis, dmin, dmax):
    """Construct an outlinebox from an outline curve

    F is a plex-2 Formex obtained from Canvas.outline()

    Returns a plex-4 Formex obtained by connecting two translated
    instance of the outline: one to the minimal z-value, one to the
    maximal z-value.
    """
    G1 = F.trl(axis, dmin)
    G2 = F.trl(axis, dmax)
    draw([G1, G2], color=green)
    H = connect([G1, G1, G2, G2], nodid=[0, 1, 1, 0])
    draw(H, color='orange')


def run():
    resetAll()
    smooth()
    clear()
    S = Horse()
    perspective(False)
    SA = draw(S, color=black)   # Default fgcolor (darkgrey) doesn't work
    setDrawOptions(view='cur', bbox=None)
    pause()

    G = pf.canvas.outline(size=[-1, 2000])
    draw(G, color=red)
    pause()

    axis = G.attrib.axis
    dmin, dmax = S.directionalSize(axis)
    outlineBox(G, axis, dmin, dmax)
    perspective()


if __name__ == '__draw__':
    run()
    perspective(True)

# End
