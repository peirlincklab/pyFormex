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
"""Partitioning tools

"""

import numpy as np

import pyformex as pf
from pyformex import Path
from pyformex import colors
from pyformex import geomtools
from pyformex.opengl import decors
from pyformex.gui import draw as ps

inverse = np.linalg.linalg.inv

VA=None

def prepare(V):
    """Prepare the surface for slicing operation."""
    global VA
    V = V.translate(-V.center())
    P = V.center()
    print("Initial P = %s" % P)
    VA = ps.draw(V, bbox=None, color='black')
    area, norm = geomtools.areaNormals(V.coords)
    N = norm[0]
    return V, P, N


def testview(F, V, P):
    global VA, waiting
    p = np.array(pf.canvas.camera.focus)
    waiting = True
    while waiting:
        pf.app.processEvents()
    p -= np.array(pf.canvas.camera.focus)
    print("TRANSLATE: %s" % p)
    m = pf.canvas.camera.getRot()
    P += p
    print("TOTAL TRANSLATE: %s" % P)
    V = V.affine(inverse(m[0:3, 0:3])).translate(-P)
    print(V.center())
    print(F.center())
    ps.undraw(VA)
    VA = draw(V)
    area, norm = geomtools.areaNormals(V.coords)
    N = np.norm[0]
    return P, N


def colorCut(F, P, N, prop):
    """Color a Formex in two by a plane (P,N)"""
    print(F.bbox())
    print(P)
    print(N)
    print(prop)
    dist = F.distanceFromPlane(P, N)
    print(dist)
    right = np.any(dist>0.0, axis=1)
    print(right)
    F.prop[right] = prop
    nright = right.sum()
    nleft = F.nelems() - nright
    print("Left part has %s elements, right part has %s elements" % (nleft, nright))
    return F


def splitProp(G, name):
    """Partition a Formex according to its prop values and export the results.

    If G has property numbers, the structure is split and according
    to the property values, and the (compacted) parts are exported
    with names 'name-propnumber'.
    """
    split = G.splitProp(compact=True)
    if split:
        names = ['%s-%s' % (name, i) for i in np.unique(G.prop)]
        ps.export2(names, split)


waiting = True

def wakeup():
    global waiting
    waiting = False


def partition(Fin, prop=0):
    """Interactively partition a Formex.

    By default, the parts will get properties 0,1,...
    If prop >= 0, the parts will get incremental props starting from prop.

    Returns the cutplanes in an array with shape (ncuts,2,3), where
      (i,0,:) is a point in the plane i and
      (i,1,:) is the normal vector on the plane i .

    As a side effect, the properties of the input Formex will be changed
    to flag the parts between successive cut planes by incrementing
    property values.
    If you wish to restore the original properties, you should copy them
    (or the input Formex) before calling this function.
    """
    global FA, VA, waiting

    # start color
    keepprops = prop
    if prop is None or prop < 0:
        prop = 0

    # Make sure the initial Formex is centered
    initial_trl = -Fin.center()
    F = Fin.translate(initial_trl)

    # Store the initial properties and make all properties equal to start value
    initial_prop = F.prop
    F.setProp(prop)

    # draw it
    ps.linewidth(1)
    ps.perspective(False)
    ps.clear()
    FA = ps.draw(F, view='front')

    # create a centered cross plane, large enough
    bb = F.bbox()
    siz = F.sizes().max()
    V = ps.Formex([[[0., 0., 0.], [1., 0., 0.], [1., 1., 0.]],
                [[1., 1., 0.], [0., 1., 0.], [0., 0., 0.]]],
               0)
    V = V.translate(-V.center()).rotate(90, 1).scale(siz)

    cut_planes = []

    pf.GUI.signals.WAKEUP.connect(wakeup)

    ps.linewidth(2)
    w, h = pf.canvas.width(), pf.canvas.height()
    ps.fgcolor('magenta')
    SD = decors.Line(w/2, 0, w/2, h)
    ps.decorate(SD)

    ps.fgcolor(colors.black)

    V, P, N = prepare(V)
    while True:
        res = ps.ask("", ["Adjust Cut", "Keep Cut", "Finish"])
        if res == "Adjust Cut":
            P, N = testview(F, V, P)
            print("Plane: point %s, normal %s" % (P, N))
        elif res == "Keep Cut":
            ps.undraw(FA)
            #undraw(VA)
            cut_planes.append((P, N))
            prop += 1
            F = colorCut(F, -P, N, prop)
            FA = ps.draw(F)
            ps.undraw(VA)
            V, P, N = prepare(V)
        else:
            break

    pf.GUI.signals.WAKEUP.disconnect(wakeup)
    ps.clear()
    ps.draw(F)
    Fin.setProp(F.prop)
    return np.array(cut_planes)


def savePartitions(F):
    print("Current dir is %s" % Path.cwd())
    if ack("Save the partitioned Formex?"):
        writeFormex(F, 'part.fmx')
        ps.clear()

    if ack("Reread/draw the partitioned Formex?"):
        F = readFormex('part.fmx')
        ps.draw(F)

    splitProp(F, 'part')

    if ack("Save the partitions separately?"):
        for (k, v) in d.items():
            writeFormex(v, "%s.fmx"%k)


# End
