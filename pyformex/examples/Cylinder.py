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

"""Cylinder

This example illustrates the use of simple.sector() and simple.cylinder()
to create a parametric cylindrical surface.

"""
_level = 'beginner'
_topics = ['geometry', 'surface', 'cylinder']
_techniques = ['import']

from pyformex.gui.draw import *
from pyformex import simple

def run():
    n=12
    h=5.
    A = simple.sector(1., 360., 1, n, diag='u')
    B = simple.cylinder(2., h, n, 4, diag='u').reverse()
    C = A.reverse()+B+A.trl(2, h)
    S = TriSurface(C)
    export({'surface': S})

    clear()
    smoothwire()
    view('iso')
    draw(S, color=red, bkcolor=black)

if __name__ == '__draw__':
    run()
# End
