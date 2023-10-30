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

"""Read geometry from files in a number of formats.

This module defines basic routines to read geometrical data
from a file and the specialized importers to read files in a number of
well known standardized formats.
"""
import re
import numpy as np

import pyformex as pf
import pyformex.arraytools as at
from pyformex import utils
from pyformex.path import Path
from pyformex.varray import Varray
from pyformex.connectivity import Connectivity
from pyformex.coords import Coords
from pyformex.mesh import Mesh
from pyformex.pzffile import loadPZF as readPZF

__all__ = ['readPZF', 'readPGF', 'readOFF', 'readOBJ', 'readPLY', 'readGTS',
           'readSTL']


def readPGF(filename, count=-1):
    """Read a pyFormex Geometry File.

    A pyFormex Geometry File can store multiple geometrical objects in a
    native format that can be efficiently read back into pyformex.
    The format is portable over different pyFormex versions and
    even to other software, as the format is stable and documented.
    This reader can restore subclasses of :class:`Geometry`:
    :class:`Formex`, :class:`Mesh`, :class:`TriSurface`,
    :class:`PolyLine`, :class:`BezierSpline`, :class:`NurbsCurve`,
    with their stored attributes (name, color, field variables).

    Parameters
    ----------
    filename: :term:`path_like`
        The name of an existing pyFormex Geometry File. If the
        filename ends on '.gz' or '.bz2', it is considered to be a gzipped,
        resp. bzipped file and it will transparently be uncompressed
        during reading.
    count: int, optional
        If specified, no more than this number of objects will be read.

    Returns
    -------
    dict
        A dictionary with the geometric objects read from the file.
        If the file contains the object names, these are used as the keys.
        Else, default names are provided.
        If the file contains attributes (colors, fields) for an object,
        these will also be restored.
    """
    from pyformex import geomfile
    filename = Path(filename)
    pf.verbose(1, f"Read PGF file {filename.absolute()}")
    f = geomfile.GeometryFile(filename, 'r')
    objects = f.read(count)
    pf.verbose(2, f"Got {len(objects)} objects")
    return objects


def readOFF(filename):
    """Read polygon meshes from an OFF file.

    Parameters
    ----------
    filename: :term:`path_like`
        The name of a file in OFF format, commonly having a suffix '.off'.
        If the name ends with '.off.gz' or '.off.bz2', then the file will
        transparently be uncompressed during reading.
    mplex: int, optional
        The maximum plexitude of the output polygons. If provided, polygons
        with a plexitude higher that mplex will be split into smaller ones.
        For example, with mplex=4, polygons with 5 or more vertices will be
        split into quads and triangles. Likewise, mplex=3 will split all
        polygons into triangles.

    Returns
    -------
    Polygons
        A :class:`Polygons` with the polygons read from the file.

    Examples
    --------
    >>> from .filewrite import writeOFF
    >>> f = Path('test_filewrite.off')
    >>> M = Mesh(eltype='quad4').convert('tri3-u')
    >>> writeOFF(f, M)
    >>> poly = readOFF(f)
    >>> print(poly)
    Polygons: nnodes: 4, nelems: 2, nplex: min 3, max 3, eltype: polygon
      BBox: [0. 0. 0.], [1. 1. 0.]
      Size: [1. 1. 0.]
    >>> print(poly.coords)
    [[0. 0. 0.]
     [1. 0. 0.]
     [1. 1. 0.]
     [0. 1. 0.]]
    >>> print(poly.elems)
    Varray (nrows=2, width=3..3)
      [0 1 2]
      [2 3 0]

    """
    from pyformex.polygons import Polygons
    filename = Path(filename)
    pf.verbose(1, f"Read OFF file {filename.absolute()}")

    class STAGE():
        INIT, HEADER, COORDS, ELEMS, EDGES = range(5)

    coords = None
    faces = []
    stage = STAGE.INIT
    name = None
    with utils.File(filename, 'r') as fil:
        for line in fil:
            comment = line.find('#')
            if comment >= 0:
                m = re.match(r'# name=(\w+)', line, flags=re.A)
                if m is not None:
                    name = m.group(1)
                    continue
                line = line[:comment]
                if not line:
                    continue
            line = line.strip()
            if not line:
                continue
            if stage == STAGE.INIT:
                stage += 1
                if "OFF" in line:
                    if line != 'OFF':
                        raise ValueError(
                            f"I can not yet read {line} files, only OFF!")
                    continue
            if stage == STAGE.HEADER:
                nnodes, nelems, nedges = [int(i) for i in line.split()]
                pf.verbose(2, f"  {nnodes} vertices, {nelems} faces, {nedges} edges")
                stage += 1
                # Prepare for reading nodes
                coords = np.empty((nnodes, 3), dtype=at.Float)
                i = 0
            elif stage == STAGE.COORDS:
                s = line.split()
                coords[i] = [float(si) for si in s]
                i += 1
                if i >= nnodes:
                    stage += 1
                    i = 0
            elif stage == STAGE.ELEMS:
                s = line.split()
                n = int(s[0])
                faces.append([int(si) for si in s[1:n+1]])
                i += 1
                if i >= nelems:
                    stage += 1
                    i = 0
            elif stage == STAGE.EDGES:
                pf.verbose(2, "Reading of edges is not yet implemented")

    if coords is None or not faces:
        raise ValueError("Could not read any vertices and/or faces")

    poly = Polygons(Coords(coords), faces)
    if name:
        poly.attrib(name=name)
    pf.verbose(2, f"Got {poly}")
    return poly


def readOBJ(filename):
    """Read a mesh from an OBJ file.

    Reads the mesh data from a wavefront .obj file.

    Parameters
    ----------
    filename: :term:`path_like`
        The name of a file in OBJ format, commonly having a suffix '.obj'.
        If the name ends with '.obj.gz' or '.obj.bz2', the file will
        transparently be uncompressed during reading.

    Returns
    -------
    Polygons
        The polygons read from the .obj file.

    Notes
    -----
    Currently only handles polygons.
    It does not handle relative indexing, subobjects, groups, lines,
    splines, beziers, materials.
    Normals and texture coordinates are read but not returned.

    Examples
    --------
    >>> from .filewrite import writeOBJ
    >>> f = Path('test_filewrite.obj')
    >>> M = Mesh(eltype='quad4')
    >>> writeOBJ(f, M)
    >>> poly = readOBJ(f)
    >>> print(poly)
    Polygons: nnodes: 4, nelems: 1, nplex: min 4, max 4, eltype: polygon
      BBox: [0. 0. 0.], [1. 1. 0.]
      Size: [1. 1. 0.]
    >>> print(poly.coords)
    [[0.  0.  0.]
     [1.  0.  0.]
     [1.  1.  0.]
     [0.  1.  0.]]
    >>> print(poly.elems)
    Varray (nrows=1, width=4..4)
      [0 1 2 3]
    """
    from pyformex.polygons import Polygons

    def vertex_data(s):
        t = s.split('/')
        vid = int(t[0])
        tid = int(t[1]) if len(t) > 1 and t[1] else -1
        nid = int(t[2]) if len(t) > 2 else -1
        return vid, tid, nid

    filename = Path(filename)
    pf.verbose(1, f"Read OBJ file {filename.absolute()}")
    # storage for coords, normals, texture coords
    coords = {'': [], 'n': [], 't': []}
    # storage for faces and edges
    faces = []
    # lines = []
    name = None
    with utils.File(filename, 'r') as fil:
        for line in fil:
            s = line.split()
            if len(s) == 0:
                continue
            typ, *data = s
            if typ[0] == 'v':
                coords[typ[1:2]].append([float(d) for d in data])
            elif typ == 'f':
                faces.append([vertex_data(d)[0] for d in data])
            elif typ == 'o':
                name = s[1]
    faces = Varray(faces)
    faces.data -= 1   # OBJ format starts at 1
    try:
        poly = Polygons(Coords(coords['']), faces)
    except Exception:
        raise ValueError("This file is too complex for our current .OBJ reader")
    if coords['n']:
        normals = Coords(coords['n'])
        if normals.shape == poly.coords.shape:
            poly._memory['avg_normals'] = normals
    if coords['t']:
        texture = Coords(coords['t'])
        if texture.shape == poly.coords.shape:
            poly._memory['tex_coords'] = texture
    if name:
        poly.attrib(name=name)
    pf.verbose(2, f"Got {poly}")
    return poly


def readPLY(filename, check=True):
    """Read polygons from a PLY file.

    Reads the polygon data from a stanford .ply file and possibly
    splits the high plexitude polygons into smaller ones.

    Parameters
    ----------
    filename: :term:`path_like`
        The name of a file in PLY format, commonly having a suffix '.ply'.
        Ascii as well as binary formats are supported
        If the name ends with '.ply.gz' or '.ply.bz2', the file will
        transparently be uncompressed during reading.

    Returns
    -------
    Polygons
        The polygons read from the PLY file.

    Notes
    -----
    This uses plyfile from https://github.com/dranjan/python-plyfile
    to read the PLY file.

    Examples
    --------
    >>> from .filewrite import writePLY
    >>> f = Path('test_filewrite.ply')
    >>> M = Mesh(eltype='quad4')
    >>> writePLY(f, M)
    >>> poly = readPLY(f)
    >>> print(poly)
    Polygons: nnodes: 4, nelems: 1, nplex: min 4, max 4, eltype: polygon
      BBox: [0. 0. 0.], [1. 1. 0.]
      Size: [1. 1. 0.]
    >>> print(poly.coords)
    [[0.  0.  0.]
     [1.  0.  0.]
     [1.  1.  0.]
     [0.  1.  0.]]
    >>> print(poly.elems)
    Varray (nrows=1, width=4..4)
      [0 1 2 3]
    >>> M = Mesh(eltype='quad4').convert('tri3-u')
    >>> writePLY(f, M, binary=True)
    >>> P = readPLY(f, check=False)
    >>> print(P)
    Polygons: nnodes: 4, nelems: 2, nplex: min 3, max 3, eltype: polygon
      BBox: [0. 0. 0.], [1. 1. 0.]
      Size: [1. 1. 0.]
    >>> print(P.coords)
    [[0. 0. 0.]
     [1. 0. 0.]
     [1. 1. 0.]
     [0. 1. 0.]]
    >>> print(P.elems)
    Varray (nrows=2, width=3..3)
      [0 1 2]
      [2 3 0]
    """
    from pyformex.polygons import Polygons
    from pyformex.plugins.plyfile import PlyData

    filename = Path(filename)
    pf.verbose(1, f"Read PLY file {filename.absolute()}")
    with utils.File(filename, 'rb') as fil:
        ply_data = PlyData.read(fil)
    name = None
    for line in ply_data._get_comments():
        m = re.match(r'name=(\w+)', line, flags=re.A)
        if m is not None:
            name = m.group(1)
    vertices = ply_data['vertex']
    faces = ply_data['face']
    # Point coordinates
    coords = Coords(np.stack([
        vertices['x'],
        vertices['y'],
        vertices['z'], ], axis=1))
    # Vertex indices
    vertex_indices = faces['vertex_indices']
    # Polygons
    poly = Polygons(coords, vertex_indices, check=check)
    if name:
        poly.attrib(name=name)
    pf.verbose(2, f"Got {poly}")
    return poly


def readGTS(filename):
    """Read a surface mesh from a GTS file.

    Parameters
    ----------
    filename: :term:`path_like`
        The name of a file in GTS format, commonly having a suffix '.gts'.
        If the name ends with '.gts.gz' or '.gts.bz2', then the file will
        transparently be uncompressed during reading.

    Returns
    -------
    coords: float array (ncoords, 3)
        The coordinates of all vertices.
    edges: int array (nedges,2)
        The edges to nodes connectivity table.
    faces: int array (nfaces,2)
        The faces to edges connectivity table.

    Examples
    --------
    >>> from .filewrite import writeGTS
    >>> f = Path('test_filewrite.gts')
    >>> M = Mesh(eltype='quad4').convert('tri3-u')
    >>> writeGTS(f, M.toSurface())
    >>> coords, edges, faces = readGTS(f)
    >>> print(coords)
    [[0. 0. 0.]
     [1. 0. 0.]
     [1. 1. 0.]
     [0. 1. 0.]]
    >>> print(edges)
    [[0 1]
     [2 0]
     [3 0]
     [1 2]
     [2 3]]
    >>> print(faces)
    [[0 3 1]
     [4 2 1]]
    """
    filename = Path(filename)
    pf.verbose(1, f"Read GTS file {filename.absolute()}")
    with utils.File(filename, 'r') as fil:
        header = fil.readline().split()
        ncoords, nedges, nfaces = [int(i) for i in header[:3]]
        if len(header) >= 7 and header[6].endswith('Binary'):
            sep = ''
            raise RuntimeError(
                "We can not read binary GTS format yet. "
                "See https://savannah.nongnu.org/bugs/index.php?38608. "
                "Maybe you should recompile the extra/gts commands."
            )
        else:
            sep = ' '
        coords = np.fromfile(
            fil, dtype=at.Float, count=3 * ncoords, sep=sep
        ).reshape(-1, 3)
        edges = np.fromfile(
            fil, dtype=np.int32, count=2 * nedges, sep=' '
        ).reshape(-1, 2) - 1
        faces = np.fromfile(
            fil, dtype=np.int32, count=3 * nfaces, sep=' '
        ).reshape(-1, 3) - 1
    pf.verbose(2, f"Got {ncoords} coords, {nedges} edges, {nfaces} faces")
    if coords.shape[0] != ncoords or \
       edges.shape[0] != nedges or \
       faces.shape[0] != nfaces:
        pf.verbose(1, "Error reading GTS file! Result may be incomplete.")
    return coords, edges, faces


def readSTL(filename):
    """Read a surface mesh from an STL file.

    Parameters
    ----------
    filename: :term:`path_like`
        The name of a file in STL format, commonly having a suffix '.stl'.
        If the name ends with '.gz' or '.bz2', then the file will
        transparently be uncompressed during reading.

    Returns
    -------
    coords: float array (ncoords, 3)
        The coordinates of all vertices.
    edges: int array (nedges,2)
        The edges to nodes connectivity table.
    faces: int array (nfaces,2)
        The faces to edges connectivity table.

    Notes
    -----
    STL files come in ascii and binary formats. As there is no simple
    way to detect the format, a binary read is tried first, and if
    unsuccessful, the ascii read is tried next.

    Examples
    --------
    >>> from .filewrite import writeSTL
    >>> f = Path('test_filewrite.stl')
    >>> M = Mesh(eltype='quad4').convert('tri3-u')
    >>> writeSTL(f, M.toFormex().coords, binary=True, color=[255,0,0,128])
    >>> coords, normals, color = readSTL(f)
    >>> print(coords)
    [[[0.  0.  0.]
      [1.  0.  0.]
      [1.  1.  0.]]
    <BLANKLINE>
     [[1.  1.  0.]
      [0.  1.  0.]
      [0.  0.  0.]]]
    >>> print(normals)
    [[0.  0.  1.]
     [0.  0.  1.]]
    >>> print(color)
    (1.0, 0.0, 0.0)
    >>> writeSTL(f, M.toFormex().coords, binary=False)
    >>> coords, normals, color = readSTL(f)
    >>> print(coords)
    [[[0.  0.  0.]
      [1.  0.  0.]
      [1.  1.  0.]]
    <BLANKLINE>
     [[1.  1.  0.]
      [0.  1.  0.]
      [0.  0.  0.]]]
    >>> print(normals)
    [[0.  0.  1.]
     [0.  0.  1.]]
    """
    filename = Path(filename)
    pf.verbose(1, f"Read STL file {filename.absolute()}")
    with utils.File(filename, 'rb') as fil:
        head = fil.read(5)
        asc = head[:5] == b'solid'
        fil.seek(0)
        pf.verbose(2, f"Reading {'ascii' if asc else 'binary'} STL file")
        if asc:
            coords, normals = read_stl_asc(fil)
            color = None
        else:
            coords, normals, color = read_stl_bin(fil)
    pf.verbose(2, f"Got {coords.shape[0]} triangles")
    return coords, normals, color


def read_stl_bin(fil):
    """Read a binary STL file.

    Note
    ----
    This is a low level routine for use in readSTL. It is not intended
    to be used directly.

    Parameters
    ----------
    fil: open file
        File opened in binary read mode, holding binary STL data.

    Returns
    -------
    coords: Coords (ntri,3,3)
        A Coords with ntri triangles. Each triangle consists of 3 vertices.
    normals: Coords (ntri,3)
        A Coords with ntri vectors: the outer normals on the triangles.
    color: None | float array (3,)
        If the STL file header contained a color in Materialise (TM) format,
        the RGB color components are returned as OpenGL color components.
        The alpha value is currently not returned.
    """

    def addTriangle(i):
        x[i] = np.fromfile(file=fil, dtype=at.Float, count=12).reshape(4, 3)
        fil.read(2)

    head = fil.read(80)
    i = head.find(b'COLOR=')
    if i >= 0 and i <= 70:
        color = np.frombuffer(head[i + 6:i + 10], dtype=np.uint8, count=4)
    else:
        color = None

    ntri = np.fromfile(fil, dtype=at.Int, count=1)[0]
    x = np.zeros((ntri, 4, 3), dtype=at.Float)
    # nbytes = 12*4 + 2
    [addTriangle(it) for it in range(ntri)]
    normals = Coords(x[:, 0])
    coords = Coords(x[:, 1:])
    if color is not None:
        from pyformex import colors
        color = colors.GLcolor(color[:3])
    return coords, normals, color


def read_stl_asc(fil):
    """Read an ascii STL file.

    Note
    ----
    This is a low level routine for use in readSTL. It is not intended
    to be used directly.

    Parameters
    ----------
    fil: open file
        File opened in binary read mode, holding ascii STL data.

    Returns
    -------
    coords: Coords (ntri,3,3)
        A Coords with ntri triangles. Each triangle consists of 3 vertices.
    normals: Coords (ntri,3)
        A Coords with ntri vectors: the outer normals on the triangles.

    """
    # different line modes and the corresponding re's
    solid, facet, outer, vertex, endloop, endfacet, endsolid = range(7)
    _re_solid = re.compile(b"\\s*solid\\s+.*")
    _re_facet = re.compile(b"\\s*facet\\s+normal\\s+(?P<data>.*)")
    _re_outer = re.compile(b"\\s*outer\\s+loop\\s*")
    _re_vertex = re.compile(b"\\s*vertex\\s+(?P<data>.*)")
    _re_endloop = re.compile(b"\\s*endloop\\s*")
    _re_endfacet = re.compile(b"\\s*endfacet\\s*")
    _re_endsolid = re.compile(b"\\s*endsolid\\s*")
    _re_expect = {
        solid: _re_solid,
        facet: _re_facet,
        outer: _re_outer,
        vertex: _re_vertex,
        endloop: _re_endloop,
        endfacet: _re_endfacet,
    }

    # place to store the results
    normals = []
    coords = []

    def getdata(s):
        """Get 3 floats from a string"""
        data = [float(i) for i in s.split()]
        if len(data) != 3:
            raise ValueError("Expected 3 float values")
        return data

    mode = solid
    facets = 0
    nverts = 0
    count = 0
    for line in fil:
        count += 1
        m = _re_expect[mode].match(line)
        if m is None:
            if mode == facet and _re_endsolid.match(line):
                # We reached the end
                break
            else:
                raise ValueError(f"Invalid input on line {count}:\n{line}")
        if mode == vertex:
            try:
                data = getdata(m.group(1))
            except Exception:
                raise ValueError(f"Data error in line {count}: \n{line}")
            nverts += 1
            coords.append(data)
            if nverts == 3:
                mode = endloop
        elif mode == facet:
            try:
                data = getdata(m.group(1))
            except Exception:
                raise ValueError(f"Data error in line {count}: \n{line}")
            normals.append(data)
            mode = outer
        elif mode == outer:
            nverts = 0
            mode = vertex
        elif mode == endloop:
            mode = endfacet
        elif mode == endfacet:
            facets += 1
            mode = facet
        elif mode == solid:
            if count != 1:
                raise ValueError(f"'solid' found on line {count}")
            mode = facet
        else:
            raise ValueError(f"Invalid input on line {count}")

    coords = Coords(coords).reshape(-1, 3, 3)
    normals = Coords(normals)
    return coords, normals


# TODO: this should unzip compressed input files and zip compressed output
# TODO: remove the default outname and warn if not specified
def stlConvert(stlname, outname=None, binary=False, options='-d'):
    """Convert an .stl file to .off or .gts or binary .stl format.

    Parameters
    ----------
    stlname: :term:`path_like`
        Name of an existing .stl file (either ascii or binary).
    outname: str or Path
        Name or suffix of the output file. The suffix defines the format
        and should be one of '.off', '.gts', '.stl', '.stla', or .stlb'.
        If a suffix only is given (other than '.stl'), then the outname
        will be constructed by changing the suffix of the input ``stlname``.
        If not specified, the suffix of the configuration variable
        'surface/stlread' is used.
    binary: bool
        Only used if the extension of ``outname`` is '.stl'. Defines whether
        the output format is a binary or ascii STL format.
    options: str

    Returns
    -------
    outname: Path
        The name of the output file.
    status: int
        The exit status (0 if successful) of the conversion program.
    stdout: str
        The output of running the conversion program or a
        'file is already up to date' message.

    Notes
    -----
    If the outname file exists and its mtime is more recent than the stlname,
    the outname file is considered up to date and the conversion program will
    not be run.

    The conversion program will be choosen depending on the extension.
    This uses the external commands 'admesh' or 'stl2gts'.

    """
    stlname = Path(stlname)
    if outname is None:
        outname = pf.cfg['surface/stlread']
    outname = Path(outname)
    if outname.suffix == '' and outname.name.startswith('.'):
        # It is considered as a suffix only
        outname = stlname.with_suffix(outname)
        if outname.resolve() == stlname.resolve():
            raise ValueError("stlname and outname resolve to the same file")
    if outname.exists() and stlname.mtime < outname.mtime:
        return outname, 0, "File '{outname}' seems to be up to date"

    ftype = outname.ftype
    if ftype == 'stl' and binary:
        ftype = 'stlb'

    if ftype in ['off', 'stl', 'stla', 'stlb']:
        utils.External.has('admesh')
        cmdopt = {'off': '--write-off', 'stlb':'-b'}.get(ftype, '-a')
        cmd = f"admesh {options} {cmdopt} '{outname}' '{stlname}'"
    elif ftype == 'gts':
        cmd = f"stl2gts < '{stlname}' > '{outname}'"
    else:
        return outname, 1, f"Can not convert file '{stlname}' to '{outname}'"

    P = utils.command(cmd, shell=True)
    return outname, P.returncode, P.stdout


# Global variables used by some functions
filename = None
mode = None
nplex = None
offset = None


def getParams(line):
    """Strip the parameters from a comment line"""
    s = line.split()
    d = {'mode': s.pop(0), 'filename': s.pop(0)}
    d.update(zip(s[::2], s[1::2]))
    return d


def readNodes(fil):
    """Read a set of nodes from an open mesh file"""
    a = np.fromfile(fil, sep=" ").reshape(-1, 3)
    x = Coords(a)
    return x


def readElems(fil, nplex):
    """Read a set of elems of plexitude nplex from an open mesh file"""
    print(f"Reading elements of plexitude {nplex}")
    e = np.fromfile(fil, sep=" ", dtype=at.Int).reshape(-1, nplex)
    e = Connectivity(e)
    return e


def readEsets(fil):
    """Read the eset data of type generate"""
    data = []
    for line in fil:
        s = line.strip('\n').split()
        if len(s) == 4:
            data.append(s[:1] + [int(i) for i in s[1:]])
    return data


def readMeshFile(filename):
    """Read a nodes/elems model from file.

    Returns a dict:

    - 'coords': a Coords with all nodes
    - 'elems': a list of Connectivities
    - 'esets': a list of element sets
    """
    d = {}
    fil = open(filename, 'r')
    for line in fil:
        if line[0] == '#':
            line = line[1:]
        globals().update(getParams(line))
        dfil = open(filename, 'r')
        if mode == 'nodes':
            d['coords'] = readNodes(dfil)
        elif mode == 'elems':
            elems = d.setdefault('elems', [])
            e = readElems(dfil, int(nplex)) - int(offset)
            elems.append(e)
        elif mode == 'esets':
            d['esets'] = readEsets(dfil)
        else:
            print(f"Skipping unrecognized line: {line}")
        dfil.close()

    fil.close()
    return d


def extractMeshes(d):
    """Extract the Meshes read from a .mesh file.

    """
    x = d['coords']
    e = d['elems']
    M = [Mesh(x, ei) for ei in e]
    return M

def convertInp(filename):
    """Convert an Abaqus .inp to a .mesh set of files"""
    filename = Path(filename).resolve()
    converter = pf.cfg['bindir'] / 'read_abq_inp.awk'
    cmd = "cd {filename.parent}; awk -f {converter} {filename.name}"
    print(cmd)
    P = utils.command(cmd, shell=True)
    print(P.stdout)
    print(P.stderr)


######## Abaqus/Calculix INP format (.inp) ##########


def readINP(filename, tempdir=None):
    """Read the geometry from an Abaqus/Calculix .inp file

    This uses :func:`plugins.ccxinp.readInpFile` to import the Finite
    Element meshes from an Abaqus or Calculix INP format file.

    Parameters
    ----------
    filename: :term:`path_like`
        The path of the input file, usually with a .inp suffix.
    tempdir: :term:`path_like`, optional
        The path of a directory where intermediary results can be stored.
        If provided but not existent, it will be created. If not provided,
        a temporary directory is used and intermediary data are not saved.

    Returns
    -------
    dict
        A dict where the keys are part names and the values are
        :class:`FeModel` instances. If the .inp file does not contain parts,
        default part names are generated.

    Warning
    -------
    Element blocks with an unrecognized element type will raise an exception,
    unless :attr:`plugins.ccxinp.skip_unknown_eltype` is set to True.
    """
    from pyformex.plugins import ccxinp
    from pyformex.plugins import fe

    model = ccxinp.readInpFile(filename, tempdir=tempdir)
    print(f"Number of parts: {len(model.parts)}")
    fem = {}
    for part in model.parts:
        try:
            coords = Coords(part['coords'])
            nodid = part['nodid']
            nodpos = at.inverseUniqueIndex(nodid)
            print(f"nnodes = {coords.shape[0]}")
            print(f"nodid: {nodid}")
            print(f"nodpos: {nodpos}")
            elems = []
            for t, e in part['elems']:
                try:
                    print(f"Converting elements of type {t}")
                    el = nodpos[e]
                    els = Connectivity(nodpos[e], eltype=t)
                    elems.append(els)
                except Exception:
                    print(f"Conversion failed for elements of type {t}")
                    print(f"Orig els {e}")
                    print(f"Trl els {el}")
            print(f"ELEM TYPES: {[e.eltype for e in elems]}")
            fem[part['name']] = fe.Model(coords, elems)
        except Exception as e:
            print(f"Skipping part {part['name']}")
            print(e)
    return fem


######## Gambit neutral file (.neu) ##########

# convert Gambit neutral node order to pyFormex order
neu_pyf_order = {
    4: (0, 1, 3, 2, 4, 5, 7, 6),
}

def readNEU(filename, return_numbering=False):
    """Read a Mesh from a Gambit neutral file.

    Parameters
    ----------
    filename: :term:`path_like`
        The name of a file in Gambit neutral format, commonly having a suffix
        '.neu'. If the name ends with '.gz' or '.bz2', the file will
        transparently be uncompressed during reading.
    return_numbering: bool
        If True, also returns the original node and element numbers as found
        in the file. The internal pyFormex numbers are always in order of
        appearance in the file.

    Returns
    -------
    Mesh
        The Mesh read from the Gambit neutral file, if reading was successful.
        None if the file could not be read. If the .neu file contains groups,
        the Mesh will have prop values equal to the material type numbers in
        the file.
    nrs: int array
        The node numbers in the .neu file corrsponding to the nodes in
        Mesh.coords. Only returned if return_numbering is True.
    enrs: in array
        The element numbers in the .neu file corresponding to the elements
        in Mesh.elems. Only returned if return_numbering is True.

    Notes
    -----
    Currently this function can only read Gambit files where all cells
    are of the same element type.

    Examples
    --------
    >>> from pyformex.plugins.neu_exp import writeNEU
    >>> f = Path('test_filewrite.neu')
    >>> M = Mesh(eltype='hex8').subdivide(3)
    >>> writeNEU(f, M)
    >>> M = readNEU(f)
    Successfully read test_filewrite.neu
     ncoords=64; nelems=27;  nplex=8; eltype=Hex8
    >>> print(M)
    Mesh: nnodes: 64, nelems: 27, nplex: 8, level: 3, eltype: hex8
      BBox: [0.  0.  0.], [1.  1.  1.]
      Size: [1.  1.  1.]
      Area: 6.0  Volume: 1.0
    """

    from pyformex.plugins.neu_exp import pyf_neu_eltype, neu_pyf_order
    neu_pyf_eltype = utils.inverseDict(pyf_neu_eltype)

    def find_line(fil, pat):
        for line in fil:
            if line.split()[:len(pat)] == pat:
                return True

    def read_coords(fil, ncoords):
        nrs = np.full((ncoords,), -1, dtype=at.Int)
        coords = np.empty((ncoords, 3), dtype=at.Float)
        for i in range(ncoords):
            line = next(fil)
            s = line.split()
            nrs[i] = int(s[0])
            coords[i] = [float(si) for si in s[1:4]]
        return nrs, coords

    def read_elems(fil, nelems):
        enrs = np.full((nelems,), -1, dtype=at.Int)
        for i in range(nelems):
            line = next(fil)
            s = line.split()
            enrs[i] = int(s[0])
            if i == 0:
                eltyp = int(s[1])
                nplex = int(s[2])
                elems = np.empty((nelems, nplex), dtype=at.Int)
            else:
                if eltyp != int(s[1]) or nplex != int(s[2]):
                    raise ValueError(
                        "Currently I can not handle .neu files with more "
                        "than 1 element type")
            s = s[3:]
            while len(s) < nplex:
                s.extend(next(fil).split())
            elems[i] = [int(si) for si in s]
        return eltyp, enrs, elems

    def read_group(fil):
        s = next(fil).split()
        group, nels, matnr, nflags = [int(i) for i in s[1::2]]
        next(fil)  # groupname
        next(fil)  # flags
        values = []
        for i in range((nels+9) // 10):
            values.extend([int(si) for si in next(fil).split()])
        return matnr, np.array(values, dtype=at.Int)

    filename = Path(filename)
    pf.verbose(1, f"Read NEU file {filename.absolute()}")
    with utils.File(filename, 'r') as fil:
        if find_line(fil, ['NUMNP']):
            # read the parameters
            line = next(fil)
            s = line.split()
            ncoords = int(s[0])
            nelems = int(s[1])
            if find_line(fil, ['NODAL', 'COORDINATES']):
                # read the nodal coordinates
                nrs, coords = read_coords(fil, ncoords)
                line = next(fil)
                if find_line(fil, ['ELEMENTS/CELLS']):
                    # read the elements
                    eltyp, enrs, elems = read_elems(fil, nelems)
                    nplex = elems.shape[-1]
                    elname = neu_pyf_eltype.get((eltyp, nplex), None)
                    if elname is None:
                        raise ValueError(
                            f"I can not convert .neu files with elements"
                            f" of type {eltyp} and plexitude {nplex}")
                    # Translate node numbers to in-order coordinates
                    inv = at.inverseUniqueIndex(nrs)
                    elems = inv[elems]
                    if elname in neu_pyf_order:
                        # Reorder the nodes to our element node numbering scheme
                        elems = elems[:, neu_pyf_order[elname]]
                    M = Mesh(coords, elems, eltype=elname)

                    # print Read groups
                    while find_line(fil, ['ELEMENT', 'GROUP']):
                        # read an element group
                        p, els = read_group(fil)
                        if M.prop is None:
                            M.setProp(0)
                        M.prop[els] = p

                    print(f"Successfully read {filename}")
                    print(f" ncoords={ncoords}; nelems={M.nelems()}; "
                          f" nplex={M.nplex()}; eltype={M.elType()}")

                    if return_numbering:
                        return M, nrs, enrs
                    else:
                        return M
        print(f"Error while reading {filename}")

# End
