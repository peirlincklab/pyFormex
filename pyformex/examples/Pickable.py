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

"""Pickable

This example illustrates the use of the pickable argument in pick functions
and the pickable attribute of Actors.
"""


_level = 'normal'
_topics = ['pick']
_techniques = ['pickable']

from pyformex.gui.draw import *
from pyformex.examples.WebGL import createGeometry


def simulate_pick(rect=None):
    """Create the events for picking the specified rectangle"""
    events = pf.canvas.mouse_rect_pick_events(rect)
    pf.canvas.events.extend(events)


def run():
    reset()
    clear()
    smoothwire()
    bgcolor(white)
    view('right')

    # Create some geometrical objects (sphere, cone, cylinder)
    objects = createGeometry()

    # Make the cone non-pickable
    objects[1].attrib(pickable=False)

    # draw the objects
    actors = draw(objects)
    zoomAll()

    # pick elements
    if pf.GUI.runallmode:
        # Start an autopick function
        do_after(2, simulate_pick)
    pick('element', prompt="Pick elements and notice that the cone is not pickable")

    # force pick from sphere and cone!
    if pf.GUI.runallmode:
        # Start an autopick function
        do_after(2, simulate_pick)
    pick('element', pickable=actors[:2], prompt="Pick elements and notice that this time the sphere and the cone are the only pickables")


if __name__ == '__draw__':
    run()

# End
