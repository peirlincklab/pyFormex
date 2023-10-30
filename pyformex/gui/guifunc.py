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

"""GUI support functions.

This module defines a collection of functions which are the equivalent of
functions defined in the draw module, but are executed in the viewport with
the current GUI focus, instead of the script viewport.
"""
import pyformex as pf
from pyformex.gui import draw

######## decorator function #############

def viewport_func(funcname):
    """Perform a function on the current GUI viewport.

    Returns a function with the same name and functionality as a function
    in the draw module, but acting on the current GUI viewport instead of
    on the current script viewport (pf.canvas).
    """
    draw_func = getattr(draw, funcname)
    def newf(*args, **kargs):
        """Performs the draw.func on the current GUI viewport"""
        save = pf.canvas
        pf.canvas = pf.GUI.viewports.current
        draw_func(*args, **kargs)
        pf.canvas = save

    newf.__name__ = funcname
    newf.__doc__ = draw_func.__doc__
    return newf


for f in ('renderMode', 'wireMode', 'zoomAll'):
    globals()[f] = viewport_func(f)


def inGUIVP(func, *args, **kargs):
    """Execute a draw function in the current GUI viewport."""
    draw_func = getattr(draw, func.__name__)
    save = pf.canvas
    pf.canvas = pf.GUI.viewports.current
    draw_func(*args, **kargs)
    pf.canvas = save


# End
