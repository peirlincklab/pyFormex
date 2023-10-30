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

"""Interactive 2D drawing in a 3D space

This pyFormex plugin provides some interactive 2D drawing functions.
While the drawing operations themselves are in 2D, they can be performed
on a plane with any orientation in space. The constructed geometry always
has 3D coordinates in the global cartesian coordinate system.
"""

import numpy as np

from pyformex.geomtools import triangleCircumCircle
from pyformex.curve import *
from pyformex.plugins.nurbs import *
from pyformex.simple import circle
from pyformex.plugins import objects
from pyformex.plugins.geometry_menu import geomList
from pyformex.gui.draw import *
from pyformex.opengl.decors import Grid

draw_mode_2d = ['point', 'polyline', 'curve', 'nurbs', 'circle']
autoname = {}
autoname['point'] = utils.autoName('coords')
autoname['polyline'] = utils.autoName('polyline')
autoname['curve'] = utils.autoName('bezierspline')
autoname['nurbs'] = utils.autoName('nurbscurve')
autoname['circle'] = utils.autoName('circle')


_preview = False


def set_preview(onoff=True):
    global _preview
    _preview = onoff


def toggle_preview(onoff=None):
    global _preview
    if onoff is None:
        try:
            onoff = pf.GUI.menu.item(_menu).item('preview').isChecked()
        except Exception:
            onoff = not _preview
    _preview = onoff


def draw2D(mode='point', npoints=-1, zvalue=0., zplane=None, func=None,
           coords=None, preview=None):
    """Enter interactive drawing mode and return the 2D drawing.

    Drawing is done on a plane perpendicular to the camera axis, at a specified
    z value. If zplane is specified, it is used directly. Else, it is computed
    from projecting the point [0.,0.,zvalue]. Specifying zvalue is in
    most cases easier for the user.
    See meth:`QtCanvas.idraw` for more details.
    This function differs in that it provides default displaying
    during the drawing operation and a button to stop the drawing operation.

    (TODO) The drawing can be edited using the methods 'undo', 'clear' and
    'close', which are presented in a combobox.
    """
    if pf.canvas.drawmode is not None:
        warning("You need to finish the previous drawing operation first!")
        return
    if func is None:
        func = highlightDrawing
    if preview is None:
        preview = _preview
    if zplane is None:
        zplane = pf.canvas.project(0., 0., zvalue)[2]
        print('Projected zplane = %s' % zplane)
    return pf.canvas.idraw(mode, npoints, zplane, func, coords, preview)


obj_params = {}

def drawnObject(points, mode='point'):
    """Return the geometric object resulting from draw2D points"""
    minor = None
    if '_' in mode:
        mode, minor = mode.split('_')
    closed = minor=='closed'

    if mode == 'point':
        return points
    elif mode == 'polyline':
        if points.ncoords() < 2:
            return None
        closed = obj_params.get('closed', None)
        return PolyLine(points, closed=closed)
    elif mode == 'curve' and points.ncoords() > 1:
        curl = obj_params.get('curl', None)
        closed = obj_params.get('closed', None)
        return BezierSpline(points, curl=curl, closed=closed)
    elif mode == 'nurbs':
        degree = obj_params.get('degree', None)
        if points.ncoords() <= degree:
            return None
        closed = obj_params.get('closed', None)
        return NurbsCurve(points, degree=degree, closed=closed)
    elif mode == 'circle' and points.ncoords() % 3 == 0:
        R, C, N = triangleCircumCircle(points.reshape(-1, 3, 3))
        circles = [circle(r=r, c=c, n=n) for r, c, n in zip(R, C, N)]
        if len(circles) == 1:
            return circles[0]
        else:
            return circles
    else:
        return None


def highlightDrawing(canvas):
    """Highlight a temporary drawing on the canvas.

    pts is an array of points.
    """
    canvas.removeHighlight()
    PA = draw(canvas.drawing, bbox='last')
    if PA:
        PA.setHighlight()
    obj = drawnObject(canvas.drawing, mode=canvas.mode)
    if obj is not None:
        OA = draw(obj, bbox='last')
        if OA:
            OA.setHighlight()
    canvas.update()


# def drawPoints2D(mode='point', npoints=-1, zvalue=0., coords=None):
#     """Draw points in 2D on the xy-plane with given z-value"""
#     return draw2D(mode='point', npoints=npoints, zvalue=zvalue, coords=coords)


def drawObject2D(mode, npoints=-1, zvalue=0., coords=None):
    """Draw a 2D opbject in the xy-plane with given z-value"""
    points = draw2D(mode, npoints=npoints, zvalue=zvalue, coords=coords)
    return drawnObject(points, mode=mode)


def selectObject(mode=None):
    selection = objects.drawAble(like=mode+'-')
    res = selectItems(selection.listAll(), caption='Known %ss' % mode,
        sort=True)
    # UNFINISHED

###################################

the_zvalue = 0.

def draw_object(mode, npoints=-1, zvalue=the_zvalue):
    print("z value = %s" % zvalue)
    points = draw2D(mode, npoints=-1, zvalue=zvalue)
    if points is None:
        return
    #print("POINTS %s" % points)
    obj = drawnObject(points, mode=mode)
    if obj is None:
        pf.canvas.removeHighlight()
        return
    print("OBJECT IS %s:\n%s" % (mode, obj))
    res = askItems([
        _I('name', autoname[mode].peek(), text='Name for storing the object'),
        _I('color', 'blue', 'color', text='Color for the object'),
        ])
    if not res:
        return

    name = res['name']
    color = res['color']
    if name == autoname[mode].peek():
        next(autoname[mode])
    export({name: obj})
    pf.canvas.removeHighlight()
    draw(points, color='black', nolight=True)
    if mode != 'point':
        draw(obj, color=color, nolight=True)
    if mode == 'nurbs':
        print("DRAWING KNOTS")
        draw(obj.knotPoints(), color=color, marksize=5)
    return name


def draw_points(npoints=-1):
    return draw_object('point', npoints=npoints)
def draw_polyline():
    res = askItems([('closed', False)])
    obj_params.update(res)
    return draw_object('polyline')
def draw_curve():
    global obj_params
    res = askItems([('curl', 1./3.), ('closed', False)])
    obj_params.update(res)
    return draw_object('curve')
def draw_nurbs():
    global obj_params
    res = askItems([('degree', 3), ('closed', False)])
    obj_params.update(res)
    return draw_object('nurbs')
def draw_circle():
    return draw_object('circle')


def objectName(actor):
    """Find the exported name corresponding to a canvas actor"""
    if hasattr(actor, 'object'):
        obj = actor.object
        print("OBJECT", type(obj))
        for name in pf.PF:
            print(name)
            print(named(name))
            if named(name) is obj:
                return name
    return None


def splitPolyLine(c):
    """Interactively split the specified polyline"""
    pf.options.debug = 1
    XA = draw(c.coords, clear=False, bbox='last', nolight=True)
    k = pickPoints(filter='single', oneshot=True, pickable=[XA])
    pf.canvas.pickable = None
    undraw(XA)
    if 0 in k:
        at = k[0]
        print(at)
        return c.split(at)
    else:
        return []


def split_curve():
    k = pickActors(filter='single', oneshot=True)
    if -1 not in k:
        return
    nr = k[-1][0]
    print("Selecting actor %s" % nr)
    actor = pf.canvas.actors[nr]
    print("Actor", actor)
    name = objectName(actor)
    print("Enter a point to split %s" % name)
    c = actor.object
    print("Object", c)
    cs = splitPolyLine(c)
    if len(cs) == 2:
        draw(cs[0], color='red')
        draw(cs[1], color='green')


_grid_data = [
    _I('autosize', False),
    _I('dx', 1., text='Horizontal distance between grid lines'),
    _I('dy', 1., text='Vertical distance between grid lines'),
    _I('width', 100., text='Horizontal grid size'),
    _I('height', 100., text='Vertical grid size'),
    _I('point', [0., 0., 0.], text='Point in grid plane'),
    _I('normal', [0., 0., 1.], text='Normal on the plane'),
    _I('lcolor', 'black', 'color', text='Line color'),
    _I('lwidth', 1.0, text='Line width'),
    _I('showplane', False, text='Show backplane'),
    _I('pcolor', 'white', 'color', text='Backplane color'),
    _I('alpha', '0.3', text='Alpha transparency'),
    ]


def create_grid():
    global dx, dy
    dia = Dialog(_grid_data)
    if hasattr(pf.canvas, '_grid'):
        if hasattr(pf.canvas, '_grid_data'):
            dia.updateData(pf.canvas._grid_data)
    res = dia.getResults()
    if res:
        pf.canvas._grid_data = res
        globals().update(res)

        nx = int(np.ceil(width/dx))
        ny = int(np.ceil(height/dy))
        obj = None
        if autosize:
            obj = geomList()
            if obj:
                bb = bbox(obj)
                nx = ny = 20
                dx = dy = bb.sizes().max() / nx * 2.

        ox = (-nx*dx/2., -ny*dy/2., 0.)
        if obj:
            c = bbox(obj).center()
            ox = c + ox

        planes = 'f' if showplane else 'n'
        grid = Grid(nx=(nx, ny, 0), ox=ox, dx=(dx, dy, 0.), linewidth=lwidth, linecolor=lcolor, planes=planes, planecolor=pcolor, alpha=0.3)
        remove_grid()
        pf.canvas._grid = draw(grid)


def remove_grid():
    if hasattr(pf.canvas, '_grid'):
        undraw(pf.canvas._grid)
        pf.canvas._grid = None


# End
