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
"""General Qt utility functions.

"""

import pyformex as pf

def Size(w):
    """Return the size of a widget as a tuple."""
    return w.width(), w.height()

def Pos(w):
    """Return the relative position of a widget as a tuple.

    This is the position relative to its parent.
    """
    return w.x(), w.y()

def relPos(w, parent=None):
    """Return the position of a widget relative to a parent.

    If no parent is specified, it is taken as the GUI main window.
    """
    if parent is None:
        parent = pf.GUI
    x, y = 0, 0
    while w != parent:
        #print(w)
        dx, dy = w.x(), w.y()
        x += dx
        y += dy
        #print("rel pos = %s, %s; abs pos = %s, %s" % (dx,dy,x,y))
        w = w.parent()
        if not w:
            break
    return x, y


def relGeom(w, parent=None):
    return (*relPos(w), w.width(), w.height())


def absRect(w):
    """Return the absolute rectangle geometry of the widget as a tuple

    Returns
    -------
    tuple:
        (x,y,w,h) where x,y is the position relative to the screen origin.
    """
    x0, y0 = Pos(pf.GUI)
    x, y = relPos(w)
    w, h = Size(w)
    return x+x0, y+y0, w, h

def MaxSize(*args):
    """Return the maximum of a list of sizes"""
    return max([i[0] for i in args]), max([i[1] for i in args])

def MinSize(*args):
    """Return the maximum of a list of sizes"""
    return min([i[0] for i in args]), min([i[1] for i in args])

def printpos(w, t=''):
    print(f"{t} {w.x()} x {w.y()}")

def sizeReport(w, t=''):
    return f"{t} {w.width()} x {w.height()}"


#### End
