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
"""Colored

This example tests all combinations of rendermode and color modes,
on a triangle and a quad.
"""
_level = 'beginner'
_topics = ['surface']
_techniques = ['color']

from pyformex.gui.draw import *
from pyformex.opengl.actors import Actor


def run():
    reset()
    smooth()
    lights(False)

    Rendermode = ['wireframe', 'flat', 'smooth']
    Lights = [False, True]
    Shapes = ['3:012', '4:0123', ]

    color0 = None  # no color: current fgcolor
    color1 = 'red'   # single color
    color2 = ['red', 'green', 'blue']  # 3 colors: will be repeated

    delay(0)
    i=0
    for shape in Shapes:
        F = Formex(shape).replicm((4, 2))
        color3 = np.resize(color2, F.shape[:2])  # full color
        for c in [color0, color1, color2, color3]:
            for mode in Rendermode:
                clear()
                renderMode(mode)
                #### draw(F,color=c) does not work for some modes!!
                FA = Actor(F, color=c)
                drawActor(FA)
                #### TODO: test if this is still the case
                zoomAll()
                for light in Lights:
                    lights(light)
                    print("%s: color %s, mode %s, lights %s" % (i, str(c), mode, light))
                    i += 1
                    pause()


if __name__ == '__draw__':
    run()
# End
