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
"""SplineSurfac

This example illustrates some advanced geometrical modeling tools using
spline curves and surfaces.

The script first creates a set of closed BezierSpline curves. Currently
two sets of curves are predefined:

- a set of transformations of a unit circle. The circle is scaled
  non-uniformously, resulting in an ellips, which is then rotated and
  translated.

- a set of curves obtained by cutting a triangulated surface model
  with a series of parallel planes. The original surface model was
  obtained from medical imaging processes and represents a human
  artery with a kink. These curves are read from a geometry file
  'splines.pgf' include in the pyFormex distribution.

In the first case, the number of curves will be equal to the specified
number.  In the latter case, the number can not be larger than the
number of curves in the file.

The set of splines are then used to create a QuadSurface (a surface
consisting of quadrilaterals). The number of elements along the
splines can be chosen. The number of elements across the splines is
currently unused.
"""

_level = 'advanced'
_topics = ['geometry', 'surface']
_techniques = ['spline']

from pyformex.gui.draw import *


##
## What follows here may become a 'NurbsSurface' plugin
##

"""Definition of surfaces in pyFormex.

This module defines classes and functions specialized for handling
two-dimensional geometry in pyFormex.
"""

import numpy as np
from pyformex import curve
from pyformex.geometry import Geometry


##############################################################################


def rollCurvePoints(curve, n=1):
    """Roll the points of a closed curve.

    Rolls the points of a curve forward over n positions. Thus point 0
    becomes point 1, etc. The function does not return a value. The
    curve is changed inplace.

    This only works for PolyLine and BezierSpline (and derived) classes.
    """
    if (isinstance(curve, PolyLine) or isinstance(curve, BezierSpline)) and curve.closed:
        if isinstance(curve, PolyLine):
            mult = 1
        else:
            mult = curve.degree
        curve.coords[:-1] = roll(curve.coords[:-1], -mult*n, axis=0)
        curve.coords[-1] = curve.coords[0]
    else:
        raise ValueError("Expected a closed PolyLine or BezierSpline.")


def alignCurvePoints(curve, axis=1, max=True):
    """Roll the points of a closed curved according to some rule.

    The points of a closed curve are rotated thus that the starting (and
    ending) point is the point with the maximum or minimum value of the
    specified coordinate.

    The function returns nothing: the points are rolled inplace.
    """
    if not curve.closed:
        raise ValueError("Expected a closed curve.")
    if max:
        ind = curve.pointsOn()[:, axis].argmax()
    else:
        ind = curve.pointsOn()[:, axis].argmin()
    rollCurvePoints(curve, ind)


class SplineSurface():
    """A surface created by a sequence of splines.

    The surface consists of a list of curves. The parametric value of
    the curves is called 'u', while 'v' is used for the parametric value
    across the splines.

    Two sets of parametric curves can be drawn: in u and in v direction.
    """

    def __init__(self, curves=None, nu=0, coords=None):
        self.curves = curves
        self.grid = None
        self.ccurves = None
        closed = [c.closed for c in self.curves]
        self.uclosed = sum(closed) > 0
        errors = [c.closed != self.uclosed for c in self.curves]
        if sum(errors) > 0:
            raise ValueError("Either ALL or NONE of the curves should be closed.")
        if nu <= 0:
            nu = len(curves)-1
        self.grid = self.createGrid(nu)


    def bbox(self):
        return bbox(self.curves)


    def createGrid(self, nu, nv=None):
        print("Creating grid %s x %s" % (nu, nv))
        if nv is None:
            nv = self.curves[0].nparts

        CA = [C.approx(nseg=nu) for C in self.curves]
        print("Curves have %s points" % CA[0].coords.shape[0])
        print("There are %s curves" % len(CA))
        if not self.uclosed:
            nu += 1
        grid = Coords(np.stack([CAi.coords[:nu] for CAi in CA]))
        print("Created grid %s x %s" % grid.shape[:2])
        return grid


    def vCurves(self):
        return [BezierSpline(self.grid[:, i, :], curl=0.375) for i in range(self.grid.shape[1])]


    def uCurves(self):
        return [BezierSpline(self.grid[i, :, :], curl=0.375) for i in range(self.grid.shape[0])]


    def approx(self, nu, nv):
        CL = self.vCurves()
        draw(CL, color=red)


    def actor(self, **kargs):
        return [draw(c, **kargs) for c in self.curves]


def gridToMesh(grid, closed=False):
    """Convert a Grid Surface to a Quad Mesh"""
    nu = grid.shape[1]
    nv = grid.shape[0] -1
    elems = np.array([[0, 1, nu+1, nu]])
    if closed:
        elems = np.concatenate([(elems+i) for i in range(nu-1)], axis=0)
        elems = np.concatenate([elems, [[nu-1, 0, nu, 2*nu-1]]], axis=0)
    else:
        #drawNumbers(self.grid.reshape(-1,3))
        #print elems
        elems = np.concatenate([(elems+i) for i in range(nu-1)], axis=0)
    #print elems
    #print nu
    elems = np.concatenate([(elems+i*nu) for i in range(nv)], axis=0)

    x = grid.reshape(-1, 3)
    #print nu,nv
    #print x.shape
    #print elems.shape
    #print elems.min(),elems.max()
    M = Mesh(grid.reshape(-1, 3), elems)
    #print M.elems
    #drawNumbers(M.coords)
    return M


def createCircles(n):
    """Create a set of BezierSpline curves.

    The curves are transformations of a unit circle.
    They are non-uniformously scaled to yield ellipses, and then rotated
    and translated.
    """
    C = curve.circle()
    t = np.arange(n+1) /float(n)
    CL = [C.scale([1., a, 0.]) for a in 0.5 + np.arange(n+1) /float(n)]
    CL = [Ci.rot(a, 2) for Ci, a in zip(CL, np.arange(n+1)/float(n)*45.)]
    CL = [Ci.trl(2, a) for Ci, a in zip(CL, np.arange(n+1)/float(n)*4.)]
    return CL


def createPowerCurves(nu, nv):
    """Create a set of BezierSpline power curves.

    The curves are transformations of a straight line. The line is
    transformed by two subsequent power law transformations:
    y = a*x**b and z = c*y**d.
    """
    X = Formex(origin()).replic(nu+1, 1.).coords.reshape(-1, 3)
    C = BezierSpline(X)
    sx = C.dsize()
    sy = 0.5*sx
    sz = 0.25*sx
    powers = 1. * (np.arange(nv+1) * 2 - nv) / float(nv)
    print(powers)
    powers = exp(powers)
    print(powers)
    CL = [C.map1(1, lambda x:sy*(x/sx)**e, 0).map1(2, lambda x:sz*(x/sx)**e, 1) for e in powers]
    return CL


def readSplines():
    """Read spline curves from a geometry file.

    The geometry file splines.pgf is provided with the pyFormex distribution.
    """
    fn = getcfg('datadir') / 'splines.pgf'
    obj = readGeometry(fn)
    T = obj.values()
    print("Number of curves: %s" % len(T))
    print("Curve lengths: %s" % [len(Si.coords) for Si in T])
    return T


def removeInvalid(CL):
    """Remove the curves that contain NaN values.

    NaN values are invalid numerical values.
    This function removes the curves containing such values from a list
    of curves.
    """
    nc = len(CL)
    CL = [Ci for Ci in CL if not np.isnan(Ci.coords).any()]
    nd = len(CL)
    if nc > nd:
        print("Removed %s invalid curves, leaving %s" % (nc-nd, nd))
    return CL


def area(C, nroll=0):
    """Compute area inside spline

    The curve is supposed to be in the (x,y) plane.
    The nroll parameter may be specified to roll the coordinates
    appropriately.
    """
    #print(nroll)
    from pyformex.plugins.section2d import PlaneSection
    F = C.toFormex().rollAxes(nroll)
    S = PlaneSection(F)
    C = S.sectionChar()
    return C['A']

###############################################################

def run():
    clear()
    smoothwire()

    from pyformex.gui.widgets import simpleInputItem as I

    res = askItems([
        I('base', itemtype='vradio', choices=[
            'Circles and Ellipses',
            'Power Curves',
            'Kinked Artery',
            ]),
        I('ncurve', value=12, text='Number of spline curves'),
        I('nu', value=36, text='Number of cells along splines'),
        I('refine', False),
        I('nv', value=12, text='Number of cells across splines'),
        I('align', False),
        I('aligndir', 1),
        I('alignmax', True),
        ])

    if not res:
        return

    globals().update(res)

    if base == 'Circles and Ellipses':
        CL = createCircles(n=ncurve)
        nroll = 0
        reverse = False
    elif base == 'Power Curves':
        CL = createPowerCurves(nu, nv)
        nroll = 0
        reverse = False
    else:
        CL = readSplines()
        nroll = -1
        reverse = True

    ncurves = len(CL)
    print("Created %s BezierSpline curves" % ncurves)
    CL = removeInvalid(CL)

    if reverse:
        areas = [area(Ci, nroll) for Ci in CL]
        print(areas)
        for i, a in enumerate(areas):
            if a < 0.0:
                print("Reversing curve %s" % i)
                CL[i] = CL[i].reverse()

    if align:
        #view('left')
        for Ci in CL:
            #clear()
            alignCurvePoints(Ci, aligndir, alignmax)
            draw(Ci.pointsOn()[0], color=green)
            #zoomAll()
            #pause()
            #return

    draw(CL)
    export({'splines': CL})
    print("Number of points in the curves:", [Ci.coords.shape[0] for Ci in CL])

    PL = [Ci.approx(ndiv=1) for Ci in CL]

    createPL = False
    if createPL:
        export({'polylines': PL})
        draw(PL, color=red)
        print("Number of points in the PolyLines:", [Ci.coords.shape[0] for Ci in PL])


    S = SplineSurface(CL, nu)
    M = gridToMesh(S.grid, closed = S.uclosed)
    M.attrib(name='quadsurface', color=yellow, bkcolor='steelblue')
    draw(M)
    export({'quadsurface': M})

    if refine:
        clear()
        print("Refining to %s" % nv)
        S = SplineSurface(S.vCurves(), nv)
        N = gridToMesh(S.grid, closed = S.uclosed)
        draw(N, color=magenta, bkcolor='olive')
        export({'quadsurface-1': N})

    zoomAll()

##############################################################################

if __name__ == '__draw__':
    run()
# End
