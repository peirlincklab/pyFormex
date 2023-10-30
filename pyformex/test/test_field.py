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

"""Unit tests for the pyformex.varray module

These unit test are based on the pytest framework.

"""
import pyformex as pf
import numpy as np
from pyformex.field import Field

from pyformex.formex import Formex
M = Formex('4:0123').replic(2).toMesh()
d = M.coords.distanceFromPlane([0.,0.,0.],[1.,0.,0.])
# >>> print(M.coords)
#     [[ 0.  0.  0.]
#      [ 0.  1.  0.]
#      [ 1.  0.  0.]
#      [ 1.  1.  0.]
#      [ 2.  0.  0.]
#      [ 2.  1.  0.]]
#     >>> print(M.elems)
#     [[0 2 3 1]
#      [2 4 5 3]]
f1 = Field(M,'node',d)
f2 = f1.convert('elemn')
f3 = f2.convert('elemc')

def test_Field_init_node():
    assert str(f1).split('\n')[0] == "Field 'field-0', type 'node', shape (6,), nnodes=6, nelems=2, nplex=4"
    assert (f1.data == np.array([0., 0., 1., 1., 2., 2.])).all()

def test_Field_convert_node_elemn():
    assert str(f2).split('\n')[0] == "Field 'field-1', type 'elemn', shape (2, 4), nnodes=6, nelems=2, nplex=4"
    assert (f2.data == np.array([[0., 1., 1., 0.], [1., 2., 2., 1.]])).all()

def test_Field_convert_elemn_elemc():
    assert str(f3).split('\n')[0] == "Field 'field-2', type 'elemc', shape (2,), nnodes=6, nelems=2, nplex=4"
    assert (f3.data == np.array([0.5, 1.5])).all()


    # >>> d1 = M.coords.distanceFromPlane([0.,0.,0.],[0.,1.,0.])
    # >>> f4 = Field(M,'node',at.column_stack([d,d1]))
    # >>> print(f4)
    # Field 'Field-3', type 'node', shape (6, 2), nnodes=6, nelems=2, nplex=4
    # [[ 0.  0.]
    #  [ 0.  1.]
    #  [ 1.  0.]
    #  [ 1.  1.]
    #  [ 2.  0.]
    #  [ 2.  1.]]
    # >>> f5 = f4.convert('elemn')
    # >>> print(f5)
    # Field 'Field-4', type 'elemn', shape (2, 4, 2), nnodes=6, nelems=2, nplex=4
    # [[[ 0.  0.]
    #   [ 1.  0.]
    #   [ 1.  1.]
    #   [ 0.  1.]]
    # <BLANKLINE>
    #  [[ 1.  0.]
    #   [ 2.  0.]
    #   [ 2.  1.]
    #   [ 1.  1.]]]
    # >>> f6 = f5.convert('elemc')
    # >>> print(f6)
    # Field 'Field-5', type 'elemc', shape (2, 2), nnodes=6, nelems=2, nplex=4
    # [[ 0.5  0.5]
    #  [ 1.5  0.5]]
    # >>> print(f3.convert('elemn'))
    # Field 'Field-6', type 'elemn', shape (2, 4), nnodes=6, nelems=2, nplex=4
    # [[ 0.5  0.5  0.5  0.5]
    #  [ 1.5  1.5  1.5  1.5]]
    # >>> print(f3.convert('node'))
    # Field 'Field-8', type 'node', shape (6, 1), nnodes=6, nelems=2, nplex=4
    # [[ 0.5]
    #  [ 0.5]
    #  [ 1. ]
    #  [ 1. ]
    #  [ 1.5]
    #  [ 1.5]]
    # >>> print(f6.convert('elemn'))
    # Field 'Field-9', type 'elemn', shape (2, 4, 2), nnodes=6, nelems=2, nplex=4
    # [[[ 0.5  0.5]
    #   [ 0.5  0.5]
    #   [ 0.5  0.5]
    #   [ 0.5  0.5]]
    # <BLANKLINE>
    #  [[ 1.5  0.5]
    #   [ 1.5  0.5]
    #   [ 1.5  0.5]
    #   [ 1.5  0.5]]]
    # >>> print(f6.convert('node'))
    # Field 'Field-11', type 'node', shape (6, 2), nnodes=6, nelems=2, nplex=4
    # [[ 0.5  0.5]
    #  [ 0.5  0.5]
    #  [ 1.   0.5]
    #  [ 1.   0.5]
    #  [ 1.5  0.5]
    #  [ 1.5  0.5]]


# End
