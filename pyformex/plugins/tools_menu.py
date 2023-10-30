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
"""Menu with graphical tools for pyFormex.

This menu contains a bunch of graphical tools for pyFormex. In many cases the
implementation is in the :mod:`pyformex.plugins.tools` module and the
menu is just a convenient way to call and use that tool.
"""
import numpy as np

import pyformex as pf
from pyformex import arraytools as at
from pyformex import geomtools as gt
from pyformex import utils
from pyformex import colors
from pyformex.gui import menu
from pyformex.gui import draw as gs
from pyformex.gui import toolbar
from pyformex.gui.menus import Globals
from pyformex.plugins import objects
from pyformex.plugins import tools

from pyformex.core import *
from pyformex.gui.draw import _I, Dialog


##################### Create Points and Labels ###################

if pf.options.doctest is None:
    LABELS = tools.Labels()


def labelPoints(edit=False):
    tools.labelPoints(LABELS, edit=edit)


def labelPointsDialog():
    """Present the dialog for labeling existing points"""
    _name = 'Label Points'
    LABELS.draw()
    def func(item):
        txt = item.value()
        if txt in utils._autoname:
            start = utils._autoname[txt].nr
        else:
            start = 0
        dia = item.dialog()
        dia['start'].setValue(start)
    # check gentext for existing autoname:
    update = {}
    gentext = LABELS.gentext
    if isinstance(gentext, utils.NameSequence):
        # check that it is an autoname:
        stem = None
        for k in utils._autoname:
            if utils._autoname[k] is gentext:
                stem = k
                break
        if stem:
            update['autoname'] = stem
            update['start'] = gentext.nr
    gencolor = LABELS.gencolor
    if isinstance(gencolor, utils.Counter):
        update['color'] = gencolor.nr
        update['step'] = gencolor.step
    dia = Dialog(caption=_name, store=_name + '_data', items=[
        _I('autoname', 'point', text='Default label text', func=func),
        _I('start', 0, text='First label number'),
        _I('color', 0, text="First color number"),
        _I('colorstep', 1, text="Color number step"),
        _I('edit', True, text="Edit each label at creation"),
        ])
    dia.updateData(update)
    res = dia.getResults()
    if res:
        gentext = utils.autoName(res.pop('autoname'))
        gentext.nr = res.pop('start')
        LABELS.gentext = gentext
        LABELS.gencolor = utils.Counter(res.pop('color'), res.pop('colorstep'))
        labelPoints(edit = res['edit'])


def labelPoints2DDialog(default='point'):
    """Present the dialog for creating and labeling new points

    This is a convenient way to set proper options for
    :func:`pyformex.plugins.tools.labelPoints2D`. It uses the global
    Labels from the Tools menu. This function is usually be called from the
    Tools->Query 2D menu.
    """
    print(f"{default=}")
    _name = "Label Points 2D"
    surfaces = ['_merged_'] + gs.listAll(clas=TriSurface)
    dia = Dialog(caption=_name, store=_name+'_ data', items=[
        _I('query', default, choices=['point', 'coords', 'dist', 'angle'],
           itemtype='radio'),
        _I('target', choices=['surface', 'plane'],),
        _I('surface', choices=surfaces),
        _I('missing', choices=['o', 'r', 'e']),
        _I('zvalue', 0.),
        _I('npoints', -1),
        _I('palette', 'dark', choices=list(colors.Palette.keys())),
        # _I('keeplines', False),
    ], enablers=[
        ('target', 'surface', 'surface', 'missing'),
        ('target', 'plane', 'zvalue'),
        ]
    )
    dia.updateData({'query':default})
    res = dia.getResults()
    if res:
        target = res.pop('target')
        if target == 'surface':
            surfname = res['surface']
            if surfname != '_merged_':
                res['surface'] = pf.PF[surfname]
            res.pop('zvalue')
        else:
            res.pop('surface')
            res.pop('missing')
        palette = res.pop('palette')
        with gs.TempPalette(colors.Palette[palette]):
            return tools.labelPoints2D(labels=LABELS, **res)


################# Pick and Query ###################


def report_selection():
    if pf.canvas.selection is None:
        gs.warning("You need to pick something first.")
        return
    print(tools.report(pf.canvas.selection))


def remove_selection(K=None):
    if K is None:
        K = pf.canvas.selection
    if K.obj_type == 'actor':
        remove = [pf.canvas.scene.actors[i] for i in K[-1]]
        pf.canvas.removeAny(remove)


def setpropCollection(K, prop):
    """Set the property of a collection.

    prop should be a single non-negative integer value or None.
    If None is given, the prop attribute will be removed from the objects
    in collection even the non-selected items.
    If a selected object does not have a setProp method, it is ignored.
    """
    if K.obj_type == 'actor':
        for k in K.get(-1, []):
            a = pf.canvas.actors[k]
            o = a.object
            if hasattr(o, 'setProp'):
                o.setProp(prop)
                a.changeColor(color = 'prop')
    elif K.obj_type == 'element':
        for k in K.keys():
            a = pf.canvas.actors[k]
            o = a.object
            if hasattr(o, 'setProp'):
                if prop is None:
                    o.setProp(prop)
                else:
                    if not hasattr(o, 'prop') or o.prop is None:
                        o.setProp(0)
                    o.prop[K[k]] = prop
                a.changeColor(color = 'prop')
    gs.removeHighlight()


def setprop_selection():
    """Set the property of the current selection.

    A property value is asked from the user and all items in the selection
    that have property have their value set to it.
    """
    if pf.canvas.selection is None:
        gs.warning("You need to pick something first.")
        return
    print(pf.canvas.selection)
    res = gs.askItems(
        [_I('property', 0)],
        caption = 'Set Property Number for Selection (negative value to remove)')
    if res:
        prop = int(res['property'])
        if prop < 0:
            prop = None
        setpropCollection(pf.canvas.selection, prop)
        gs.removeHighlight()


# TODO: can this be removed? zoomRectangle probably works well

def focus_selection(K=None):
    """Focus on the specified or current selection.

    """
    gs.removeHighlight()
    if K is None:
        K = pf.canvas.selection
    if K is None:
        gs.warning("You need to pick some points first.")
        return
    print(K)
    if K.obj_type != 'point':
        gs.warning("You need to pick some points first.")
        return
    X = []
    for k in K.keys():
        a = pf.canvas.actors[k]
        o = a.object
        x = o.coords[K[k]]
        X.append(x.center())
    X = Coords(X).center()
    gs.focus(X)


def grow_selection():
    """Show and execute the Grow selection dialog

    If a current selection exists, it can be grown it the object
    has a growSelection method. This includes Mesh type objects.
    The dialogs lets the user set the frontal method: using node
    or edge connections and the number of steps. After growing,
    the new current selection is highlighted.

    See Also
    --------
    tools.growCollection: the function used to grow the selection.
    """
    if pf.canvas.selection is None:
        gs.warning("You need to pick something first.")
        return
    print("Selection:", pf.canvas.selection)
    pf.canvas.highlightSelection(pf.canvas.selection)
    res = gs.askItems(caption='Grow selection', items=[
        _I('mode', 'node', itemtype='radio', choices=['node', 'edge'],
           text='Connected by'),
        _I('nsteps', 1, text='Number of steps'),])
    if res:
        tools.growCollection(pf.canvas.selection, **res)
        print("Selection:", pf.canvas.selection)
        pf.canvas.highlightSelection(pf.canvas.selection)


def partition_selection():
    """Partition the current selection and show the result."""
    if pf.canvas.selection is None:
        gs.warning("You need to pick something first.")
        return
    if not pf.canvas.selection.obj_type in ['actor', 'element']:
        gs.warning("You need to pick actors or elements.")
        return
    for A in pf.canvas.actors:
        if not A.getType() == TriSurface:
            gs.warning("Currently I can only partition TriSurfaces.")
            return
    tools.partitionCollection(pf,canvas.selection)
    pf.canvas.highlightSelection(pf.canvas.selection)


def get_partition():
    """Select some partitions from the current selection and show the result."""
    if pf.canvas.selection is None:
        gs.warning("You need to pick something first.")
        return
    if not pf.canvas.selection.obj_type in ['partition']:
        gs.warning("You need to partition the selection first.")
        return
    res = gs.askItems([_I('property', [1])],
                 caption='Partition property')
    if res:
        prop = res['property']
        getPartition(pf.canvas.selection, prop)
        pf.canvas.highlightSelection(pf.canvas.selection)


def actor_dialog():
    print("actor_dialog")
    if pf.canvas.selection is None or not pf.canvas.selection.obj_type == 'actor':
        gs.warning("You need to pick some actors first.")
        return

    actors = [pf.canvas.actors[i] for i in pf.canvas.selection.get(-1, [])]
    print("Creating actor dialog for %s actors" % len(actors))
    tools.actorDialog(pf.canvas.selection.get(-1, []))


##################### planes ##########################

from pyformex.plugins.tools import Plane
planes = objects.DrawableObjects(clas=Plane)
pname = utils.autoName(Plane)

def editPlane(plane, name):
    res = gs.askItems([_I('Point', list(plane.point())),
                         _I('Normal', list(plane.normal())),
                         _I('Size', list(plane.size()))],
                        caption = 'Edit Plane')
    if res:
        plane.P = res['Point']
        plane.n = res['Normal']
        plane.s = res['Size']

Plane.edit = editPlane


def exportDrawPlane(P, name):
    pf.PF[name] = P
    gs.draw(P, name=name, mode='flatwire')


def createPlaneCoordsPointNormal():
    res = gs.askItems([_I('Name', next(pname)),
                         _I('Point', (0., 0., 0.)),
                         _I('Normal', (1., 0., 0.)),
                         _I('Size', (1., 1.))],
                        caption = 'Create a new Plane')
    if res:
        name = res['Name']
        p = res['Point']
        n = res['Normal']
        s = res['Size']
        P = Plane(p, n, s)
        exportDrawPlane(P, name)


def createPlaneCoords3Points():
    res = gs.askItems([_I('Name', next(pname)),
                         _I('Point 1', (0., 0., 0.)),
                         _I('Point 2', (0., 1., 0.)),
                         _I('Point 3', (0., 0., 1.)),
                         _I('Size', (1., 1.))],
                        caption = 'Create a new Plane')
    if res:
        name = res['Name']
        p1 = res['Point 1']
        p2 = res['Point 2']
        p3 = res['Point 3']
        s = res['Size']
        pts=[p1, p2, p3]
        P = Plane(pts, size=s)
        exportDrawPlane(P, name)


def createPlaneVisual3Points():
    res = gs.askItems([_I('Name', next(pname)),
                         _I('Size', (1., 1.))],
                        caption = 'Create a new Plane')
    if res:
        name = res['Name']
        s = res['Size']
        picked = gs.pick('point')
        pts = tools.getCollection(picked)
        print(pts)
        pts = Coords.concatenate(pts).reshape(-1, 3)
        if len(pts) == 3:
            P = Plane(pts, size=s)
            exportDrawPlane(P, name)
        else:
            gs.warning("You have to pick exactly three points.")


###############################################################

def dos2unix():
    fn = gs.askFilename(mode='multi')
    if fn:
        for f in fn:
            print("Converting file to UNIX: %s" % f)
            utils.dos2unix(f)


def unix2dos():
    fn = gs.askFilename(mode='multi')
    if fn:
        for f in fn:
            print("Converting file to DOS: %s" % f)
            utils.unix2dos(f)

def sendMail():
    from pyformex import sendmail
    sender = pf.cfg['mail/sender']
    if not sender:
        gs.warning("You have to configure your email settings first")
        return

    res = gs.askItems([
        _I('sender', sender, text="From:", readonly=True),
        _I('to', '', text="To:"),
        _I('cc', '', text="Cc:"),
        _I('subject', '', text="Subject:"),
        _I('text', '', itemtype='text', text="Message:"),
       ])
    if not res:
        return

    print(**res)
    msg = res['text']
    print(msg)
    to = res['to'].split(',')
    cc = res['cc'].split(',')
    sendmail.sendmail(message=msg, sender=res['sender'], to=to+cc)
    print("Mail has been sent to %s" % to)
    if cc:
        print("  with copy to %s" % cc)

###################### images #############################

def selectImage(extra_items=[]):
    """Open a dialog to read an image file.

    """
    global image
    from pyformex.gui.widgets import ImageView
    from pyformex.plugins.imagearray import resizeImage

    # some default values
    filename = getcfg('datadir') / 'butterfly.png'
    w, h = 200, 200
    image = None  # the loaded image
    diag = None  # the image dialog

    # construct the image previewer widget
    viewer = ImageView(filename, maxheight=h)

    def select_image(field):
        """Helper function to load and preview image"""
        fn = gs.askImageFile(field.value())
        if fn:
            viewer.showImage(fn)
            load_image(fn)
        return fn

    def load_image(fn):
        """Helper function to load the image and set its size in the dialog"""
        global image
        image = resizeImage(fn)
        if image.isNull():
            gs.warning("Could not load image '%s'" % fn)
            return None

        w, h = image.width(), image.height()
        print("size = %sx%s" % (w, h))

        diag = currentDialog()
        if diag:
            diag.updateData({'nx': w, 'ny': h})

        maxsiz = 40000.
        if w*h > maxsiz:
            scale = sqrt(maxsiz/w/h)
            w = int(w*scale)
            h = int(h*scale)
        return w, h

    res = gs.askItems([
        _I('filename', filename, text='Image file', itemtype='button', func=select_image),
        _I('viewer', viewer, itemtype='widget'),  # the image previewing widget
        _I('nx', w, text='width'),
        _I('ny', h, text='height'),
        ] + extra_items)

    if not res:
        return None, None

    if image is None:
        print("Loading image")
        load_image(res['filename'])

    image = resizeImage(image, res['nx'], res['ny'])
    return image, res


def showImage():
    clear()
    im, res = selectImage()
    if im:
        drawImage(im)

def showImage3D():
    clear()
    im, res = selectImage([_I('pixel cell', choices=['dot', 'quad'])])
    if im:
        drawImage3D(im, pixel=res['pixel cell'])


################### menu #################

def create_menu(before='help'):
    """Create the Tools menu."""
    MenuData = [
        ('Labels', [
            ('Quick Create/Remove', labelPoints, {'data': False}),
            ('Create/Edit/Remove', labelPoints, {'data': True}),
            ('Customize', labelPointsDialog),
            ('Hide Labels', LABELS.undraw),
            ('Show Labels', LABELS.draw),
            ('Clear Labels', LABELS.clear),
            ('Print Labels', LABELS.printc),
            ]),
        ('Query/Label 2D', [
            ('Point', labelPoints2DDialog, {'data': 'point'}),
            ('Coords', labelPoints2DDialog, {'data': 'coords'}),
            ('Distance', labelPoints2DDialog, {'data': 'dist'}),
            ('Angle', labelPoints2DDialog, {'data': 'angle'}),
            ]),
        ('Query', [
            ('Actors', toolbar.query, {'data': 'actor'}),
            ('Elements', toolbar.query, {'data': 'element'}),
            ('Points', toolbar.query, {'data': 'point'}),
            ('Distance', toolbar.query_distance),
            ('Angle', toolbar.query_angle),
            ]),
        ('Pick', [
            ("Actors", toolbar.picksel, {'data': 'actor'}),
            ("Elements", toolbar.picksel, {'data': 'element'}),
            ("Points", toolbar.picksel, {'data': 'point'}),
            ]),
        ('With picked', [
            ('Show Report', report_selection),
            ('Set Property', setprop_selection),
            ('Remove', remove_selection),
            ('Grow', grow_selection),
            ('Partition', partition_selection),
            ('Get Partition', get_partition),
            # ('Export', export_selection),
            ('Focus', focus_selection),
            ('Actor dialog', actor_dialog),
            ]),
        ("Remove Highlights", gs.removeHighlight),
        ("---", None),
        ("Create Plane", [
            ("Coordinates",
                [("Point and normal", createPlaneCoordsPointNormal),
                ("Three points", createPlaneCoords3Points),
                ]),
            ("Visually",
                [("Three points", createPlaneVisual3Points),
                ]),
            ]),
        ('Planes', [
            ("Select", planes.ask),
            ("Draw Selection", planes.draw),
            ("Forget Selection", planes.forget),
            ]),
        ("---", None),
        ("Show an Image file on the canvas", showImage),
        ("Show an Image file as Formex", showImage3D),
        ("DOS to Unix", dos2unix, dict(tooltip="Convert a text file from DOS to Unix line terminators")),
        ("Unix to DOS", unix2dos),
        ("Send Mail", sendMail),
        ("---", None),
        ]
    return menu.Menu('Tools', items=MenuData, parent=pf.GUI.menu, before=before)


# End
