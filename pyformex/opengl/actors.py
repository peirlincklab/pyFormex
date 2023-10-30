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
"""OpenGL Actors.

This module defines all OpenGL Actors that are directly available to the users.

"""
import numpy as np
from numpy import int32, float32
from .gl import GL

import pyformex as pf
from pyformex import utils
from pyformex import colors
from pyformex import geomtools as gt
from pyformex import arraytools as at
from pyformex.formex import Formex
from pyformex.mesh import Mesh
from pyformex.attributes import Attributes
from pyformex.elements import ElementType
from .texture import Texture

if not pf.sphinx and pf.options.gl3:
    from pyformex.opengl3.drawable import Actor
else:
    from .drawable import Actor

# We import the other Actors, so they they all can be imported from actors.
from .textext import *
from .decors import *


#  TODO: this replaces legacy PlaneActor, but could probably be derived from
#  decors.Grid

class PlaneActor(Actor):
    """A plane in a 3D scene.

    The default plane is perpendicular to the x-axis at the origin.
    """
    def __init__(self, n=(1.0, 0.0, 0.0), P=(0.0, 0.0, 0.0), size=(1., 1., 0.),
                 color='white', alpha=0.5, mode='flatwire', linecolor='black',
                 **kargs):
        """A plane perpendicular to the x-axis at the origin."""
        from pyformex.formex import Formex
        F = Formex('4:0123').replicm((2, 2)).centered().scale(size).\
            rotate(at.rotMatrix2([0, 0, 1], n, [0, 1, 0])).trl(P)
        F.attrib(mode=mode, lighting=False, color=color, alpha=alpha,
                 linecolor=linecolor)
        Actor.__init__(self, F, **kargs)



# End
