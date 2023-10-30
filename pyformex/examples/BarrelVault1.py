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
"""Barrel Vault Shell

"""
_level = 'beginner'
_topics = ['frame']
_techniques = ['dialog']

from pyformex.gui.draw import *

def run():
    reset()
    smoothwire()

    res = askItems([
        _I('m', 12, min=1, text='number of modules in axial direction'),
        _I('n', 8, min=1, text='number of modules in tangential direction'),
        _I('r', 10., text='barrel radius'),
        _I('a', 180., text='barrel opening angle'),
        _I('l', 30., text='barrel length'),
        _I('eltype', 'quad8', text='element type', itemtype='radio',
           choices=['tri3', 'quad4', 'quad8', 'quad9']),
        ])
    print(res)
    if not res:
        return

    globals().update(res)

    # Grid
    g = Formex('4:0123').replicm((m, n)).toMesh().convert(eltype)

    # Create barrel
    barrel = g.rotate(90, 1).translate(0, r).scale([1., a/n, l/m]).cylindrical()

    draw(barrel, color=red, bkcolor=blue)

    export({'Barrel': barrel})

if __name__ == '__draw__':
    run()
# End
