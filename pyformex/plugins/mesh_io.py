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

"""
Mesh import and export using meshio

You need to have python3-meshio installed to use this module.
Source available from https://github.com/nschloe/meshio

"""
from pyformex import software
software.Module.require('meshio')
import meshio

import pyformex as pf
from pyformex.path import Path
from pyformex.mesh import Mesh

pyformex_to_meshio_type = {
    'line2': 'line',
    'line3': 'line3',
    'tri3': 'triangle',
    'tri6': 'triangle6',
    'quad4': 'quad',
    'quad8': 'quad8',
    'quad9': 'quad9',
    'tet4': 'tetra',
    'tet10': 'tetra10',
    'tet14': 'tetra14',
    'wedge6': 'wedge',
    'hex8': 'hexahedron',
    'hex20': 'hexahedron20',
    'hex27': 'hexahedron27',
    'pyramid': 'pyramid',
}

def writeMesh(fn, M):
    """Write a mesh to one of many file formats.

    Parameters
    ----------
    fn: :term:`path_like`
        The output file name. The extentension should be any of the
        formats accepted by meshio (https://pypi.org/project/meshio/).
    mesh: Mesh
        The Mesh to be written to the file.

    Examples
    --------
    >>> f = Path('test_filewrite.off')
    >>> M = Mesh(eltype='quad4').convert('tri3-u')
    >>> writeMesh(f, M)
    >>> print(f.read_text())
    OFF
    # Created by meshio
    <BLANKLINE>
    4 2 0
    <BLANKLINE>
    0.0 0.0 0.0
    1.0 0.0 0.0
    1.0 1.0 0.0
    0.0 1.0 0.0
    3  0 1 2
    3  2 3 0
    <BLANKLINE>
    >>> f.remove()
    """
    fn = Path(fn)
    eltype = M.elName()
    cell_type = pyformex_to_meshio_type.get(eltype, None)
    if cell_type is None:
        raise ValueError(
            f"Can not write Mesh with eltype {eltype} to file {fn}")
    pf.verbose(1, f"Write Mesh to file {fn}")
    points = M.coords
    cells = { cell_type: M.elems }
    meshio.write_points_cells(fn, points, cells)
    pf.verbose(2, f"File size: {fn.size} bytes")


# End
