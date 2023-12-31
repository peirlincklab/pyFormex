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
"""NonManifold

This example illustrates the detection of non-manifold nodes and edges in a
Mesh.
"""


_level = 'normal'
_topics = ['mesh']
_techniques = ['']

from pyformex.gui.draw import *
from pyformex import simple


def hex_mesh():
    nx, ny, nz = 3, 2, 2
    F = simple.cuboid().replicm((nx, ny, nz))
    F += F.trl([nx, ny, 0])
    F += F.trl([2*nx, 2*ny, nz])
    return F.toMesh()

def quad_mesh():
    nx, ny = 3, 2
    F = Formex('4:0123').replicm((nx, ny))
    F += F.trl([nx, ny, 0.])
    return F.toMesh()

def tri_mesh():
    return quad_mesh().convert('tri3')

def hex_mesh_orig(nx=10, ny=10, nz=8):
    F = simple.cuboid().replicm((nx, ny, nz))
    F += F.trl([nx, ny, nz])
    return F.toMesh()

def hex_mesh_huge():
    return hex_mesh_orig(20, 20, 8)

def quad_mesh_orig():
    F = hex_mesh_orig()
    return Mesh(F.coords, F.getFreeEntities()).compact().trl(1, 3*y)

def quad_mesh_plus():
    # If the point is already a part of the border, with quads
    F = Formex([[[0., 0., 0.], [x, 0., 0.], [x, y, 0.], [0., y, 0.]]])
    F += F.trl([x, y, 0.])
    return Mesh(F)

def tri_mesh_plus():
    # If the point is already a part of the border, with triangles
    F = Formex([[[0., 0.], [-1., -0.1], [-0.1, -1.]], [[0., 0.], [1., 0.1], [0.1, 1.]], [[0., 0.], [-1., 0.1], [-0.1, 1.]], [[0., 0.], [1., -0.1], [0.1, -1.]]])
    return Mesh(F)

def sphere_mesh():
    F =simple.sphere(6)
    F += F.trl([2., 0., 0.])
    return Mesh(F).scale(x/2.).trl(1, -y)


def showNonMan(M):
    p = M.partitionByConnection(1)
    M.setProp(p)
    draw(M)
    if M.nelems()<100 and M.nnodes() < 100:
        drawNumbers(M.coords)
        drawNumbers(M, color=red)

    nm = M.nonManifoldNodes()
    print(nm)
    if len(nm) > 0:
        draw(M.coords[nm], marksize=10, color=red)

    nm = M.nonManifoldEdgeNodes()
    print(nm)
    if len(nm) > 0:
        draw(M.coords[nm], marksize=10, color=blue)

    nm = M.nonManifoldEdges()
    print(nm)
    if len(nm) > 0:
        ed = M.edges[nm]
        print(ed)
        ME = Mesh(M.coords, ed, eltype='line2')
        draw(ME, color=cyan, linewidth=5)

def run():
    examples = [
        hex_mesh,
        quad_mesh,
        tri_mesh,
        hex_mesh_orig,
        quad_mesh_orig,
        quad_mesh_plus,
        tri_mesh_plus,
        sphere_mesh,
        hex_mesh_huge,
        ]

    examplenames = [f.__name__ for f in examples]

    clear()

    res = askItems([
        _I('example', choices=examplenames),
        ])

    if res:
        ex = res['example']
        f = globals()[ex]
        showNonMan(f())
        zoomAll()


if __name__ == '__draw__':
    reset()
    clear()

    run()

# End
