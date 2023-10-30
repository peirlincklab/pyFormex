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
"""Inside

This example shows how to find out if points are inside a closed surface.

"""
_name = 'Inside'
_level = 'normal'
_topics = ['surface', 'vtk']
_techniques = ['inside', 'timer', 'multitask']

from pyformex.gui.draw import *

filename = getcfg('datadir') / 'horse.off'


def getData():
    """Ask input data from the user."""
    dia = Dialog(caption=_name, store=_name+'_data', items=[
        _G('Surface', [
            _I('surface', 'file', choices=['file', 'sphere']),
            _I('filename', filename, text='Image file', itemtype='filename', filter='surface', mode='exist'),
            _I('grade', 8),
            _I('refine', 0),
        ]),
        _G('Points', [
            _I('points', 'grid', choices=['grid', 'random']),
            _I('npts', [30, 30, 30], itemtype='ivector'),
            _I('scale', [1., 1., 1.], itemptype='point'),
            _I('trl', [0., 0., 0.], itemptype='point'),
        ]),
        _I('method', choices=['gts', 'vtk']),
        _I('multi', True, text='Allow parallel processing'),
        _I('atol', 0.001),
    ], enablers = [
        ('surface', 'file', 'filename', ),
        ('surface', 'sphere', 'grade', ),
        ('method', 'gts', 'multi', ),
    ])
    res = dia.getResults()
    if res:
        globals().update(res)

    return res


def create():
    """Create a closed surface and a set of points."""
    nx, ny, nz = npts

    # Create surface
    if surface == 'file':
        S = TriSurface.read(filename).centered()
    elif surface == 'sphere':
        S = simple.sphere(ndiv=grade)

    if refine > S.nedges():
        S = S.refine(refine)

    draw(S, color='red')

    if not S.isClosedManifold():
        warning("This is not a closed manifold surface. Try another.")
        return None, None

    # Create points

    if points == 'grid':
        P = simple.regularGrid([-1., -1., -1.], [1., 1., 1.], [nx-1, ny-1, nz-1])
    else:
        P = np.random.rand(nx*ny*nz*3)

    sc = np.array(scale)
    siz = np.array(S.sizes())
    tr = np.array(trl)
    P = Formex(P.reshape(-1, 3)).resized(sc*siz).centered().translate(tr*siz)
    draw(P, marksize=1, color='black')
    zoomAll()

    return S, P


def testInside(S, P, method, atol, multi):
    """Test which of the points P are inside surface S"""

    print("Testing %s points against %s faces" % (P.nelems(), S.nelems()))

    bb = bboxIntersection(S, P)
    drawBbox(bb, color=np.array(red), linewidth=2)
    P = Coords(P).points()

    if method == 'vtk' and not utils.Module.has('vtk'):
        warning("You need to install python-vtk!")
        return

    with Timer() as t:
        ind = S.inside(P, method=method, tol=atol, multi=multi)

    print(f"{method}_inside: {P.shape[0]} points / {S.nelems()} faces:"
          f" found {len(ind)} inside points in {t.mem:.6f} seconds")

    if len(ind) > 0:
        draw(P[ind], color=green, marksize=3, ontop=True, nolight=True, bbox='last')


def run():
    resetAll()
    clear()
    smooth()

    if getData():
        S, P = create()
        if S:
            testInside(S, P, method, atol, multi)


if __name__ == '__draw__':
    run()
# End
