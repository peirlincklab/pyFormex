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
"""NurbsDecompose

Illustrates some special techniques on Nurbs Curves:

- inserting knots
- removing knots
- curve decomposing
- degree elevation
"""
_level = 'advanced'
_topics = ['Geometry', 'Curve']
_techniques = ['nurbs']
_name = 'NurbsOperations'

from pyformex.gui.draw import *
from pyformex.plugins.nurbs_menu import _options
from pyformex.examples.NurbsCurveExamples import drawNurbs, nurbs_book_examples, createNurbs
from pyformex import simple
from pyformex.lib import nurbs


def showCurve(reverse=False):
    """Select and show a Nurbs curve."""
    global N, dialog
    if dialog.validate():
        curv = dialog.results['curv']
        N = createNurbs(curv)
        if reverse:
            N = N.reverse()
        print(N)
        drawNurbs(N, color=blue, knotsize=5)


def showReverse():
    showCurve(reverse=True)


def insertKnot():
    """Insert a knot in the knot vector of Nurbs curve N."""
    global N, dialog

    if dialog.validate():
        res = dialog.results
        u = eval('[%s]' % res['u'])
        N = N.insertKnots(u)
        print(N)
        drawNurbs(N, color=red, knotsize=5)
        zoomAll()


def removeKnot():
    """Remove a knot from the knot vector of Nurbs curve N."""
    global N, dialog

    if dialog.validate():
        res = dialog.results
        ur = res['ur']
        m = res['m']
        tol = res['tol']
        N = N.removeKnot(ur, m, tol)
        print(N)
        drawNurbs(N, color=blue, knotsize=5)
        zoomAll()


def removeAllKnots():
    """Remove all removable knots."""
    global N, dialog

    if dialog.validate():
        res = dialog.results
        tol = res['tol']
        N = N.removeAllKnots(tol=tol)
        print(N)
        drawNurbs(N, color=blue)
        zoomAll()


def distance(self, N, ndiv=100):
    """Evaluate the distance between two Nurbs Curves"""
    u0, u1 = N.urange()
    u = u0 + np.arange(ndiv+1) * (u1-u0) / ndiv
    pts = N.pointsAt(u)
    return pts


def elevateDegree():
    """Elevate the degree of the Nurbs curve N."""
    global N, dialog

    if dialog.validate():
        res = dialog.results
        nd = res['nd']
        if nd > 0:
            N = N.elevateDegree(nd)
        elif nd < 0:
            M = N
            N = N.reduceDegree(-nd)
            P = distance(M,N,10)
            draw(P)
            Q = Coords([M.projectPoint(Pi)[1] for Pi in P])
            #Q = distance(M,M,10)
            draw(Q, color=blue)
            d = at.length(P-Q)
            draw(Formex(np.stack([P,Q]).transpose(1,0,2)))
            print(f"Distances: {d}")
            print(f"Max: {d.max()}")
        else:
            return
        print(N)
        draw(N, color=cyan, linewidth=3)
        zoomAll()


def decompose():
    """Decompose Nurbs curve N"""
    global N, C

    N1 = N.decompose()
    print(N1)
    drawNurbs(N1, color=black, knotsize=10, knot_values=False)
    zoomAll()
    C = BezierSpline(control=N1.coords, degree=N1.degree)
    #draw(C, color=blue)

    for i, Ci in enumerate(C.split()):
        print(Ci)
        Ci.setProp(i)
        draw(Ci, color=i, linewidth=5)


def unclamp():
    """(Un)Clamp the curve N"""
    global N

    if N.isClamped():
        N = N.unclamp()
    else:
        N = N.clamp()
    print(N)
    drawNurbs(N, color=red, linewidth=3, clear=False)



def projectPoints():
    """Project points on the NurbsCurve N"""
    global N, dialog

    if dialog.validate():
        res = dialog.results
        npts = res['npts']
        show_distance = res['show_distance']

        X = simple.randomPoints(npts, N.bbox())
        draw(X, marksize=5)

        for Xi in X:
            u, P, d = N.projectPoint(Xi)
            draw(Formex([[P, Xi]]), color=red)
            if show_distance:
                drawText(f"{d}", 0.5*(P+Xi))


def close():
    global dialog
    if dialog:
        dialog.close()
        dialog = None
    # Release script lock
    scriptRelease(__file__)


def timeOut():
    try:
        showCurve()
        decompose()
    finally:
        close()


dialog = None

def run():
    global N, dialog
    clear()
    flat()

    clear()
    linewidth(1)
    _options.ctrl = True
    _options.ctrl_numbers = True
    _options.ctrl_polygon = True
    _options.knot_values = True


    createNurbs('default')

    if dialog:
        dialog.close()
    dialog = Dialog(caption=_name, store=_name+'_data', items=[
            _G('Curve Selection', [
                _I('curv', 'default', choices=utils.hsorted(nurbs_book_examples.keys()),
                   buttons=[('Show Curve', showCurve), ('Show Reverse', showReverse)]),
            ]),
            _G('Knot Insertion', [
                _I('u', 0.5, text='Knot value(s) to insert',                   buttons=[('Insert Knot', insertKnot)]),
            ]),
            _G('Knot Removal', [
                _I('ur', 0.5, text='Knot value to remove'),
                _I('m', 1, text='How many times to remove', buttons=[('Remove Knot', removeKnot)]),
                _I('tol', 0.001, text='Tolerance', buttons=[('Remove All Knots', removeAllKnots)]),
            ]),
            _G('Degree Elevation/Reduction', [
                _I('nd', 1, text='How much to elevate/reduce the degree', buttons=[('Change Degree', elevateDegree)]),
            ]),
            _G('Point Projection', [
                _I('npts', 10, text='How many points to project', buttons=[('Project Points', projectPoints)]),
                _I('show_distance', True, text='Show distance'),
            ]),
        ], actions=[
            ('Close', close),
            ('Decompose', decompose),
            ('(Un)Clamp', unclamp),
            ('Decompose', decompose),
        ])
    dialog.show(timeoutfunc=timeOut)

    # Block other scripts
    scriptLock(__file__)


if __name__ == '__draw__':
    run()

# End
