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
"""Polyline

Examples of PolyLine approximation of curves and coarsening of PolyLines.

"""
_level = 'normal'
_topics = ['geometry', 'curve']
_techniques = ['widgets', 'persistence', 'import', 'polyline', 'coarsening']

from pyformex.gui.draw import *


def drawCurve(dset, closed, nseg, chordal, method, coarsen, tol, maxlen, refine, numbers):
    global S
    P = dataset[dset]
    S = BezierSpline(P, closed=closed)

    if method == 'chordal':
        nseg = None

    PL = S.approx(nseg=nseg, chordal=chordal, equidistant=method=='equidistant')
    draw(PL, color=red)
    draw(PL.pointsOn(), color=black)
    if numbers:
        drawNumbers(PL.pointsOn(), color=black)

    if coarsen:
        PC = PL.coarsen(tol, maxlen)
        print("Coarsened from %s to %s points" % (PL.npoints(), PC.npoints()))
        if refine:
            print(PC)
            PC = PC.refine(maxlen)
            print(PC)
        draw(PC, color=blue)
        draw(PC.pointsOn(), color=blue, marksize=10)


dataset = [
    Coords([[1., 0., 0.], [0., 1., 0.], [-1., 0., 0.],  [0., -1., 0.]]),
    Coords([[6., 7., 12.], [9., 5., 6.], [11., -2., 6.],  [9.,  -4., 14.]]),
    Coords([[-5., -10., -4.], [-3., -5., 2.], [-4., 0., -4.], [-4.,  5, 4.],
            [6., 3., -1.], [6., -9., -1.]]),
    Coords([[-1., 7., -14.], [-4., 7., -8.], [-7., 5., -14.], [-8., 2., -14.],
            [-7.,  0, -6.], [-5., -3., -11.], [-7., -4., -11.]]),
    Coords([[-1., 1., -4.], [1., 1., 2.], [2.6, 2., -4.], [2.9,  3.5, 4.],
            [2., 4., -1.], [1., 3., 1.], [0., 0., 0.], [0., -3., 0.],
            [2., -1.5, -2.], [1.5, -1.5, 2.], [0., -8., 0.], [-1., -8., -1.],
            [3., -3., 1.]]),
    Coords([[0., 1., 0.], [0., 0.1, 0.], [0.1, 0., 0.],  [1., 0., 0.]]),
    Coords([[0., 1., 0.], [0., 0., 0.], [0., 0., 0.], [1., 0., 0.]]),
    Coords([[0., 0., 0.], [1., 0., 0.], [1., 1., 1.], [0., 1., 0.]]).scale(3),
    ]

_items = [
    _I('DataSet', '0', choices=[str(i) for i in range(len(dataset))]),
    _I('Closed', False),
    _I('Method', choices=['chordal', 'parametric', 'equidistant'], text='Approximation Method'),
    _I('Chordal', 0.01),
    _I('Nseg', 4),
    _G('Coarsen', [
        _I('Tol', 0.01),
        _I('UseMaxlen', False),
        _I('Maxlen', 0.1),
        _I('Refine', False),
        ], check=False),
    _I('Clear', True),
    _I('ShowNumbers', True),
    ]

_enablers = [
    ('Method', 'chordal', 'Chordal'),
    ('Method', 'parametric', 'Nseg'),
    ('Method', 'equidistant', 'Nseg'),
    ('UseMaxlen', True, 'Maxlen', 'Refine'),
    ]


clear()
setDrawOptions({'bbox': 'auto', 'view': 'front'})
linewidth(2)
flat()

dialog = None

from pyformex import script

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



def show():
    global Maxlen
    if not dialog.validate():
        return
    res = dialog.results
    globals().update(res)
    if not UseMaxlen:
        Maxlen = None
    export({'_Curves_data_': res})
    if Clear:
        clear()
    setDrawOptions({'bbox': 'auto'})
    drawCurve(int(DataSet), Closed, Nseg, Chordal, Method, Coarsen, Tol, Maxlen, Refine, ShowNumbers)
    setDrawOptions({'bbox': None})


def timeOut():
    try:
        show()
    finally:
        close()


def run():
    global dialog
    dialog = Dialog(
        items=_items,
        enablers=_enablers,
        caption='Curve parameters',
        actions = [('Close', close), ('Clear', clear), ('Show', show)],
        default='Show')

    if '_Curves_data_' in pf.PF:
        #print pf.PF['_Curves_data_']
        dialog.updateData(pf.PF['_Curves_data_'])

    dialog.show(timeoutfunc=timeOut)
    # Block other scripts
    scriptLock(__file__)



if __name__ == '__draw__':
    run()
# End
