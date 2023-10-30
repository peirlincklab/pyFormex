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
"""Geometry menu

This is a pyFormex plugin menu. It is not intended to be loaded into
pyFormex using the plugin facility.

The geometry menu is the major interactive geometry menu in pyFormex.
Many features from other tool menus may later be inegrated into this one.
"""

import pyformex as pf
from pyformex import utils
from pyformex import fileread
from pyformex import filewrite
from pyformex import simple

from pyformex.geomfile import GeometryFile
from pyformex.gui import menu
from pyformex.plugins import objects
from pyformex.plugins import partition
from pyformex.plugins import sectionize
from pyformex.gui import draw as gs
from pyformex.gui.draw import *

_name = 'geometry_menu_'

##################### selection of objects ##########################

selection = pf.GS

#############  Print info about selction ###############

def printNames():
    print(selection.names)


def printInfo(info, allowed=None):
    """Print some info about an object"""
    for name in selection.names:
        obj = named(name)
        s = f"* {name} ({obj.__class__.__name__})"
        if allowed is None or isinstance(obj, allowed):
            s += objectInfo(obj, info)
        print(s)
    if info=='bbox' and len(selection.names) > 0:
        bb = coords.bbox(selection.check())
        print(f"** Overal bbox: {bb}")


def objectInfo(obj, info):
    """Return some info about an object"""
    if info == 'value':
        s = f"{obj}"
    elif info == 'size':
        s = (f" has {obj.ncoords()} vertices, {obj.nedges()} edges "
             f"and {obj.nelems()} faces")
    elif info == 'bbox':
        s = f" has bbox: {obj.bbox()}"
    elif info == 'type' and isinstance(obj, TriSurface):
        manifold, orientable, closed, mincon, maxcon = obj.surfaceType()
        if not manifold:
            s = " is not a manifold"
        else:
            s_closed = 'a closed' if closed else 'an open'
            s_orient = 'orientable' if orientable else 'non-orientable'
            s = f" is {s_closed} {s_orient} manifold"
    elif info == 'area':
        s = f" has area {obj.area()}"
    elif info == 'volume':
        s = f" has volume {obj.volume()}"
    elif info == 'stats' and isinstance(obj, TriSurface):
        s = f" stats:\n{obj.stats()}"
    else:
        s = ""
    return s

####### Annotation functions ########

_my_annotations = {}

def annotation(name):
    """Decorator function to register an annotation"""
    def decorator(func):
        _my_annotations[name] = func
        #kargs = {name: func}
        #pf.GS.registerAnnotation(**kargs)
        return func
    return decorator

@annotation('Object name')
def draw_object_name(n):
    """Draw the name of an object at its center."""
    return drawText(n, named(n).center())

@annotation('Element numbers')
def draw_elem_numbers(n):
    """Draw the numbers of an object's elements."""
    return drawNumbers(named(n), color='red')

@annotation('Node marks')
def draw_nodes(n):
    """Draw the nodes of an object."""
    return draw(named(n).coords, nolight=True, wait=False)

@annotation('Node numbers')
def draw_node_numbers(n):
    """Draw the numbers of an object's nodes."""
    return drawNumbers(named(n).coords, color='black')

@annotation('Edge numbers')
def draw_edge_numbers(n):
    """Draw the edge numbers of an object."""
    O = named(n)
    if isinstance(O, Mesh):
        E = Formex(O.coords[O.edges])
        return drawNumbers(E, color='blue')

@annotation('Free edges')
def draw_free_edges(n):
    """Draw the feature edges of an object."""
    O = named(n)
    if isinstance(O, Mesh):
        return drawFreeEdges(O, color='red')

@annotation('Bounding box')
def draw_bbox(n):
    """Draw the bbox of an object."""
    from pyformex.gui.draw import drawBbox
    return drawBbox(named(n))

@annotation('Convex hull')
def draw_convex_hull(n):
    """Draw the convex hull of a Geometry.

    """
    pf.PF['_convex_hull_'] = H = named(n).convexHull()
    draw(H, color='red')

@annotation('Convex hull 2D')
def draw_convex_hull2D(n):
    """Draw the 2D convex hulls of a Geometry.

    """
    pf.PF['_convex_hull_2D'] = H = [named(n).convexHull(i) for i in range(3)]
    draw(H, color='green')

####### TriSurface annotation functions ########

@annotation('Surface Normals')
def draw_normals(n, avg=False):
    """Draw the surface normals at centers or averaged normals at the nodes."""
    S = named(n)
    if not isinstance(S, TriSurface):
        return
    if avg:
        C = S.coords
        N = S.avgVertexNormals()
    else:
        C = S.centroids()
        N = S.normals()
    siz = pf.cfg['draw/normalsize']
    if siz == 'area' and not avg:
        siz = sqrt(S.areas()).reshape(-1, 1)
    else:
        try:
            siz = float(siz)
        except Exception:
            siz = 0.05 * C.dsize()
    if avg:
        color = 'orange'
    else:
        color = 'red'
    return drawVectors(C, N, size=siz, color=color, wait=False)

@annotation('AVG Surface Normals')
def draw_avg_normals(n):
    return draw_normals(n, True)


def shrinkRedraw():
    """Toggle the shrink mode"""
    setShrink()
    selection.draw()


def geomList():
    """Return a list with all the currently displayed geometry actors"""
    return selection.check()

def set_selection(data='geometry'):
    geometry_subclasses = {
        'formex': gs.Formex,
        'mesh': gs.Mesh,
        'surface': gs.TriSurface,
        }
    if data in geometry_subclasses:
        allowed = geometry_subclasses[data]
        data = 'geometry'
    else:
        allowed = None
        data = 'geometry'
    sel = pf.GUI.selection.get(data)
    print(f"SELECTION {data} = {sel}")
    if sel:
        res = sel.ask(allowed=allowed)
        if res is None:
            return

        if not sel.names:
            print("Nothing selected")

        selection.set(sel.names)
        selection.draw()

##################### read and write ##########################


def importGeometry(ftype=None, compr=False, multi=False, target=None,
                   select=True, draw=True):
    """Import geometry from file(s).

    Pops up a :class:`FileDialog` to select one (or more) geometry file(s) to
    be imported.

    Parameters
    ----------
    ftype: :term:`file_types`
        One or more file type strings. The popup dialog will contain a
        filter for each of these file types. Only the files matching the
        selected filte will be shown and selectable in the FileDialog.
        If not provided, it is set to a list of all known geometry file
        types in pyFormex.
    compr: bool
        If True, compressed files (with .gz or .bz2 suffices) of the
        file types in ftype will also be selectable.
    target: class
        If a file type allows returning different Geometry classes, the
        prefered target can be set.
    multi: bool
        If True, the FileDialog will allow to select multiple files and
        they will all be imported at once.
    select: bool
        If True (default), the imported geometry becomes the current
        selection in the Geometry menu.
    draw: bool
        If True (default) and ``select`` is also True, the selection
        is drawn after importing.

    """
    from pyformex.gui.dialogs import FileDialog
    if ftype is None:
        ftype = ['geometry', 'all']
    elif isinstance(ftype, list):
        pass
    else:
        ftype = [ftype]
    cur = pf.cfg['workdir']
    # if ftype == ['poly']:
    #     extra = [_I('mplex', 4)]
    # else:
    mode = 'exist' if not multi else 'multi'
    extra = []
    dia = FileDialog(filter=ftype, mode=mode, extra=extra, compr=compr)
    res = dia.getResults()
    all_obj = {}
    if res:
        files = res.pop('filename')
        if not isinstance(files, list):
            files = [files]
        for path in files:
            print(f"Reading geometry file {path}")
            with busyCursor():
                obj = readGeometry(filename=path, **res, target=target)
                export(obj)
            print("Items read: " + ', '.join([
                f"{k}:{obj[k].__class__.__name__}" for k in obj]))
            all_obj.update(obj)
            print(list(all_obj.keys()))
        if select:
            selection.set([k for k in all_obj.keys() if not k.startswith('_')])
            if draw:
                selection.draw()
                zoomAll()
        return all_obj
    return {}


def importPgf():
    importGeometry(ftype='pgf', compr=True)

def importPzf(_canvas=True, _camera=True):
    # Drawing is postponed because we may need to set canvas layout
    res = importGeometry(ftype='pzf', compr=False, draw=False)
    draw_args = {}
    if '_canvas' in res:
        if _canvas or ack("The PZF file contains canvas and camera settings.\nDo you want to apply them?"):
            pf.GUI.viewports.loadConfig(res['_canvas'])
            pf.GUI.viewports.update()
            draw_args = {'view': None} # Keep the camera view
    elif '_camera' in res:
        if _camera or ack("The PZF file contains camera settings.\nDo you want to apply them?"):
            pf.canvas.initCamera(res['_camera'])
            pf.canvas.update()
            draw_args = {'view': None} # Keep the camera view
    selection.draw(**draw_args)

def importPoly():
    importGeometry(ftype=['poly'])

def importSurface(multi=False):
    importGeometry(ftype=['surface', 'pgf', 'vtk', 'all'], compr=True,
                   multi=multi, target='surface')

def importObj():
    importGeometry(ftype='obj')

def importNeu():
    importGeometry(ftype='neu')

def importInp():
    importGeometry(ftype='inp')

def importTetgen():
    importGeometry(ftype='tetgen')

def importAny(multi=False):
    importGeometry(ftype=['geometry', 'all'], multi=multi)

def importSurfaceMulti():
    importSurface(multi=True)

def importAnyMulti():
    importAny(multi=True)

def importModel(*filenames):
    """Read one or more element meshes into pyFormex.

    Models are composed of nodes and elems stored on a .mesh file.
    One or more filenames can be specified.
    If none is given, the user will be asaked.
    """
    if not filenames:
        filenames = askFilename(".", "*.mesh", mode='multi')
        if not filenames:
            return

    with busyCursor():
        for f in filenames:
            fn = Path(f)
            d = fileread.readMeshFile(fn)
            modelname = fn.stem
            export({modelname: d})
            M = fileread.extractMeshes(d)
            names = ["%s-%d"%(modelname, i) for i in range(len(M))]
            export2(names, M)


def readInp(fn=None):
    """Read an Abaqus .inp file and convert to pyFormex .mesh.

    """
    if fn is None:
        fn = askFilename(".", "*.inp", mode='multi')
        if not fn:
            return

        with busyCursor():
            for f in fn:
                fileread.convertInp(f)
        return


def exportGeometry(ftype, single=False, compr=True, allowed=None, **kargs):
    """Write geometry to file.

    Parameters
    ----------
    ftype: str
        The output file format. This is the filename extension in lower case
        and without a leading dot.
    single: bool
        If True, only a single object can be written to the file.
    compr: bool
        If True, transparent compression is supported for the format.
    allowed: class | tuple of class
        Allowed Geometry types for this format.
    """
    if ftype=='pzf':
        from pyformex.gui.menus.Globals import database as db
    else:
        db = selection
    if not db.checkOrAsk(single=single, allowed=allowed):
        return
    print(f"Exporting {list(db.keys())}")
    def changeSelection(buttons):
        print(buttons)
        item = buttons.parent
        db.ask(single=single, allowed=allowed)
        item.setValue(len(db.names))
    if ftype=='pzf':
        kargs['extra'].append(
            _I('_select', len(db.names), itemtype='info',
               text=f"Number of selected objects",
               buttons=[('Change selection', changeSelection)]))

    cur = pf.cfg['workdir']
    res = askFile(cur=cur, filter=ftype, compr=compr, **kargs)
    if res:

        # convert widget data to writeGeometry parameters
        if ftype == 'pzf':
            res.pop('_select')
            env = res.pop('environ')
            if env == 'Camera':
                obj['_camera'] = True
            elif env == 'Canvas':
                obj['_canvas'] = True

        fn = res.pop('filename')
        print(f"Writing geometry file {fn}")
        nobj = writeGeometry(fn, db.odict(), compr=compr, **res)
        print(f"Objects written: {nobj}")


def exportPzf():
    exportGeometry('pzf', single=False, extra=[
        _I('environ', choices=['None', 'Camera', 'Canvas'],
           itemtype='hradio', text='Add environment',),
    ])

def exportPgf():
    kargs = {
        'compr': True,
        'compression': 4,
        'fmode': 'binary',
    }
    exportGeometry('pgf', single=False, **kargs)

def exportOff():
    exportGeometry('off', single=True, allowed=(Mesh, Polygons))

def exportObj():
    exportGeometry('obj', single=True, allowed=(Mesh, Polygons))

def exportPly():
    exportGeometry('ply', single=True, allowed=(Mesh, Polygons))

def exportNeu():
    exportGeometry('neu', single=True, allowed=Mesh)

def exportStl():
    exportGeometry('stl', single=True, allowed=TriSurface, extra=[
        _I('binary', True),
        _I('color', 'red', itemtype='color'),
        _I('alpha', 0.5),
    ])

def exportGts():
    exportGeometry('gts', single=True, allowed=TriSurface)

def exportSurf():
    exportGeometry(['smesh', 'vtp', 'vtk'],
                   single=True, allowed=TriSurface, compr=False)

def exportInp():
    exportGeometry(['inp'], single=True, allowed=Mesh, extra=[
        _I('eltype', 'ELTYPE', text='Abaqus element type (required)'),
    ])

def exportMesh():
    exportGeometry(['*'], single=True, allowed=Mesh, extra=[
        _I('writer', 'meshio', itemtype='info'),
    ])

# TODO: this should be merged with export_surface
def exportWebgl():
    F = selection.check(single=True)
    if F:
        fn = askNewFilename(pf.cfg['workdir'], 'stl')
        if fn:
            print("Exporting surface model to %s" % fn)
            with busyCursor():
                F.webgl(fn)


def convertGeometryFile():
    """Convert pyFormex geometry file to latest format."""
    cur = pf.cfg['workdir']
    fn = askFilename(cur=cur, filter=['pgf', 'all'])
    if fn:
        from pyformex.geomfile import GeometryFile
        print("Converting geometry file %s to version %s" % (fn, GeometryFile._version_))
        GeometryFile(fn).rewrite()

##################### properties ##########################


def setAttributes():
    """Set the attributes of a collection."""
    FL = selection.check()
    if FL:
        name = selection.names[0]
        F = FL[0]
        try:
            color = F.color
        except Exception:
            color = 'black'
        try:
            alpha = F.alpha
        except Exception:
            alpha = 0.7
        try:
            visible = F.visible
        except Exception:
            visible = True
        res = askItems([
            _I('caption', name),
            _I('color', color, itemtype='color'),
            _I('alpha', alpha, itemtype='fslider', min=0.0, max=1.0),
            _I('visible', visible, itemtype='bool'),
            ])
        if res:
            color = res['color']
            print(color)
            for F in FL:
                F.color = color
            selection.draw()


##################### conversion ##########################

def toFormex(suffix=''):
    """Transform the selected Geometry objects to Formices.

    If a suffix is given, the Formices are stored with names equal to the
    object names plus the suffix, else, the original object names will be
    reused.
    """
    if not selection.check():
        selection.ask()

    if not selection.names:
        return

    names = selection.names
    if suffix:
        names = [n + suffix for n in names]

    values = [named(n).toFormex() for n in names]
    export2(names, values)

    clear()
    selection.draw()


def toMesh(suffix=''):
    """Transform the selected Geometry objects to Meshes.

    If a suffix is given, the Meshes are stored with names equal to the
    Formex names plus the suffix, else, the Formex names will be used
    (and the Formices will thus be cleared from memory).
    """
    if not selection.check():
        selection.ask()

    if not selection.names:
        return

    names = selection.names
    objects = [named(n) for n in names]
    if suffix:
        names = [n + suffix for n in names]

    print("CONVERTING %s" % names)
    meshes =  dict([(n, o.toMesh()) for n, o in zip(names, objects) if hasattr(o, 'toMesh')])
    print("Converted %s" % list(meshes.keys()))
    export(meshes)

    selection.set(list(meshes.keys()))


def toSurface(suffix=''):
    """Transform the selected Geometry objects to TriSurfaces.

    If a suffix is given, the TriSurfaces are stored with names equal to the
    Formex names plus the suffix, else, the Formex names will be used
    (and the Formices will thus be cleared from memory).
    """
    if not selection.check():
        selection.ask()

    if not selection.names:
        return

    names = selection.names
    objects = [named(n) for n in names]

    ok = [o.nplex()==3 for o in objects]
    print(ok)
    if not all(ok):
        warning("Only objects with plexitude 3 can be converted to TriSurface. I can not convert the following objects: %s" % [n for i, n in zip(ok, names) if not i])
        return

    if suffix:
        names = [n + suffix for n in names]

    print("CONVERTING %s" % names)
    surfaces =  dict([(n, TriSurface(o)) for n, o in zip(names, objects)])
    print("Converted %s" % list(surfaces.keys()))
    export(surfaces)

    selection.set(list(surfaces.keys()))


#############################################
### Perform operations on selection #########
#############################################


def scaleSelection():
    """Scale the selection."""
    FL = List(selection.checkOrAsk())
    if FL:
        res = askItems(caption = 'Scale Parameters', items=[
            _I('uniform', True),
            _I('scale1', 1.0, text='Uniform scale'),
            _I('scale3', (1.0, 1.0, 1.0), itemtype='point',
               text='Non-uniform scale'),
            ], enablers=[
                ('uniform', True, 'scale1'),
                ('uniform', False, 'scale3'),
            ])
        if res:
            scale = res['scale1'] if res['uniform'] else res['scale3']
            selection.changeValues(FL.scale(scale=scale))
            selection.drawChanges()


def translateSelection():
    """Translate the selection."""
    FL = List(selection.checkOrAsk())
    if FL:
        res = askItems(caption = 'Translation Parameters', items=[
            _C('',[
                _I('global', True,
                   tooltip='If checked, translate in global axis direction')
            ]),
            _C('',[
                _I('axis', 0, min=0, max=2)
            ]),
            _I('direction', (1.,0.,0.), itemtype='point'),
            _I('distance', 1.0),
            ], enablers=[
                ('global', True, 'axis'),
                ('global', False, 'direction'),
            ])
        if res:
            dir = res['axis'] if res['global'] else res['direction']
            dist = res['distance']
            selection.changeValues([
                F.translate(dir=dir, step=dist)
                for F in FL])
            selection.drawChanges()


def centerSelection():
    """Center the selection."""
    FL = List(selection.checkOrAsk())
    if FL:
        selection.changeValues([F.translate(-F.center()) for F in FL])
        selection.drawChanges()


def rotateSelection():
    """Rotate the selection."""
    FL = List(selection.checkOrAsk())
    if FL:
        res = askItems(caption = 'Rotation Parameters', items=[
            _C('',[
                _I('global', True,
                   tooltip='If checked, rotate around global axis')
            ]),
            _C('',[
                _I('axis', 0, min=0, max=2)
            ]),
            _I('direction', (1.,0.,0.), itemtype='point',
               tooltip='Vector along rotation axis'),
            _I('point', (0.,0.,0.), itemtype='point',
               tooltip='Point on rotation axis'),
            _I('angle', 90.0, tooltip='Rotation angle in degrees'),
            ], enablers=[
                ('global', True, 'axis'),
                ('global', False, 'direction'),
            ])
        if res:
            axis = res['axis'] if res['global'] else res['direction']
            angle = res['angle']
            around = res['point']
            print(type(around))
            if all([x==0.0 for x in around]):
                around = None
            selection.changeValues([
                F.rotate(angle=angle, axis=axis, around=around) for F in FL])
            selection.drawChanges()


def permuteAxes():
    """Permute the global axes."""
    FL = List(selection.checkOrAsk())
    if FL:
        res = askItems(caption = 'Axes Permutation Parameters', items=[
            _I('order', (0,1,2), itemtype='ivector',
               tooltip='The old axes to become the new x,y,z')
            ])
        if res:
            order = res['order']
            selection.changeValues([F.permuteAxes(order) for F in FL])
            selection.drawChanges()


def clipSelection():
    """Clip the selection."""
    FL = List(selection.checkOrAsk())
    if FL:
        res = askItems(caption = 'Clip Parameters', items=[
            _I('relative', True, readonly=True),
            _I('axis', 0, min=0, max=2),
            _I('min', 0.0, min=0., max=1.),
            _I('max', 1.0, min=0., max=1.),
            _I('nodes', 'all', choices=['all', 'any', 'none']),
        ])
        if res:
            bb = bbox(FL)
            axis = res['axis']
            xmi = bb[0][axis]
            xma = bb[1][axis]
            dx = xma-xmi
            xc1 = xmi + res['min'] * dx
            xc2 = xmi + res['max'] * dx
            selection.changeValues([F.clip(F.test(
                nodes=res['nodes'], dir=axis, min=xc1, max=xc2)) for F in FL])
            selection.drawChanges()


def cutSelection():
    """Cut the selection with a plane."""
    FL = List(selection.checkOrAsk())
    if FL:
        FLok = [F for F in FL if F.nplex() in [2, 3]]
        if len(FLok) < len(FL):
            warning(
                "Currently I can only cut Geometries with plexitude 2 or 3.\n"
                "I will ignore the others.")
        FL = FLok
    if not FL:
        return
    dsize = bbox(FL).dsize()
    if dsize > 0.:
        esize = 10 ** (niceLogSize(dsize)-5)
    else:
        esize = 1.e-5
    res = askItems(caption='Cut Plane Parameters', items=[
        _I('Point', (0.0, 0.0, 0.0), itemtype='point'),
        _I('Normal', (1.0, 0.0, 0.0)),
        _I('New props', [1, 2, 2, 3, 4, 5, 6]),
        _I('Side', 'positive', itemtype='radio',
           choices=['positive', 'negative', 'both']),
        _I('Tolerance', esize),
    ])
    if res:
        P = res['Point']
        N = res['Normal']
        atol = res['Tolerance']
        p = res['New props']
        side = res['Side']
        if side == 'both':
            G = [F.cutWithPlane(P, N, side=side, atol=atol, newprops=p) for F in FL]
            draw(G[0])
            G_pos = [g[0] for g in G]
            G_neg = [g[1] for g in G]
            export(dict([('%s/pos' % n, g) for n, g in zip(selection, G_pos)]))
            export(dict([('%s/neg' % n, g) for n, g in zip(selection, G_neg)]))
            selection.set(['%s/pos' % n for n in selection] + ['%s/neg' % n for n in selection])
            selection.draw()
        else:
            selection.changeValues([F.cutWithPlane(P, N, side=side, atol=atol, newprops=p) for F in FL])
            selection.drawChanges()


#############################################
###  Property functions
#############################################


def splitProp():
    """Split the selected object based on property values"""
    F = selection.check(single=True)
    if not F:
        return

    name = selection[0]
    partition.splitProp(F, name)


#############################################
###  Create Geometry functions
#############################################

def exportSelectDraw(name, obj):
    if name == '__auto__':
        name = next(utils.autoName(obj.__class__.__name__))
    export({name: obj})
    selection.set([name])
    selection.draw()


def convertFormex(F, totype):
    if totype != 'Formex':
        F = F.toMesh()
        if totype == 'TriSurface':
            F = TriSurface(F)
    return F


def convert_Mesh_TriSurface(F, totype):
    if totype == 'Formex':
        return F.toFormex()
    else:
        F = F.toMesh()
        if totype == 'TriSurface':
            F = F.convert('tri3').toSurface()
        return F


base_patterns = [
    'l:1',
    'l:2',
    'l:12',
    'l:127',
    ]

def createGrid():
    _name = 'createGrid'
    _data = _name + '_data'
    res = askItems(caption=_name, store=_data, items=[
        _I('name', '__auto__'),
        _I('object type', 'Mesh', choices=['Formex', 'Mesh', 'TriSurface']),
        _I('base', choices=base_patterns),
        _I('n1', 4, text='nx', min=1),
        _I('n2', 2, text='ny', min=1),
        _I('t1', 1., text='stepx'),
        _I('t2', 1., text='stepy'),
        _I('taper', 0),
        _I('bias', 0.),
    ])
    if res:
        name = res.pop('name')
        objtype = res.pop('object type')
        if name == '__auto__':
            name = next(utils.autoName(objtype))
        base = res.pop('base')
        F = Formex(base).replic2(**res)
        F = convertFormex(F, objtype)
        exportSelectDraw(name,F)


def createRectangle():
    _name = 'createRectangle'
    _data = _name + '_data'
    res = askItems(caption=_name, store=_data, items=[
        _I('name', '__auto__'),
        _I('object type', 'Mesh', choices=['Formex', 'Mesh', 'TriSurface']),
        _I('nx', 1, min=1),
        _I('ny', 1, min=1),
        _I('b', 1., text='width'),
        _I('h', 1., text='height'),
        _I('bias', 0.),
        _I('diag', 'up', choices=['none', 'up', 'down', 'x-both']),
    ])
    if res:
        name = res.pop('name')
        objtype = res.pop('object type')
        if name == '__auto__':
            name = next(utils.autoName(objtype))
        F = simple.rectangle(**res)
        F = convertFormex(F, objtype)
        exportSelectDraw(name,F)


def createCube():
    _name = 'createCube'
    _data = _name + '_data'
    levels = {'volume': 3, 'faces': 2, 'edges': 1, 'points':0}
    res = askItems(caption=_name, store=_data, items=[
        _I('name', '__auto__'),
        _I('object type', 'Mesh', choices=['Formex', 'Mesh', 'TriSurface']),
        _I('level', choices=levels),
    ])
    if res:
        name = res['name']
        objtype = res.pop('object type')
        if name == '__auto__':
            name = next(utils.autoName(objtype))
        F = simple.Cube(levels[res['level']])
        print(F)
        F = convert_Mesh_TriSurface(F, objtype)
        exportSelectDraw(name, F)


def createCylinder():
    # TODO: we should reverse the surface if it is Mesh/TriSurface
    # or better: do it in simple.sphere
    _name = 'createCylinder'
    _data = _name + '_data'
    res = askItems(caption=_name, store=_data, items=[
        _I('name', '__auto__'),
        _I('object type', 'Mesh', choices=['Formex', 'Mesh', 'TriSurface']),
        _I('D', 1., text='base diameter'),
        _I('D1', 1., text='top diameter'),
        _I('L', 2., text='height'),
        _I('angle', 360.),
        _I('nl', 6, text='div_along_length', min=1),
        _I('nt', 12, text='div_along_circ', min=1),
        _I('bias', 0.),
        _I('diag', 'up', choices=['none', 'up', 'down', 'x-both']),
    ])
    if res:
        name = res.pop('name')
        objtype = res.pop('object type')
        if name == '__auto__':
            name = next(utils.autoName(objtype))
        F = simple.cylinder(**res)
        F = convertFormex(F, objtype)
        exportSelectDraw(name, F)


def createCone():
    _name = 'createCone'
    _data = _name + '_data'
    res = askItems(caption=_name, store=_data, items=[
        _I('name', '__auto__'),
        _I('object type', 'Mesh', choices=['Formex', 'Mesh', 'TriSurface']),
        _I('r', 1., text='radius'),
        _I('h', 1., text='height'),
        _I('t', 360., text='angle'),
        _I('nr', 6, text='div_along_radius', min=1),
        _I('nt', 12, text='div_along_circ', min=1),
        _I('diag', 'up', text='diagonals', choices=['none', 'up', 'down']),
        ])
    if res:
        name = res.pop('name')
        objtype = res.pop('object type')
        if name == '__auto__':
            name = next(utils.autoName(objtype))
        F = simple.sector(**res)
        F = convertFormex(F, objtype)
        exportSelectDraw(name, F)


def createSphere():
    _name = 'createSphere'
    _data = _name + '_data'
    res = askItems(caption=_name, store=_data, items=[
        _I('name', '__auto__'),
        _I('object type', 'TriSurface', choices=['Formex', 'Mesh', 'TriSurface']),
        _I('method', choices=['icosa', 'octa', 'geo']),
        _I('ndiv', 8),
        _I('nx', 36),
        _I('ny', 18),
    ], enablers=[
        ('method', 'icosa', 'ndiv'),
        ('method', 'octa', 'ndiv'),
        ('method', 'geo', 'nx', 'ny'),
    ])
    if res:
        name = res.pop('name')
        objtype = res.pop('object type')
        if name == '__auto__':
            name = next(utils.autoName(objtype))
        method = res.pop('method')
        if method in ('icosa', 'octa'):
            F = simple.sphere(res['ndiv'], base=method)
            print("Surface has %s vertices and %s faces" % (F.ncoords(), F.nelems()))
            F = convert_Mesh_TriSurface(F, objtype)
        else:
            F = simple.sphere3(res['nx'], res['ny'])
            F = convertFormex(F, objtype)
            print("Surface has  %s faces" % F.nelems())
        exportSelectDraw(name, F)


#############################################
###  Principal Axes
#############################################

def showPrincipal():
    """Show the principal axes."""
    from pyformex import coordsys
    F = selection.check(single=True)
    if not F:
        return
    # compute the axes
    if isinstance(F, TriSurface):
        res = ask("Does the model represent a surface or a volume?", ["Surface", "Volume"])
        I = F.inertia(res == "Volume")
    else:
        I = F.inertia()
    C = I.ctr
    Iprin, Iaxes = I.principal()
    at.printar("Center of gravity: ", C)
    at.printar("Principal Directions: ", Iaxes)
    at.printar("Principal Values: ", Iprin)
    at.printar("Inertia tensor: ", I)
    # display the axes
    CS = coordsys.CoordSys(rot=Iaxes, trl=C)
    size = F.dsize()
    gs.drawAxes(CS, size=size, psize=0.1*size)
    data = (I, Iprin, Iaxes)
    gs.export({'_principal_data': data})
    return data


def rotatePrincipal():
    """Rotate the selection according to the last shown principal axes."""
    try:
        data = gs.named('_principal_data')
    except Exception:
        data = showPrincipal()
    FL = selection.check()
    if FL:
        ctr, rot = data[0].ctr, data[2]
        selection.changeValues([F.trl(-ctr).rot(rot.transpose()).trl(ctr) for F in FL])
        selection.drawChanges()


def transformPrincipal():
    """Transform the selection according to the last shown principal axes.

    This is analog to rotatePrincipal, but positions the object at its center.
    """
    try:
        data = gs.named('_principal_data')
    except Exception:
        data = showPrincipal()
    FL = selection.check()
    if FL:
        ctr, rot = data[0].ctr, data[2]
        selection.changeValues([F.trl(-ctr).rot(rot.transpose()) for F in FL])
        selection.drawChanges()

# TODO: generalize for Formex + Mesh (Curve?)
################### Perform operations on Formex #######################


def concatenateSelection():
    """Concatenate the selection."""
    FL = selection.checkOrAsk(allowed=Formex)
    if not FL:
        return

    plexitude = np.array([F.nplex() for F in FL])
    if plexitude.min() == plexitude.max():
        res = gs.askItems(caption='Concatenate Formices', items=[
            _I('name', utils.autoName('formex'))
            ])
        if res:
            name = res['name']
            gs.export({name: Formex.concatenate(FL)})
            selection.set(name)
            selection.draw()
    else:
        warning('You can only concatenate Formices with the same plexitude!')

# TODO: merge with above and call concatenate
def merge():
    """Merge the selected surfaces."""
    SL = selection.check(warn=False)
    if len(SL) < 2:
        warning("You should at least select two surfaces!")
        return

    S = TriSurface.concatenate(SL)
    name = '--merged-surface--'
    export({name: S})
    selection.set(name)
    selection.draw()


def partitionSelection():
    """Partition the selection."""
    F = selection.checkOrAsk(allowed=Formex, single=True)
    if not F:
        return

    name = selection[0]
    print("Partitioning Formex '%s'" % name)
    cuts = partition.partition(F)
    print("Subsequent cutting planes: %s" % cuts)
    if gs.ack('Save cutting plane data?'):
        types = ['Text Files (*.txt)', 'All Files (*)']
        fn = gs.askNewFilename(pf.cfg['workdir'], types)
        if fn:
            gs.chdir(fn)
            fil = open(fn, 'w')
            fil.write("%s\n" % cuts)
            fil.close()


def sectionizeSelection():
    """Sectionize the selection."""
    F = selection.checkOrAsk(allowed=Formex, single=True)
    if not F:
        return

    name = selection[0]
    print("Sectionizing Formex '%s'" % name)
    ns, th, segments = sectionize.createSegments(F)
    if not ns:
        return

    sections, ctr, diam = sectionize.sectionize(F, segments, th)
    #print("Centers: %s" % ctr)
    #print("Diameters: %s" % diam)
    if ack('Save section data?'):
        types = ['Text Files (*.txt)', 'All Files (*)']
        fn = askNewFilename(pf.cfg['workdir'], types)
        if fn:
            chdir(fn)
            fil = open(fn, 'w')
            fil.write("%s\n" % ctr)
            fil.write("%s\n" % diam)
            fil.close()
    if ack('Draw circles?'):
        circles = sectionize.drawCircles(sections, ctr, diam)
        ctrline = sectionize.connectPoints(ctr)
        if ack('Draw circles on Formex ?'):
            sectionize.drawAllCircles(F, circles)
        circles = Formex.concatenate(circles)
        circles.setProp(3)
        ctrline.setProp(1)
        draw(ctrline, color='red')
        export({'circles': circles, 'ctrline': ctrline, 'flypath': ctrline})
        if ack('Fly through the Formex ?'):
            flyAlong(ctrline)
##        if ack('Fly through in smooth mode ?'):
##            smooth()
##            flytruCircles(ctr)
    selection.draw()


def fly():
    path = named('flypath')
    if path is not None:
        flyAlong(path)
    else:
        warning("You should define the flypath first")


def addOutline():
    """Draw the outline of the current rendering"""
    w, h = pf.canvas.getSize()
    res = askItems([
        _I('w', w, text='Resolution width'),
        _I('h', h, text='Resolution height'),
        _I('level', 0.5, text='Isoline level'),
#        _I('Background color', 1),
        _I('nproc', 0, text='Number of processors'),
        ])

    if not res:
        return

    G = pf.canvas.outline(size=(res['w'], res['h']), level=res['level'], nproc=res['nproc'])
    OA = draw(G, color=pf.cfg['geometry_menu/outline_color'], view='cur',
              bbox='last', linewidth=pf.cfg['geometry_menu/outline_linewidth'],
              flat=-True, ontop=True)
    if OA:
        OA = OA.object
        export({'_outline_': OA})


################### menu #################

def mySettings():
    from pyformex.gui.menus.Settings import updateSettings
    res = askItems(
        caption='Geometry menu settings', store=pf.cfg, save=False, items=[
            _I('geometry_menu/numbersontop'),
            _I('geometry_menu/bbox', choices=['bbox', 'grid']),
            _I('geometry_menu/outline_linewidth', ),
            _I('geometry_menu/outline_color', ),
            _I('_save_', False, text='Save in my preferences'),
        ])
    if res:
        updateSettings(res)


def loadDxfMenu():
    pass


def toggleNumbersOntop():
    selection.editAnnotations(ontop='')


def create_menu(before='help'):
    """Create the plugin menu."""
    # Register the annotations
    pf.GS.registerAnnotation(**_my_annotations)

    annotations_menu = [
        (f, selection.toggleAnnotation,
         dict(checkable=True, checked=selection.hasAnnotation(f), data=f))
        for f in pf.GS.registeredAnnotations()]

    MenuData = [
        ("Import", [
            (utils.fileDescription('pzf'), importPzf),
            (utils.fileDescription('pgf'), importPgf),
            (utils.fileDescription('poly'), importPoly),
            (utils.fileDescription('surface'), importSurface),
            ("Multiple surfaces", importSurfaceMulti),
            (utils.fileDescription('tetgen'), importTetgen),
            (utils.fileDescription('inp'), importInp),
            (utils.fileDescription('neu'), importNeu),
            ("All known geometry formats", importAny),
            ("Multiple imports of any kind", importAnyMulti),
            ("Abaqus .inp", [
                ("Convert Abaqus .inp file", readInp),
                ("Import Converted Abaqus Model", importModel),
                ]),
#            ("AutoCAD .dxf",[
#                ("Import .dxf or .dxftext",importDxf),
#                ("Load DXF plugin menu",loadDxfMenu),
#                ]),
            ('Upgrade pyFormex Geometry File', convertGeometryFile, dict(tooltip="Convert a pyFormex Geometry File (.pgf) to the latest format, overwriting the file.")),
            ]),
        ("Export", [
            (utils.fileDescription('pzf'), exportPzf),
            (utils.fileDescription('pgf'), exportPgf),
            (utils.fileDescription('off'), exportOff),
            (utils.fileDescription('obj'), exportObj),
            (utils.fileDescription('ply'), exportPly),
            (utils.fileDescription('neu'), exportNeu),
            (utils.fileDescription('stl'), exportStl),
            (utils.fileDescription('gts'), exportGts),
            ("Abaqus .inp", exportInp),
            ("meshio", exportMesh),
            ("Alternate Surface Formats", exportSurf),
            ("Export WebGL", exportWebgl),
            ]),
        ("---", None),
        ("Select", [
            ('Any', set_selection),
            ('Formex', set_selection, {'data': 'formex'}),
            ('Mesh', set_selection, {'data': 'mesh'}),
            ('TriSurface', set_selection, {'data': 'surface'}),
            ('PolyLine', set_selection, {'data': 'polyline'}),
            ('Curve', set_selection, {'data': 'curve'}),
            ('NurbsCurve', set_selection, {'data': 'nurbs'}),
            ]),
        ("Selection", [
            ("List", print, {'data':selection.names}),
            ('Print Type', printInfo, {'data':'type'}),
            ('Print Data Size', printInfo, {'data':'size'}),
            ('Print BBox', printInfo, {'data':'bbox'}),
            ('Print Object', printInfo, {'data':'value'}),
            ('Print Area', printInfo, {'data':'area'}),
            ('Print Volume', printInfo, {'data':'volume'}),
            ('Print Stats', printInfo, {'data':'stats'}),
            ("Clear", selection.clear),
            ("Forget", selection.forget),
            ]),
        ("(Re)Draw", selection.draw),
        ("---", None),
        ("Create Object", [
            ('Grid', createGrid),
            ('Rectangle', createRectangle),
            ('Cube', createCube),
            ('Cylinder, Cone, Truncated Cone', createCylinder),
            ('Circle, Sector, Cone', createCone),
            ('Sphere', createSphere),
            ]),
        ("Convert Objects", [
            ("To Formex", toFormex),
            ("To Mesh", toMesh),
            ("To TriSurface", toSurface),
            ## ("To PolyLine",toPolyLine),
            ## ("To BezierSpline",toBezierSpline),
            ## ("To NurbsCurve",toNurbsCurve),
            ]),
        ("Transform Objects", [
            ("Scale", scaleSelection),
            ("Translate", translateSelection),
            ("Center", centerSelection),
            ("Rotate", rotateSelection),
            ("Permute Axes", permuteAxes),
            ("Clip", clipSelection),
            ("Cut With Plane", cutSelection),
            ("Undo Last Changes", selection.undoChanges),
            ]),
        ("Property Numbers", [
            ("Set", selection.setProp),
            ("Delete", selection.delProp),
            ("Split", splitProp),
            ]),
        ("Set Attributes", setAttributes),
        ("---", None),
        ("Principal", [
            ("Show Principal Axes", showPrincipal),
            ("Rotate to Principal Axes", rotatePrincipal),
            ("Transform to Principal Axes", transformPrincipal),
            ]),
        # TODO: Needs to be reactivated or moved to scripts/attic
        # ("Formex", [
        #     ("Concatenate Selection", concatenateSelection),
        #     ("Partition Selection", partitionSelection),
        #     ("Sectionize Selection", sectionizeSelection),
        #     ]),
        ("Outline", addOutline),
        ("Fly", fly),
        ("---", None),
        ("Annotations", annotations_menu),
        ("Toggle Shrink", shrinkRedraw),
        ("Geometry Settings", mySettings),
        ("---", None),
        ]
    m = menu.Menu('Geometry', items=MenuData, parent=pf.GUI.menu, before=before)

    ## if not utils.External.has('dxfparser'):
    ##     I = m.item("Import").item("AutoCAD .dxf")
    ##     I.setEnabled(False)

    # if pf.GUI.modebar and pf.cfg['gui/shrinkbutton']:
    #     from pyformex.gui.toolbar import addButton
    #     addButton(pf.GUI.modebar, 'Toggle Shrink', 'shrink', shrinkRedraw,
    #               toggle=True)
    m['Export']['meshio'].setEnabled(utils.Module.has('meshio') != '')
    return m


# End
