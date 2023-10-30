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

"""BeamFreq

This example computes the first natural vibration modes of an elastic beam.
It demonstrates the use of some functions and classes in the fe subpackage.

The example BeamFreq_calix provides comparable functionality, but based on
the external program calix.
"""

_level = 'normal'
_topics = ['FEA', 'curve', 'drawing']
_techniques = ['external', 'viewport']

from pyformex.gui.draw import *
from pyformex.fe.eigen import *
from pyformex.fe.beam2d import *


def header(s):
    """Print a header"""
    print('='*10 + s + '='*10)


def eigen(K, M, neig, method='subspace'):
    """Compute first neig eigensolutions of (K,M)

    K: stiffness matrix (n,n)
    M: mass matrix (n,n)
    neig: number of eigenfrequencies to compute
    method: 'subspace', 'lanczos' or 'inverse'
    """
    solver = globals()[method]
    header(' '+method+' ')
    e, x = solver(K, M, neig)
    f = sqrt(e)/2/pi
    print("eigenvectors")
    print(x)
    print("eigenvalues")
    print(e)
    print("frequencies")
    print(f)
    return f, x


def drawBeam(x, u, d=None, color=black):
    """Draw a deflected beam.

    x: [2,3] coordinates of endpoints
    u: [2,3] displacements at endpoints
    d: [2,3] tangents at endpoints
    """
    C = BezierSpline(x+u, tangents=d, degree=3)
    draw(C.approx(ndiv=10), color=color, linewidth=2)
    draw(C.pointsOn(), color=color)


def run():
    clear()

    lt = 5.
    nel = 40
    neig = 4
    maxu = 0.1*lt  # max deflexion

    F = Formex('l:1')
    x = Formex('l:1').scale(lt).toCurve().approx(nel).coords
    u = np.zeros((nel+1, 3))
    d = np.zeros((nel+1, 3))

    # Create the stiffness and mass matrix
    K, M = createBeam(lt, nel, addbc=True)
    # Compute the eigenfrequencies and modes
    f, v = eigen(K, M, neig, method='subspace')

    # Compute the theoretical eigenfrequencies (for comparison)
    fth = cantilever_frequencies(IPE100.rho, IPE100.A, lt, steel.E, IPE100.I)
    print("theoretical frequencies")
    print(fth)

    separate = True

    if separate:
        ncol = int(np.ceil(np.sqrt(neig)))
        layout(neig,ncol)

    for i in range(neig):
        # split deflections and rotations
        vi = asarray(v[:, i].reshape(-1, 2))
        # find maximum deflection ( in absolute value)
        ind = argmax(abs(vi[:, 0]))
        # scale to make maximum = maxu
        scale = maxu / vi[ind, 0]
        #print("scale = %s" % scale)
        vi *= scale
        # store deflections in u
        u[:, 1] = vi[:, 0]
        # compute direction vectors
        d = Coords.concatenate([Coords([1.0, 0.0, 0.0]).rotate(ri) for ri in vi[:, 1]/at.DEG])
        if separate:
            viewport(i)
            clear()
        drawBeam(x, u=0., d=None, color=black)
        drawBeam(x, u, d, color=pf.canvas.settings.colormap[i+1])

# End
