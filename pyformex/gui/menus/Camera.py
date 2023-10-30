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
"""Camera handling menu.

"""
from pyformex.gui.draw import setLocalAxes, setGlobalAxes
from pyformex.gui.toolbar import setProjection, setPerspective
from pyformex.gui.guifunc import viewport_func
from pyformex.plugins.cameratools import showCameraTool


def getfunc(name):
    if not name in globals():
        globals()[name] = viewport_func(name)
    return globals()[name]


def cameraAction(action):
    if action.parent().title() in ['Camera', 'Rotate', 'Translate']:
        # only react on actions defined here!
        func = action.data()
        if isinstance(func, str):
            func = getfunc(func)
        if callable(func):
            func()
        else:
            raise ValueError("Unknown function {func}")


MenuData = ('Camera', [
    ('LocalAxes', 'setLocalAxes'),
    ('GlobalAxes', 'setGlobalAxes'),
    ('Projection', 'setProjection'),
    ('Perspective', 'setPerspective'),
    ('Zoom Rectangle', 'zoomRectangle'),
    ('Zoom All', 'zoomAll'),
    ('Zoom In', 'zoomIn'),
    ('Zoom Out', 'zoomOut'),
    ('Dolly In', 'dollyIn'),
    ('Dolly Out', 'dollyOut'),
    ('Pan Left', 'panLeft'),
    ('Pan Right', 'panRight'),
    ('Pan Down', 'panDown'),
    ('Pan Up', 'panUp'),
    ('Rotate', [
        ('Rotate Left', 'rotLeft'),
        ('Rotate Right', 'rotRight'),
        ('Rotate Down', 'rotDown'),
        ('Rotate Up', 'rotUp'),
        ('Rotate ClockWise', 'twistRight'),
        ('Rotate CCW', 'twistLeft'),
        ]),
    # TODO: Translate is currently incorrect. Do we need it?
    # ('Translate', [
    #     ('Translate Left', 'transLeft'),
    #     ('Translate Right', 'transRight'),
    #     ('Translate Down', 'transDown'),
    #     ('Translate Up', 'transUp'),
    #     ]),
    ('Lock', 'lockCamera'),
    ('Lock View', 'lockView'),
    ('Unlock', 'unlockCamera'),
    ('---', None),
    ('Report', 'reportCamera'),
    ('Settings', 'showCameraTool'),
    ('Save', 'saveCamera'),
    ('Load', 'loadCamera'),
    ], {'func':cameraAction})


# End
