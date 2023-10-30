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

"""Interactive modification of the rendered scene

This module contains some tools that can be used to interactively
modify the rendered scene.
"""

import pyformex as pf
from .actors import Actor
from pyformex import colors
from pyformex.gui.widgets import _T, _G, _I, Dialog


def objectDialog(obj=None, unlike='object_', **kargs):
    """Create an interactive object dialog for drawn objects

    obj is a single drawn object or a list thereof.
    If no objects are specified, the current scene actors are
    used.
    A drawn object is the return value of a draw() function call.
    """
    items = None

    def set_attr(field):
        actor = field.data
        key = field.text()
        val = field.value()
        if key in ['objectColor', 'objectBkColor']:
            #print("VALUE %s" % val)
            val = colors.GLcolor(val)
        print("%s: %s = %s" % (actor.name, key, val))
        setattr(actor, key, val)
        pf.canvas.update()

    def objectItems(obj):
        if not isinstance(obj, Actor):
           return []

        items = [
#            _I('name', obj.name),
            _I('visible', True, func=set_attr, data=obj),
            _I('opak', obj.opak, func=set_attr, data=obj),
            ]

        if 'objectColor' in obj:
            items.append(_I('objectColor', obj.objectColor, itemtype='color',min=0.0, max=100.0, scale=0.01, func=set_attr, data=obj))
        if 'objectBkColor' in obj:
            items.append(_I('objectBkColor', obj.objectBkColor, itemtype='color', min=0.0, max=100.0, scale=0.01, func=set_attr, data=obj))
        if 'alpha' in obj:
            items.append(_I('alpha', obj.alpha, itemtype='fslider', min=0.0, max=1.0, scale=0.01, func=set_attr, data=obj))
        if 'bkalpha' in obj:
            items.append(_I('bkalpha', obj.bkalpha, itemtype='fslider', min=0.0, max=1.0, scale=0.01, func=set_attr, data=obj))
        if 'pointsize' in obj:
            items.append(_I('pointsize', obj.marksize, itemtype='fslider', min=0.0, max=100.0, scale=0.1, func=set_attr, data=obj))

        return items

    # process obj
    if obj is None:
        obj = pf.canvas.actors

    if isinstance(obj, Actor):
        items = objectItems(obj)

    elif isinstance(obj, list):
        print([type(o) for o in obj])
        obj = [o for o in obj if isinstance(o, Actor)]
        print([o.name for o in obj])
        if unlike:
            obj = [o for o in obj if not o.name.startswith(unlike)]
        items = [
            _T(o.name, objectItems(o)) for o in obj
            ]

    if items:
        return Dialog(items, caption='Object Render Dialog', **kargs)


# End
