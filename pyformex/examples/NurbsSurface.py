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

"""NurbsSurface

This example illustrates the functionalities of the nurbs plugin for
drawing Nurbs surfaces.

As the nurbs plugin is still under development, so is this example.

The example creates a Nurbs surface from a 6x4 grid of control points.
The grid is originally created in the x,y plane, but two points of it
are moved out of the plane: one in positive z-direction, one in negative
direction. The Nurbs surface has degree 3 in the x-direction and degree 2
in the y-direction.

Several parts can be drawn on request of the user:

- points: the control points used to construct the Nurbs
- surf: the Nurbs surface
- curves: Nurbs curves created by using the grid points in single
  parametric directions
- curvepoints: points on the Nurbs curves, at fixed parametric values
- isocurves: curves on the surface for given parametric values. These curves
  are actually Nurbs curves with the above curvepoints as control points.
- randompoints: a set of randomly distributed points on the surface.

"""
_level = 'advanced'
_topics = ['geometry', 'surface']
_techniques = ['nurbs']

from pyformex.gui.draw import *
from pyformex.plugins.nurbs import *

AN = utils.autoName('nurbssurface')

# Default data

draw_points = True
draw_surf = True
draw_curves = False
draw_curvepoints = False
draw_isocurves = False
draw_tangents = False
draw_randompoints = False



def run():

    global options

    clear()
    smoothwire()

    createView('myview', angles=(0, -15, 0), addtogui=True)
    view('myview')

    #############################
    ####   DATA
    #############################

    # size of the control point grid
    nx, ny = 6, 4

    # degree of the NURBS surface
    px, py = 3, 2

    # To create a 3D surface, we add z-elevation to some points of the grid
    # The list contains tuples of grid position (x,y) and z-value of peaks
    peaks = [
        (1, 1, 3.),
        (2, 2, -2.)
        ]

    # number of isoparametric curves (-1) to draw on the surface
    kx, ky = 10, 4

    # number of random points
    nP = 100

    # what to draw
    options = askItems(store=globals(), items=[
        _I('draw_points',),
        _I('draw_surf',),
        _I('draw_curves',),
        _I('draw_curvepoints', ),
        _I('draw_isocurves', ),
        _I('draw_tangents', ),
        _I('draw_randompoints', ),
        ])

    if not options:
        return

    print(options)

    ###########################
    ####   CONTROL GRID
    ###########################

    # create the grid of control points
    X = Formex(origin()).replicm((nx, ny)).coords.reshape(ny, nx, 3)
    for x, y, v in peaks:
        X[x, y, 2] = v

    if draw_points:
        # draw the numbered control points
        draw(X, nolight=True)
        drawNumbers(X.reshape(-1, 3), trl=[0.05, 0.05, 0.0])

    ###########################
    ####   NURBS SURFACE
    ###########################

    # create the Nurbs surface
    S = NurbsSurface(X, degree=(px, py))
    pf.PF[next(AN)] = S

    if draw_surf:
        # draw the Nurbs surface, with random colors
        #colors = 0.5*np.random.rand(*S.coords.shape)
        draw(S, color=red)  # colors[..., :3])
    return

    ###########################
    ####   ISOPARAMETRIC CURVES
    ###########################

    # define isoparametric values for the isocurves
    u = uniformParamValues(kx)  # creates kx+1 u-values
    v = uniformParamValues(ky)

    # create Nurbs curves through 1-d sets of control points, in both directions
    Cu = [NurbsCurve(X[i], degree=px, knots=S.uknots) for i in range(ny)]
    Cv = [NurbsCurve(X[:, i], degree=py, knots=S.vknots) for i in range(nx)]
    if draw_curves:
        # draw the Nurbs curves
        draw(Cu, color=red, nolight=True, ontop=True)
        draw(Cv, color=blue, nolight=True, ontop=True)

    # get points on the Nurbs curves at isoparametric values
    CuP = Coords.concatenate([Ci.pointsAt(u) for Ci in Cu]).reshape(ny, kx+1, 3)
    CvP = Coords.concatenate([Ci.pointsAt(v) for Ci in Cv]).reshape(nx, ky+1, 3)
    if draw_curvepoints:
        # draw the isoparametric points
        draw(CuP, marksize=10, ontop=True, nolight=True, color=red)
        drawNumbers(CuP, color=red)
        draw(CvP, marksize=10, ontop=True, nolight=True, color=blue)
        drawNumbers(CvP, color=blue)

    # Create the isocurves: they are Nurbs curves using the isoparametric points
    # in the cross direction as control points
    # First swap the isoparametric point grids, then create curves
    PuC = CuP.swapaxes(0, 1)
    PvC = CvP.swapaxes(0, 1)
    Vc = [NurbsCurve(PuC[i], degree=py, knots=S.vknots) for i in range(kx+1)]
    Uc = [NurbsCurve(PvC[i], degree=px, knots=S.uknots) for i in range(ky+1)]
    if draw_isocurves:
        # draw the isocurves
        draw(Vc, color=red, linewidth=2, nolight=True)  # ,ontop=True)
        color = 0.5*np.random.rand(Uc[0].coords.shape[0], 3)
        print(color.shape)
        print(color)
        draw(Uc, color=[red, yellow, green, cyan, blue, magenta], linewidth=3, nolight=True)  # ,ontop=True)

    ###########################
    ####   POINTS and TANGENTS
    ###########################

    if draw_tangents:
        uv = np.zeros((len(u), len(v), 2))
        uv[..., 0] = u.reshape(-1, 1)
        uv[:, :, 1] = v
        uv = uv.reshape(-1, 2)
        D = S.derivs(uv, (1, 1))
        P = D[0, 0]
        U = D[1, 0]
        V = D[0, 1]
        drawVectors(P, U, size=1, color=red, ontop=True)
        drawVectors(P, V, size=1, color=blue, ontop=True)


    ###########################
    ####   RANDOM POINTS
    ###########################

    # create random parametric values and compute points on the surface
    u = np.random.random(2*nP).reshape(-1, 2)
    P = S.pointsAt(u)
    if draw_randompoints:
        # draw the random points
        draw(P, color=black, nolight=True, ontop=True)


if __name__ == '__draw__':
    run()
# End
