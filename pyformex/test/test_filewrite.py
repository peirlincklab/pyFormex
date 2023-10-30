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

"""Unit tests for the pyformex.fileread/write/ module

These unit test are based on the pytest framework.

"""
import os
import pyformex as pf
import numpy as np

from pyformex.fileread import *
from pyformex.filewrite import *
from pyformex.pzffile import *
from pyformex.mesh import Mesh

M = Mesh(eltype='quad4').convert('tri3-u')

pf.verbose(1,"\n===> Writing uncompressed files")
pf.verbose(1,f"\n===> curdir is {os.getcwd()}")

writeOFF('test/filewrite_mesh.off', M)
writeOFF('test/filewrite_coords_elems.off', M.coords, M.elems)
writeOFF('test/filewrite_coords_elemlist.off', M.coords, [M.elems])
writeOBJ('test/filewrite_mesh.obj', M)
writeOBJ('test/filewrite_coords_elems.obj', M.coords, M.elems)
writeOBJ('test/filewrite_coords_elemlist.obj', M.coords, [M.elems])
writePLY('test/filewrite_mesh.ply', M)
writePLY('test/filewrite_coords_elems.ply', M.coords, M.elems)
writePLY('test/filewrite_coords_elemlist.ply', M.coords, [M.elems])
writePLY('test/filewrite_binary.ply', M, binary=True)
writeGTS('test/filewrite.gts', M.toSurface())
writeSTL('test/filewrite.stl', M.toFormex())
writeSTL('test/filewrite_binary.stl', M.toFormex(), binary=True)
writePGF('test/filewrite.pgf', [M])
writePZF('test/filewrite.pzf', mesh=M)

pf.verbose(1,"\n===> Writing compressed files")

writeOFF('test/filewrite.off.gz', M)
writeOBJ('test/filewrite.obj.gz', M)
writePLY('test/filewrite.ply.gz', M)
writeGTS('test/filewrite.gts.gz', M.toSurface())
writeSTL('test/filewrite.stl.gz', M.toFormex())
writeSTL('test/filewrite_binary.stl.gz', M.toFormex(), binary=True)
writePGF('test/filewrite.pgf.gz', [M])
# !! PZF is a zip, no further compressing needed

pf.verbose(1,"\n===> Reading back uncompressed files")

readOFF('test/filewrite_mesh.off')
readOFF('test/filewrite_coords_elems.off')
readOFF('test/filewrite_coords_elemlist.off')
readOBJ('test/filewrite_mesh.obj')
readOBJ('test/filewrite_coords_elems.obj')
readOBJ('test/filewrite_coords_elemlist.obj')
readPLY('test/filewrite_mesh.ply')
readPLY('test/filewrite_coords_elems.ply')
readPLY('test/filewrite_coords_elemlist.ply')
readPLY('test/filewrite_binary.ply')
readGTS('test/filewrite.gts')
readSTL('test/filewrite.stl')
readSTL('test/filewrite_binary.stl')
readPGF('test/filewrite.pgf')
readPZF('test/filewrite.pzf')

pf.verbose(1,"\n===> Reading back compressed files")

readOFF('test/filewrite.off.gz')
readOBJ('test/filewrite.obj.gz')
readPLY('test/filewrite.ply.gz')
readGTS('test/filewrite.gts.gz')
readSTL('test/filewrite.stl.gz')
readSTL('test/filewrite_binary.stl.gz')
readPGF('test/filewrite.pgf.gz')
# !! PZF is a zip, no further compressing needed

# End
