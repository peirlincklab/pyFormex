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

"""2D drawing menu

This pyFormex plugin menu provides some interactive 2D drawing functions.
While the drawing operations themselves are in 2D, they can be performed
on a plane with any orientation in space. The constructed geometry always
has 3D coordinates in the global cartesian coordinate system.
"""

from pyformex.gui import menu
from pyformex.plugins import geometry_menu as gm
from pyformex.plugins.draw2d import *

################################## Menu #############################

def create_menu(before='help'):
    """Create the menu."""
    MenuData = [
        ("&Set grid", create_grid),
        ("&Remove grid", remove_grid),
        ("---", None),
        ("&Toggle Preview", toggle_preview, {'checkable': True}),
        ("---", None),
        ("&Draw Points", draw_points),
        ("&Draw Polyline", draw_polyline),
        ("&Draw Curve", draw_curve),
        ("&Draw Nurbs", draw_nurbs),
        ("&Draw Circle", draw_circle),
        ("---", None),
        ("&Split Curve", split_curve),
        ("---", None),
        ]
    w = menu.Menu('Draw2d', items=MenuData, parent=pf.GUI.menu, before=before)
    return w

def on_reload():
    setDrawOptions({'bbox': 'last'})


# End
