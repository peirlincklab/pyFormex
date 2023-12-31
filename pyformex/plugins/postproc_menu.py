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
"""Postprocessing Menu

"""
import numpy as np

import pyformex as pf
from pyformex import utils
#from pyformex import colors
from pyformex.gui import menu, QtGui, QtCore, QtWidgets
from pyformex.core import *
from pyformex.gui.colorscale import ColorScale
from pyformex.opengl.decors import ColorLegend
from pyformex.gui.draw import *
from pyformex.plugins.postproc import *
from pyformex.plugins.fe_post import FeResult
from pyformex.plugins.objects import Objects


class AttributeModel(QtCore.QAbstractTableModel):
    """A model representing the attributes of an object.

    """
    header = ['attribute', 'value', 'is a dict', 'has __dict__', '__class__']
    def __init__(self, name, dic=None, parent=None, *args):
        QtCore.QAbstractItemModel.__init__(self, parent, *args)
        if dic is None:
            dic = gobals()
        self.dic = dic
        self.name = name
        self.obj = dic.get(name, None)
        keys = dir(self.obj)
        vals = [str(getattr(self.obj, k)) for k in keys]
        isdict = [isinstance(self.obj, dict) for k in keys]
        has_dict = [hasattr(self.obj, '__dict__') for k in keys]
        has_class = [getattr(self.obj, '__class__') for k in keys]
        self.items = list(zip(keys, vals, isdict, has_dict, has_class))


    def rowCount(self, parent):
        return len(self.items)

    def columnCount(self, parent):
        return len(self.header)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if index.isValid() and role == QtCore.Qt.DisplayRole:
            return self.items[index.row()][index.column()]
        return None

    def headerData(self, col, orientation=QtCore.Qt.Horizontal, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return AttributeModel.header[col]
        return None


class DictModel(QtCore.QAbstractTableModel):
    """A model representing a dictionary."""

    header = ['key', 'type', 'value']

    def __init__(self, dic, name, parent=None, *args):

        QtCore.QAbstractItemModel.__init__(self, parent, *args)
        self.dic = dic
        self.name = name
        keys = dic.keys()
        vals = dic.values()
        typs = [str(type(v)) for v in vals]
        self.items = list(zip(keys, typs, vals))
        #print(self.items)

    def rowCount(self, parent):
        return len(self.items)

    def columnCount(self, parent):
        return len(self.header)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if index.isValid() and role == QtCore.Qt.DisplayRole:
            return self.items[index.row()][index.column()]

        return None

    def headerData(self, col, orientation=QtCore.Qt.Horizontal, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return DictModel.header[col]
        return None


class Table(QtWidgets.QDialog):
    """A dialog widget to show two-dimensional arrays of items."""

    def __init__(self, datamodel, caption="pyFormex - Table", parent=None, actions=[('OK',)], default='OK'):
        """Create the Table dialog.

        data is a 2-D array of items, mith nrow rows and ncol columns.
        chead is an optional list of ncol column headers.
        rhead is an optional list of nrow row headers.
        """
        if parent is None:
            parent = pf.GUI

        QtWidgets.QDialog.__init__(self, parent)
        self.setWindowTitle(str(caption))

        form = QtGui.QVBoxLayout()
        table = QtGui.QTableView()
        table.setModel(datamodel)
        table.horizontalHeader().setVisible(True)
        table.verticalHeader().setVisible(False)
        table.resizeColumnsToContents()
        #print(table.size())
        form.addWidget(table)

        but = widgets.ButtonBox(actions, default, parent=self)
        form.addWidget(but)
        self.setLayout(form)
        #print(table.size())
        #print(form.size())
        #self.resize(table.size())
        self.table = table
        self.show()
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        #form.setSizePolicy(QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Minimum)
        table.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)




if 'tbl' in globals():
    if tbl is not None:
        tbl.close()
tbl = None

def showfields():
    """Show the table of field acronyms."""
    global tbl
    tbl = widgets.Table(result_types.items(), ['acronym', 'description'], actions=[('Cancel',), ('Ok',), ('Print', tblIndex)])
    tbl.show()



def tblIndex():
    #print(tbl.table.currentIndex())
    r = tbl.table.currentIndex().row()
    c = tbl.table.currentIndex().column()
    #print("(%s,%s)" % (r,c))
    m = tbl.table.model()
    p = m.data(m.index(r, c))
    #print(p,p.toString(),p.toBool())

def showattr(name=None, dic=None):
    """Show the table of field acronyms."""
    global tbl
    if dic is None:
        dic = globals()
    k = dic.keys()
    sort(k)
    #print(k)
    if name is None:
        name = 'dia_full'
    tbl = AttributeTable(name, dic, actions=[('Cancel',), ('Ok',), ('Print', tblIndex)])
    tbl.show()

def showdict(dic, name=None):
    global tbl
    model = DictModel(dic, name)
    tbl = Table(model, caption="Dict '%s'" % name, actions=[('Cancel',), ('Ok',), ('Print', tblIndex)])
    tbl.show()
    tbl.table.resizeColumnsToContents()
    tbl.table.updateGeometry()
    tbl.updateGeometry()


####################


def keys(items):
    """Return the list of keys in items"""
    return [i[0] for i in items]

def named_item(items, name):
    """Return the named item"""
    n = keys(items).index(name)
    return items[n]


def showModel(nodes=True, elems=True):
    clear()
    smoothwire()
    lights(False)
    transparent(True)
    clear()
    #print(DB.elems)
    for k in DB.elems:
        # TODO: WHY HAS THIS LOST THE ELTYPE coming from EeEx calpy????????
        #print("%s: %s" % (k, len(DB.elems[k])))
        #print(type(DB.elems[k]))
        DB.elems[k] = Elems(DB.elems[k], eltype='quad%d'%DB.elems[k].shape[1])
    M = [Mesh(DB.nodes, DB.elems[k], prop=k) for k in DB.elems]
    if nodes:
        draw([m.coords for m in M], nolight=True)
    if elems:
        draw(M)
    zoomAll()


def showResults(nodes, elems, displ, text, val, showref=False, dscale=100.,
                count=1, sleeptime=-1., symmetric_scale=False):
    """Display a constant or linear field on triangular elements.

    nodes is an array with nodal coordinates
    elems is a single element group or a list of elem groups
    displ are the displacements at the nodes, may be set to None.
    val are the scalar values at the nodes, may also be None.
    If not None, displ should have the same shape as nodes and val
    should have shape (nnodes).

    If dscale is a list of values, the results will be drawn with
    subsequent deformation scales, with a sleeptime intermission,
    and the whole cycle will be repeated count times.
    """
    clear()

    if displ is not None:
    # expand displ if it is smaller than nodes
        # e.g. in 2d returning only 2d displacements
        n = nodes.shape[1] - displ.shape[1]
        if n > 0:
            displ = growAxis(displ, n, axis=1, fill=0.0)

        if nodes.shape != displ.shape:
            warning("The displacements do not match the mesh: the mesh coords have shape %s; but the displacements have shape %s. I will continue without displacements." % (nodes.shape, displ.shape))
            displ = None

    # print(f"Type of elems is {type(elems)}")
    if not isinstance(elems, list):
        elems = [elems]

    if val is not None:
        print("VAL: %s" % str(val.shape))

    # draw undeformed structure
    if showref:
        ref = [Mesh(nodes, el, eltype='quad%d'%el.shape[1]) for el in elems]
        draw(ref, bbox=None, color='green', linewidth=1, mode='wireframe', nolight=True)

    # compute the colors according to the values
    multiplier = 0
    if val is not None:
        if val.shape != (nodes.shape[0],):
            warning("The values do not match the mesh: there are %s nodes in the mesh, and I got values with shape %s. I will continue without showing values." % (nodes.shape[0], val.shape))
            val = None

    if val is not None:
        # create a colorscale and draw the colorlegend
        vmin, vmax = val.min(), val.max()
        if vmin*vmax < 0.0 and not symmetric_scale:
            vmid = 0.0
        else:
            vmid = 0.5*(vmin+vmax)

        scalev = [vmin, vmid, vmax]
        if max(scalev) > 0.0:
            logv = [abs(a) for a in scalev if a != 0.0]
            logs = log10(logv)
            logma = int(logs.max())
        else:
            # All data = 0.0
            logma = 0

        if logma < 0:
            multiplier = 3 * ((2 - logma) // 3)
            #print("MULTIPLIER %s" % multiplier)

        CS = ColorScale('RAINBOW', vmin, vmax, vmid, 1., 1.)
        cval = np.array([CS.color(v) for v in val])
        CLA = ColorLegend(CS, 100, 20, 20, 30, 200, scale=multiplier)
        drawActor(CLA)

    # the supplied text
    if text:
        # Replace text tags
        text = text.replace('%S', str(DB.step))
        text = text.replace('%I', str(DB.inc))
        if multiplier != 0:
            text = text.replace('%M', ' (* 10**%s)' % -multiplier)
        drawText(text, (200, 30))

    smooth()
    lights(False)
    transparent(False)

    # create the frames while displaying them
    dscale = np.array(dscale)
    frames = []   # a place to store the drawn frames
    bboxes = []
    if sleeptime >= 0:
        delay(sleeptime)
    for dsc in dscale.flat:

        if displ is None:
            dnodes = nodes
        else:
            dnodes = nodes + dsc * displ
        deformed = [Mesh(dnodes, el, eltype='quad%d'%el.shape[1]) for el in elems]
        bboxes.append(bbox(deformed))
        # We store the changing parts of the display, so that we can
        # easily remove/redisplay them
        #print(val)
        if val is None:
            F = [draw(df, color='blue', view=None, bbox='last', wait=False) for df in deformed]
        else:
            #print([ df.report() + "\nCOLORS %s" % str(cval[el].shape)  for df,el in zip(deformed,elems) ])
            F = [draw(df, color=cval[el], view=None, bbox='last', wait=False) for df, el in zip(deformed, elems)]
        T = drawText('Deformation scale = %s' % dsc, (200, 10))

        # remove the last frame
        # This is a clever trick: we remove the old drawings only after
        # displaying new ones. This makes the animation a lot smoother
        # (though the code is less clear and compact).
        if len(frames) > 0:
            pf.canvas.removeActor(frames[-1][0])
            pf.canvas.removeDecoration(frames[-1][2])
        # add the latest frame to the stored list of frames
        frames.append((F, [], T))
        wait()

    zoomBbox(bbox(bboxes))

    animateScenes(frames, count, sleeptime)


def animateScenes(scenes, count=1, sleeptime=None):
    """Animate a series of scenes.

    Each scene is a triple of (actors, annots, decors), where each item is
    either a single item of resp. type Actor, Annotation, Decoration, or a
    (possibly empty) list of such items.
    """
    if sleeptime is not None:
        delay(sleeptime)

    # prepare to remove last scene
    FA, AA, TA = scenes[-1]  # !! not None: that would remove everything !!

    while count > 0:
        count -= 1

        for F, A, T in scenes:
            # annotations and decorations should not change smoothly
            # therefore remove the old ones first
            pf.canvas.removeAnnotation(AA)
            pf.canvas.removeDecoration(TA)
            # draw the new items
            pf.canvas.addActor(F)
            pf.canvas.addAnnotation(A)
            pf.canvas.addDecoration(T)
            # remove the old actors after drawing the new ones
            pf.canvas.removeActor(FA)
            pf.canvas.display()
            pf.canvas.update()
            FA, AA, TA = F, A, T
            wait()


############################# PostProc #################################
## class PostProc():
##     """A class to visualize Fe Results."""

##     def __init__(self,DB=None):
##         """Initialize the PostProc. An Fe Results database may be given."""
##         self.resetAll()
##         self.setDB(DB)


##     def resetAll(self):
##         """Reset settings to defaults"""
##         self._show_model = True
##         self._show_elems = True


##     def postABQ(self,fn=None):
##         """Translate an Abaqus .fil file in a postproc script."""
##         types = [ 'Abaqus results file (*.fil)' ]
##         fn = askFilename(pf.cfg['workdir'],types)
##         if fn:
##             chdir(fn)
##             post = fn.with_suffix('.post')
##             cmd = "%s/lib/postabq %s > %s" % (pf.cfg['pyformexdir'],fn,post)
##             P = utils.command(cmd,shell=True)
##             if P.returncode:
##                 print(P.stdout)



################### menu #################


## class PostProcGui(PostProc):

##     def __init__(self,*args,**kargs):
##         self.post_button = None
##         self._step_combo = None
##         self._inc_combo = None
##         self.selection = Objects(clas=FeResult)
##         PostProc.__init__(self,*args,**kargs)


##     def setDB(self,DB=None,name=None):
##         """Set the FeResult database.

##         DB can either be an FeResult instance or the name of an exported
##         FeResult.
##         If a name is given, it is displayed on the status bar.
##         """
##         if isinstance(DB, str):
##             DB = named(DB)
##         if isinstance(DB,FeResult):
##             self.DB = DB
##         else:
##             self.DB = None

##         if self.DB:
## #            self.hideStepInc()
## #            self.hideName()
##             self.showName(name)
##             self.showStepInc()
##         else:
##             self.hideName()
##             self.hideStepInc()


##     def showName(self,name=None):
##         """Show a statusbar button with the name of the DB (hide if None)."""
##         if name is None:
##             self.hideName()
##         else:
##             if self.post_button is None:
##                 self.post_button = widgets.ButtonBox('PostDB:',['None'],[self.select])
##                 pf.GUI.statusbar.addWidget(self.post_button)
##             self.post_button.setText(name)


##     def hideName(self):
##         """Hide the statusbar button with the name of the DB."""
##         if self.post_button:
##             pf.GUI.statusbar.removeWidget(self.post_button)


##     def showStepInc(self):
##         """Show the step/inc combo boxes"""
##         steps = self.DB.getSteps()
##         if steps:
##             self.step_combo = widgets.ComboBox('Step:',steps,self.setStep)
##             pf.GUI.statusbar.addWidget(self.step_combo)
##             self.showInc(steps[0])


##     def showInc(self,step=None):
##         """Show the inc combo boxes"""
##         if step:
##             incs = self.DB.getIncs(step)
##             self.inc_combo = widgets.ComboBox('Inc:',incs,self.setInc)
##             pf.GUI.statusbar.addWidget(self.inc_combo)


##     def hideStepInc(self):
##         """Hide the step/inc combo boxes"""
##         if self._inc_combo:
##             pf.GUI.statusbar.removeWidget(self._inc_combo)
##         if self._step_combo:
##             pf.GUI.statusbar.removeWidget(self._step_combo)


##     def setStep(self,i):
##         print( "Current index: %s" % i)
##         step = str(self.step_combo.combo.input.currentText())
##         if step != self.DB.step:
##             print("Current step: %s" % step)
##             self.showInc(step)
##             inc = self.DB.getIncs(step)[0]
##             self.setInc(-1)
##             self.DB.setStepInc(step,inc)


########## Postproc results dialog #######

result_types = {
    '': 'None',
    'U0': 'X-Displacement',
    'U1': 'Y-Displacement',
    'U2': 'Z-Displacement',
    'U': '[Displacement]',
    'S0': 'X-Normal Stress',
    'S1': 'Y-Normal Stress',
    'S2': 'Z-Normal Stress',
    'S3': 'XY-Shear Stress',
    'S4': 'XZ-Shear Stress',
    'S5': 'YZ-Shear Stress',
    'SP0': '1-Principal Stress',
    'SP1': '2-Principal Stress',
    'SP2': '3-Principal Stress',
    'SF0': 'x-Normal Membrane Force',
    'SF1': 'y-Normal Membrane Force',
    'SF2': 'xy-Shear Membrane Force',
    'SF3': 'x-Bending Moment',
    'SF4': 'y-Bending Moment',
    'SF5': 'xy-Twisting Moment',
    'SINV0': 'Mises Stress',
    'SINV1': 'Tresca Stress',
    'SINV2': 'Hydrostatic Pressure',
    'SINV6': 'Third Invariant',
    'COORD0': 'X-Coordinate',
    'COORD1': 'Y-Coordinate',
    'COORD2': 'Z-Coordinate',
    'Computed': 'Distance from a point',
}


selection = Objects(clas=FeResult)
dialog = None
DB = None


def setDB(db):
    """Set the current result. db is an FeResult instance."""
    global DB
    if isinstance(db, FeResult):
        DB = db
    else:
        DB = None
    pf.PF['PostProcMenu_result'] = DB


def selectDB(db=None):
    """Select the result database to work upon.

    If db is an FeResult instance, it is set as the current database.
    If None is given, a dialog is popped up to select one.

    If a database is successfully selected, the screen is cleared and the
    geometry of the model is displayed.

    Returns the database or None.
    """
    if not isinstance(db, FeResult):
        db = selection.ask1()
        if db:
            print("Selected results database: %s" % selection.names[0])
    if db:
        setDB(db)
        clear()
        print(DB.about.get('heading', 'No Heading'))
        print('Stress tensor has %s components' % DB.datasize['S'])
        DB.printSteps()
        showModel()
    return db


def importCalculix(fn=None):
    """Import a CalculiX results file and select it as the current results.

    CalculiX result files are the .dat files resulting from a run of the
    ccx program with an .inp file as input. This function will need both
    files and supposes that the names are the same except for the extension.

    If no file name is specified, the user is asked to select one (either the
    .inp or .dat file), will then read both the mesh and corresponding results
    files, and store the results in a FeResult instance, which will be set as
    the current results database for the postprocessing menu.
    """
    from pyformex.plugins import ccxdat, ccxinp
    if fn is None:
        fn = askFilename(pf.cfg['workdir'], 'ccx')
    else:
        fn = Path(fn)
    if fn:
        chdir(fn)
        if fn.lsuffix == '.inp':
            meshfile = fn
            resfile = fn.with_suffix('.dat')
        else:
            resfile = fn
            meshfile = fn.with_suffix('.inp')

        parts = ccxinp.readINP(meshfile)
        print(type(parts))
        print(parts.keys())
        # TODO: this does no longer work in py3
        meshes = list(parts.values())[0]
        print(type(meshes))
        #fem = FEModel(meshes=meshes,fuse=False)
        DB = ccxdat.createResultDB(meshes)
        ngp = 8
        ccxdat.readResults(resfile, DB, DB.nnodes, DB.nelems, ngp)
        DB.printSteps()
        name = 'FeResult-%s' % meshfile[:-4]
        export({name: DB})
        selection.set([name])
        selectDB(DB)


def importFlavia(fn=None):
    """Import a flavia file and select it as the current results.

    Flavia files are the postprocessing format used by GiD pre- and
    postprocessor, and can also be written by the FE program calix.
    There usually are two files named 'BASE.flavia.msh' and 'BASE.flavia.res'
    which hold the FE mesh and results, respectively.

    This functions asks the user to select a flavia file (either mesh or
    results), will then read both the mesh and corrseponding results files,
    and store the results in a FeResult instance, which will be set as the
    current results database for the postprocessing menu.
    """
    from pyformex.plugins.flavia import readFlavia
    if fn is None:
        fn = askFilename(pf.cfg['workdir'], ['flavia', 'all'])
    else:
        fn = Path(fn)
    if fn:
        chdir(fn)
        if fn.lsuffix == '.msh':
            meshfile = fn
            resfile = fn.with_suffix('.res')
        else:
            resfile = fn
            meshfile = fn.with_suffix('.msh')

        db = readFlavia(meshfile, resfile)
        if not isinstance(db, FeResult):
            warning("!Something went wrong during the import of the flavia database %s" % fn)
            return

        ### ok: export and select the DB
        name = fn.with_suffix('.flavia')
        export({name: db})
        db.printSteps()
        print(db.R)
        print(db.datasize)

        selection.set([name])
        selectDB(db)



def importDB(fn=None):
    """Import a .post.py database and select it as the current."""

    if fn is None:
        fn = askFilename(pf.cfg['workdir'], 'postproc')
    if fn:
        chdir(fn)
        sizeM = round(os.stat(fn).st_size * 1.e-6, 0)
        if sizeM > 10.0 and ask("""
BEWARE!!!

The size of this file is very large: %.1fMB.
It is unlikely that I will be able to process this file.
I strongly recommend you to cancel the operation now.
""" % sizeM, ["Continue", "Cancel"]) != "Continue":
            return

        # import the results DB
        with busyCursor():
            runScript(fn)

        ### check whether the import succeeded
        name = FeResult._name_
        db = pf.PF[name]
        if not isinstance(db, FeResult):
            warning("!Something went wrong during the import of the database %s" % fn)
            return

        ### ok: select the DB
        selection.set([name])
        selectDB(db)


def checkDB():
    """Make sure that a database is selected.

    If no results database was already selected, asks the user to do so.
    Returns True if a databases is selected.
    """
    if not isinstance(DB, FeResult):
        selectDB()
    return isinstance(DB, FeResult)


def shortkey_results(data):
    """Return the dialog data with short keys."""
    # TODO sanitize the use of list
    data['resindex'] = list(result_types.values()).index(data['restype'])
    return data


def dialog_reset(data=None):
    # data is a dict with short keys/data
    if data is None:
        data = dict((i['name'], i.get('value', None)) for i in input_items)
    dialog.updateData(data)


def show():
    """Show the results """
    if dialog.validate():
        data = shortkey_results(dialog.results)
        show_results(data)


def show_results(data):
    """Show the current DB results using the settings in data.

    Note that while the data may contain a 'step' and 'inc' value,
    the displayed results are those of the step/inc in the database.
    """
    globals().update(data)
    DB.setStepInc(int(data['step']), int(data['inc']))

    nodes = DB.nodes
    if elgroup == '--ALL--':
        elems = list(DB.elems.values())
        print("ALL ELEMS")
    else:
        elems = [DB.elems[elgroup]]

    dscale = data['dscale']
    displ = DB.getres('U')
    if displ is not None:
        displ = displ[:, 0:3]

        if autoscale:
            siz0 = Coords(nodes).sizes()
            siz1 = Coords(displ).sizes()
            if siz1.max() == 0.:
                # all displacements are zero
                dscale = 1.
            else:
                print(siz0, siz1)
                w = np.where(siz0 > 0.0)[0]
                print(w)
                dscale = 0.5/(siz1[w]/siz0[w]).max()
                print(dscale)
                dscale = niceNumber(0.5/(siz1[w]/siz0[w]).max())

    if animate:
        dscale = dscale * frameScale(nframes, cycle=cycle, shape=shape)

    txt = "Step %S; Inc %I; "

    # Get the scalar element result values from the results.
    val = None
    if resindex > 0:
        key = list(result_types.keys())[resindex]
        if key == 'Computed':
            if askPoint():
                val = Coords(nodes).distanceFromPoint(point)
        else:
            val = DB.getres(key)
            if key == 'U':
                val = norm2(val)
    if val is not None:
        txt += list(result_types.values())[resindex]
    showResults(nodes, elems, displ, txt, val, showref, dscale, count, sleeptime, symmetric_scale)
    return val


def show_DB_results():
    """Show the results at the current DB step,inc pointer.

    If the result dialog is shown, its step,inc fields are also updated.
    """
    global dialog
    if dialog:
        dialog.updateData({
            'step': DB.step,
            'inc': DB.inc,
            })
    # This shoud use show_results instead, with the stored data
    show()


def prev_step():
    DB.prevStep()
    show_DB_results()

def prev_inc():
    DB.prevInc()
    show_DB_results()

def next_inc():
    DB.nextInc()
    show_DB_results()

def next_step():
    DB.nextStep()
    show_DB_results()


def open_dialog():
    global dialog
    if not checkDB():
        warning("No results database was selected!")
        return
    close_dialog()

    def set_inc_choices(item):
        step = item.value()
        if step:  # to avoid an error when called before data set
            print("  Incs for step %s: %s" % (step, DB.getIncs(int(step))))
            dialog['inc'].setChoices(DB.getIncs(int(step)))

    input_items = [
        _T('Result', [
            _I('feresult', text='FE Result DB', value='', itemtype='info'),
            _I('step', text='Step', choices=DB.getSteps(), func=set_inc_choices),
            _I('inc', text='Increment', choices=[1]),
            _I('elgroup', text='Element Group', choices=['--ALL--', ]),
            _I('restype', text='Type of result', choices=list(result_types.values())),
            _I('autoscale', text='Autocalculate deformation scale', value=True),
            _I('dscale', text='Deformation scale', value=100.),
            _I('symmetric_scale', text='Symmetric scale', value=False),
            _I('showref', text='Show undeformed configuration', value=True),
            ]),
        _T('Animation', [
            _I('animate', text='Animate results', value=False),
            _I('shape', text='Amplitude shape', value='linear', itemtype='radio', choices=['linear', 'sine']),
            _I('cycle', text='Animation cycle', value='updown', itemtype='radio', choices=['up', 'updown', 'revert']),
            _I('count', text='Number of cycles', value=5),
            _I('nframes', text='Number of frames', value=10),
            _I('sleeptime', text='Animation sleeptime', value=0.1),
            ]),
        ]

    enablers = [
        ('autoscale', False, 'dscale'),
        ('animate', True, 'shape', 'cycle', 'count', 'nframes', 'sleeptime'),
        ]

    actions = [
        ('Prev Step', prev_step, 'rew'),
        ('Prev', prev_inc, 'prev'),
        ('Next', next_inc, 'next'),
        ('Next Step', next_step, 'ff'),
        ('---',),
        ('Close', close_dialog),
        ('Reset', reset),
        # ('Select DB',selectDB),
        ('Show', show),
        # ('Show Fields',showfields),
        # ('Show Attr',showattr),
        ]
    dialog = Dialog(
        input_items,
        enablers = enablers,
        caption='Results Dialog',
        actions=actions,
        default='Show',
        )
    # Update the data items from saved values
    # try:
    #     newdata = named('PostProcMenu_data')
    # except Exception:
    #     newdata = {}
    #     pass
    # if selection.check(single=True):
    #     newdata['feresult'] = selection.names[0]
    # if DB:
    #     newdata['elgroup'] = ['--ALL--', ] + list(DB.elems.keys())
    # dialog.updateData(newdata)

    # dialog['step'].setChoices(DB.getSteps())
    # dialog['inc'].setChoices(DB.getIncs(DB.getSteps()[0]))
    dialog.show()
    #pf.PF['__PostProcMenu_dialog__'] = dialog


def close_dialog():
    global dialog
    if dialog:
        if dialog.validate():
            data = shortkey_results(dialog.results)
            pf.PF['PostProcMenu_data'] = data
        dialog.close()
        dialog = None
    if tbl:
        tbl.close()


def askPoint():
    global point
    res = askItems([('Point', point)])
    if res:
        point = res['Point']
        return point
    else:
        return None


################################## Menu #############################

def create_menu(before='help'):
    """Create the Postproc menu."""
    MenuData = [
#        ("&Translate Abaqus .fil to FeResult database",P.postABQ),
        ("&Read FeResult Database", importDB),
        ("&Read CalculiX results", importCalculix),
        ("&Read Flavia Database", importFlavia),
        ("&Select FeResult Data", selectDB),
#        ("&Forget FeResult Data",P.selection.forget),
        ("---", None),
        ("Show Geometry", showModel),
#        ("Select Step/Inc",P.selectStepInc),
#        ("Show Results",P.postProc),
        ("Results Dialog", open_dialog),
        ("---", None),
        ]
    return menu.Menu('PostProc', items=MenuData, parent=pf.GUI.menu, before=before)


def on_reload():
    global DB
    DB = pf.PF.get('PostProcMenu_result', None)


# End
