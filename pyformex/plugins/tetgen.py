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
"""Interface with tetgen

A collection of functions to read/write tetgen files and to run the
tetgen program

tetgen is a quality tetrahedral mesh generator and a 3D Delaunay triangulator.
See http://tetgen.org
"""
import numpy as np

from pyformex import utils
utils.External.require('tetgen')

from pyformex import Path
from pyformex.core import *
from pyformex.connectivity import Connectivity
from pyformex.mesh import Mesh
from pyformex.filewrite import *


def readNodeFile(fn):
    """Read a tetgen .node file.

    Returns a tuple as described in :func:`readNodesBlock`.
    """
    with open(fn, 'r') as fil:
        line = skipComments(fil)
        npts, ndim, nattr, nbmark = getInts(line, 4)
        return readNodesBlock(fil, npts, ndim, nattr, nbmark)


def readEleFile(fn):
    """Read a tetgen .ele file.

    Returns a tuple as described in readElemsBlock.
    """
    with open(fn, 'r') as fil:
        line = skipComments(fil)
        nelems, nplex, nattr = getInts(line, 3)
        return readElemsBlock(fil, nelems, nplex, nattr)


def readFaceFile(fn):
    """Read a tetgen .face file.

    Returns a tuple as described in readFacesBlock.
    """
    with open(fn, 'r') as fil:
        line = skipComments(fil)
        nelems, nbmark = getInts(line, 2)
        return readFacesBlock(fil, nelems, nbmark)


def readSmeshFile(fn):
    """Read a tetgen .smesh file.

    Returns an array of triangle elements.
    """
    fn = Path(fn)
    with open(fn, 'r') as fil:

        # node section.
        line = skipComments(fil)
        npts, ndim, nattr, nbmark = getInts(line, 4)
        if npts > 0:
            nodeInfo = readNodesBlock(fil, npts, ndim, nattr, nbmark)
        else:
            # corresponding .node file
            nodeInfo = readNodeFile(fn.with_suffix('.node'))

        # facet section
        line = skipComments(fil)
        nelems, nbmark = getInts(line, 2)
        facetInfo = readSmeshFacetsBlock(fil, nelems, nbmark)

        nodenrs = nodeInfo[1]
        if nodenrs.min() == 1 and nodenrs.max()==nodenrs.size:
            elems = facetInfo[0]
            for e in elems:
                elems[e] -= 1

        # We currently do not read the holes and attributes

        return nodeInfo[0], facetInfo[0]


def readPolyFile(fn):
    """Read a tetgen .poly file.

    Returns an array of triangle elements.
    """
    fn = Path(fn)
    with open(fn, 'r') as fil:

        # node section.
        line = skipComments(fil)
        npts, ndim, nattr, nbmark = getInts(line, 4)
        if npts > 0:
            nodeInfo = readNodesBlock(fil, npts, ndim, nattr, nbmark)
        else:
            # corresponding .node file
            nodeInfo = readNodeFile(fn.with_suffix('.node'))

        # facet section
        line = skipComments(fil)
        nelems, nbmark = getInts(line, 2)
        facetInfo = readFacesBlock(fil, nelems, nbmark)
        #print("NEXT LINE:")
        #print(line)
        return nodeInfo[0], facetInfo[0]

        ## s = line.strip('\n').split()
        ## nelems = int(s[0])
        ## elems = fromfile(fil,sep=' ',dtype=np.int32, count=4*nelems)
        ## elems = elems.reshape((-1,4))
        ## return elems[:,1:]


def readSurface(fn):
    """Read a tetgen surface from a .node/.face file pair.

    The given filename is either the .node or .face file.
    Returns a tuple of (nodes,elems).
    """
    fn = Path(fn)
    nodeInfo = readNodeFile(fn.with_suffix('.node'))
    nodes = nodeInfo[0]
    print("Read %s nodes" % nodes.shape[0])
    elemInfo = readFaceFile(fn.with_suffix('.face'))
    elems = elemInfo[0]
    print("Read %s elems" % elems.shape[0])
    #if numbers[0] == 1:
    #    elems -= 1
    return nodes, elems


######### Support functions ####################################


def skipComments(fil):
    """Skip comments and blank lines on a tetgen file.

    Reads from a file until the first non-comment and non-empty line.
    Then returns the non-empty, non-comment line, stripped from possible
    trailing comments.
    Returns None if end of file is reached.
    """
    while True:
        line = fil.readline()
        if len(line) == 0:
            return None      # EOF
        line = stripLine(line)
        if len(line) > 0:
            return line         # non-comment line found


def stripLine(line):
    """Strip blanks, newline and comments from a line of text.

    """
    nc = line.find('#')
    if nc >= 0:
        line = line[:nc]  # strip comments
    return line.strip()  # strips blanks and end of line


def getInts(line, nint):
    """Read a number of ints from a line, adding zero for omitted values.

    line is a string with b;anks separated integer values.
    Returns a list of nint integers. The trailing ones are set to zero
    if the strings contains less values.
    """
    s = [int(i) for i in line.split()]
    if len(s) < nint:
        s.extend([0]*(nint-len(s)))
    return s


def addElem(elems, nrs, e, n, nplex):
    """Add an element to a collection."""
    if nplex not in elems:
        elems[nplex] = []
        nrs[nplex] = []
    elems[nplex].append(e)
    nrs[nplex].append(n)


def readNodesBlock(fil, npts, ndim, nattr, nbmark):
    """Read a tetgen nodes block.

    Returns a tuple with:

    - coords: Coords array with nodal coordinates
    - nrs: node numbers
    - attr: node attributes
    - bmrk: node boundary marker

    The last two may be None.
    """
    ndata = 1 + ndim + nattr + nbmark
    data = np.fromfile(fil, sep=' ', dtype=at.Float, count=npts*(ndata)).reshape(npts, ndata)
    nrs = data[:, 0].astype(np.int32)
    coords = Coords(data[:, 1:ndim+1])
    if nattr > 0:
        attr = data[:, 1+ndim:1+ndim+nattr].astype(np.int32)
    else:
        attr = None
    if nbmark == 1:
        bmark = data[:, -1].astype(np.int32)
    else:
        bmark = None
    return coords, nrs, attr, bmark


def readElemsBlock(fil, nelems, nplex, nattr):
    """Read a tetgen elems block.

    Returns a tuple with:

    - elems: Connectivity of type 'tet4' or 'tet10'
    - nrs: the element numbers
    - attr: the element attributes

    The last can be None.
    """
    ndata = 1 + nplex + nattr
    data = np.fromfile(fil, sep=' ', dtype=np.int32, count=ndata*nelems).reshape(nelems, ndata)
    nrs = data[:, 0]
    elems = data[:, 1:1+nplex]
    if nattr > 0:
        attr = data[:, 1+nplex:]
    else:
        attr = None
    if nplex == 4:
        eltype = 'tet4'
    elif nplex == 10:
        eltype= 'tet10'
    else:
        raise ValueError("Unknown tetgen .ele plexitude %s" % nplex)
    elems = Connectivity(elems, eltype=eltype)
    return elems, nrs, attr


def readFacesBlock(fil, nelems, nbmark):
    """Read a tetgen faces block.

    Returns a a tuple with:

    - elems: Connectivity of type 'tri3'
    - nrs: face numbers
    - bmrk: face boundary marker

    The last can be None.
    """
    ndata = 1 + 3 + nbmark
    data = np.fromfile(fil, sep=' ', dtype=np.int32, count=ndata*nelems).reshape(nelems, ndata)
    nrs = data[:, 0]
    elems = data[:, 1:4]
    if nbmark == 1:
        bmark = data[:, -1]
    else:
        bmark = None
    return Connectivity(elems, eltype='tri3'), nrs, bmark


def readSmeshFacetsBlock(fil, nfacets, nbmark):
    """Read a tetgen .smesh facets bock.

    Returns a tuple of dictionaries with plexitudes as keys:

    - elems: for each plexitude a Connectivity array
    - nrs: for each plexitude a list of element numbers in corresponding elems

    """
    elems = {}
    nrs = {}
    for i in range(nfacets):
        line = fil.readline()
        line = line.strip()
        if len(line) > 0:
            data = np.fromstring(line, sep=' ', dtype=np.int32)
            nplex = data[0]
            if nplex > 0:
                e = data[1:1+nplex]
                # bmark currently not read
                addElem(elems, nrs, e, i, nplex)
            else:
                raise ValueError("Invalid data line:\n%s" % line)

    for nplex in elems:
        if nplex == 3:
            eltype= 'tri3'
        elif nplex == 4:
            eltype = 'quad4'
        else:
            eltype = None
        elems[nplex] = Connectivity(elems[np], eltype=eltype)
        nrs[nplex] = np.array(nrs[np])
    return elems, nrs


def readNeigh(fn):
    """Read a tetgen .neigh file.

    Returns an array containing the tetrahedra neighbours:
    """
    fil = open(fn, 'r')
    line = fil.readline()
    nelems, nneigh = [int(i) for i in line.strip('\n').split()]
    elems = np.fromfile(fil, sep=' ', dtype=np.int32).reshape((nelems, nneigh+1))
    return elems[:, 1:]


def writeNodes(fn, coords, offset=0):
    """Write a tetgen .node file"""
    coords = np.asarray(coords).reshape((-1, 3))
    with open(fn, 'w') as fil:
        fil.write("%d %d 0 0\n" % coords.shape)
        writeIData(fil, coords, fmt="%f ", ind=offset)


def writeSmesh(fn, facets, coords=None, holes=None, regions=None):
    """Write a tetgen .smesh file.

    Currently it only writes the facets of a triangular surface mesh.
    Coords should be written independently to a .node file.
    """
    with open(fn, 'w') as fil:
        fil.write("# part 1: node list.\n")
        if coords is None:
            fil.write("0  3  0  0  # coords are found in %s.node.\n")
        fil.write("# part 2: facet list.\n")
        fil.write("%s 0\n" % facets.shape[0])
        for i, n in enumerate(facets):
            # adding comments breaks fast readback
            # fil.write("3 %s %s %s # %s\n" % (n[0],n[1],n[2],i))
            fil.write("3 %s %s %s\n" % (n[0], n[1], n[2]))
        fil.write("# part 3: hole list.\n")
        if holes is None:
            fil.write("0\n")
        fil.write("# part 4: region list.\n")
        if regions is None:
            fil.write("0\n")
        fil.write("# Generated by pyFormex\n")


def writeTmesh(fn, elems, offset=0):
    """Write a tetgen .ele file.

    Writes elements of a tet4 mesh.
    """
    elems = asarray(elems).reshape((-1, 4))
    with open(fn, 'w') as fil:
        fil.write("%d %d 0\n" % elems.shape)
        for i, e in  enumerate(elems):
            fil.write('%d %d %d %d %d\n'%(i, e[0], e[1], e[2], e[3]))
        fil.write("# Generated by pyFormex\n")


def writeSurface(fn, coords, elems):
    """Write a tetgen surface model to .node and .smesh files.

    Parameters
    ----------
    fn: :term:`path_like`
        Filename of the files to which the model sohould be exported.
        The provided file name is either the .node or the .smesh filename,
        or else it is the basename where .node and .smesh extensions will
        be appended.
    coords: Coords
        The vertices in the surface model.
    elems: array
        The element definitions in function of the vertex numbers.
    """
    fn = Path(fn)
    writeNodes(fn.with_suffix('.node'), coords)
    writeSmesh(fn.with_suffix('.smesh'), elems)


def writeTetMesh(fn, coords, elems):
    """Write a tetgen tetrahedral mesh model to .node and .ele files.

    The provided file name is either the .node or the .smesh filename,
    or else it is the basename where .node and .ele extensions will
    be appended.
    """
    fn = Path(fn)
    writeNodes(fn.with_suffix('.node'), coords)
    writeTmesh(fn.with_suffix('.ele'), elems)


def runTetgen(fn, options=''):
    """Run tetgen mesher on the specified file.

    The input file is a closed triangulated surface.
    tetgen will generate a volume tetraeder mesh inside the surface,
    and create a new approximation of the surface as a by-product.
    """
    if not utils.External.has('tetgen'):
        pf.warning("""..

I could not find the 'tetgen' command.

tetgen is a quality tetrahedral mesh generator and a 3D Delaunay triangulator. See http://tetgen.org. It is available from the Debian non-free section.
""")
        return

    if Path(fn).exists():
        P = utils.command('tetgen -z%s %s' % (options, fn))
        return P


def readTetgen(fn):
    """Read a tetgen model.

    This reads a file created by the 'tetgen' tetrahedral mesher
    and returns corresponding pyFormex objects.

    Parameters
    ----------
    fn: :term:`path_like`
        Path to a tetgen file. This can be one of .node, .ele, .face,
        .smesh or .poly files.

    Returns
    -------
    dict
        If the suffix of ``fn`` is one of .node, .ele or .face, the dict
        contains one item with key 'tetgen.SUFFIX'. For suffix .node, the
        value is a Coords read from the .node file, for suffix .ele or .face,
        the value is a Mesh with elems read from the .ele or .face, and coords
        read from the corresponding .node. If the suffix is .smesh or .poly,
        the dict contains a number of Meshes, with keys 'Mesh-NPLEX' where
        NPLEX is the plexitude of the corresponding Mesh.

    """
    res = {}
    fn = Path(fn)
    ext = fn.suffix
    if ext == '.node':
        nodes = readNodeFile(fn)[0]
        res['tetgen'+ext] = nodes
    elif ext in ['.ele', '.face']:
        nodes, nodenrs = readNodeFile(fn.with_suffix('.node'))[:2]
        if ext == '.ele':
            elems = readEleFile(fn)[0]
        elif ext == '.face':
            elems = readFaceFile(fn)[0]
        if nodenrs.min() == 1 and nodenrs.max()==nodenrs.size:
            elems = elems-1
        M = Mesh(nodes, elems, eltype=elems.eltype)
        res['tetgen'+ext] = M

    elif ext == '.smesh':
        nodes, elems = readSmeshFile(fn)
        ML = [Mesh(nodes, elems[e]) for e in elems]
        res = dict([('Mesh-%s'%M.nplex(), M) for M in ML])

    elif ext == '.poly':
        nodes, elems = readPolyFile(fn)
        ML = [Mesh(nodes, elems[e]) for e in elems]
        res = dict([('Mesh-%s'%M.nplex(), M) for M in ML])

    return res


#
#  TODO: This should just be merged with tetMesh
#
#    This could be made an example:
#
#    from pyformex.simple import regularGrid
#    X = Coords(regularGrid([0., 0., 0.], [1., 1., 1.], [10, 10, 10]).reshape(-1, 3)).addNoise(rsize=0.05,asize=0.5)
#    draw(X)
#    from pyformex.plugins.tetgen import tetgenConvexHull
#    tch, ch =tetgenConvexHull( X)
#    draw(ch, color='red', marksize=10)

def tetgenConvexHull(pts):
    """Tetralize the convex hull of some points.

    Parameters
    ----------
    pts: Coords
        A collection of points to find the convex hull of.

    Returns
    -------
    convexhull: TriSurface
        The smallest TriSurface enclosing all the points.
    tetmesh: Mesh
        A tetraeder Mesh filling the convex hull.

    If all points are on the same plane there is no convex hull.

    """
    with utils.TempDir() as tmpdir:
        fn = tmpdir / 'convexhull.node'
        writeNodes(fn, coords=pts, offset=0)
        P = utils.command('tetgen %s' % fn)
        if P.returncode:
            print(P.stdout)
            raise RuntimeError("Error occurred in tetgen command")
        tetmesh = readTetgen(fn.with_suffix('.1.ele'))['tetgen.ele']
        convexhull = TriSurface(tetmesh.getBorderMesh())
        return convexhull, tetmesh


#################################################################
## Extra TriSurface Methods ##

def checkSelfIntersectionsWithTetgen(self, verbose=False):
    """check self intersections using tetgen

    Returns pairs of intersecting triangles
    """
    with utils.TempDir() as tmpdir:
        fn = tmpdir / 'surface'
        writeSurface(fn, self.coords, self.elems)
        options = '-V' if verbose else ''
        cmd = "tetgen -d %s %s" % (options, fn)
        P = utils.command(cmd)
        print(P.stdout)
        return asarray([int(l.split(' ')[0]) for l in P.stdout.split('acet #')[1:]]).reshape(-1, 2)-1


def tetMesh(surfacefile, quality=2.0, volume=None, outputdir=None):
    """Create a tetrahedral mesh inside a surface

    This uses the external program 'tetgen' to create a tetrahedral mesh
    inside a closed manifold surface.

    Parameters
    ----------
    surfacefile: :term:`path_like`
        Path to a file holding a surface model. The file can be either a .off
        or .stl.
    quality: float
        The quality of the output tetrahedral mesh. The value is a
        constraint on the circumradius-to-shortest-edge ratio. The
        default (2.0) already provides a high quality mesh. Providing
        a larger value will reduce quality but increase speed. With
        quality=None, no quality constraint will be imposed.
    volume: float, optional
        If provided, applies a maximum tetrahedron volume constraint.
    outputdir: :term:`path_like`
        Path to an existing directory where the results will be placed.
        The default is to use the directory where the input file resides.

    Returns
    -------
    Mesh
        A tetrahedral Mesh (eltype='tet4') filling the input surface,
        provided the tetgen program finished successfully.
    """
    options = ''
    if quality is True:
        options += 'q'
    elif isinstance(quality, float):
        options += 'q%f' % quality
    if volume is not None:
        options += 'a%f' % volume
    surfacefile = Path(surfacefile)
    if not surfacefile.exists() or \
       surfacefile.suffix not in ['.off', '.stl']:
        raise ValueError("Invalid surfacefile %s" % surfacefile)
    if outputdir is None:
        outputdir = surfacefile.parent
    else:
        outputdir = Path(outputdir)
        surfacefile.symlink(outputdir)
        surfacefile = outputdir / surfacefile.name
    runTetgen(surfacefile, options)
    tetfile = surfacefile.with_suffix('.1.ele')
    res = readTetgen(tetfile)
    return res


def install_more_trisurface_methods():
    """_

    """
    from pyformex.trisurface import TriSurface
    TriSurface.checkSelfIntersectionsWithTetgen = checkSelfIntersectionsWithTetgen


# End
