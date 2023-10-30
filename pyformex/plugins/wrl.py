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
"""Wrl

"""
import numpy as np

from pyformex.gui.draw import *

_prop_ = 0
_name_ = "_dummy_"


def name(s):
    global _name_
    _name_ = str(s)


def position(*args):
    pass


def IndexedFaceSet(coords, faces=None):
    global _prop_
    _prop_ += 1
    coords = np.asarray(coords).reshape(-1, 3)
    print(coords.shape, _prop_)
    F = Formex(coords, _prop_)
    print(F.prop)
    draw(F)
    export({"%s-%s" % (_name_, 'coords'): F})
    if faces is None:
        return


def IndexedLineSet(coords, lines):
    coords = np.asarray(coords).reshape(-1, 3)
    print(coords.shape)
    F = Formex(coords, _prop_)
    draw(F)
    export({"%s-%s" % (_name_, 'coords'): F})
    lines = np.column_stack([lines[:-1], lines[1:]])
    print(lines.shape)
    G = Formex(coords[lines], _prop_)
    export({_name_: G})
    draw(G)





# End
