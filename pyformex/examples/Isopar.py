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
"""Isopar

This example illustrates the power of the isoparametric transformation
(isopar). An isoparametric transformation is a geometrical transformation
defined by an initial regular configuration of some points and some deformed
configuration of the same points. These points do not have to be part of the
structure that is to be transformed. The deformed positions form the parameters
in the transformation.

In the example a 1D, 2D, or 3D regular grid is constructed and then deformed
by a 1D, 2D or 3D isoparametric transformation. The parameters of the
transformations are hardwirded in the script.

First the points defining the isoparametric transformation are shown.
Then, the original and the transformed structure are first shown
superimposed, in black and red respectively. Transparency is set on.
After the pause, the original structure is removed, and transparency is set off.
"""

_level = 'normal'
_topics = ['geometry']
_techniques = ['dialog', 'color', 'isopar', 'undraw']
_name = 'Isopar'
_data = _name+'_data'

from pyformex.gui.draw import *

from pyformex import elements
from pyformex.plugins import isopar

# First and second order elements to be used for geometry, resp. transform
elems1 = [elements.Line2, elements.Quad4, elements.Hex8]
elems2 = [elements.Line3, elements.Quad9, elements.Hex27]


def run():
    clear()
    res = askItems(caption=_name, store=_data, items=[
        _I('geometry', '3D', itemtype='radio', choices=['1D', '2D', '3D']),
        _I('transformation', '3D', itemtype='radio', choices=['1D', '2D', '3D']),
        _I('Show trf points', True),
        ])
    if not res:
        return

    sdim = int(res['geometry'][0])
    tdim = int(res['transformation'][0])

    # create a unit quadratic grid in tdim dimensions
    eltype = elems2[tdim-1]
    x0 = Formex(eltype.vertices)

    # create a copy and move a few points
    x1 = x0.copy()
    if tdim == 1:
        x1[1] = x1[1].rot(-20)
        x1[2] = x1[2].rot(20)
    elif tdim == 2:
        x1[6] = x1[3].rot(-22.5)
        x1[2] = x1[3].rot(-45.)
        x1[5] = x1[3].rot(-67.5)
        x1[8] = x1[2] * 0.6
    else:
        tol = 0.01
        d = x1.distanceFromPoint(x1[0])
        w = np.where((d > 0.5+tol) * (d < 1.0 - tol))[0]
        x1[w] = x1.projectOnSphere(0.5)[w]
        w = np.where(d > 1.+tol)[0]
        x1[w] = x1.projectOnSphere(1.)[w]

    clear()
    if sdim == 1:
        wireframe()
    else:
        smoothwire()

    # Create the structure
    n = 8
    F = elems1[sdim-1].toFormex()
    for i in range(sdim):
        F = F.replic(n, 1., dir=i)

    for i in range(sdim, tdim):
        F = F.trl(i, 0.5)

    transparent()
    print('This is the initial Formex')
    FA=draw(F)
    sz = F.sizes()

    sz[sz==0.] = 1.
    x0 = x0.scale(sz)
    x1 = x1.scale(sz)

    if res['Show trf points']:
        print('This is the set of nodes in natural coordinates')
        draw(x0, color=blue, nolights=True, marksize=5)
        drawNumbers(x0, color=blue)
        pause()
        print('This is the set of nodes in cartesian coordinates')
        draw(x1, color=yellow, nolights=True, marksize=10)
        drawNumbers(x1, color=red)
        pause()

    G = F.isopar(eltype.lname, x1.points(), x0.points())
    G.setProp(1)

    print('This is the transformed Formex')
    draw(G)

    pause()
    undraw(FA)
    transparent(False)

if __name__ == '__draw__':
    run()
# End
