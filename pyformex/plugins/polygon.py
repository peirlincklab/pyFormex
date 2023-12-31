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

"""Polygonal facets.

"""
import numpy as np

import pyformex as pf
from pyformex.core import *
from pyformex.geometry import Geometry
from pyformex.curve import PolyLine
from pyformex.trisurface import TriSurface
from pyformex import utils

############################################################################

#
# TODO : this should be integrated with CoordSys
#
def projected(X, N):
    """Returns 2-D coordinates of a set of 3D coordinates.

    The returned 2D coordinates are still stored in a 3D Coords object.
    The last coordinate will however (approximately) be zero.
    """
    from pyformex.geomtools import rotationAngle
    if N is None:
        N = self.normal
    a, A = rotationAngle([0., 0., 1.], N)
    a, A = a[0], A[0]
    X = X.rotate(angle=-a, axis=A)
    C = X.center()
    X = X.translate(-C)
    return X, C, A, a


# TODO: replace with scipy delaunay/voronoi

## def delaunay(X):
##     """Return a Delaunay triangulation of the specified Coords.

##     While the Coords are 3d, only the first 2 components are used.

##     Returns a TriSurface with the Delaunay triangulation in the x-y plane.
##     """
##     from voronoi import voronoi
##     return TriSurface(X, voronoi(X[:, :2]).triangles)

# TODO: Use PolyLine to represent coords?
# TODO: Subclass from PolyLine? : and block opening the curve

class Polygon(Geometry):
    """A Polygon is a flat surface bounded by a closed PolyLine.

    The border is specified as a Coords object with shape (nvertex,3)
    specifying the vertex coordinates in order.
    While the Coords are 3d, only the first 2 components are used.
    """

    def __init__(self, border, normal=2, holes=[]):
        """Initialize a Polygon instance"""
        Geometry.__init__(self)
        self.prop = None
        self.coords = border.reshape(-1, 3)

    # implement abstractmethods
    def nelems(self):
        return 1
    def _select(self, sel, compact=False):
        return self


    def npoints(self):
        """Return the number of points and edges."""
        return self.coords.shape[0]


    def vectors(self):
        """Return the vectors from each point to the next one."""
        x = self.coords
        return np.roll(x, -1, axis=0) - x


    def angles(self):
        """Return the angles of the line segments with the x-axis."""
        v = self.vectors()
        return at.arctand2(v[:, 1], v[:, 0])


    def externalAngles(self):
        """Return the angles between subsequent line segments.

        The returned angles are the change in direction between the segment
        ending at the vertex and the segment leaving.
        The angles are given in degrees, in the range ]-180,180].
        The sum of the external angles is always (a multiple of) 360.
        A convex polygon has all angles of the same sign.
        """
        a = self.angles()
        va =  a - np.roll(a, 1)
        va[va <= -180.] += 360.
        va[va > 180.] -= 360.
        return va


    def isConvex(self):
        """Check if the polygon is convex and turning anticlockwise.

        Returns:

        - +1 if the Polygon is convex and turning anticlockwise,
        - -1 if the Polygon is convex, but turning clockwise,
        - 0 if the Polygon is not convex.
        """
        return int(sign(self.externalAngles()).sum()) / self.npoints()


    def internalAngles(self):
        """Return the internal angles.

        The returned angles are those between the two line segments at
        each vertex.
        The angles are given in degrees, in the range ]-180,180].
        These angles are the complement of the
        """
        return 180.-self.externalAngles()


    def reverse(self):
        """Return the Polygon with reversed order of vertices."""
        return Polygon(Coords(at.reverseAxis(self.coords, 0)))


    def fill(self):
        """Fill the surface inside the polygon with triangles.

        Returns a TriSurface filling the surface inside the polygon.
        """
        #print("AREA(self) %s" % self.area())
        # creating elems array at once (more efficient than appending)
        #from pyformex.gui.draw import draw, pause, undraw, drawNumbers
        from pyformex.geomtools import insideTriangle
        x = self.coords
        n = x.shape[0]
        tri = -np.ones((n-2, 3), dtype=at.Int)
        # compute all internal angles
        e = np.arange(x.shape[0])
        c = self.internalAngles()
        # loop in order of smallest angles
        itri = 0
        #draw(x)
        #drawNumbers(x)
        while n > 3:
            #print("ANGLES",c)
            # try minimal angle
            srt = c.argsort()
            for j in srt:
                #print("ANGLE: %s" % c[j])
                if c[j] > 180.:
                    print("OOPS, I GOT STUCK!\nMaybe the curve is self-intersecting?")
                    #print("Remaining points: %s" % e)
                    #raise
                    #
                    # We could return here also the remaining part
                    #
                    return TriSurface(x, tri[:itri])
                i = (j - 1) % n
                k = (j + 1) % n
                newtri = [e[i], e[j], e[k]]
                # remove the point j of triangle i,j,k
                # recompute adjacent angles of edge i,k
                ii = (i-1) % n
                kk = (k+1) % n
                iq = e[[ii, i, k, kk]]
                PQ = Polygon(x[iq])
                cn = PQ.internalAngles()
                cnew = cn[1:3]
                reme = np.roll(e, -j)[2:-1]
                T = x[newtri].reshape(1, 3, 3)
                P = x[reme].reshape(1, -1, 3)
                check = insideTriangle(T, P)
                if not check.any():
                    # Triangle is ok
                    break
            #draw(TriSurface(x,newtri),bbox='last',color='red')
            # accept new triangle
            tri[itri] = newtri
            c = np.roll(np.concatenate([cnew, np.roll(c, 1-j)[3:]]), j-1)
            e = np.roll(np.roll(e, -j)[1:], j)
            n -= 1
            itri += 1
        tri[itri] = e
        return TriSurface(x, tri)


    def area(self):
        """Compute area inside a polygon.

        """
        from pyformex.plugins.section2d import PlaneSection
        return PlaneSection(Formex(self.coords)).sectionChar()['A']


    def toMesh(self):
        from pyformex.mesh import Mesh
        a = np.arange(self.coords.shape[0])
        e = np.column_stack([a, np.roll(a, -1)])
        return Mesh(self.coords, e)


    def toFormex(self):
        from pyformex.formex import Formex
        x = np.stack([self.coords, np.roll(self.coords, -1, axis=0)], axis=1)
        return Formex(x)



if __name__ == '__draw__':

    def randomPL(n=5, r=0.7, noise=0.0):
        x = at.randomNoise((n), r*3., 3.)
        y = sorted(at.randomNoise((n), 0., 360.))
        #y = y[::-1] # reverse
        z = np.zeros(n)
        X = Coords(np.column_stack([x, y, z])).cylindrical().addNoise(noise)
        return PolyLine(X, closed=True)

    def readPL(n=5, r=0.7, noise=0.0):
        fn = askFilename()
        if not fn:
            return None
        G = fileread.readPGF(fn)
        return G.values()[0]


    def run():
        from pyformex.trisurface import fillBorder
        clear()

        ## layout(3,2)
        ## for i in range(2):
        ##     viewport(i)
        ##     clear()
        ##     smoothwire()

        ans = ask("Read curve or create random?", ["Read", "Random", "Cancel"])

        PL = None
        if ans == "Random":
            PL = randomPL(n=5, r=0.7, noise=0.0)
        elif ans == "Read":
            PL = readPL()

        if PL is None:
            return

        PG = Polygon(PL.coords).reverse()
        X = PG.coords
        #drawNumbers(X)
        draw(PL, color=cyan, linewidth=3)

        v = at.normalize(PG.vectors())
        #drawVectors(PG.coords,v,color=red,linewidth=2)

        a = PG.angles()
        ae = PG.externalAngles()
        ai = PG.internalAngles()

        print("Direction angles:", a)
        print("External angles:", ae)
        print("Internal angles:", ai)

        print("Sum of external angles: ", ae.sum())
        print("The polygon is convex: %s" % PG.isConvex())

        ## viewport(2)
        S = PG.fill()
        draw(S, color=red)
        #drawNumbers(S)
        drawText(S.check(), (100, 20))

    run()

# End
