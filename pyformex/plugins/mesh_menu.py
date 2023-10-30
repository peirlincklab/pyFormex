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

"""mesh_menu.py

Plugin menu with mesh operations.
"""

import pyformex as pf
from pyformex.gui import menu
from pyformex.gui import draw as gs
from pyformex.mesh import Mesh
from pyformex.gui.draw import *

_name_ = 'mesh_menu_'

##################### selection and annotations ##########################

selection = pf.GS

##################### Mesh functions ######################################

def doOnSelectedMeshes(method):
    """Apply some method to all selected meshes"""
    meshes = selection.checkOrAsk(allowed=Mesh)
    if not meshes:
        return

    meshes = [method(m) for m in meshes]
    gs.export2(selection.names, meshes)
    gs.clear()
    selection.draw()


def reverseMesh():
    """Fuse the nodes of a Mesh"""
    doOnSelectedMeshes(Mesh.reverse)

def removeDegenerate():
    doOnSelectedMeshes(Mesh.removeDegenerate)

def removeDuplicate():
    doOnSelectedMeshes(Mesh.removeDuplicate)

def compactMesh():
    """Compact the Mesh"""
    doOnSelectedMeshes(Mesh.compact)

def peelOffMesh():
    """Peel the Mesh"""
    doOnSelectedMeshes(Mesh.peel)


def fuseMesh():
    """Fuse the nodes of a Mesh"""
    meshes = selection.checkOrAsk(allowed=Mesh)
    if not meshes:
        return

    res = askItems(caption='Fuse parameters', items=[
        _I('Relative Tolerance', 1.e-5),
        _I('Absolute Tolerance', 1.e-5),
        _I('Shift', 0.5),
        _I('Points per box', 1)])
    if not res:
        return

    before = [m.ncoords() for m in meshes]
    meshes = [m.fuse(
        rtol = res['Relative Tolerance'],
        atol = res['Absolute Tolerance'],
        shift = res['Shift'],
        ppb = res['Points per box'],
        ) for m in meshes]
    after = [m.ncoords() for m in meshes]
    print("Number of points before fusing: %s" % before)
    print("Number of points after fusing: %s" % after)
    names = ["%s_fused" % n for n in selection.names]
    gs.export2(names, meshes)
    selection.set(names)
    gs.clear()
    selection.draw()


def smoothMesh():
    """Smooth the Mesh."""
    meshes = selection.checkOrAsk(allowed=Mesh)
    if not meshes:
        return

    _name = 'Smoothing parameters'
    _data = _name + '_data'
    res = askItems(caption=_name, store=_data, items=[
        _I('niter',1, min=1),
        _I('lamb', 0.5, min=0.0, max=1.0),
        _I('mu', -0.5, min=-1.0, max=0.0),
        _I('border', choices=['sep', 'fix', 'incl'],),
        _I('level', 1, min=0, max=3),
        _I('exclude', []),
        _I('weight', choices=['uniform', 'inverse', 'distance',
                              'sqinverse', 'sqdistance']),
    ],)
    if not res:
        return

    meshes = [m.smooth(**res) for m in meshes]
    export2(selection.names, meshes)
    clear()
    selection.draw()


def subdivideMesh():
    """Create a mesh by subdividing existing elements.

    """
    meshes = selection.checkOrAsk(allowed=Mesh)
    if not meshes:
        return

    eltypes = {m.elName() for m in meshes}
    print("eltypes in selected meshes: %s" % eltypes)
    if len(eltypes) > 1:
        warning("I can only subdivide meshes with the same element type\nPlease narrow your selection before trying conversion.")
        return

    oktypes = ['tri3', 'quad4']
    eltype = eltypes.pop()
    if eltype not in ['tri3', 'quad4']:
        warning("I can only subdivide meshes of types %s" % ', '.join(oktypes))
        return

    if eltype == 'tri3':
        items = [_I('ndiv', 4)]
    elif eltype == 'quad4':
        items = [_I('nx', 4), _I('ny', 4)]
    res = askItems(items)

    if not res:
        return
    if eltype == 'tri3':
        ndiv = [res['ndiv']]
    elif eltype == 'quad4':
        ndiv = [res['nx'], res['ny']]
    meshes = [m.subdivide(*ndiv) for m in meshes]
    gs.export2(selection.names, meshes)
    gs.clear()
    selection.draw()


def convertMesh():
    """Transform the element type of the selected meshes.

    """
    meshes = selection.checkOrAsk(allowed=Mesh)
    if not meshes:
        return

    eltypes = {m.eltype for m in meshes}
    print("eltypes in selected meshes: %s" % [str(e) for e in eltypes])
    if len(eltypes) > 1:
        warning("I can only convert meshes with the same element type\nPlease narrow your selection before trying conversion.")
        return
    if len(eltypes) == 1:
        fromtype = eltypes.pop()
        choices = ["%s -> %s" % (fromtype, to) for to in fromtype.conversions]
        if len(choices) == 0:
            warning("Sorry, can not convert a %s mesh"%fromtype)
            return
        res = askItems([
            _I('_conversion', itemtype='vradio', text='Conversion Type', choices=choices),
            _I('_compact', True),
            _I('_merge', itemtype='hradio', text="Merge Meshes", choices=['None', 'Each', 'All']),
            ])
        if res:
            globals().update(res)
            print("Selected conversion %s" % _conversion)
            totype = _conversion.split()[-1]
            names = ["%s_converted" % n for n in selection.names]
            meshes = [m.convert(totype) for m in meshes]
            if _merge == 'Each':
                meshes = [m.fuse() for m in meshes]
            elif  _merge == 'All':
                from pyformex.mesh import mergeMeshes
                #print(_merge)
                coords, elems = mergeMeshes(meshes)
                #print(elems)
                ## names = [ "_merged_mesh_%s" % e.nplex() for e in elems ]
                ## meshes = [ Mesh(coords,e,eltype=meshes[0].eltype) for e in elems ]
                ## print meshes[0].elems
                meshes = [Mesh(coords, e, m.prop, m.eltype) for e, m in zip(elems, meshes)]
            if _compact:
                print("compacting meshes")
                meshes = [m.compact() for m in meshes]

            gs.export2(names, meshes)
            selection.set(names)
            gs.clear()
            selection.draw()


def renumberMesh(order='elems'):
    """Renumber the nodes of the selected Meshes.

    """
    meshes = selection.checkOrAsk(allowed=Mesh)
    if not meshes:
        return

    meshes = [M.renumber(order) for M in meshes]
    gs.export2(selection.names, meshes)
    gs.clear()
    selection.draw()


def renumberMeshRandom():
    """Renumber the nodes of the selected Meshes in random order.

    """
    renumberMesh('random')


def renumberMeshFront():
    """Renumber the nodes of the selected Meshes in random order.

    """
    renumberMesh('front')


def getBorderMesh():
    """Create the border Meshes for the selected Meshes.

    """
    meshes = selection.checkOrAsk(allowed=Mesh)
    if not meshes:
        return

    meshes = [M.getBorderMesh() for M in meshes]
    names = ["%s_border" % n for n in selection.names]
    gs.export2(names, meshes)
    selection.set(names)
    gs.clear()
    selection.draw()


def colorByFront():
    S = selection.check(single=True)
    if S:
        res  = askItems([_I('front type', choices=['node', 'edge']),
                         _I('number of colors', -1),
                         _I('front width', 1),
                         _I('start at', 0),
                         _I('first prop', 0),
                         ])
        pf.app.processEvents()
        if res:
            selection.remember()
            with Timer() as t:
                ftype = res['front type']
                nwidth = res['front width']
                maxval = nwidth * res['number of colors']
                startat = res['start at']
                firstprop = res['first prop']
                if ftype == 'node':
                    p = S.frontWalk(level=0, maxval=maxval, startat=startat)
                else:
                    p = S.frontWalk(level=1, maxval=maxval, startat=startat)
                S.setProp(p//nwidth + firstprop)
            nprops = len(S.propSet())
            print(f"Colored in {nprops} parts ({t.mem:.6f} sec.)")
            selection.draw()


def partitionByConnection():
    S = selection.check(single=True)
    if S:
        selection.remember()
        with Timer() as t:
            S.prop = S.partitionByConnection()
        nprops = S.prop.max()+1
        print(f"Partitioned in {nprops} parts ({t.mem:.6f} sec.)")
        selection.draw()

################### menu #################

def create_menu(before='help'):
    """Create the Mesh menu."""
    MenuData = [
        ("&Reverse mesh elements", reverseMesh),
        ("&Convert element type", convertMesh),
        ("&Compact", compactMesh),
        ("&Fuse nodes", fuseMesh),
        ("&Remove degenerate", removeDegenerate),
        ("&Remove duplicate", removeDuplicate),
        ("&Renumber nodes", [
            ("In element order", renumberMesh),
            ("In random order", renumberMeshRandom),
            ("In frontal order", renumberMeshFront),
            ]),
        ("&Subdivide", subdivideMesh),
        ("&Smooth", smoothMesh),
        ("&Get border mesh", getBorderMesh),
        ("&Peel off border", peelOffMesh),
        ("&Color By Front", colorByFront),
        ("&Partition By Connection", partitionByConnection),
        ("---", None),
    ]
    m = menu.Menu('Mesh', items=MenuData, parent=pf.GUI.menu, before=before)
    return m


# End
