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
"""Curves

Examples showing the use of the 'curve' plugin

"""
_name = 'Curves'
_level = 'normal'
_topics = ['geometry', 'curve']
_techniques = ['widgets', 'persistence', 'import', 'spline', 'frenet']

from pyformex.gui.draw import *
from pyformex import curve
from pyformex.plugins import nurbs


ctype_color = ['red', 'green', 'blue', 'cyan', 'magenta', 'yellow', 'white']
point_color = ['black', 'white']

open_or_closed = {True: 'A closed', False: 'An open'}

TA = None

curvetypes = [
    'BezierSpline',
    'PolyLine',
    'NaturalSpline',
    'NurbsCurve',
]

all_curves = (
    ('BezierSpline', 3),
    ('BezierSpline', 2),
    ('PolyLine', None),
    ('NaturalSpline', 3),
    ('NurbsCurve', 3),
    )

def drawCurve(ctype, dset, closed, degree, endcond, curl, nseg, chordal, method, approx, extend, scale=None, cutWP=False, frenet=False, avgdir=True, upvector=None, sweep=False):
    global S, TA
    dset = coordset.get(dset, dset)
    P = Coords(dset)
    text = "%s %s with %s points" % (open_or_closed[closed], ctype.lower(), len(P))
    if TA is not None:
        undecorate(TA)
    TA = drawText(text, (10, 20), size=20)
    draw(P, color='black', nolight=True)
    drawNumbers(P)
    if ctype == 'PolyLine':
        S = curve.PolyLine(P, closed=closed)
        color = 0
    elif ctype == 'BezierSpline':
        S = curve.BezierSpline(P, degree=degree, curl=curl, closed=closed)
        color = 4-degree
    elif ctype == 'NaturalSpline':
        S = curve.NaturalSpline(P, closed=closed, endzerocurv=(endcond, endcond))
        color = 3
        directions = False
    elif ctype == 'NurbsCurve':
        S = nurbs.globalInterpolationCurve(P, degree=degree)
        color = 4
        scale = None
        directions = False
        drawtype = 'Curve'

    if scale:
        S = S.scale(scale)

    im = curvetypes.index(ctype)
    print("%s control points" % S.coords.shape[0])
    draw(S.approx(), color=color)

    if approx:
        print(method)
        if method == 'chordal':
            nseg = None

        PL = S.approx(nseg=nseg, chordal=chordal, equidistant=method=='equidistant')

        if cutWP:
            PC = PL.cutWithPlane([0., 0.42, 0.], [0., 1., 0.])
            draw(PC[0], color=red)
            draw(PC[1], color=green)
        else:
            draw(PL, color=ctype_color[im])
        draw(PL.pointsOn(), color=black)

    if approx:
        C = PL
    else:
        C = S

    if frenet:
        X, T, N, B = C.frenet(upvector=upvector, avgdir=avgdir)[:4]
        drawVectors(X, T, size=1., nolight=True, color='red')
        drawVectors(X, N, size=1., nolight=True, color='green')
        drawVectors(X, B, size=1., nolight=True, color='blue')
        if  C.closed:
            X, T, N, B = C.frenet(upvector=upvector, avgdir=avgdir,
                                  compensate=True)[:4]
            drawVectors(X, T, size=1., nolight=True, color='magenta')
            drawVectors(X, N, size=1., nolight=True, color='yellow')
            drawVectors(X, B, size=1., nolight=True, color='cyan')

    if sweep and isinstance(C, Curve):
        F = Formex('l:b').mirror(2)
        draw(F)
        F = C.sweep(F.scale(0.05*C.dsize()))
        smoothwire()
        draw(F, color=red, mode='smoothwire')

coordset = {
    'gianluca': ((-1., 1., -4.), (1., 1., 2.), (2.6, 2., -4.), (2.9,  3.5, 4.),
            (2., 4., -1.), (1., 3., 1.), (0., 0., 0.), (0., -3., 0.),
            (2., -1.5, -2.), (1.5, -1.5, 2.), (0., -8., 0.), (-1., -8., -1.),
                 (3., -3., 1.)),
    'strange': ((1.49626994, 30.21483994,  17.10247993),
                (9.15044022, 27.19248009, 15.05076027),
                (15.75351048, 24.26766014, 12.36573982),
                (13.35517025, 17.80452919,  9.27042007),
                (31.15517044, 18.58106995,  0.63323998),
                (27.05437088, -0.60475999, -2.6461401),
                (7.66548014, -12.33625031, 17.51568985),
                (-3.34934998, -12.35941029, 28.64728928),
                (-9.86301041, -10.66467953, 38.48815918),
                (-19.86301041, -10.66467953, 0.),
                (-19.86301041, 10.66467953, 0.),
                (-19.86301041, 10.66467953, 10.)),
}

dataset = (
    '0123',
    '01234',
    '012',
    '012141214',
    '0678',
    '021Da',
    '0Fg4Dh7',
    'gianluca',
    '0/4/4/4/4/4/4/4/448/1/1/1/1/1/1/1/11',
    '04.1',
    'strange',
    )

_items = [
    _I('dset', text='DataSet', choices=dataset),
    _I('ctype', text='CurveType', choices=curvetypes),
    _I('closed', False, text='Closed'),
    _I('degree', 3, text='Degree', min=1, max=3),
    _I('curl', 1./3., text='Curl'),
    _I('endcond', False, text='EndCurvatureZero'),
    _G('approx', text='Approximation', items=[
        _I('method', text='Method', choices=['chordal', 'parametric', 'equidistant']),
        _I('chordal', 0.01, text='Chordal'),
        _I('nseg', 4, text='Nseg'),
        ], check=False),
    _I('extend0', 0.0, text='ExtendAtStart'),
    _I('extend1', 0.0, text='ExtendAtEnd'),
    _I('scale', [1.0, 1.0, 1.0], text='Scale'),
    _I('cutWP', False, text='CutWithPlane'),
    _I('clear', True, text='Clear'),
    _G('frenet', text='FrenetFrame', items=[
        _I('avgdir', True, text='AvgDirections'),
        _I('autoup', True, text='AutoUpVector'),
        _I('upvector', [0., 0., 1.], text='UpVector'),
        ], check=False),
    _I('sweep', False, text='Sweep'),
    ]

_enablers = [
    ('ctype', 'BezierSpline', 'degree', 'curl',),
    ('ctype', 'NaturalSpline', 'endcond'),
    ('ctype', 'NurbsCurve', 'degree'),
    ('method', 'chordal', 'chordal'),
    ('method', 'parametric', 'nseg'),
    ('method', 'equidistant', 'nseg'),
    ('autoup', False, 'upvector'),
    ]


clear()
setDrawOptions({'bbox': 'auto', 'view': 'front'})
linewidth(2)
flat()

dialog = None

#
# TODO: closing the window (by a button) should also
#       call a function to release the scriptlock!
#
def close():
    global dialog
    if dialog:
        dialog.close()
        dialog = None
    # Release script lock
    scriptRelease(__file__)

def show(w=None, all=False):
    if not dialog.validate():
        return
    res = dialog.results
    res['extend'] = (res.pop('extend0'), res.pop('extend1'))
    if res.pop('autoup'):
        res['upvector'] = None
    if res.pop('clear'):
        clear()
    setDrawOptions({'bbox': 'auto'})
    if all:
        res.pop('ctype')
        res.pop('degree')
        for ctype, degree in all_curves:
            drawCurve(ctype=ctype, degree=degree, **res)
            setDrawOptions({'bbox': None})
    else:
        drawCurve(**res)

def showAll():
    show(all=True)

def timeOut():
    showAll()
    wait()
    close()


def run():
    global dialog
    dialog = Dialog(caption=_name, store=_name+'_data',
        items=_items,
        enablers=_enablers,
        actions = [('Close', close), ('Clear', clear), ('Show All', showAll), ('Show', show)],
        default='Show')

    dialog.show(timeoutfunc=timeOut)
    # Block other scripts
    scriptLock(__file__)



if __name__ == '__draw__':
    run()
# End
