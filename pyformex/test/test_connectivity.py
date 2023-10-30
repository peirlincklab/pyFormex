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

"""Unit tests for the pyformex.connectivity module

These unit test are based on the pytest framework.

"""
from . import *
from pyformex.connectivity import *


def test_chained():
    assert leq(Connectivity([[0,1],[1,2],[0,4],[4,2]]).chained(),
               [Connectivity([[0, 1],
                              [1, 2],
                              [2, 4],
                              [4, 0]])])

    assert leq(Connectivity([[0,1],[1,2],[0,4]]).chained(),
               [Connectivity([[4, 0],
                              [0, 1],
                              [1, 2]])])

    assert leq(Connectivity([[0,1],[0,2],[0,3],[4,5]]).chained(),
               [Connectivity([[1, 0],
                              [0, 2]]),
                Connectivity([[4, 5]]),
                Connectivity([[0, 3]])])

    assert leq(Connectivity([[0,1],[0,2],[0,3],[5,4]]).chained(
        disconnect='branch'),
               [Connectivity([[5, 4]]),
                Connectivity([[0, 3]]),
                Connectivity([[0, 2]]),
                Connectivity([[0, 1]])])

    assert leq(Connectivity([[0,1,2],[2,0,3],[0,3,1],[4,5,2]]).chained(),
               [Connectivity([[1, 3, 0],
                              [0, 1, 2],
                              [2, 0, 3]]),
                Connectivity([[4, 5, 2]])])

    assert leq(Connectivity([[0,1,2],[2,0,3],[0,3,1],[4,5,2]],).chained(
        disconnect=[0]),
               [Connectivity([[0, 1, 2],
                              [2, 0, 3]]),
                Connectivity([[4, 5, 2]]),
                Connectivity([[0, 3, 1]])])

# End
