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
"""NurbsInterpolation

This example illustrates the creation of NurbsCurves interpolating or
approximating a given point set.
"""
_level = 'advanced'
_topics = ['geometry', 'curve']
_techniques = ['nurbs', 'connect', 'border', 'frenet']
_name = 'NurbsInterpolation'

from pyformex.gui.draw import *
from pyformex.plugins.nurbs import *

np.set_printoptions(precision=3)

point_set = {
#    'pt_9.1': [
#        ( 3.5,),
#        ( 4.9,),
#        ( 7.0,),
#        ( 9.0,),
#        (11.0,),
#    ],
    'pt_9.3': (
        (3.9, -6.4),
        (4.0, -5.2),
        (5.3, -3.5),
        (8.0, -4.2),
        (9.4, -5.6),
        (10.7, -5.3),
        (12.2, -5.5),
    ),
    'ex_9.1': ((0,0), (3,4), (-1,4), (-4,0), (-4,-3)),
    'pt_9.7': (
        (-12.1, -8.6),
        (-12.1, -7.8),
        (-12.1, -4.9),
        (-12.1, -4.0),
        (-10.7, -2.6),
        (- 9.3, -2.6),
        (- 8.6, -3.3),
        (- 8.6, -4.0),
        (- 8.6, -4.8),
        (- 7.9, -5.6),
        (- 7.2, -5.6),
        (- 4.4, -5.6),
        (- 3.5, -5.6),
    ),
    'pt_9.8': (
        (0.0, 2.6),
        (0.4, 4.3),
        (2.8, 5.0),
        (4.2, 3.0),
        (7.1, 2.5),
        (8.5, 6.3),
        (7.0, 6.5),
    ),
    'pt_9.10': (
        (0.0, -7.2),
        (0.5, -5.5),
        (3.7, -4.8),
        (4.5, -6.3),
        (5.2, -7.2),
        (9.0, -5.1),
        (7.5, -3.3),
    ),
    'pt_9.11': (
        (-11.4, 4.4),
        (-10.2, 7.5),
        ( -7.8, 5.7),
        ( -6.5, 3.8),
        ( -4.1, 7.0),
    ),
    'pt_9.20': (
        (-12.2, 2.5),
        (-11.6, 5.5),
        ( -9.5, 7.3),
        ( -6.0, 7.3),
        ( -4.2, 5.5),
        ( -3.9, 3.3),
    ),
    'pt_9.21': (
        ( 4.7, 3.6),
        ( 4.1, 6.4),
        ( 6.2, 9.0),
        ( 9.1, 9.3),
        (11.7, 7.2),
        (11.0, 3.7),
    ),
    'pt_9.23': '0115811',
    'pt_9.24': (
        ( 0.0, 0.0),
        ( 0.0, 1.4),
        ( 0.0, 2.8),
        ( 2.8, 2.8),
        ( 2.8, 1.4),
        ( 2.8, 0.0),
        ( 5.6, 0.0),
        ( 8.4, 0.0),
        ( 8.4, 1.4),
        ( 8.4, 4.4),
    ),
    'pt_9.30': (
        (-12.5, 3.4),
        (-12.1, 4.9),
        ( -8.8, 5.7),
        ( -8.8, 3.3),
        ( -7.3, 3.3),
        ( -3.6, 5.3),
        ( -5.1, 7.1),
    ),
    'pt_9.37' : (
        (-11.5, 1.7),
        (-10.5, 1.9),
        (-10.0, 2.3),
        ( -9.7, 3.4),
        ( -9.4, 4.2),
        ( -9.2, 4.8),
        ( -9.0, 5.5),
        ( -8.6, 5.5),
        ( -7.9, 5.5),
        ( -7.3, 5.5),
        ( -7.3, 4.7),
        ( -7.3, 3.7),
        ( -7.3, 2.9),
        ( -6.9, 2.3),
        ( -6.1, 1.7),
        ( -5.0, 1.7),
        ( -4.2, 1.7),
    ),
    'pt_9.38' : PolyLine([
        (-12.3, 4.5),
        (-10.9, 8.2),
        ( -8.7, 8.2),
        ( -7.2, 3.7),
        ( -5.0, 3.7),
        ( -3.5, 7.5),
    ]).subdivide((4,3,6,3,4)).coords,
}

point_patterns = [
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

point_ids = utils.hsorted(point_set.keys()) + point_patterns

def interpolationCurve(Q, p, D, D0, D1, strat):
    print(f"END TANGENTS: {D0} {D1}")
    if p not in (2,3):
        raise ValueError("Degree should be 2 or 3")
    if strat == 'c':
        if D0 is None or D1 is None:
            D = akimTangents(Q) * PolyLine(Q).length()
            if D0 is None:
                D0 = D[0]
            if D1 is None:
                D1 = D[-1]
        N = cubicSpline(Q, D0, D1)
    elif strat == 'g':
        if D0 is None or D1 is None:
            _D = akimTangents(Q) * PolyLine(Q).length()
            if D0 is None:
                D0 = _D[0]
            if D1 is None:
                D1 = _D[-1]
        N = globalInterpolationCurve(Q, degree=p, D=D, D0=D0, D1=D1)
    else:
        if D0 is not None or D1 is not None:
            if D is None:
                D = akimTangents(Q)
            if D0 is not None:
                D[0] = D0
            if D1 is not None:
                D[-1] = D1
        if p == 3:
           N = cubicInterpolate(Q, D)
        elif p == 2:
            N = quadraticInterpolate(Q, D)
    return N


def drawPoints(Q):
    draw(Q, marksize=10, bbox='auto', view='front')
    drawNumbers(Q, prefix='Q', gravity='ne')

def drawNurbs(N, color, show_control):
    print(N)
    draw(N, color=color)
    if show_control:
        P = N.coords
        draw(PolyLine(P))
        drawNumbers(P, gravity='se')
    zoomAll()


color = 1

def doit(points, degree, tangents, endtangents, t0, t1, strategy, tmult,
         Clear=False, show_control=False):
    """Show single curve with single point set"""
    global color
    if Clear or show_control:
        clear()
        color = 1
    else:
        color += 1

    print("Selected point set: %s" % points)
    Q = Coords(point_set.get(points, points))
    degree = int(degree)
    if len(Q) <= degree:
        print(f"Skipping point set: {points}: not enough points ({len(Q)}) "
              f"for degree {degree}")
        return
    drawPoints(Q)
    if strategy != 'local':
        tmult *= PolyLine(Q).length()
    if tangents == 'none':
        D = None
    if tangents == 'akim':
        D = akimTangents(Q) * tmult
    elif tangents == 'avg':
        D = PolyLine(Q).avgDirections() * tmult
    else:
        D = None
    if endtangents or strategy == 'classic':
        D0 = at.checkArray(t0, (3,), 'f') * tmult
        D1 = at.checkArray(t1, (3,), 'f') * tmult
    else:
        D0 = D1 = None
    print(f"Strategy: {strategy}")
    try:
        N = interpolationCurve(Q, degree, D, D0, D1, strategy[0])
        drawNurbs(N, color, show_control)
    except ValueError as e:
        print(e)


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
        doit(**res)

def showAllPoints():
    if dialog.validate():
        res = dialog.results
        res['Clear'] = True
        for points in point_ids:
            res['points'] = points
            doit(**res)
            sleep(1)

def showAllStrats():
    global color
    color = 0
    clear()
    if dialog.validate():
        res = dialog.results
        res['show_control'] = False
        for strategy, degree in (
                ('local', 3), ('local', 2),
                ('classic', 3),
                ('global', 3), ('global', 2),
                ):
            res['strategy'] = strategy
            res['degree'] = degree
            doit(**res)
            sleep(1)


def timeOut():
    print(f"TIMEOUT CALLED")
    try:
        showAll()
        wait()
    finally:
        close()


def run():
    global dialog
    clear()
    setDrawOptions({'bbox': None})
    linewidth(2)
    flat()

    ## Closing this dialog should release the script lock
    items=[
        _I('points', text='Point set', choices=point_ids),
        _I('strategy', choices=['local', 'global', 'classic']),
        _I('degree', itemtype='radio', choices=['3', '2']),
        _I('tangents', choices=['akim', 'avg', 'none'],),
        _I('endtangents', False, text='Set end tangents',),
        _I('t0', (1.,0.,0.), itemtype='point', text='Start tangent'),
        _I('t1', (1.,0.,0.), itemtype='point', text='End tangent'),
        _I('tmult', 1., text='Tangent length multiplier'),
        _I('Clear', True),
        _I('show_control', False, text='Show control points'),
    ]
    dialog = Dialog(
        items=items, caption=_name, store=_name+'_ data',
        enablers=(('strategy', 'local', 'degree'),
                  ('strategy', 'global', 'degree'),
                  ('strategy', 'classic', 't0', 't1'),
                  ('endtangents', True, 't0', 't1'),
                  ),
        actions=[('Close', close), ('Clear', clear),
                 ('Show All Point Sets', showAllPoints),
                 ('Show All Strategies', showAllStrats),
                 ('Show', show)],
        default='Show',
    )
    dialog.show(timeoutfunc=timeOut)

    # Block other scripts
    scriptLock(__file__)


if __name__ == '__draw__':
    run()
# End
