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

"""Centerline.py

Determine the (inner) voronoi diagram of a triangulated surface.
Determine approximation for the centerline.
"""

import numpy as np

import pyformex as pf
from pyformex import arraytools as at
from pyformex import Path
from pyformex import utils
from pyformex.trisurface import TriSurface
from pyformex.coords import Coords
from pyformex.connectivity import Connectivity
from pyformex.plugins import tetgen


def circumcenter(nodes, elems):
    """Calculate the circumcenters of a list of tetrahedrons.

    For a description of the method: http://mathworld.wolfram.com/Circumsphere.html
    The output are the circumcenters and the corresponding radii.
    """
    kwadSum = (nodes*nodes).sum(axis=-1)
    one = np.zeros(nodes.shape[0])+1
    nodesOne = np.append(nodes, one.reshape(-1, 1), 1)
    nodesKwadOne = np.append(kwadSum.reshape(-1, 1), nodesOne, 1)
    #construct necessary 4 by 4 arrays
    Wx = nodesKwadOne[:, [0, 2, 3, 4]]
    Wy = nodesKwadOne[:, [0, 1, 3, 4]]
    Wz = nodesKwadOne[:, [0, 1, 2, 4]]
    #calculate derminants of the 4 by 4 arrays
    Dx = at.det4(Wx[elems])
    Dy = -at.det4(Wy[elems])
    Dz = at.det4(Wz[elems])
    alfa = at.det4(nodesOne[elems[:]])
    #circumcenters
    centers = np.column_stack([Dx[:]/(2*alfa[:]), Dy[:]/(2*alfa[:]), Dz[:]/(2*alfa[:])])
    #calculate radii of the circumscribed spheres
    vec = centers[:]-nodes[elems[:, 0]]
    radii = np.sqrt((vec*vec).sum(axis=-1))
    return centers, radii

## Voronoi: vor diagram is determined using Tetgen. Some of the vor nodes may fall outside the surface. This should be avoided as this may compromise the centerline determination. Therefore, we created a second definition to determine the inner voronoi diagram (voronoiInner).

def voronoi(fn):
    """Determine the voronoi diagram of a triangulated surface.

    fn is the file name of a surface, including the extension
    (.off, .stl, .gts, .neu or .smesh)
    The voronoi diagram is determined by Tetgen.
    The output are the voronoi nodes and the corresponding radii
    of the voronoi spheres.
    """
    fn = Path(fn)
    S = TriSurface.read(fn)
    ftype = fn.lsuffix
    if ftype != '.smesh':
        fn = fn.with_suffix('.smesh')
        S.write(fn)
    P = utils.command('tetgen -zpv %s' % fn)
    #information tetrahedra
    elems = tetgen.readEleFile(fn.with_suffix('.1.ele'))[0]
    nodes = tetgen.readNodeFile(fn.with_suffix('.1.node'))[0]
    #voronoi information
    nodesVor = tetgen.readNodeFile(fn.with_suffix('.1.v.node'))[0]
    #calculate the radii of the voronoi spheres
    vec = nodesVor[:]-nodes[elems[:, 0]]
    radii = np.sqrt((vec*vec).sum(axis=-1))
    return nodesVor, radii


def voronoiInner(fn):
    """Determine the inner voronoi diagram of a triangulated surface.

    fn is the file name of a surface, including the extension
    (.off, .stl, .gts, .neu or .smesh)
    The output are the voronoi nodes and the corresponding radii
    of the voronoi spheres.
    """
    fn = Path(fn)
    S = TriSurface.read(fn)
    ftype = fn.lsuffix
    if ftype != '.smesh':
        fn = fn.with_suffix('.smesh')
        S.write(fn)
    P = utils.command('tetgen -zp %s' % fn)
    #information tetrahedra
    elems = tetgen.readEleFile(fn.with_suffix('.1.ele'))[0]
    nodes = tetgen.readNodeFile(fn.with_suffix('.1.node'))[0]
    #calculate surface normal for each point
    elemsS = np.array(S.elems)
    NT = S.normals()
    NP = np.zeros([nodes.shape[0], 3])
    for i in [0, 1, 2]:
        NP[elemsS[:, i]] = NT
    #calculate centrum circumsphere of each tetrahedron
    centers = circumcenter(nodes, elems)[0]
    #check if circumcenter falls within the geomety described by the surface
    ie = np.column_stack([((nodes[elems[:, j]] - centers[:])*NP[elems[:, j]]).sum(axis=-1) for j in [0, 1, 2, 3]])
    ie = ie[:, :]>=0
    w = np.where(ie.all(1))[0]
    elemsInner = elems[w]
    nodesVorInner = centers[w]
    #calculate the radii of the voronoi spheres
    vec = nodesVorInner[:]-nodes[elemsInner[:, 0]]
    radii = np.sqrt((vec*vec).sum(axis=-1))
    return nodesVorInner, radii


def selectMaxVor(nodesVor, radii, r1=1., r2=2., q=0.7, maxruns=-1):
    """Select the local maxima of the voronoi spheres.

    Description of the procedure:
    1) The largest voronoi sphere in the record is selected (voronoi node N and radius R).
    2) All the voronoi nodes laying within a cube all deleted from the record.
    This cube is defined by:
        a) the centrum of the cube N.
        b) the edge length which is 2*r1*R.
    3) Some voronoi nodes laying within a 2nd, larger cube are also deleted.
    This is when their corresponding radius is smaller than q times R.
    This cube is defined by:
        a) the centrum of the cube N.
        b) the edge length which is 2*r2*R.
    4) These three operations are repeated until all nodes are deleted.
    """
    nodesCent = np.array([])
    radCent = np.array([])
    run = 0
    while nodesVor.shape[0] and (maxruns < 0 or run < maxruns):
        #find maximum voronoi sphere in the record
        w = np.where(radii[:] == radii[:].max())[0]
        maxR = radii[w].reshape(-1)
        maxP = nodesVor[w].reshape(-1)
        #remove all the nodes within the first cube
        t1 =  (nodesVor[:] > (maxP-r1*maxR)).all(axis=1)
        t2 =  (nodesVor[:] < (maxP+r1*maxR)).all(axis=1)
        ttot1 = t1*t2
        radii = radii[~ttot1]
        nodesVor = nodesVor[~ttot1]
        #remove some of the nodes within the second cube
        t3 =  (nodesVor[:] > (maxP-r2*maxR)).all(axis=1)
        t4 =  (nodesVor[:] < (maxP+r2*maxR)).all(axis=1)
        t5 = (radii<maxR*q)
        ttot2 = t3*t4*t5
        if ttot2.shape[0]:
            radii = radii[~ttot2]
            nodesVor = nodesVor[~ttot2]
        #add local maximum to a list
        nodesCent = np.append(nodesCent, maxP)
        radCent = np.append(radCent, maxR)
        run += 1
    return nodesCent.reshape(-1, 1, 3), radCent


def connectVorNodes(nodes, radii):
    """Create connections between the voronoi nodes.

    Each of the nodes is connected with its closest neighbours.
    The input is an array of n nodes and an array of n corresponding radii.
    Two voronoi nodes are connected if the distance between these two nodes
    is smaller than the sum of their corresponding radii.
    The output is an array containing the connectivity information.
    """
    connections = np.array([]).astype(int)
    v = 4
    for i in range(nodes.shape[0]):
        t1 = (nodes[:] > (nodes[i]-v*radii[i])).all(axis=2)
        t2 = (nodes[:] < (nodes[i]+v*radii[i])).all(axis=2)
        t = t1*t2
        t[i] = False
        w1 = np.where(t == 1)[0]
        c = Coords(nodes[w1])
        d =c.distanceFromPoint(nodes[i]).reshape(-1)
        w2 = d < radii[w1] + radii[i]
        w = w1[w2]
        for j in w:
            connections = np.append(connections, i)
            connections = np.append(connections, j)
    connections = Connectivity(connections.reshape(-1, 2), eltype='line2')
    return connections.removeDuplicate()


def removeTriangles(elems):
    """Remove the triangles from the centerline.

    This is a clean-up function for the centerline.
    Triangles appearing in the centerline are removed by this function.
    Both input and output are the connectivity of the centerline.
    """
    rev = Connectivity(elems).inverse(expand=True)
    if rev.shape[1] > 2:
        w = np.where(rev[:, -3] != -1)[0]
        for i in w:
            el = rev[i].compress(rev[i] != -1)
            u = np.unique(elems[el].reshape(-1))
            NB = u.compress(u != i)
            inter = np.intersect1d(w, NB)
            if inter.shape[0] == 2:
                tri = np.append(inter, i)
                w1 = np.where(tri != tri.min())[0]
                t = (elems[:, 0] == tri[w1[0]])*(elems[:, 1] == tri[w1[1]])
                elems[t] = -1
    w2 = np.where(elems[:, 0] != -1)[0]
    return elems[w2]


def centerline(fn):
    """Determine an approximated centerline corresponding with a triangulated surface.

    fn is the file name of a surface, including the extension (.off, .stl, .gts, .neu or .smesh)
    The output are the centerline nodes, an array containing the connectivity information
    and radii of the voronoi spheres.
    """
    nodesVor, radii = voronoiInner('%s' %fn)
    nodesC, radii = selectMaxVor(nodesVor, radii)
    elemsC = connectVorNodes(nodesC, radii)
    elemsC = removeTriangles(elemsC)
    return nodesC, elemsC, radii

# End
