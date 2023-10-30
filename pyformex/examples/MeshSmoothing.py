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

"""MeshSmoothing

This example illustrates the use of the mesh smoothing algorithm.

Three versions of a mesh are shown: the original regular mesh (in black),
the mesh after some noise has been added (in red), the noised mesh after
smoothing (in blue).

The user can choose the element type (quadrilateral, triangular, hexahedral
or tetrahedral), the number of elements in the regular grid, the amount of
noise to be added, and the number of smoothing iterations
"""
_name = 'MeshSmoothing'
_level = 'normal'
_topics = ['geometry', 'mesh']
_techniques = ['dialog', 'smooth', 'noise', 'convert', 'extrude']

from pyformex.gui.draw import *

def createMesh(eltype, n):
    """Create a mesh of the given type with n cells in each direction.

    eltype should be one of 'quad4','tri3','hex8','tet4'.
    """
    if eltype == 'tet4':   # Tet conversions produces many elements, reduce n
        n //= 2
    M = Formex('4:0123').repm([n, n]).toMesh()
    if eltype == 'tri3':
        M = M.convert('tri3')
    elif eltype in ['hex8', 'tet4']:
        M = M.extrude(n, dir=2).convert(eltype)
    return M


def noiseSmooth(M, noise, **kargs):
    """Draw 3 versions of a mesh: original, with noise, smoothed noise

    M is any mesh. A version with added noise is created. Then that version
    is smoothed. The three versions are displayed.
    """
    draw(M)
    M1 = M.addNoise(noise)
    # Remove the noise on the first half of the nodes
    nfix = M.ncoords()//2
    M1.coords[:nfix] = M.coords[:nfix]
    M1 = M1.trl(0, M.dsize()).setProp(1)
    draw(M1)
    M2 = M1.smooth(**kargs).trl(0, M.dsize()).setProp(3)
    draw([M, M1, M2])


def run():
    clear()
    res = askItems(caption=_name, store=_name+'data', items=[
        _I('eltype', text='Element type', itemtype='radio', choices=['quad4', 'tri3', 'hex8', 'tet4']),
        _I('n', 6, text='Grid size', itemtype='slider', min=2, max=24,
           tooltip='Number of elements in each direction'),
        _I('noise', 0.05, text='Noise', itemtype='fslider', min=0., max=1.,
           scale=0.01, tooltip='Amount of noise added to the coordinates'),
        _I('niter', 5, text='Smoothing iterations', itemtype='slider',
           min=1, max=20),
        _I('border', text='Border handling', choices=['sep', 'fix', 'incl']),
        _I('weight', text='Weight', choices=[
            'uniform', 'inverse', 'distance', 'sqinverse', 'sqdistance']),
    ])
    if res:
        M = createMesh(res.pop('eltype'), res.pop('n'))
        noiseSmooth(M, **res)


if __name__ == '__draw__':
    view('front')
    run()
# End
