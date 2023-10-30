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

"""Write geometry to file in a whole number of formats.

This module defines both the basic routines to write geometrical data
to a file and the specialized exporters to write files in a number of
well known standardized formats.

Most of the exporters support transparent compression of the output files
by just specifying a file name that ends in '.gz' or '.bz2'.

The basic routines are very versatile as well as optimized and allow to
easily create new exporters for other formats.
"""
import sys
import datetime

import numpy as np

import pyformex as pf
from pyformex import utils
from pyformex import arraytools as at
from pyformex.path import Path
from pyformex.varray import Varray
from pyformex.coords import Coords
from pyformex.formex import Formex
from pyformex.plugins.neu_exp import writeNEU
from pyformex.pzffile import savePZF as writePZF


__all__ = ['writePZF', 'writePGF', 'writeOFF', 'writeOBJ', 'writePLY',
           'writeGTS', 'writeSTL', 'writeNEU', 'writeData', 'writeIData']


def writePGF(filename, objects, sep=' ', mode='w', shortlines=False,
             **kargs):
    """Save geometric objects to a pyFormex Geometry File.

    A pyFormex Geometry File can store multiple geometrical objects in a
    native format that can be efficiently read back into pyFormex.
    The format is portable over different pyFormex versions and
    even to other software.

    Parameters
    ----------
    filename: :term:`path_like`
        The name of the file to be written. Usually this has a suffix '.pgf'.
        If a '.gz' or '.bz2' is added, the file will be compressed with gzip
        or bzip2, respectively.
    objects: object | list | dict
        One or more objects to be saved on the file.
        If it is a dictionary, the keys are saved in the file as the names
        of the objects.
        Objects that can not be exported to a pyFormex Geometry File are
        silently ignored.
    mode: 'w' | 'a'
        The mode in which to open the file. The default 'w' will overwrite
        an existing file. Use 'a' to append to an existing file.
    sep: str
        The string used to separate data. If set to an empty string, the
        data will be written in binary format and the resulting file
        will be smaller, but less portable.
    **kargs:
        Extra keyword arguments are passed to
        :meth:`~geomfile.GeometryFile.write`.

    Returns
    -------
    int:
        The number of objects that were written to the file.

    Examples
    --------
    >>> from pyformex.mesh import Mesh
    >>> f = Path('test_filewrite.pgf')
    >>> M = Mesh(eltype='quad4').convert('tri3-u')
    >>> writePGF(f, M)
    1
    >>> print(f.read_text())
    # pyFormex Geometry File (http://pyformex.org) version='2.1'; sep=' '
    # objtype='Mesh'; ncoords=4; nelems=2; nplex=3; props=False; normals=False;\
    color=None; sep=' '; name='test_filewrite-0'; eltype='tri3'
    0.0 0.0 0.0 1.0 0.0 0.0 1.0 1.0 0.0 0.0 1.0 0.0
    0 1 2 2 3 0
    <BLANKLINE>
    >>> f.remove()
    """
    from pyformex import geomfile
    pf.debug(f"WriteGeomFile filename{filename}; sep='{sep}'; "
             f"shortlines={shortlines}; kargs={kargs}", pf.DEBUG.PGF)
    filename = Path(filename)
    pf.verbose(1, f"Write PGF file {filename.absolute()}")
    f = geomfile.GeometryFile(filename, mode, sep=sep, **kargs)
    # TODO: this option could goto into GeometryFile
    if shortlines:
        f.fmt = {'i': '%i ', 'f': '%f '}
    nobj = f.write(objects)
    f.close()
    return nobj


def _check_coords_faces(coords, faces):
    """Check coords, faces arguments for some write... functions"""
    from pyformex.mesh import Mesh
    from pyformex.polygons import Polygons
    if isinstance(coords, (Mesh, Polygons)):
        coords, faces = coords.coords, coords.elems
    if not isinstance(coords, Coords):
        coords = Coords(coords)
    ncoords = coords.shape[0]
    if isinstance(faces, Varray):
        nfaces = faces.nrows
    elif isinstance(faces, np.ndarray) and faces.ndim==2:
        nfaces = faces.shape[0]
        faces = [faces]
    elif isinstance(faces, list):
        faces = [np.asarray(f, dtype=at.Int) for f in faces]
        nfaces = sum(f.shape[0] for f in faces)
    else:
        raise ValueError("Invalid faces")
    return coords, faces, ncoords, nfaces


def writeOFF(fn, coords, faces=None, *, name=None,
             comment=None, signature=True):
    """Write polygons to a file in OFF format.

    Parameters
    ----------
    fn: :term:`path_like`
        The output file name, commonly having a suffix '.off'.
        If the suffix ends on '.gz' or '.bz2', the file will transparently
        be compressed during writing.
    coords: :term:`coords_like` | :class:`~mesh.Mesh` | :class:`~polygons.Polygons`
        A float array (ncoords, 3) with the coordinates of all vertices.
        As a convenience, a Mesh or Polygons object may be provided instead.
        In that case the coords will be taken from that object and the faces
        argument will be set to the object's elems attribute.
    faces: :class:`~varray.Varray` | ndarray | list of ndarray
        Specifies the connectivity of the faces to be stored in the OFF file.
        It is either a Varray like in a :class:`Polygons` object, or a 2D
        int array or a list of arrays, holding one or more connectivity
        tables of plexitude >= 3.
        This argument is required if coords is a :term:`coords_like` and is
        ignored if coords is a Mesh or Polygons.
    name: str, optional
        The name of the object to be stored in the file.
    comment: str, optional
        An extra comment to be stored in the file.
    signature: bool
        If True (default), a comment is inserted with the creator name and
        version and the creation date. This can be switch off for cases
        where the file has to be further processed by software that does not
        understand comments in .off files.

    Notes
    -----
    See https://en.wikipedia.org/wiki/OFF_(file_format).

    Examples
    --------
    >>> from pyformex.polygons import Polygons
    >>> from pyformex.fileread import readOFF
    >>> f = Path('test_filewrite.off')
    >>> P = Polygons(Coords('011233'), [[0,1,4,5], [4,1,2], [2,3,4]])
    >>> writeOFF(f, P.coords, P.elems, name='test', comment='This is a test')
    >>> print(f.read_text())
    OFF
    # OFF file written by pyFormex ...
    # This is a test
    # name=test
    6 3 0
    0.0 0.0 0.0
    1.0 0.0 0.0
    2.0 0.0 0.0
    2.0 1.0 0.0
    1.0 1.0 0.0
    0.0 1.0 0.0
    4 0 1 4 5
    3 4 1 2
    3 2 3 4
    >>> P = readOFF(f)
    >>> print(P)
    Polygons: nnodes: 6, nelems: 3, nplex: min 3, max 4, eltype: polygon
      BBox: [0. 0. 0.], [2. 1. 0.]
      Size: [2. 1. 0.]
    >>> print(P.coords)
    [[0. 0. 0.]
     [1. 0. 0.]
     [2. 0. 0.]
     [2. 1. 0.]
     [1. 1. 0.]
     [0. 1. 0.]]
    >>> print(P.elems)
    Varray (nrows=3, width=3..4)
      [0 1 4 5]
      [4 1 2]
      [2 3 4]
    >>> f.remove()
    """
    coords, faces, ncoords, nfaces = _check_coords_faces(coords, faces)
    nedges = 0  # This is currently not used
    fn = Path(fn)
    pf.verbose(1, f"Write OFF file {fn}")
    now = datetime.datetime.now().isoformat()
    with utils.File(fn, 'wb') as fil:
        writeText(fil, "OFF\n")
        if signature:
            writeText(fil, f"# OFF file written by {pf.Version()} on {now}\n")
        if comment is not None:
            writeText(fil, f"# {comment}\n")
        if name is not None:
            writeText(fil, f"# name={name}\n")
        writeText(fil, f"{ncoords} {nfaces} {nedges}\n")
        pf.verbose(2, f"Writing {ncoords} vertices")
        writeData(fil, coords, fmt='%s', sep=' ')
        pf.verbose(2, f"Writing {nfaces} faces")
        if isinstance(faces, Varray):
            for row in faces:
                elemdata = np.concatenate([[len(row)], row]).astype(at.Int)
                writeData(fil, elemdata, fmt='%i', sep=' ')
        else:
            for fplex in faces:
                elemdata = np.pad(fplex, ((0, 0), (1, 0)),
                                  constant_values=fplex.shape[1])
                writeData(fil, elemdata, fmt='%i', sep=' ')
    pf.verbose(2, f"File size: {fn.size} bytes")


def writeOBJ(fn, coords, faces=None, *, edges=None, points=None,
             name=None, comment=None):
    """Write polygons to a file in OBJ format.

    Parameters
    ----------
    fn: :term:`path_like`
        The output file name, commonly having a suffix '.obj'.
        If the suffix ends on '.gz' or '.bz2', the file will transparently
        be compressed during writing.
    coords: :term:`coords_like` | :class:`~mesh.Mesh` | :class:`~polygons.Polygons`
        A float array (ncoords, 3) with the coordinates of all vertices.
        As a convenience, a Mesh or Polygons object may be provided instead.
        In that case the coords will be taken from that object and the faces
        argument will be set to the object's elems attribute.
    faces: :class:`~varray.Varray` | ndarray | list of ndarray
        Specifies the connectivity of the faces to be stored in the OFF file.
        It is either a Varray like in a :class:`Polygons` object, or a 2D
        int array or a list of arrays, holding one or more connectivity
        tables of plexitude >= 3.
        This argument is required if coords is a :term:`coords_like` and is
        ignored if coords is a Mesh or Polygons.
    edges: :class:`~connectivity.Connectivity` like, optional
        A connectivity table with plexitude 2, specifying the edges to be
        stored in the OBJ file.
    points: :class:`~connectivity.Connectivity` like, optional
        A connectivity table with plexitude 1 specifying the points to be
        stored in the OBJ file.
    name: str, optional
        The name of the object to be stored in the file.
    comment: str, optional
        An extra comment to be stored in the file.

    Notes
    -----
    See https://en.wikipedia.org/wiki/OBJ_(file_format).

    Examples
    --------
    >>> from pyformex.polygons import Polygons
    >>> from pyformex.fileread import readOBJ
    >>> f = Path('test_filewrite.obj')
    >>> P = Polygons(Coords('011233'), [[0,1,4,5], [4,1,2], [2,3,4]])
    >>> writeOBJ(f, P.coords, P.elems, name='test', comment='This is a test')
    >>> print(f.read_text())
    # OBJ file written by pyFormex ...
    # This is a test
    o test
    v 0.0 0.0 0.0
    v 1.0 0.0 0.0
    v 2.0 0.0 0.0
    v 2.0 1.0 0.0
    v 1.0 1.0 0.0
    v 0.0 1.0 0.0
    f 1 2 5 6
    f 5 2 3
    f 3 4 5
    # End
    >>> P = readOBJ(f)
    >>> print(P)
    Polygons: nnodes: 6, nelems: 3, nplex: min 3, max 4, eltype: polygon
      BBox: [0. 0. 0.], [2. 1. 0.]
      Size: [2. 1. 0.]
    >>> print(P.coords)
    [[0. 0. 0.]
     [1. 0. 0.]
     [2. 0. 0.]
     [2. 1. 0.]
     [1. 1. 0.]
     [0. 1. 0.]]
    >>> print(P.elems)
    Varray (nrows=3, width=3..4)
      [0 1 4 5]
      [4 1 2]
      [2 3 4]
    >>> f.remove()
    """
    _format_ = {}

    def _format(nplex):
        """Return the output format for a give plexitude"""
        try:
            fmt = _format_[nplex]
        except Exception:
            # element code: p(oint), l(ine) or f(ace)
            code = {1: 'p', 2: 'l'}.get(nplex, 'f')
            fmt = _format_[nplex] = code + (' %s'*nplex) + '\n'
        return fmt

    coords, faces, ncoords, nfaces = _check_coords_faces(coords, faces)
    fn = Path(fn)
    pf.verbose(1, f"Write OBJ file {fn.absolute()}")
    now = datetime.datetime.now().isoformat()
    with utils.File(fn, 'w') as fil:
        fil.write(f"# OBJ file written by {pf.Version()} on {now}"+'\n')
        if comment:
            fil.write(f"# {comment}\n")
        if name is not None:
            fil.write(f"o {name}\n")
        pf.verbose(2, f"Writing {ncoords} vertices")
        for v in coords:
            fil.write("v %s %s %s\n" % tuple(v))
        pf.verbose(2, f"Writing {nfaces} faces")
        if isinstance(faces, Varray):
            faces = [faces]
        for fplex in faces:
            for e in fplex:
                fil.write(_format(len(e)) % tuple(e+1))  # OBJ format starts at 1
        fil.write('# End\n')
    pf.verbose(2, f"File size: {fn.size} bytes")


def writePLY(fn, coords, faces=None, *, edges=None,
             vcolor=None, fcolor=None, ecolor=None,
             name=None, comment=None, binary=False):
    """Write polygons to a file in PLY format.

    Parameters
    ----------
    fn: :term:`path_like`
        The output file name, commonly having a suffix '.ply'.
        If the suffix ends on '.gz' or '.bz2', the file will transparently
        be compressed during writing.
    coords: :term:`coords_like` | :class:`~mesh.Mesh` | :class:`~polygons.Polygons`
        A float array (ncoords, 3) with the coordinates of all vertices.
        As a convenience, a Mesh or Polygons object may be provided instead.
        In that case the coords will be taken from that object and the faces
        argument will be set to the object's elems attribute.
    faces: :class:`~varray.Varray` | ndarray | list of ndarray
        Specifies the connectivity of the faces to be stored in the OFF file.
        It is either a Varray like in a :class:`Polygons` object, or a 2D
        int array or a list of arrays, holding one or more connectivity
        tables of plexitude >= 3.
        This argument is required if coords is a :term:`coords_like` and is
        ignored if coords is a Mesh or Polygons.
    edges: :class:`~connectivity.Connectivity` like, optional
        A connectivity table with plexitude 2, specifying the edges to be
        stored in the PLY file.
    name: str, optional
        The name of the object to be stored in the file.
    comment: str, optional
        An extra comment to be stored in the file.
    binary: bool
        If True, a binary file is written. The default is ascii.

    Notes
    -----
    For details on the PLY format,
    see `<https://en.wikipedia.org/wiki/PLY_(file_format)>`_.

    Examples
    --------
    >>> from pyformex.polygons import Polygons
    >>> from pyformex.fileread import readPLY
    >>> f = Path('test_filewrite.ply')
    >>> P = Polygons(Coords('011233'), [[0,1,4,5], [4,1,2], [2,3,4]])
    >>> writePLY(f, P.coords, P.elems, name='test', comment='This is a test')
    >>> print(f.read_text())
    ply
    format ascii 1.0
    comment PLY file written by pyFormex ...
    comment This is a test
    comment name=test
    element vertex 6
    property float x
    property float y
    property float z
    element face 3
    property list int int vertex_indices
    end_header
    0.0 0.0 0.0
    1.0 0.0 0.0
    2.0 0.0 0.0
    2.0 1.0 0.0
    1.0 1.0 0.0
    0.0 1.0 0.0
    4 0 1 4 5
    3 4 1 2
    3 2 3 4
    >>> P = readPLY(f)
    >>> print(P)
    Polygons: nnodes: 6, nelems: 3, nplex: min 3, max 4, eltype: polygon
      BBox: [0. 0. 0.], [2. 1. 0.]
      Size: [2. 1. 0.]
    >>> print(P.coords)
    [[0. 0. 0.]
     [1. 0. 0.]
     [2. 0. 0.]
     [2. 1. 0.]
     [1. 1. 0.]
     [0. 1. 0.]]
    >>> print(P.elems)
    Varray (nrows=3, width=3..4)
      [0 1 4 5]
      [4 1 2]
      [2 3 4]
    >>> writePLY(f, P, comment='This is a test', binary=True)
    >>> P = readPLY(f)
    >>> print(P)
    Polygons: nnodes: 6, nelems: 3, nplex: min 3, max 4, eltype: polygon
      BBox: [0. 0. 0.], [2. 1. 0.]
      Size: [2. 1. 0.]
    >>> f.remove()
    """

    def int_color(color):
        return (255*vcolor).astype(at.Int).clip(0, 255)

    coords, faces, ncoords, nfaces = _check_coords_faces(coords, faces)
    fn = Path(fn)
    pf.verbose(1, f"Write PLY file {fn.absolute()}")
    now = datetime.datetime.now().isoformat()
    if binary:
        fmt = f"binary_{sys.byteorder}_endian 1.0"
    else:
        fmt = "ascii 1.0"
    header = ["ply",
              f"format {fmt}",
              f"comment PLY file written by {pf.Version()} on {now}"]
    if comment is not None:
        header.append(f"comment {comment}")
    if name is not None:
        header.append(f"comment name={name}")
    cprop_type = 'uchar'
    color_type = [f"property {cprop_type} {color}"
                  for color in ['red', 'green', 'blue']]
    # vertices
    header.extend([f"element vertex {ncoords}",
                   "property float x",
                   "property float y",
                   "property float z"])
    if vcolor:
        header.extend(color_type)
        vcolor = int_color(vcolor)
    # faces
    header.extend([f"element face {nfaces}",
                   "property list int int vertex_indices"])
    if fcolor:
        header.extend(color_type)
        fcolor = int_color(fcolor)
    # edges
    if edges is not None:
        nedges = edges.shape[0]
        header.append(f"element edge {nedges}")
        header.extend([f"property int vertex{i}" for i in (1, 2)])
        if ecolor:
            header.append(color_type)
            ecolor = int_color(ecolor)
    # finalize header
    header.append("end_header\n")
    header = '\n'.join(header)
    with utils.File(fn, 'wb') as fil:
        fil.write(header.encode('utf-8'))
        pf.verbose(2, f"Writing {ncoords} vertices")
        if binary:
            fil.write(coords.tobytes())
        else:
            writeData(fil, coords, fmt='%s', sep=' ')
        pf.verbose(2, f"Writing {nfaces} faces")
        if isinstance(faces, Varray):
            for row in faces:
                elemdata = np.concatenate([[len(row)], row])
                elemdata = elemdata.astype(np.int32)
                if binary:
                    fil.write(elemdata.tobytes())
                else:
                    writeData(fil, elemdata, fmt='%i', sep=' ')
        else:
            for fplex in faces:
                # print(fplex.dtype) !! sometimes it's int64!!
                # which is a disaster for the binary file
                elemdata = np.pad(fplex, ((0, 0), (1, 0)),
                                  constant_values=fplex.shape[1])
                elemdata = elemdata.astype(np.int32)
                if binary:
                    fil.write(elemdata.tobytes())
                else:
                    writeData(fil, elemdata, fmt='%i', sep=' ')
    pf.verbose(2, f"File size: {fn.size} bytes")


# Output of surface file formats

def writeGTS(fn, surf):
    """Write a TriSurface to a file in GTS format.

    Parameters
    ----------
    fn: :term:`path_like`
        The output file name, commonly having a suffix '.gts'.
        If the suffix ends on '.gz' or '.bz2', the file will transparently
        be compressed during writing.
    surf: TriSurface
        The TriSurface to write to the file.

    Examples
    --------
    >>> from pyformex.mesh import Mesh
    >>> f = Path('test_filewrite.gts')
    >>> M = Mesh(eltype='quad4').convert('tri3-u')
    >>> writeGTS(f, M.toSurface())
    >>> print(f.read_text())
    4 5 2
    0.000000 0.000000 0.000000
    1.000000 0.000000 0.000000
    1.000000 1.000000 0.000000
    0.000000 1.000000 0.000000
    1 2
    3 1
    4 1
    2 3
    3 4
    1 4 2
    5 3 2
    #GTS file written by pyFormex ...
    <BLANKLINE>
    >>> f.remove()
    """
    fn = Path(fn)
    from pyformex.trisurface import TriSurface
    if not isinstance(surf, TriSurface):
        raise ValueError("Expected TriSurface as second argument'")
    pf.verbose(1, f"Write GTS file {fn.absolute()}")
    coords = surf.coords
    edges = surf.edges
    faces = surf.elem_edges
    with utils.File(fn, 'wb') as fil:
        writeText(fil, f"{coords.shape[0]} {edges.shape[0]} "
                       f"{faces.shape[0]}\n")
        writeData(fil, coords, fmt='%f', sep=' ')
        writeData(fil, edges+1, fmt='%i', sep=' ')
        writeData(fil, faces+1, fmt='%i', sep=' ')
        writeText(fil, f"#GTS file written by {pf.Version()}\n")
    pf.verbose(2, f"File size: {fn.size} bytes")


def writeSTL(fn, x, n=None, binary=False, color=None):
    """Write a collection of triangles to an STL file.

    Parameters
    ----------
    fn: :term:`path_like`
        The output file name, commonly having a suffix '.stl' or
        '.stla' (for ascii output) or '.stlb' (for binary output).
        If the suffix ends on '.gz' or '.bz2', the file will transparently
        be compressed during writing.
    x: Coords | Formex
        A Coords or Formex with shape (ntriangles,3,3) holding the coordinates of
        the vertices of the triangles to write to the file.
    n: Coords, optional
        A Coords with shape (ntriangles,3) holding the normal vectors to the
        triangles. If not specified, they will be calculated.
    binary: bool
        If True, the output file format  will be a binary STL.
        The default is an ascii STL.
    color: array
        An int of float array with the color to be added to the header of
        a binary STL (in Magics format).
        If float, values are in the range 0..1.
        If int, values are in the range 0..255. Either 3 (RGB) or 4 (RGBA)
        components should be given. If only 3, an alpha value will be added:
        pf.canvas.transparency if float, or 128 in int type was used.
        Float values are converted to int using :func:`colors.RGBAcolors`.
        Note that color can only be used with a binary STL format, and
        is not recognized by all STL processing software.

    Warning
    -------
    The STL format stores a loose collection of triangles and does
    not include connectivity information between the triangles.
    Therefore the use of this format for intermediate storage is
    **strongly discouraged**, as many processing algorithms will need
    to build the connectivity information over and again, which may
    lead to different results depending on round-off errors.
    The STL format should only be used as a **final export** to
    e.g. visualisation methods or machining processes.

    Examples
    --------
    >>> from pyformex.mesh import Mesh
    >>> f = Path('test_filewrite.stl')
    >>> M = Mesh(eltype='quad4').convert('tri3-u')
    >>> writeSTL(f, M.toFormex())
    >>> print(f.read_text())
    solid  Created by pyFormex ...
      facet normal 0.0 0.0 1.0
        outer loop
          vertex 0.0 0.0 0.0
          vertex 1.0 0.0 0.0
          vertex 1.0 1.0 0.0
        endloop
      endfacet
      facet normal 0.0 0.0 1.0
        outer loop
          vertex 1.0 1.0 0.0
          vertex 0.0 1.0 0.0
          vertex 0.0 0.0 0.0
        endloop
      endfacet
    endsolid
    <BLANKLINE>
    >>> f.remove()
    """
    fn = Path(fn)
    if isinstance(x, Formex):
        x = x.coords
    if not x.shape[1:] == (3, 3):
        raise ValueError(f"Expected an (ntri,3,3) array, got {x.shape}")

    stltype = 'binary' if binary else 'ascii'
    pf.verbose(1, f"Write {stltype} STL file {fn.absolute()}")
    if n is None:
        from pyformex import geomtools
        a, n = geomtools.areaNormals(x)
        ndegen = geomtools.degenerate(a, n).shape[0]
        if ndegen > 0:
            pf.verbose(2, f"The model contains {ndegen} degenerate triangles")
    x = np.column_stack([n.reshape(-1, 1, 3), x])
    x = at.checkArray(x, shape=(-1, 4, 3), kind='f')
    pf.verbose(2, f"Writing {x.shape[0]} triangles")
    mode = 'wb' if binary else 'w'
    with utils.File(fn, mode) as fil:
        if binary:
            write_stl_bin(fil, x, color)
        else:
            write_stl_asc(fil, x)
    pf.verbose(2, f"File size: {fn.size} bytes")


def write_stl_bin(fil, x, color=None):
    """Write a binary stl.

    Note
    ----
    This is a low level routine for use in writeSTL. It is not intended
    to be used directly.

    Parameters
    ----------
    fil: :term:`file_like`
        The file to write the data to. It can be any object supporting
        the write(bytes) method, like a file opened in binary write mode.
    x: (ntri,4,3) float array
        Array with 1 normal and 3 vertices and 1 normal per triangle.
    color: (4,) int array, optional
        Four color components in the range 0..255: red, green, blue and alpha.
        If specified, these will be stored in the header and **may** be
        recognized by some other software.


    Examples
    --------
    >>> from pyformex.mesh import Mesh
    >>> from pyformex.fileread import readSTL
    >>> f = Path('test_filewrite.stl')
    >>> M = Mesh(eltype='quad4').convert('tri3-u')
    >>> writeSTL(f, M.toFormex().coords, binary=True, color=[255,0,0,128])
    >>> x, n, c = readSTL(f)
    >>> print(x)
    [[[0.  0.  0.]
      [1.  0.  0.]
      [1.  1.  0.]]
    <BLANKLINE>
     [[1.  1.  0.]
      [0.  1.  0.]
      [0.  0.  0.]]]
    >>> print(n)
    [[0.  0.  1.]
     [0.  0.  1.]]
    >>> print(c)
    (1.0, 0.0, 0.0)
    >>> f.remove()

    """
    if color is not None:
        from pyformex.colors import RGBAcolor
        color = RGBAcolor(color)
    ver = pf.fullVersion().encode('latin1')
    if len(ver) > 50:
        ver = ver[:50]
    if color is None:
        color = b''
    else:
        color = b" COLOR=%c%c%c%c" % tuple(color)
        pf.verbose(2, f"Adding {color} to the header")

    head = b"%-50s %-29s" % (ver, color)
    fil.write(head)
    ntri = x.shape[0]
    np.array(ntri).astype(np.int32).tofile(fil)
    x = x.astype(np.float32)
    for i in range(ntri):
        x[i].tofile(fil)
        fil.write(b'\x00\x00')


def write_stl_asc(fil, x):
    """Write a collection of triangles to an ascii .stl file.

    Note
    ----
    This is a low level routine for use in writeSTL. It is not intended
    to be used directly.

    Parameters
    ----------
    fil: :term:`file_like`
        The file to write the data to. It can be any object supporting
        the write(bytes) method, like a file opened in binary write mode.
    x: (ntri,4,3) float array
        Array with 1 normal and 3 vertices and 1 normal per triangle.
    """
    fil.write(f"solid  Created by {pf.fullVersion()}\n")
    for e in x:
        fil.write("  facet normal %s %s %s\n" % tuple(e[0]))
        fil.write("    outer loop\n")
        for p in e[1:]:
            fil.write("      vertex %s %s %s\n" % tuple(p))
        fil.write("    endloop\n")
        fil.write("  endfacet\n")
    fil.write("endsolid\n")


def writeData(fil, data, fmt=None, sep='', end='\n'):
    """Write an array of numerical data to an open file.

    Parameters
    ----------
    fil: :term:`file_like`
        The file to write the data to. It can be any object supporting
        the write(bytes) method, like a file opened in binary write mode.
    data: :term:`array_like`
        A numerical array of int or float type. For output, the array
        will be reshaped to a 2D array, keeping the length of the last axis.
    fmt: str, optional
        A format string compatible with the array data type.
        If not provided, the data are written as a single block
        using :func:`numpy.tofile`.
        If provided, the format string should contain a valid format
        converter for a single data item. It may also contain the necessary
        spacing or separator.
        Examples are '%5i ' for int data and '%f,' or '%10.3e'
        for float data.
    sep: str, optional
        A string to be used as separator between single items.
        Only used if fmt is provided and the file is written in ascii mode.
    end: str, optional
        A string to be written at the end of the data block (if no `fmt`)
        or at the end of each row (with `fmt`). The default value is a newline
        character.
        Only used if fmt is provided and the file is written in ascii mode.

    Examples
    --------
    >>> i = np.eye(3)
    >>> f = Path('test_filewrite.out')
    >>> with f.open('wb') as fil:
    ...     writeData(fil,i,sep=' ')
    >>> f.size
    35
    >>> print(f.read_text())
    1.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 1.0
    >>> with f.open('wb') as fil:
    ...     writeData(fil,i,fmt='%.4f',sep=' ')
    >>> f.size
    63
    >>> print(f.read_text())
    1.0000 0.0000 0.0000
    0.0000 1.0000 0.0000
    0.0000 0.0000 1.0000
    >>> i = np.arange(24).reshape(2,3,4)
    >>> with f.open('wb') as fil:
    ...     writeData(fil,i,fmt='%.4f',sep=' ')
    >>> print(f.read_text())
    0.0000 1.0000 2.0000 3.0000
    4.0000 5.0000 6.0000 7.0000
    8.0000 9.0000 10.0000 11.0000
    12.0000 13.0000 14.0000 15.0000
    16.0000 17.0000 18.0000 19.0000
    20.0000 21.0000 22.0000 23.0000
    >>> f.remove()
    """
    if fmt is None:
        data.tofile(fil, sep)
    else:
        ncols = data.shape[-1]
        val = data.reshape(-1, ncols)
        template = sep.join([fmt] * ncols) + end
        for v in val:
            writeText(fil, template % tuple(v))


def writeIData(fil, data, fmt, ind=1, sep=' ', end='\n'):
    """Write an indexed array of numerical data to an open file.

    Parameters
    ----------
    fil: :term:`file_like`
        The file to write the data to. It can be any object supporting
        the write(bytes) method, like a file opened in binary write mode.
    data: :term:`array_like`
        A numerical array of int or float type. For output, the array
        will be reshaped to a 2D array, keeping the length of the last axis.
    fmt: str
        A format string compatible with the array data type.
        The format string should contain a valid format converter for a
        a single data item. It may also contain the necessary spacing or
        separator. Examples are '%5i ' for int data and '%f,' or '%10.3e'
        for float data.
    ind: int or int :term:`array_like`
        The row indices to write with the data. If an array, its length
        should be equal to the numbe of rows in the (2D-reshaped) `data`
        array. If a single int, it specifies the index for the first row,
        and the value will be automatically incremented for the other rows.
    sep: str, optional
        A string to be used as separator between single items.
    end: str, optional
        A string to be written at the end of the data block (if no `fmt`)
        or at the end of each row (with `fmt`). The default value is a newline
        character.

    Examples
    --------
    >>> i = np.eye(3)
    >>> f = Path('test_filewrite.out')
    >>> with f.open('wb') as fil:
    ...     writeIData(fil,i,fmt='%.4f',sep=' ')
    >>> f.size
    72
    >>> print(f.read_text())
    1  1.0000 0.0000 0.0000
    2  0.0000 1.0000 0.0000
    3  0.0000 0.0000 1.0000
    >>> f.remove()
    """
    ncols = data.shape[-1]
    val = data.reshape(-1, ncols)
    nrows = val.shape[0]
    if at.isInt(ind):
        ind = ind + np.arange(nrows)
    else:
        ind = ind.reshape(-1)
        if ind.shape[0] != nrows:
            raise ValueError("Index should have same length as data")
    template = "%d  " + sep.join([fmt] * ncols) + end
    for i, v in zip(ind, val):
        writeText(fil, template % (i, *v))


def writeText(fil, text):
    """Write text to a file opened in text or binary mode

    text can be either str or bytes. If not matching the open mode,
    text is encoded to/decoded from utf-8
    """
    if 'b' in fil.mode:
        if isinstance(text, bytes):
            out = text
        else:
            out = text.encode('utf-8')
    else:
        if isinstance(text, bytes):
            out = text.decode('utf-8')
        else:
            out = text
    fil.write(out)


# End
