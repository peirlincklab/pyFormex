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
"""Create tetraeder mesh inside .stl or .off surface and export in Abaqus format.

Usage::

   pyformex --nogui plugins.surface_abq SURFACE_FILES

For every INPUT.stl or INPUT.off file, generates INPUT-surface.inp
and INPUT-volume.inp with the surface and volume modules in Abaqus(R)
input format.
"""

import pyformex as pf
from pyformex import Path
from pyformex.mesh import Mesh
from pyformex.plugins import fe_abq, tetgen


def surface_to_abaqus(fn):
    fn = Path(fn)
    print("Converting %s to Abaqus .INP format" % fn)
    tetgen.runTetgen(fn)
    coords, nrs, attr, bmark = tetgen.readNodeFile(fn.with_suffix('.1.node'))
    #print(coords)
    elems, nrs, attr = tetgen.readEleFile(fn.with_suffix('.1.ele'))
    #print(elems)
    nodes2, faces = tetgen.readSmeshFile(fn.with_suffix('.1.smesh'))
    #print(faces)
    print("Exporting surface model")
    header=f"Abaqus model generated by tetgen from surface in STL file {fn}"
    smesh = Mesh(coords, faces[3], eltype='tri3')
    fe_abq.exportMesh(
        fn.with_suffix('-surface.inp'), smesh, eltype='S3', header=header)
    print("Exporting volume model")
    vmesh = Mesh(coords, elems)
    fe_abq.exportMesh(
        fn.with_suffix('-volume.inp'), vmesh, eltype='C3D4', header=header)


def run():
    while pf.options.args:
        fn = Path(pf.options.args.pop(0))
        if fn.suffix in ['.stl', '.off'] and fn.exists():
            print("Processing %s" % fn)
            surface_to_abaqus(fn)
        else:
            print("Ignore argument %s" % fn)


# Processing starts here

if __name__ == '__script__':
    run()

# End
