# flake8: noqa
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
"""Default imports in the scripting language.

This module defines which symbols are always imported when
you run a script, and thus constitute the core part
of the pyFormex scripting language.

In an app, you implicitely import these definitions by adding::

  from pyformex.script import *

or, if you also need GUI functionality::

  from pyformex.gui.draw import *

Warning
-------
This module is currently in transient state and subject to future changes.
"""
import numpy as np

import pyformex as pf

from pyformex import arraytools as at
from pyformex import geomtools as gt
from pyformex import utils
from pyformex import software
from pyformex import simple
from pyformex import fileread
from pyformex import filewrite
from pyformex import colors

from numpy import pi, sin, cos, tan, arcsin, arccos, arctan, arctan2, sqrt, abs
from pyformex.coords import *
from pyformex.coordsys import *
from pyformex.curve import PolyLine, BezierSpline
from pyformex.elements import Elems
from pyformex.field import Field
from pyformex.formex import *
from pyformex.geomfile import GeometryFile
from pyformex.globalformat import floatformat
from pyformex.mesh import Mesh
from pyformex.path import Path
from pyformex.polygons import Polygons
from pyformex.project import Project
from pyformex.pzffile import PzfFile
from pyformex.olist import List
from pyformex.varray import Varray
from pyformex.timer import Timer
from pyformex.trisurface import *


def readGeometry(filename, filetype=None, target=None, **kargs):
    """Read geometry from a stored file.

    This is a wrapper function over several other functions specialized
    for some file type. Some file types require the existence of more
    than one file, may need to write intermediate files, or may call
    external programs. Some file types contain a single geometric object,
    others can contain collections of objects. Some formats store other
    than geometric information, like colors, normals or field variables.

    Parameters
    ----------
    filename: :term:`path-like`
        The name of the file to read. If the filetype requires the existence
        of more than one file (e.g. tetgen), only a single one should be
        specified and the others are derived from it. Usually, the filename
        has a suffix that hints at the filetype.
        Most of the pyFormex readers transparently support decompression of
        compressed files. This works if the filename ends on '.gz' or '.bz2'.
    filetype: str, optional
        The file type. If not specified, it is derived from the filename
        suffix. Currently the following file types can be handled:

        pzf: pyFormex Zip File, see :class:`PzfFile`,
        pyf: pyFormex Project File, see :class:`GeometryFile`,
        pgf: pyFormex Geometry File, see :func:`fileread.readPGF`,
        obj: Wavefront .obj file, see :func:`fileread.readOBJ`,
        off: Geomview .off file, see :func:`fileread.readOFF`,
        ply: Polygon File Format, see :func:`fileread.readPLY`,
        neu: Gambit Neutral file, see :func:`fileread.readNEU`,
        stl: stereolithography file, see :func:`fileread.readSTL`,
        gts: libgts file format, see :func:`fileread.readGTS`,
        surface: a generic filetype for any of the following formats
            holding a triangulated surface: stl, gts, off, neu,
            see :func:`TriSurface.read`,
        inp: Abaqus and CalculiX input format, see :func:`fileread.readINP`,
        tetgen: a generic filetype for several tetgen files,
            see :func:`plugins.tetgen.readTetgen`
    target: str, optional
        The target object type. Currently, the only accepted value is
        'surface'. In combination with a file of type 'obj', 'off', 'ply'
        or 'neu', it will return TriSurface objects instead of the more general
        Mesh objects.
    mplex: int, optional
        For 'obj', 'off' and 'ply' types, specifies the maximum accepted
        plexitude of the objects. Larger plexitudes are decomposed into
        smaller ones.

    Returns
    -------
    dict
        A dictionary with named geometry objects read from the file.

    """
    filename = Path(filename)
    res = {}
    compr = None
    if filetype is None:
        filetype, compr = filename.ftype_compr()
    else:
        filetype = filetype.lower()

    print(f"Reading file {filename} of type {filetype.upper()}")

    if filetype == 'pzf':
        res = PzfFile(filename).load()

    elif filetype == 'pyf':
        res = dict(Project(filename, access='r'))

    elif filetype == 'pgf':
        res = fileread.readPGF(filename)

    elif filetype in ['obj', 'off', 'ply'] and target != 'surface':
        reader = getattr(fileread, 'read'+filetype.upper())
        poly = reader(filename)
        name = poly.attrib('name')
        # mplex = kargs.get('mplex',None)
        # if mplex is not None:
        #     poly = poly.reduce(mplex)
        if name is None:
            name = next(utils.autoName(Polygons))
        res = {name: poly}

    elif filetype == 'neu' and target != 'surface':
        mesh = fileread.readNEU(filename)
        res[f"{filename.stem}"] = mesh

    # Beware! this should come after 'obj'... poly types, otherwise
    # non-triangles in the files will be skipped
    elif filetype in utils.fileTypes('surface') or \
         filetype in utils.fileTypes('tetsurf') or \
         filetype in utils.fileTypes('vtk'):
        S = TriSurface.read(filename)
        name = next(utils.autoName(TriSurface))
        res = {name: S}

    elif filetype == 'inp':
        parts = fileread.readINP(filename)
        color_by_part = len(parts) > 1
        j = 0
        for name in parts:
            for i, mesh in enumerate(parts[name].meshes()):
                p = j if color_by_part else i
                print(f"Color {p}")
                res[f"{name}-{i}"] = mesh.setProp(p)
            j += 1

    elif filetype in utils.fileTypes('tetgen'):
        from pyformex.plugins import tetgen
        res = tetgen.readTetgen(filename)

    else:
        raise ValueError(
            f"Can not import files of type {filetype} ({filename})")

    return res


def writeGeometry(filename, obj, ftype=None, compr=False, **kargs):
    """Write geometry items to the specified file.

    This is a wrapper function around the many dedicated file
    exporter functions. It provides a single interface to export
    geometry to one of many file formats:

    - pyFormex native formats: PZF, PYF, PGF
    - widely supported geometry formats: OBJ, OFF, PLY, STL, VTP, VTK
    - GTS, NEU(gambit), SMESH(tetgen), INP(Abaqus)
    - many more formats supported through mesh_io

    Parameters
    ----------
    filename:
    obj:
    ftype: str, optional
    compr: str, optional
    writer: str, optional
        If not specified, internal pyFormex functions are used to do
        the export.
        If specified, an external library is used to do the export.
        Currently the only available value is 'meshio'. You need to
        have the meshio library installed to use it.
        See https://github.com/nschloe/meshio.
    mode: str
        'ascii', 'binary' or 'shortascii'


    Returns the number of objects written.
    """
    print(f"Exporting {list(obj.keys())}")
    nobj = 0
    filename = Path(filename)
    writer = kargs.pop('writer', None)
    if writer == 'meshio':
        from pyformex.plugins.mesh_io import writeMesh
        for name in obj:
            writeMesh(filename, obj[name])
            return 1

    if ftype is None:
        ftype, compr = filename.ftype_compr()

    print(f"Writing file of type {ftype}")

    if ftype == 'pzf':
        PzfFile(filename).save(**obj, **kargs)
        nobj = len(obj)

    elif ftype == 'pyf':
        Project(filename, data=obj).save()
        nobj = len(obj)

    elif ftype == 'pgf':
        mode = kargs.pop('mode', 'ascii')
        sep = '' if mode=='binary' else ' '
        shortlines = mode.startswith('short')
        nobj = filewrite.writePGF(filename, obj, sep=sep, shortlines=shortlines)

    elif ftype in ('obj', 'off', 'ply'):
        for name in obj: # There is only one and it's a Mesh or Polygons
            M = obj[name]
            if not isinstance(M, (Mesh, Polygons)):
                raise ValueError(
                    f"Can only export Mesh or Polygon type to {ftype.upper()}")
            writer = getattr(filewrite, 'write'+ftype.upper())
            writer(filename, M, name=name)
            nobj += 1
            break

    elif ftype in ('neu'):
        for name in obj: # There is only one and it's a Mesh
            M = obj[name]
            filewrite.writeNEU(filename, M)
            nobj += 1
            break

    elif ftype == 'stl':
        if kargs['binary']:
            from pyformex import colors
            ftype = 'stlb'
            color = colors.RGBAcolor(kargs['color'], kargs['alpha'])
            print(f"Also saving color {color}")
        else:
            color = None
        for name in obj:  # There is only one and it's a TriSurface
            S = obj[name]
            S.write(filename, ftype, color=color)
            nobj += 1

    elif ftype in ('gts', 'neu', 'smesh', 'vtp', 'vtk'):
        for name in obj: # There is only one and it's a TriSurface
            S = obj[name]
            S.write(filename, ftype)
            nobj += 1

    elif ftype == 'inp':
        from pyformex.plugins import fe_abq
        for name in obj: # There is only one and it's a Mesh
            M = obj[name]
            fe_abq.exportMesh(filename, M, eltype=kargs['eltype'])
            nobj += 1

    else:
        pf.error("Don't know how to export in '{ftype}' format")

    return nobj

#print("After loading core")
#print(sorted(globals().keys()))
#print(pyformex.utils)

# End
