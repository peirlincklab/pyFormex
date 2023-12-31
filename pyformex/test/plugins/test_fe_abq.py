#
##
##  This file is part of pyFormex 1.0.2  (Thu Jun 18 15:35:31 CEST 2015)
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: http://pyformex.org
##  Project page:  http://savannah.nongnu.org/projects/pyformex/
##  Copyright 2004-2015 (C) Benedict Verhegghe (benedict.verhegghe@feops.com)
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

"""Unittests for the pyformex.plugins.fe_abq module

These unittest are based on the pytest framework.

"""
import pyformex as pf
import numpy as np
from pyformex.plugins.fe_abq import *
from pyformex.mydict import CDict



def test_abqInputNames():
    assert abqInputNames('/aa/bb/job1') == ('job1', '/aa/bb/job1.inp')
    assert abqInputNames('/aa/bb/job1.inp') == ('job1','/aa/bb/job1.inp')
    #assert abqInputNames('/aa/bb/job1.in') == ('job1.in','/aa/bb/job1.in.inp')

def test_nsetName():
    assert nsetName(CDict()) == 'Nall'
    assert nsetName(CDict({'name':'myname'})) == 'myname'

def test_esetName():
    assert esetName(CDict()) == 'Eall'
    assert esetName(CDict({'name':'myname'})) == 'myname'


# End
