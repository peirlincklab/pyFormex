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
"""sectionize.py

Create, measure and approximate cross section of a Formex.
"""
import pyformex as pf
from pyformex.curve import PolyLine
from pyformex import simple
from pyformex.gui.draw import *

def connectPoints(F, close=False):
    """Return a Formex with straight segments connecting subsequent points.

    F can be a Formex or data that can be turned into a Formex (e.g. an (n,3)
    array of points). The result is a plex-2 Formex connecting the subsequent
    points of F or the first point of subsequent elements in case the plexitude
    of F > 1.
    If close=True, the last point is connected back to the first to create a
    closed polyline.
    """
    if not isinstance(F, Formex):
        F = Formex(F)
    return connect([F, F], bias=[0, 1], loop=close)


def centerline(F, dir, nx=2, mode=2, th=0.2):
    """Compute the centerline in the direction dir.

    """
    bb = F.bbox()
    x0 = F.center()
    x1 = F.center()
    x0[dir] = bb[0][dir]
    x1[dir] = bb[1][dir]
    n = np.array((0, 0, 0))
    n[dir] = nx

    grid = simple.regularGrid(x0, x1, n, swapaxes=True).reshape((-1, 3))

    th *= (x1[dir]-x0[dir])/nx
    n = np.zeros((3,))
    n[dir] = 1.0

    def localCenter(X, P, n):
        """Return the local center of points X in the plane P,n"""
        test = abs(X.distanceFromPlane(P, n)) < th  # points close to plane
        if mode == 1:
            C = X[test].center()
        elif mode == 2:
            C = X[test].centroid()
        return C

    center = [localCenter(F, P, n) for P in grid]
    return PolyLine(center)


def createSegments(F, ns=None, th=None):
    """Create segments along 0 axis for sectionizing the Formex F."""
    bb = F.bbox()
    print("Bounding box = %s" % bb)
    if ns is None or th is None:
        res = askItems([['number of sections', 20],
                        ['relative thickness', 0.1]],
                       'Sectioning Parameters')
        if res:
            ns = int(res['number of sections'])
            th = float(res['relative thickness'])
    if at.isInt(ns) and isinstance(th, float):
        xmin, ymin, zmin = bb[0]
        xmax, ymax, zmax = bb[1]
        xgem, ygem, zgem = F.center()
        A = [xmin, ygem, zgem]
        B = [xmax, ygem, zgem]
        segments = Formex([[A, B]]).subdivide(ns)
        print("Segments: %s" % segments)
        return ns, th, segments
    return 0, 0, []


def sectionize(F, segments, th=0.1, visual=True):
    """Sectionize a Formex in planes perpendicular to the segments.

    F is any Formex.
    segments is a plex-2 Formex.

    Planes are chosen in each center of a segment, perpendicular to
    that segment. Then parts of the Formex F are selected in the
    neighbourhood of each plane. Each part is then approximated by a
    circle in that plane.

    th is the relative thickness of the selected part of the Formex.
    If th = 0.5, that part will be delimited by two planes in the endpoints
    of and perpendicular to the segments.
    """
    sections = []
    ctr = []
    diam = []
    if visual:
        clear()
        linewidth(1)
        draw(F, color='yellow')
        linewidth(2)
    for s in segments:
        c = 0.5 * (s[0]+s[1])
        d = s[1]-s[0]
        l = at.length(d)
        n = d/l
        t = th*l
        test = abs(F.distanceFromPlane(c, n)) < th*l
        test = test.sum(axis=-1)
        G = F.select(test==3)
        if visual:
            draw(G, color='blue', view=None)
            pf.canvas.update()
        print(G)
        C = G.center()
        D = 2 * G.distanceFromLine(C, n).mean()
        print("Section Center: %s; Diameter: %s" % (C, D))
        sections.append(G)
        ctr.append(C)
        diam.append(D)
    return sections, ctr, diam


def drawCircles(sections, ctr, diam):
    """Draw circles as approximation of Formices."""
    circle = simple.circle().rotate(-90, 1)
    cross = simple.shape('plus').rotate(-90, 1)
    circles = []
    n = len(sections)
    for i in range(n):
        C = cross.translate(ctr[i])
        B = circle.scale(diam[i]/2).translate(ctr[i])
        S = sections[i]
        clear()
        draw(S, view='left', wait=False)
        draw(C, color='red', bbox=None, wait=False)
        draw(B, color='blue', bbox=None)
        circles.append(B)
    return circles


def drawAllCircles(F, circles):
    clear()
    linewidth(1)
    draw(F, color='yellow', view='front')
    linewidth(2)
    for circ in circles:
        bb = circ.bbox()
        d = (bb[1] - bb[0]) * 0.5
        bb[0] -= d
        bb[1] += d
        draw(circ, color='blue', bbox=bb)
    zoomAll()


# End
