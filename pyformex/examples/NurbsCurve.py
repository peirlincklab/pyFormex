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

"""NurbsCurve

This example illustrates the use of the NurbsCurve class from the nurbs
plugin.
"""

_level = 'advanced'
_topics = ['geometry', 'curve']
_techniques = ['nurbs', 'connect', 'border', 'frenet']

from pyformex.gui.draw import *
from pyformex import simple
from pyformex.plugins.nurbs import *

AN = utils.autoName('Nurbscurve')


def drawThePoints(N, n, color=None):
    umin = N.knots[N.degree]
    umax = N.knots[-N.degree-1]
    #print "Umin = %s, Umax = %s" % (umin,umax)
    u = umin + np.arange(n+1) * (umax-umin) / float(n)
    P = N.pointsAt(u)
    draw(P, color=color, marksize=5)
    drawNumbers(P, color=color)

    XD = N.derivs(u, 5)[:4]
    if XD.shape[-1] == 4:
        XD = XD.toCoords()
    x, d1, d2, d3 = XD[:4]
    e1, e2, e3, k, t = frenet(d1, d2, d3)
    #print t

    #k = 1./k
    #k[np.isnan(k)] = 0.
    k /= k[np.isnan(k) == 0].max()
    tmax = t[np.isnan(t) == 0].max()
    if tmax > 0:
        t /= tmax
    #print t
    s = 0.3
    x1 = x+s*e1
    x2 = x+s*e2
    x3 = x+s*e3
    x2k = x+k.reshape(-1, 1)*e2  # draw curvature along normal
    x3t = x+t.reshape(-1, 1)*e3
    draw(x, marksize=10, color=yellow)
    draw(connect([Formex(x), Formex(x1)]), color=yellow, linewidth=3)
    draw(connect([Formex(x), Formex(x2)]), color=cyan, linewidth=2)
    draw(connect([Formex(x), Formex(x2k)]), color=blue, linewidth=5)
    draw(connect([Formex(x), Formex(x3)]), color=magenta, linewidth=2)
    draw(connect([Formex(x), Formex(x3t)]), color=red, linewidth=5)


def drawCurvature(N, ncur):
    """Compute and draw the curvature of Nurbs N at ncur points"""
    umin, umax = N.urange()    # Nurbs parameter range
    u = uniformParamValues(ncur, umin, umax)   # parameter space for curvature
    k = N.curvature(u)        # curvature
    #print(k)
    # Draw as field
    mline = PolyLine(N.pointsAt(u)).toMesh()
    mline.addField('node', k, 'curv')
    drawField(mline.getField('curv'), linewidth=10)


def drawNurbs(points, pointtype, degree, strategy, closed, blended, weighted=False, Clear=False, showpoints=False, npoints=10, showcurv=False, ncurv=100):
    if Clear:
        clear()

    X = pattern(points)
    F = Formex(X)
    draw(F, marksize=10, bbox='auto', view='front')
    drawNumbers(F, prefix='P', trl=[0.02, 0.02, 0.])
    if closed:
        # remove last point if it coincides with first
        x, e = Coords.concatenate([X[0], X[-1]]).fuse()
        if x.shape[0] == 1:
            X = X[:-1]
        blended=True
    draw(PolyLine(X, closed=closed))
    if not blended:
        nX = ((len(X)-1) // degree) * degree + 1
        X = X[:nX]
    if weighted:
        wts = np.array([1.]*len(X))
        wts[1::2] = 0.5
        #print wts,wts.shape
    else:
        wts=None
    if pointtype == 'Control':
        try:
            N = NurbsCurve(X, wts=wts, degree=degree, closed=closed, blended=blended)
        except Exception as e:
            showError(str(e))
            return
    else:
        N = globalInterpolationCurve(X, degree=degree, strategy=strategy)
    draw(N, color=red)
    pf.PF[next(AN)] = N
    if showpoints:
        drawThePoints(N, npoints, color=black)
    if showcurv:
        drawCurvature(N, ncurv)


dialog = None


def close():
    global dialog
    if dialog:
        dialog.close()
        dialog = None
    # Release script lock
    scriptRelease(__file__)


def show():
    if dialog.validate():
        res = dialog.results
        export({'_Nurbs_data_': res})
        drawNurbs(**res)

def showAll():
    if dialog.validate():
        res = dialog.results
        export({'_Nurbs_data_': res})
        for points in predefined:
            print(res)
            res['points'] = points
            drawNurbs(**res)


def timeOut():
    try:
        showAll()
    finally:
        close()


predefined = [
    '51414336',
    '51i4143I36',
    '2584',
    '25984',
    '184',
    '514',
    '1234',
    '5858585858',
    '12345678',
    '121873',
    '1218973',
    '8585',
    '85985',
    '214121',
    '214412',
    '151783',
    'ABCDABCD',
    ]

data_items = [
    _I('points', text='Point set', choices=predefined),
    _I('pointtype', text='Point type', choices=['Control', 'OnCurve']),
    _I('degree', 3),
    _I('strategy', 0.5),
    _I('closed', False),
    _I('blended', True, enabled=False),
    _I('weighted', False),
    _I('showpoints', False, text='Show Frenet vectors'),
    _I('npoints', 20, text='Number of curve points'),
    _I('showcurv', False, text='Show curvature'),
    _I('ncurv', 100, text='Number of curvature points'),
    _I('Clear', True),
    ]
input_enablers = [
    ('pointtype', 'OnCurve', 'strategy'),
    ('pointtype', 'Control', 'closed'),
    ('pointtype', 'Control', 'blended'),
    ('pointtype', 'Control', 'weighted'),
    ('closed', False, 'blended'),
#    ('blended',True,'closed'),
    ('showpoints', True, 'npoints'),
    ('showcurv', True, 'ncurv'),
    ]


def run():
    global dialog
    clear()
    setDrawOptions({'bbox': None})
    linewidth(2)
    flat()

    ## Closing this dialog should release the script lock
    dialog = Dialog(
        data_items,
        enablers = input_enablers,
        caption = 'Nurbs parameters',
        actions = [('Close', close), ('Clear', clear), ('Show All', showAll), ('Show', show)],
        default = 'Show',
        )

    if '_Nurbs_data_' in pf.PF:
        dialog.updateData(pf.PF['_Nurbs_data_'])

    dialog.show(timeoutfunc=timeOut)

    # Block other scripts
    scriptLock(__file__)


if __name__ == '__draw__':
    run()
# End
