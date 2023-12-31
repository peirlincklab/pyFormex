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
#
"""Python equivalents of the functions in :mod:`lib.misc_c`

The functions in this module should be exact emulations of the
external functions in the compiled library.
"""

# There should be no other imports here than numpy and pyformex
import pyformex as pf
import numpy as np

__version__ = pf.__version__
_accelerated = False


def coordsfuse(x, val, flag, sel, tol):
    """Fusing nodes.

    This is a low level function performing the internal loop of
    the fuse operation. It is not intended to be called by the user.
    """
    nnod = val.shape[0]
    nexti = 1
    for i in range(1, nnod):
        j = i-1
        while j>=0 and val[i]==val[j]:
            if abs(x[i]-x[j]).max() < tol:
                # node i is same as previous node j
                flag[i] = 0
                sel[i] = sel[j]
                break
            j = j-1
        if flag[i]:
            # node i is a new node
            sel[i] = nexti
            nexti += 1


def nodalsum(val, elems, nnod):
    """Compute the nodal sum of values defined on elements.

    Parameters:

    - `val`   : float (nelems,nplex,nval): nval values at nplex nodes
      of nelems elements.
    - `elems` : int (nelems,nplex): node indices of the elements.
    - `nnod`  : int: the number of nodes. Should be higher than the maxnod,
      the highest node number in elems. If negative, will be set to
      maxnod+1.

    Returns a tuple of two arrays:

    - `sum`: float: (nnod, nval): sum of all the values at same node
    - `cnt`: int: (nnod): number of values summed at each node

    """
    if nnod < 0:
        nnod = elems.max() + 1

    # create return arrays
    nval = val.shape[2]
    sum = np.zeros((nnod, nval), dtype=np.float32)
    cnt = np.zeros((nnod,), dtype=np.int32)

    for i, elem in enumerate(elems):
        for j, node in enumerate(elem):
            sum[node] += val[i, j].reshape(nval)
            cnt[node] += 1

    return sum, cnt


########## isoline #############################################

from pyformex import olist

linetable = (
    (), (0, 3), (0, 1), (1, 3), (1, 2), (0, 1, 2, 3), (0, 2), (2, 3),
    (2, 3), (0, 2), (0, 3, 1, 2), (1, 2), (1, 3), (0, 1), (0, 3), (),
    )

vertextable = [
    [0, 1],
    [1, 2],
    [2, 3],
    [3, 0],
    ]

def splitSquare(pos, val, level):
    """Split a single square

    """
    pos = pos.astype(np.float32)

    # Determine the index into the edge table which
    # tells us which vertices are inside of the surface

    cubeindex = 0
    for i in range(4):
        if val[i] >= level:
            cubeindex |= 1 << i

    # Find the vertices where the surface intersects the cube
    vertlist = []

    for edges in olist.group(linetable[cubeindex], 2):
        print("edges: %s" % str(edges))
        for e in edges:
            verts = vertextable[e]
            p1, p2 = pos[verts]
            v1, v2 = val[verts]
            print("INTERPOL %s, %s, %s, %s" % (p1, p2, v1, v2))
            vert = vertexinterp(level, p1, p2, v1, v2)
            vertlist.append(vert)

    return vertlist


def isoline(data, level):
    """Create an isoline through data at given level.

    - `data`: (nx,ny) shaped array of data values at points with
      coordinates equal to their indices. This defines a 2D area
      [0,nx-1], [0,ny-1],
    - `level`: data value at which the isoline is to be constructed

    Returns an (nseg,2,2) array defining the segments of the isoline.
    The result may be empty (if level is outside the data range).
    """
    grid = np.array([
        [0, 0],
        [1, 0],
        [1, 1],
        [0, 1],
        ])
    segments=[]
    def addSegments(x, y):
        pos = grid + [x, y]
        val = data[pos[:, 1], pos[:, 0]]
        print("pos, val\n%s\n%s" % (pos, val))
        verts = splitSquare(pos, val, level)
        segments.extend(verts)
        return len(segments)

    [[addSegments(x, y)
        for x in range(data.shape[1]-1)]
      for y in range(data.shape[0]-1)]

    segments = np.asarray(segments).reshape(-1, 2, 2)
    return segments

########## isosurface #############################################

#  edgeTable[256].  It corresponds to the 2^8 possible combinations of
#  of the eight (n) vertices either existing inside or outside (2^n) of the
#  surface.  A vertex is inside of a surface if the value at that vertex is
#  less than that of the surface you are scanning for.  The table index is
#  constructed bitwise with bit 0 corresponding to vertex 0, bit 1 to vert
#  1.. bit 7 to vert 7.  The value in the table tells you which edges of
#  the table are intersected by the surface.  Once again bit 0 corresponds
#  to edge 0 and so on, up to edge 12.
#  Constructing the table simply consisted of having a program run thru
#  the 256 cases and setting the edge bit if the vertices at either end of
#  the edge had different values (one is inside while the other is out).
#  The purpose of the table is to speed up the scanning process.  Only the
#  edges whose bit's are set contain vertices of the surface.
#  Vertex 0 is on the bottom face, back edge, left side.
#  The progression of vertices is clockwise around the bottom face
#  and then clockwise around the top face of the cube.  Edge 0 goes from
#  vertex 0 to vertex 1, Edge 1 is from 2->3 and so on around clockwise to
#  vertex 0 again. Then Edge 4 to 7 make up the top face, 4->5, 5->6, 6->7
#  and 7->4.  Edge 8 thru 11 are the vertical edges from vert 0->4, 1->5,
#  2->6, and 3->7.
#      4--------5     *---4----*
#     /|       /|    /|       /|
#    / |      / |   7 |      5 |
#   /  |     /  |  /  8     /  9
#  7--------6   | *----6---*   |
#  |   |    |   | |   |    |   |
#  |   0----|---1 |   *---0|---*
#  |  /     |  /  11 /     10 /
#  | /      | /   | 3      | 1
#  |/       |/    |/       |/
#  3--------2     *---2----*

edgetable=(0x0, 0x109, 0x203, 0x30a, 0x406, 0x50f, 0x605, 0x70c,
           0x80c, 0x905, 0xa0f, 0xb06, 0xc0a, 0xd03, 0xe09, 0xf00,
           0x190, 0x99, 0x393, 0x29a, 0x596, 0x49f, 0x795, 0x69c,
           0x99c, 0x895, 0xb9f, 0xa96, 0xd9a, 0xc93, 0xf99, 0xe90,
           0x230, 0x339, 0x33, 0x13a, 0x636, 0x73f, 0x435, 0x53c,
           0xa3c, 0xb35, 0x83f, 0x936, 0xe3a, 0xf33, 0xc39, 0xd30,
           0x3a0, 0x2a9, 0x1a3, 0xaa, 0x7a6, 0x6af, 0x5a5, 0x4ac,
           0xbac, 0xaa5, 0x9af, 0x8a6, 0xfaa, 0xea3, 0xda9, 0xca0,
           0x460, 0x569, 0x663, 0x76a, 0x66, 0x16f, 0x265, 0x36c,
           0xc6c, 0xd65, 0xe6f, 0xf66, 0x86a, 0x963, 0xa69, 0xb60,
           0x5f0, 0x4f9, 0x7f3, 0x6fa, 0x1f6, 0xff, 0x3f5, 0x2fc,
           0xdfc, 0xcf5, 0xfff, 0xef6, 0x9fa, 0x8f3, 0xbf9, 0xaf0,
           0x650, 0x759, 0x453, 0x55a, 0x256, 0x35f, 0x55, 0x15c,
           0xe5c, 0xf55, 0xc5f, 0xd56, 0xa5a, 0xb53, 0x859, 0x950,
           0x7c0, 0x6c9, 0x5c3, 0x4ca, 0x3c6, 0x2cf, 0x1c5, 0xcc,
           0xfcc, 0xec5, 0xdcf, 0xcc6, 0xbca, 0xac3, 0x9c9, 0x8c0,
           0x8c0, 0x9c9, 0xac3, 0xbca, 0xcc6, 0xdcf, 0xec5, 0xfcc,
           0xcc, 0x1c5, 0x2cf, 0x3c6, 0x4ca, 0x5c3, 0x6c9, 0x7c0,
           0x950, 0x859, 0xb53, 0xa5a, 0xd56, 0xc5f, 0xf55, 0xe5c,
           0x15c, 0x55, 0x35f, 0x256, 0x55a, 0x453, 0x759, 0x650,
           0xaf0, 0xbf9, 0x8f3, 0x9fa, 0xef6, 0xfff, 0xcf5, 0xdfc,
           0x2fc, 0x3f5, 0xff, 0x1f6, 0x6fa, 0x7f3, 0x4f9, 0x5f0,
           0xb60, 0xa69, 0x963, 0x86a, 0xf66, 0xe6f, 0xd65, 0xc6c,
           0x36c, 0x265, 0x16f, 0x66, 0x76a, 0x663, 0x569, 0x460,
           0xca0, 0xda9, 0xea3, 0xfaa, 0x8a6, 0x9af, 0xaa5, 0xbac,
           0x4ac, 0x5a5, 0x6af, 0x7a6, 0xaa, 0x1a3, 0x2a9, 0x3a0,
           0xd30, 0xc39, 0xf33, 0xe3a, 0x936, 0x83f, 0xb35, 0xa3c,
           0x53c, 0x435, 0x73f, 0x636, 0x13a, 0x33, 0x339, 0x230,
           0xe90, 0xf99, 0xc93, 0xd9a, 0xa96, 0xb9f, 0x895, 0x99c,
           0x69c, 0x795, 0x49f, 0x596, 0x29a, 0x393, 0x99, 0x190,
           0xf00, 0xe09, 0xd03, 0xc0a, 0xb06, 0xa0f, 0x905, 0x80c,
           0x70c, 0x605, 0x50f, 0x406, 0x30a, 0x203, 0x109, 0x0)

#  int triTable[256][16] also corresponds to the 256 possible combinations
#  of vertices.
#  The [16] dimension of the table is again the list of edges of the cube
#  which are intersected by the surface.  This time however, the edges are
#  enumerated in the order of the vertices making up the triangle mesh of
#  the surface.  Each edge contains one vertex that is on the surface.
#  Each triple of edges listed in the table contains the vertices of one
#  triangle on the mesh.  The are 16 entries because it has been shown that
#  there are at most 5 triangles in a cube and each "edge triple" list is
#  terminated with the value -1.
#  For example triTable[3] contains
#  {1, 8, 3, 9, 8, 1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1}
#  This corresponds to the case of a cube whose vertex 0 and 1 are inside
#  of the surface and the rest of the verts are outside (00000001 bitwise
#  OR'ed with 00000010 makes 00000011 == 3).  Therefore, this cube is
#  intersected by the surface roughly in the form of a plane which cuts
#  edges 8,9,1 and 3.  This quadrilateral can be constructed from two
#  triangles: one which is made of the intersection vertices found on edges
#  1,8, and 3; the other is formed from the vertices on edges 9,8, and 1.
#  Remember, each intersected edge contains only one surface vertex.  The
#  vertex triples are listed in counter clockwise order for proper facing.

tritable = (
    (),
    (0, 8, 3),
    (0, 1, 9),
    (1, 8, 3, 9, 8, 1),
    (1, 2, 10),
    (0, 8, 3, 1, 2, 10),
    (9, 2, 10, 0, 2, 9),
    (2, 8, 3, 2, 10, 8, 10, 9, 8),
    (3, 11, 2),
    (0, 11, 2, 8, 11, 0),
    (1, 9, 0, 2, 3, 11),
    (1, 11, 2, 1, 9, 11, 9, 8, 11),
    (3, 10, 1, 11, 10, 3),
    (0, 10, 1, 0, 8, 10, 8, 11, 10),
    (3, 9, 0, 3, 11, 9, 11, 10, 9),
    (9, 8, 10, 10, 8, 11),
    (4, 7, 8),
    (4, 3, 0, 7, 3, 4),
    (0, 1, 9, 8, 4, 7),
    (4, 1, 9, 4, 7, 1, 7, 3, 1),
    (1, 2, 10, 8, 4, 7),
    (3, 4, 7, 3, 0, 4, 1, 2, 10),
    (9, 2, 10, 9, 0, 2, 8, 4, 7),
    (2, 10, 9, 2, 9, 7, 2, 7, 3, 7, 9, 4),
    (8, 4, 7, 3, 11, 2),
    (11, 4, 7, 11, 2, 4, 2, 0, 4),
    (9, 0, 1, 8, 4, 7, 2, 3, 11),
    (4, 7, 11, 9, 4, 11, 9, 11, 2, 9, 2, 1),
    (3, 10, 1, 3, 11, 10, 7, 8, 4),
    (1, 11, 10, 1, 4, 11, 1, 0, 4, 7, 11, 4),
    (4, 7, 8, 9, 0, 11, 9, 11, 10, 11, 0, 3),
    (4, 7, 11, 4, 11, 9, 9, 11, 10),
    (9, 5, 4),
    (9, 5, 4, 0, 8, 3),
    (0, 5, 4, 1, 5, 0),
    (8, 5, 4, 8, 3, 5, 3, 1, 5),
    (1, 2, 10, 9, 5, 4),
    (3, 0, 8, 1, 2, 10, 4, 9, 5),
    (5, 2, 10, 5, 4, 2, 4, 0, 2),
    (2, 10, 5, 3, 2, 5, 3, 5, 4, 3, 4, 8),
    (9, 5, 4, 2, 3, 11),
    (0, 11, 2, 0, 8, 11, 4, 9, 5),
    (0, 5, 4, 0, 1, 5, 2, 3, 11),
    (2, 1, 5, 2, 5, 8, 2, 8, 11, 4, 8, 5),
    (10, 3, 11, 10, 1, 3, 9, 5, 4),
    (4, 9, 5, 0, 8, 1, 8, 10, 1, 8, 11, 10),
    (5, 4, 0, 5, 0, 11, 5, 11, 10, 11, 0, 3),
    (5, 4, 8, 5, 8, 10, 10, 8, 11),
    (9, 7, 8, 5, 7, 9),
    (9, 3, 0, 9, 5, 3, 5, 7, 3),
    (0, 7, 8, 0, 1, 7, 1, 5, 7),
    (1, 5, 3, 3, 5, 7),
    (9, 7, 8, 9, 5, 7, 10, 1, 2),
    (10, 1, 2, 9, 5, 0, 5, 3, 0, 5, 7, 3),
    (8, 0, 2, 8, 2, 5, 8, 5, 7, 10, 5, 2),
    (2, 10, 5, 2, 5, 3, 3, 5, 7),
    (7, 9, 5, 7, 8, 9, 3, 11, 2),
    (9, 5, 7, 9, 7, 2, 9, 2, 0, 2, 7, 11),
    (2, 3, 11, 0, 1, 8, 1, 7, 8, 1, 5, 7),
    (11, 2, 1, 11, 1, 7, 7, 1, 5),
    (9, 5, 8, 8, 5, 7, 10, 1, 3, 10, 3, 11),
    (5, 7, 0, 5, 0, 9, 7, 11, 0, 1, 0, 10, 11, 10, 0),
    (11, 10, 0, 11, 0, 3, 10, 5, 0, 8, 0, 7, 5, 7, 0),
    (11, 10, 5, 7, 11, 5),
    (10, 6, 5),
    (0, 8, 3, 5, 10, 6),
    (9, 0, 1, 5, 10, 6),
    (1, 8, 3, 1, 9, 8, 5, 10, 6),
    (1, 6, 5, 2, 6, 1),
    (1, 6, 5, 1, 2, 6, 3, 0, 8),
    (9, 6, 5, 9, 0, 6, 0, 2, 6),
    (5, 9, 8, 5, 8, 2, 5, 2, 6, 3, 2, 8),
    (2, 3, 11, 10, 6, 5),
    (11, 0, 8, 11, 2, 0, 10, 6, 5),
    (0, 1, 9, 2, 3, 11, 5, 10, 6),
    (5, 10, 6, 1, 9, 2, 9, 11, 2, 9, 8, 11),
    (6, 3, 11, 6, 5, 3, 5, 1, 3),
    (0, 8, 11, 0, 11, 5, 0, 5, 1, 5, 11, 6),
    (3, 11, 6, 0, 3, 6, 0, 6, 5, 0, 5, 9),
    (6, 5, 9, 6, 9, 11, 11, 9, 8),
    (5, 10, 6, 4, 7, 8),
    (4, 3, 0, 4, 7, 3, 6, 5, 10),
    (1, 9, 0, 5, 10, 6, 8, 4, 7),
    (10, 6, 5, 1, 9, 7, 1, 7, 3, 7, 9, 4),
    (6, 1, 2, 6, 5, 1, 4, 7, 8),
    (1, 2, 5, 5, 2, 6, 3, 0, 4, 3, 4, 7),
    (8, 4, 7, 9, 0, 5, 0, 6, 5, 0, 2, 6),
    (7, 3, 9, 7, 9, 4, 3, 2, 9, 5, 9, 6, 2, 6, 9),
    (3, 11, 2, 7, 8, 4, 10, 6, 5),
    (5, 10, 6, 4, 7, 2, 4, 2, 0, 2, 7, 11),
    (0, 1, 9, 4, 7, 8, 2, 3, 11, 5, 10, 6),
    (9, 2, 1, 9, 11, 2, 9, 4, 11, 7, 11, 4, 5, 10, 6),
    (8, 4, 7, 3, 11, 5, 3, 5, 1, 5, 11, 6),
    (5, 1, 11, 5, 11, 6, 1, 0, 11, 7, 11, 4, 0, 4, 11),
    (0, 5, 9, 0, 6, 5, 0, 3, 6, 11, 6, 3, 8, 4, 7),
    (6, 5, 9, 6, 9, 11, 4, 7, 9, 7, 11, 9),
    (10, 4, 9, 6, 4, 10),
    (4, 10, 6, 4, 9, 10, 0, 8, 3),
    (10, 0, 1, 10, 6, 0, 6, 4, 0),
    (8, 3, 1, 8, 1, 6, 8, 6, 4, 6, 1, 10),
    (1, 4, 9, 1, 2, 4, 2, 6, 4),
    (3, 0, 8, 1, 2, 9, 2, 4, 9, 2, 6, 4),
    (0, 2, 4, 4, 2, 6),
    (8, 3, 2, 8, 2, 4, 4, 2, 6),
    (10, 4, 9, 10, 6, 4, 11, 2, 3),
    (0, 8, 2, 2, 8, 11, 4, 9, 10, 4, 10, 6),
    (3, 11, 2, 0, 1, 6, 0, 6, 4, 6, 1, 10),
    (6, 4, 1, 6, 1, 10, 4, 8, 1, 2, 1, 11, 8, 11, 1),
    (9, 6, 4, 9, 3, 6, 9, 1, 3, 11, 6, 3),
    (8, 11, 1, 8, 1, 0, 11, 6, 1, 9, 1, 4, 6, 4, 1),
    (3, 11, 6, 3, 6, 0, 0, 6, 4),
    (6, 4, 8, 11, 6, 8),
    (7, 10, 6, 7, 8, 10, 8, 9, 10),
    (0, 7, 3, 0, 10, 7, 0, 9, 10, 6, 7, 10),
    (10, 6, 7, 1, 10, 7, 1, 7, 8, 1, 8, 0),
    (10, 6, 7, 10, 7, 1, 1, 7, 3),
    (1, 2, 6, 1, 6, 8, 1, 8, 9, 8, 6, 7),
    (2, 6, 9, 2, 9, 1, 6, 7, 9, 0, 9, 3, 7, 3, 9),
    (7, 8, 0, 7, 0, 6, 6, 0, 2),
    (7, 3, 2, 6, 7, 2),
    (2, 3, 11, 10, 6, 8, 10, 8, 9, 8, 6, 7),
    (2, 0, 7, 2, 7, 11, 0, 9, 7, 6, 7, 10, 9, 10, 7),
    (1, 8, 0, 1, 7, 8, 1, 10, 7, 6, 7, 10, 2, 3, 11),
    (11, 2, 1, 11, 1, 7, 10, 6, 1, 6, 7, 1),
    (8, 9, 6, 8, 6, 7, 9, 1, 6, 11, 6, 3, 1, 3, 6),
    (0, 9, 1, 11, 6, 7),
    (7, 8, 0, 7, 0, 6, 3, 11, 0, 11, 6, 0),
    (7, 11, 6),
    (7, 6, 11),
    (3, 0, 8, 11, 7, 6),
    (0, 1, 9, 11, 7, 6),
    (8, 1, 9, 8, 3, 1, 11, 7, 6),
    (10, 1, 2, 6, 11, 7),
    (1, 2, 10, 3, 0, 8, 6, 11, 7),
    (2, 9, 0, 2, 10, 9, 6, 11, 7),
    (6, 11, 7, 2, 10, 3, 10, 8, 3, 10, 9, 8),
    (7, 2, 3, 6, 2, 7),
    (7, 0, 8, 7, 6, 0, 6, 2, 0),
    (2, 7, 6, 2, 3, 7, 0, 1, 9),
    (1, 6, 2, 1, 8, 6, 1, 9, 8, 8, 7, 6),
    (10, 7, 6, 10, 1, 7, 1, 3, 7),
    (10, 7, 6, 1, 7, 10, 1, 8, 7, 1, 0, 8),
    (0, 3, 7, 0, 7, 10, 0, 10, 9, 6, 10, 7),
    (7, 6, 10, 7, 10, 8, 8, 10, 9),
    (6, 8, 4, 11, 8, 6),
    (3, 6, 11, 3, 0, 6, 0, 4, 6),
    (8, 6, 11, 8, 4, 6, 9, 0, 1),
    (9, 4, 6, 9, 6, 3, 9, 3, 1, 11, 3, 6),
    (6, 8, 4, 6, 11, 8, 2, 10, 1),
    (1, 2, 10, 3, 0, 11, 0, 6, 11, 0, 4, 6),
    (4, 11, 8, 4, 6, 11, 0, 2, 9, 2, 10, 9),
    (10, 9, 3, 10, 3, 2, 9, 4, 3, 11, 3, 6, 4, 6, 3),
    (8, 2, 3, 8, 4, 2, 4, 6, 2),
    (0, 4, 2, 4, 6, 2),
    (1, 9, 0, 2, 3, 4, 2, 4, 6, 4, 3, 8),
    (1, 9, 4, 1, 4, 2, 2, 4, 6),
    (8, 1, 3, 8, 6, 1, 8, 4, 6, 6, 10, 1),
    (10, 1, 0, 10, 0, 6, 6, 0, 4),
    (4, 6, 3, 4, 3, 8, 6, 10, 3, 0, 3, 9, 10, 9, 3),
    (10, 9, 4, 6, 10, 4),
    (4, 9, 5, 7, 6, 11),
    (0, 8, 3, 4, 9, 5, 11, 7, 6),
    (5, 0, 1, 5, 4, 0, 7, 6, 11),
    (11, 7, 6, 8, 3, 4, 3, 5, 4, 3, 1, 5),
    (9, 5, 4, 10, 1, 2, 7, 6, 11),
    (6, 11, 7, 1, 2, 10, 0, 8, 3, 4, 9, 5),
    (7, 6, 11, 5, 4, 10, 4, 2, 10, 4, 0, 2),
    (3, 4, 8, 3, 5, 4, 3, 2, 5, 10, 5, 2, 11, 7, 6),
    (7, 2, 3, 7, 6, 2, 5, 4, 9),
    (9, 5, 4, 0, 8, 6, 0, 6, 2, 6, 8, 7),
    (3, 6, 2, 3, 7, 6, 1, 5, 0, 5, 4, 0),
    (6, 2, 8, 6, 8, 7, 2, 1, 8, 4, 8, 5, 1, 5, 8),
    (9, 5, 4, 10, 1, 6, 1, 7, 6, 1, 3, 7),
    (1, 6, 10, 1, 7, 6, 1, 0, 7, 8, 7, 0, 9, 5, 4),
    (4, 0, 10, 4, 10, 5, 0, 3, 10, 6, 10, 7, 3, 7, 10),
    (7, 6, 10, 7, 10, 8, 5, 4, 10, 4, 8, 10),
    (6, 9, 5, 6, 11, 9, 11, 8, 9),
    (3, 6, 11, 0, 6, 3, 0, 5, 6, 0, 9, 5),
    (0, 11, 8, 0, 5, 11, 0, 1, 5, 5, 6, 11),
    (6, 11, 3, 6, 3, 5, 5, 3, 1),
    (1, 2, 10, 9, 5, 11, 9, 11, 8, 11, 5, 6),
    (0, 11, 3, 0, 6, 11, 0, 9, 6, 5, 6, 9, 1, 2, 10),
    (11, 8, 5, 11, 5, 6, 8, 0, 5, 10, 5, 2, 0, 2, 5),
    (6, 11, 3, 6, 3, 5, 2, 10, 3, 10, 5, 3),
    (5, 8, 9, 5, 2, 8, 5, 6, 2, 3, 8, 2),
    (9, 5, 6, 9, 6, 0, 0, 6, 2),
    (1, 5, 8, 1, 8, 0, 5, 6, 8, 3, 8, 2, 6, 2, 8),
    (1, 5, 6, 2, 1, 6),
    (1, 3, 6, 1, 6, 10, 3, 8, 6, 5, 6, 9, 8, 9, 6),
    (10, 1, 0, 10, 0, 6, 9, 5, 0, 5, 6, 0),
    (0, 3, 8, 5, 6, 10),
    (10, 5, 6),
    (11, 5, 10, 7, 5, 11),
    (11, 5, 10, 11, 7, 5, 8, 3, 0),
    (5, 11, 7, 5, 10, 11, 1, 9, 0),
    (10, 7, 5, 10, 11, 7, 9, 8, 1, 8, 3, 1),
    (11, 1, 2, 11, 7, 1, 7, 5, 1),
    (0, 8, 3, 1, 2, 7, 1, 7, 5, 7, 2, 11),
    (9, 7, 5, 9, 2, 7, 9, 0, 2, 2, 11, 7),
    (7, 5, 2, 7, 2, 11, 5, 9, 2, 3, 2, 8, 9, 8, 2),
    (2, 5, 10, 2, 3, 5, 3, 7, 5),
    (8, 2, 0, 8, 5, 2, 8, 7, 5, 10, 2, 5),
    (9, 0, 1, 5, 10, 3, 5, 3, 7, 3, 10, 2),
    (9, 8, 2, 9, 2, 1, 8, 7, 2, 10, 2, 5, 7, 5, 2),
    (1, 3, 5, 3, 7, 5),
    (0, 8, 7, 0, 7, 1, 1, 7, 5),
    (9, 0, 3, 9, 3, 5, 5, 3, 7),
    (9, 8, 7, 5, 9, 7),
    (5, 8, 4, 5, 10, 8, 10, 11, 8),
    (5, 0, 4, 5, 11, 0, 5, 10, 11, 11, 3, 0),
    (0, 1, 9, 8, 4, 10, 8, 10, 11, 10, 4, 5),
    (10, 11, 4, 10, 4, 5, 11, 3, 4, 9, 4, 1, 3, 1, 4),
    (2, 5, 1, 2, 8, 5, 2, 11, 8, 4, 5, 8),
    (0, 4, 11, 0, 11, 3, 4, 5, 11, 2, 11, 1, 5, 1, 11),
    (0, 2, 5, 0, 5, 9, 2, 11, 5, 4, 5, 8, 11, 8, 5),
    (9, 4, 5, 2, 11, 3),
    (2, 5, 10, 3, 5, 2, 3, 4, 5, 3, 8, 4),
    (5, 10, 2, 5, 2, 4, 4, 2, 0),
    (3, 10, 2, 3, 5, 10, 3, 8, 5, 4, 5, 8, 0, 1, 9),
    (5, 10, 2, 5, 2, 4, 1, 9, 2, 9, 4, 2),
    (8, 4, 5, 8, 5, 3, 3, 5, 1),
    (0, 4, 5, 1, 0, 5),
    (8, 4, 5, 8, 5, 3, 9, 0, 5, 0, 3, 5),
    (9, 4, 5),
    (4, 11, 7, 4, 9, 11, 9, 10, 11),
    (0, 8, 3, 4, 9, 7, 9, 11, 7, 9, 10, 11),
    (1, 10, 11, 1, 11, 4, 1, 4, 0, 7, 4, 11),
    (3, 1, 4, 3, 4, 8, 1, 10, 4, 7, 4, 11, 10, 11, 4),
    (4, 11, 7, 9, 11, 4, 9, 2, 11, 9, 1, 2),
    (9, 7, 4, 9, 11, 7, 9, 1, 11, 2, 11, 1, 0, 8, 3),
    (11, 7, 4, 11, 4, 2, 2, 4, 0),
    (11, 7, 4, 11, 4, 2, 8, 3, 4, 3, 2, 4),
    (2, 9, 10, 2, 7, 9, 2, 3, 7, 7, 4, 9),
    (9, 10, 7, 9, 7, 4, 10, 2, 7, 8, 7, 0, 2, 0, 7),
    (3, 7, 10, 3, 10, 2, 7, 4, 10, 1, 10, 0, 4, 0, 10),
    (1, 10, 2, 8, 7, 4),
    (4, 9, 1, 4, 1, 7, 7, 1, 3),
    (4, 9, 1, 4, 1, 7, 0, 8, 1, 8, 7, 1),
    (4, 0, 3, 7, 4, 3),
    (4, 8, 7),
    (9, 10, 8, 10, 11, 8),
    (3, 0, 9, 3, 9, 11, 11, 9, 10),
    (0, 1, 10, 0, 10, 8, 8, 10, 11),
    (3, 1, 10, 11, 3, 10),
    (1, 2, 11, 1, 11, 9, 9, 11, 8),
    (3, 0, 9, 3, 9, 11, 1, 2, 9, 2, 11, 9),
    (0, 2, 11, 8, 0, 11),
    (3, 2, 11),
    (2, 3, 8, 2, 8, 10, 10, 8, 9),
    (9, 10, 2, 0, 9, 2),
    (2, 3, 8, 2, 8, 10, 0, 1, 8, 1, 10, 8),
    (1, 10, 2),
    (1, 3, 8, 9, 1, 8),
    (0, 9, 1),
    (0, 3, 8),
    (),
    )

def polygoniseCube(pos, val, level):
    """Polygonise a single cube

    """
    pos = pos.astype(np.float32)
    # Determine the index into the edge table which
    # tells us which vertices are inside of the surface

    # print(pos,val)

    cubeindex = 0
    for i in range(8):
        if val[i] < level:
            cubeindex |= 1 << i

    if edgetable[cubeindex] == 0:
        return []

    vertlist = np.zeros((12, 3))

    # Find the vertices where the surface intersects the cube
    edge_table = [
        [0, 1],
        [1, 2],
        [2, 3],
        [3, 0],
        [4, 5],
        [5, 6],
        [6, 7],
        [7, 4],
        [0, 4],
        [1, 5],
        [2, 6],
        [3, 7],
        ]

    for i, verts in enumerate(edge_table):
        if edgetable[cubeindex] & (1 << i):
            p1, p2 = pos[verts]
            val1, val2 = val[verts]
            vertlist[i] = vertexinterp(level, p1, p2, val1, val2)

    # Create the triangles
    tritab = tritable[cubeindex]
    triangles = [
        [vertlist[j] for j in tritab[i:i+3]]
        for i in range(0, len(tritab), 3)
        ]
    return triangles


def vertexinterp(level, p1, p2, val1, val2):
    """Interpolate between cube vertices

    Linearly interpolate the position where an isosurface cuts
    an edge between two vertices, each with their own scalar value

    p1,p2 are (3,) arrays, marking the cubes opposite corners (0 and 6)
    v1,v2 are values at these points
    level is the level value of the surface
    """
    if abs(level-val1) < 0.00001:
        return p1
    if abs(level-val2) < 0.00001:
        return p2
    if abs(val1-val2) < 0.00001:
        return p1
    mu = float(level - val1) / (val2 - val1)
    return p1 + mu * (p2-p1)


grid = np.array([
    [0, 0, 0],
    [1, 0, 0],
    [1, 1, 0],
    [0, 1, 0],
    [0, 0, 1],
    [1, 0, 1],
    [1, 1, 1],
    [0, 1, 1],
    ])

def isosurface(data, level, tet=False):
    """Create an isosurface through data at given level.

    Parameters
    ----------
    data: :term:`array_like`
        An (nx,ny,nz) shaped array of data values at points with
        coordinates equal to their indices. This defines a 3D volume
        [0,nx-1], [0,ny-1], [0,nz-1]
    level: float
        Data value at which the isosurface is to be constructed.

    Returns
    -------
    array
        An (ntr,3,3) array defining the triangles of the isosurface.
        The result is empty if level is outside the data range.

    See Also
    --------
    :func:`plugins.isosurface.isosurface`: a faster parallel version

    Notes
    -----
    This function was inspired by the example by Paul Bourke on
    http://paulbourke.net/geometry/polygonise/.

    Normally this function is invoked from the higer level function
    :func:`plugins.isosurface.isosurface`, which allows multiprocessing
    to further speed up the process.
    """
    if tet:
        raise ValueError(
            "Marching tetrahedrons has not been implemented yet "
            "in the emulation library. Use the acceleration library.")
    triangles=[]
    def addTriangles(x, y, z):
        pos = grid + [x, y, z]
        val = data[pos[:, 2], pos[:, 1], pos[:, 0]]
        # print("Values",pos,val)
        t = polygoniseCube(pos, val, level)
        triangles.extend(t)
        return len(triangles)

    [[[addTriangles(x, y, z)
          for x in range(data.shape[2]-1)]
        for y in range(data.shape[1]-1)]
      for z in range(data.shape[0]-1)]

    triangles = np.asarray(triangles).reshape(-1, 3, 3)
    return triangles


# End
