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
"""Graphical User Interface for pyFormex.

This module contains the main functions responsible for constructing
and starting the pyFormex GUI.
"""
import sys
import os
import importlib
import datetime
import types
import warnings

import pyformex as pf
from pyformex import Path
from pyformex import process
from pyformex import utils
from pyformex import software

# If we get here, either PySide2 or PyQt5 are imported
# Check for OpenGL
if not pf.sphinx:
    if pf.options.mgl:
        software.Module.has('moderngl', fatal=True)
    elif not pf.options.gl3:
        software.Module.has('pyopengl', fatal=True)
software.Module.has('pil', fatal=True)

from pyformex.gui import (QtCore, QtGui, QtWidgets, QPixmap)
from pyformex.gui import signals
from pyformex.gui import qtgl
from pyformex.gui import qtutils
from pyformex.gui import menu
from pyformex.gui import appMenu
from pyformex.gui import toolbar
from pyformex.gui import viewport
from pyformex.gui import pyconsole
from pyformex.gui import guifunc
from pyformex.gui import draw
from pyformex.gui import widgets
from pyformex.gui import drawlock
from pyformex.gui import views
from pyformex.gui.menus import (File, Settings, Viewport, Globals)
from pyformex.opengl import canvas_settings
from pyformex import plugins

#####################################
################# GUI ###############
#####################################

easter_egg=''

def splitXgeometry(geometry):
    """Split an X11 window geometry string in its components.

    Parameters
    ----------
    geometry: str
        A string in X11 window geometry format: WxH+X+Y, where W, H are the
        width and height of the window, and X,Y are the position of the top
        left corner. The +Y or +X+Y parts may be missing and will thendefault
        to 0.

    Returns
    -------
    (W, H, X, Y)
        A tuple of four ints.

    Examples
    --------
    >>> splitXgeometry('1000x800+20')
    (1000, 800, 20, 0)
    """
    wh, *xy = geometry.split('+')
    w, h = wh.split('x')
    if len(xy) == 0:
        x, y = 0, 0
    elif len(xy) == 1:
        x, y = xy[0], 0
    else:
        x, y = xy[:2]
    return int(w), int(h), int(x), int(y)


def Xgeometry(w, h, x=0, y=0):
    """Return an X11 window geometry string.

    Parameters
    ----------
    (w, h, x, y): tuple of int
        The width, height, xpos and ypos to pack into an X11 geometry string.

    Returns
    -------
    str:
        A string of the format WxH+X+Y.

    Examples
    --------
    >>> Xgeometry(1000, 800, 20, 0)
    '1000x800+20+0'
    """
    return f"{w}x{h}+{x}+{y}"


#########################################################################
## The File watcher ##
######################

class FileWatcher(QtCore.QFileSystemWatcher):
    """Watch for changes in files and then execute an associated function.

    """
    def __init__(self, *args):
        super().__init__(*args)
        self.filesWatched = {}

    def addWatch(self, path, func):
        """Watch for changes in file and the execute func.

        When the specified file is changed, func is executed.

        Parameters
        ----------
        path: :term:`path_like`
            The path of the file to be watched.
        func: callable
            The function to be called when the file changes. The path
            is passed as an argument.
        """
        self.filesWatched[path] = func
        self.addPath(path)
        self.fileChanged.connect(self.onFileChanged)

    def removeWatch(self, path):
        """Remove the watch for a file path

        Parameters
        ----------
        path: :term:`path_like`
            The path of the file to be watched.
        """
        if path in self.fileWatched:
            self.removePath(path)
            del self.filesWatched[path]

    def onFileChanged(self, path):
        """Call installed function when file changed"""
        print(f"FileWatcher: file {path} has changed")
        f = self.filesWatched.get(path, None)
        if f:
            pf.verbose(2, f"FileWatcher: calling {f.__name__}({path})")
            f(path)


#########################################################################
## The GUI ##
#############

class Gui(QtWidgets.QMainWindow):
    """Implements the pyFormex GUI.

    The GUI has a main window with a menubar on top and a statusbar
    at the bottom. One or more toolbars may be located at the top, bottom,
    left or right side of the main window. The central part is split up
    over a display canvas at the top and a Python console at the bottom.
    The split size of these two parts can be adjusted. The canvas may
    contain one or more OpenGL widgets for 3D rendering. The console
    displays messages from the applications and can be used to access
    any internal part of pyFormex and interactively execute pyFormex
    instructions.

    """

    toolbar_area = {'top': QtCore.Qt.TopToolBarArea,
                    'bottom': QtCore.Qt.BottomToolBarArea,
                    'left': QtCore.Qt.LeftToolBarArea,
                    'right': QtCore.Qt.RightToolBarArea,
                    }


    def __init__(self, windowname, size=(800, 600), pos=(0, 0),
                 splitsize=(450, 150)):
        """Constructs the GUI."""
        pf.debug(f'Creating Main Window with size {size} at {pos}', pf.DEBUG.GUI)
        super().__init__()
        self.setWindowTitle(windowname)
        self.on_exit = set()    # exit functions
        self.fullscreen = False
        self.maxsize = pf.app.maxSize()
        size = qtutils.MinSize(size, self.maxsize)

        # The status bar
        pf.debug('Creating Status Bar', pf.DEBUG.GUI)
        self.statusbar = self.statusBar()
        self.curproj = self.addStatusbarButtons(
            'Project:', actions=[('None', File.openExistingProject)])
        self.curfile = self.addStatusbarButtons(
            '', actions=[('Script:', self.toggleAppScript),
                         ('None', File.openScript)])
        self.curdir = self.addStatusbarButtons(
            'Cwd:', actions=[('None', draw.askDirname)])

        self.canPlay = False
        self.canEdit = False

        ################# MENUBAR ###########################
        pf.debug('Creating Menu Bar', pf.DEBUG.GUI)
        self.menu = menu.MenuBar('TopMenu')
        for key in pf.cfg['gui/menu']:
            self.insertModuleMenu(key)
        self.setMenuBar(self.menu)

        ################# CENTRAL ###########################
        # Create a box for the central widget
        self.box = QtWidgets.QWidget()
        self.setCentralWidget(self.box)
        self.boxlayout = QtWidgets.QVBoxLayout()
        self.boxlayout.setContentsMargins(*pf.cfg['gui/boxmargins'])
        self.box.setLayout(self.boxlayout)
        # Create a splitter
        self.splitter = QtWidgets.QSplitter()
        self.boxlayout.addWidget(self.splitter)
        self.splitter.setOrientation(QtCore.Qt.Vertical)

        # The central widget is where the rendering viewports will be
        # For now, use an empty widget
        pf.debug('Creating Central Widget', pf.DEBUG.GUI)
        self.central = QtWidgets.QWidget()
        self.central.autoFillBackground()
        self.central.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                   QtWidgets.QSizePolicy.MinimumExpanding)
        #self.central.resize(*size)
        if pf.options.canvas:
            self.viewports = viewport.MultiCanvas(parent=self.central)
            self.central.setLayout(self.viewports)
        self.splitter.addWidget(self.central)

        # Create the console
        self.console = pyconsole.PyConsole(context=pf.interpreter, parent=self)
        histfile = pf.cfg['gui/consolehistfile']
        if histfile.exists():
            self.console.editline.loadhistory(histfile)
        self.splitter.addWidget(self.console)
        self.console.setFocus()

        self.splitter.setSizes(splitsize)

        ################# TOOLBAR ###########################
        pf.debug('Creating ToolBar', pf.DEBUG.GUI)
        self.toolbar = self.addToolBar('Top ToolBar')

        # Define Toolbar contents
        self.actions = toolbar.addActionButtons(self.toolbar)
        # timeout button
        toolbar.addTimeoutButton(self.toolbar)
        pf.debug('Creating Toolbars', pf.DEBUG.GUI)
        self.camerabar = self.updateToolBar('camerabar', 'Camera ToolBar')
        self.modebar = self.updateToolBar('modebar', 'RenderMode ToolBar')
        self.viewbar = self.updateToolBar('viewbar', 'Views ToolBar')
        self.toolbars = [self.toolbar, self.camerabar, self.modebar,
                         self.viewbar]
        self.enableToolbars(False)

        ###############  CAMERA menu and toolbar #############
        if self.camerabar:
            toolbar.addCameraButtons(self.camerabar)
            toolbar.addButton(self.camerabar, "Pick to focus", 'focus',
                              draw.pickFocus)
            toolbar.addPerspectiveButton(self.camerabar)

        ###############  RENDERMODE menu and toolbar #############
        pmenu = self.menu['viewport']

        mmenu = QtWidgets.QMenu('Render Mode')
        modes = ['wireframe', 'smooth', 'smoothwire', 'flat', 'flatwire']
        self.modebtns = menu.ActionList(
            modes, guifunc.renderMode, menu=mmenu, toolbar=self.modebar)
        pmenu.insertMenu(pmenu['background color'], mmenu)

        mmenu = QtWidgets.QMenu('Wire Mode')
        modes = ['none', 'all', 'border', 'feature']
        self.wmodebtns = menu.ActionList(
            modes, guifunc.wireMode, menu=mmenu, toolbar=None)
        pmenu.insertMenu(pmenu['background color'], mmenu)

        # Add the toggle type buttons
        if self.modebar and pf.cfg['gui/wirebutton']:
            toolbar.addWireButton(self.modebar)
        if self.modebar and pf.cfg['gui/transbutton']:
            toolbar.addTransparencyButton(self.modebar)
        if self.modebar and pf.cfg['gui/lightbutton']:
            toolbar.addLightButton(self.modebar)
        if self.modebar and pf.cfg['gui/normalsbutton']:
            toolbar.addNormalsButton(self.modebar)
        # We can not add the shrinkButton here, because
        # we can not yet import the geometry menu
        if self.modebar:
            toolbar.addButton(
                self.modebar,
                "Popup dialog to interactively change object rendering",
                'objects', Viewport.showObjectDialog)

        ###############  VIEWS menu ################
        if pf.cfg['gui/viewmenu']:
            if pf.cfg['gui/viewmenu'] == 'main':
                parent = self.menu
                before = 'help'
            else:
                parent = self.menu['camera']
                before = parent.action('---0')
            self.viewsMenu = menu.Menu('Views', parent=parent, before=before)
        else:
            self.viewsMenu = None

        # Save front orientation
        self.frontview = None
        self.setViewButtons(pf.cfg['gui/frontview'])

        ## TESTING SAVE CURRENT VIEW ##
        self.saved_views = {}
        self.saved_views_name = utils.NameSequence('View')

        if self.viewsMenu:
            name = next(self.saved_views_name)
            self.menu['Camera'].addAction('Save View', self.saveView)

        # Set specified geometry
        pf.debug(f'Restore size {size}, pos {pos}', pf.DEBUG.GUI)
        self.resize(*size)
        self.move(*pos)

        pf.debug('Set Curdir', pf.DEBUG.GUI)
        self.setcurdir()

        # Drawing lock
        self.drawwait = pf.cfg['draw/wait']
        self.drawlock = drawlock.DrawLock()
        # Runall mode register
        self.runallmode = False

        # Materials and Lights database
        self.materials = canvas_settings.createMaterials()
        ## for m in self.materials:
        ##     print self.materials[m]

        # Modeless child dialogs
        self.doc_dialog = None
        pf.debug('Done initializing GUI', pf.DEBUG.GUI)

        # Set up signal/slot connections
        self.signals = signals.Signals()
        self.signals.FULLSCREEN.connect(self.fullScreen)

        self.filewatch = FileWatcher()

        # Set up hot keys: hitting the key will emit the corresponding signal
        self.hotkey  = {
            QtCore.Qt.Key_F2: self.signals.SAVE,
            QtCore.Qt.Key_F11: self.signals.FULLSCREEN,
            }

        # keep a list of the Dialog children
        self.dialogs = []


    def dialog(self, caption):
        """Return the dialog with the named caption

        Parameters
        ----------
        caption: str
            The window caption to find.

        Returns
        -------
        Dialog | None
            The dialog with the specified caption, or None if there is no
            such dialog.
        """
        found = None
        delete = []
        for d in self.dialogs:
            try:
                if d.windowTitle() == caption:
                    found = d
                    break
            except RuntimeError:
                # Window has disappeared
                delete.append(d)
        for d in delete:
            self.dialogs.remove(d)
        return found


    def insertModuleMenu(self, name):
        """Insert the menu from module name in the top menu

        If the module defines an attribute MenuData, it is
        inserted in the MenuBar. If it defines a function
        menu_enabler, it is called afterwards.

        """
        pf.debug(f"Creating Top Menu item {name}", pf.DEBUG.GUI)
        modname = 'pyformex.gui.menus.'+name
        module = importlib.import_module(modname)
        self.menu.insertItems([module.MenuData])
        enabler = getattr(module, 'menu_enabler', None)
        if callable(enabler):
            enabler(self.menu)


    def addStatusbarButtons(self, name, actions, **kargs):
        """Install a group of buttons in the statusbar"""
        w = widgets.ButtonBox(name=name, actions=actions,
                              parent=self.statusbar, spacer='', **kargs)
        self.addStatusbarWidget(w)
        return w


    def addStatusbarWidget(self, w):
        self.statusbar.addWidget(w)
        r = self.statusbar.childrenRect()
        self.statusbar.setFixedHeight(r.height()+6)


    def saveConsoleHistory(self):
        """Save the console history"""
        pf.debug("Save console history")
        self.console.editline.savehistory(
            pf.cfg['gui/consolehistfile'], pf.cfg['gui/consolehistmax'])


    def close_doc_dialog(self):
        """Close the doc_dialog if it is open."""
        if self.doc_dialog is not None:
            self.doc_dialog.close()
            self.doc_dialog = None


    def clearViewButtons(self):
        """Clear the view buttons in views toolbar and views menu.

        This is typically use from setViewButtons to change the
        current buttons to a new set.
        """
        viewbtns = getattr(self, 'viewbtns', None)
        if viewbtns:
            viewbtns.removeAll()
            self.viewbtns = None
            self.update()

    def setViewButtons(self, defviews):
        """Set view buttons in views toolbar and views menu.

        defviews can be on of 'xy' or 'xz', or else it is
        a list of tuple (viewname, viewicon)
        """
        if isinstance(defviews, str):
            self.frontview = defviews
            viewnames, realnames, viewicons = views.setOrientation(defviews)
        else:
            viewnames = [v[0] for v in defviews]
            viewicons = [v[1] for v in defviews]

        self.clearViewButtons()

        self.viewbtns = menu.ActionList(
            viewnames, self.setView,
            menu=self.viewsMenu,
            toolbar=self.viewbar,
            icons = viewicons
            )
        self.update()


    def createView(self, name, angles):
        """Create a new view and add it to the list of predefined views.

        This creates a named view with specified angles or, if the name
        already exists, changes its angles to the new values.

        It adds the view to the views Menu and Toolbar, if these exist and
        do not have the name yet.
        """
        if name not in self.viewbtns.names():
            iconpath = utils.findIcon('userview')
            self.viewbtns.add(name, iconpath)
        views.setAngles(name, angles)


    def saveView(self, name=None, addtogui=True):
        """Save the current view and optionally create a button for it.

        This saves the current viewport ModelView and Projection matrices
        under the specified name.

        It adds the view to the views Menu and Toolbar, if these exist and
        do not have the name yet.
        """
        if name is None:
            name = next(self.saved_views_name)
        self.saved_views[name] = (pf.canvas.camera.modelview, None)
        if name not in self.viewbtns.names():
            iconpath = utils.findIcon('userview')
            self.viewbtns.add(name, iconpath)


    def applyView(self, name):
        """Apply a saved view to the current camera.

        """
        m, p = self.saved_views.get(name, (None, None))
        if m is not None:
            self.viewports.current.camera.setModelview(m)


    def setView(self, view):
        """Change the view of the current GUI viewport, keeping the bbox.

        view is the name of one of the defined views.
        """
        view = str(view)
        if view in self.saved_views:
            self.applyView(view)
        else:
            self.viewports.current.setCamera(angles=view)
        self.viewports.current.update()


    def updateAppdirs(self):
        appMenu.reloadMenu()


    def updateToolBars(self):
        for t in ['camerabar', 'modebar', 'viewbar']:
            self.updateToolBar(t)


    def updateToolBar(self, shortname, fullname=None):
        """Add a toolbar or change its position.

        This function adds a toolbar to the GUI main window at the position
        specified in the configuration. If the toolbar already exists, it is
        moved from its previous location to the requested position. If the
        toolbar does not exist, it is created with the given fullname, or the
        shortname by default.

        The full name is the name as displayed to the user.
        The short name is the name as used in the config settings.

        The config setting for the toolbar determines its placement:
        - None: the toolbar is not created
        - 'left', 'right', 'top' or 'bottom': a separate toolbar is created
        - 'default': the default top toolbar is used and a separator is added.
        """
        area = pf.cfg[f"gui/{shortname}"]
        try:
            toolbar = getattr(self, shortname)
        except Exception:
            toolbar = None

        if area:
            area = self.toolbar_area.get(area, 4)  # default is top
            # Add/reposition the toolbar
            if toolbar is None:
                if fullname is None:
                    fullname = shortname
                toolbar = QtWidgets.QToolBar(fullname, self)
            self.addToolBar(area, toolbar)
        else:
            if toolbar is not None:
                self.removeToolBar(toolbar)
                toolbar = None

        return toolbar


    def toggleAppScript(self):
        pf.debug("Toggle between app and script", pf.DEBUG.APPS)
        from pyformex import apps
        appname = pf.cfg['curfile']
        if utils.is_script(appname):
            path = Path(appname).parent
            appdir = apps.findAppDir(path)
            if appdir:
                appname = appname.stem
                pkgname = appdir.pkg
                appname = f"{pkgname}.{appname}"
                self.setcurfile(appname)
            else:
                if pf.warning(
                        "This script is not in an application directory.\n\n"
                        f"You should add the directory path '{path}' to the"
                        " application paths before you can run this file as"
                        " an application.",
                        actions=['Not this time', 'Add this directory now']
                ).startswith('Add'):
                    Settings.addAppdir(path, dircfg='appdirs')
                    draw.showInfo(f"Added the path {path}")

        else:
            fn = apps.findAppSource(appname)
            if fn.exists():
                self.setcurfile(fn)
            else:
                pf.warning("I can not find the source file for this application.")


    def addCoordsTracker(self):
        self.coordsbox = widgets.CoordsBox()
        self.statusbar.addPermanentWidget(self.coordsbox)


    def toggleCoordsTracker(self, onoff=None):
        def track(x, y, z):
            (X, Y, Z), = pf.canvas.unproject(x, y, z)
            # print(f"{(x, y, z)} --> {(X, Y, Z)}")
            pf.GUI.coordsbox.setValues([X, Y, Z])

        if onoff is None:
            onoff = self.coordsbox.isHidden()
        if onoff:
            func = track
        else:
            func = None
        for vp in self.viewports.all:
            vp.trackfunc = func
        self.coordsbox.setVisible(onoff)


    def maxCanvasSize(self):
        """Return the maximum canvas size.

        The maximum canvas size is the size of the central space in the
        main window, occupied by the OpenGL viewports.
        """
        return qtutils.Size(pf.GUI.central)


    def setcurproj(self, project=''):
        """Show the current project name."""
        self.curproj.setText(Path(project).name)


    def setcurfile(self, appname):
        """Set the current application or script.

        appname is either an application module name or a script file.
        """
        is_app = appname != '' and not utils.is_script(appname)
        if is_app:
            # application
            label = 'App:'
            name = appname
            from pyformex import apps
            app = apps.load(appname)
            if app is None:
                self.canPlay = False
                try:
                    self.canEdit = apps.findAppSource(appname).exists()
                except Exception:
                    self.canEdit = False
            else:
                self.canPlay = hasattr(app, 'run')
                appsource = apps.findAppSource(app)
                if appsource:
                    self.canEdit = apps.findAppSource(app).exists()
                else:
                    print(f"Could not find source of app '{app}'")
                    self.canEdit = False
        else:
            # script file
            label = 'Script:'
            name = Path(appname).name
            self.canPlay = self.canEdit = utils.is_pyFormex(appname)

        pf.prefcfg['curfile'] = appname
        #self.curfile.label.setText(label)
        self.curfile.setText(label, 0)
        self.curfile.setText(name, 1)
        self.enableButtons(self.actions, ['Play', 'Info'], self.canPlay)
        self.enableButtons(self.actions, ['Edit'], self.canEdit)
        self.enableButtons(self.actions, ['ReRun'], is_app and(self.canEdit or self.canPlay))
        self.enableButtons(self.actions, ['Step', 'Continue'], False)
        icon = 'ok' if self.canPlay else 'notok'
        iconpath = utils.findIcon(icon)
        self.curfile.setIcon(QtGui.QIcon(QPixmap(iconpath)), 1)


    def setcurdir(self):
        """Show the current workdir."""
        dirname = Path.cwd()
        shortname = dirname.name
        self.curdir.setText(shortname)
        self.curdir.setToolTip(str(dirname))


    def setBusy(self, busy=True, force=False):
        if busy:
            pf.app.setOverrideCursor(QtCore.Qt.WaitCursor)
        else:
            pf.app.restoreOverrideCursor()
        pf.app.processEvents()


    def resetCursor(self):
        """Clear the override cursor stack.

        This will reset the application cursor to the initial default.
        """
        while pf.app.overrideCursor():
            pf.app.restoreOverrideCursor()
        pf.app.processEvents()


    def keyPressEvent(self, e):
        """Top level key press event handler.

        Events get here if they are not handled by a lower level handler.
        Every key press arriving here generates a WAKEUP signal, and if a
        dedicated signal for the key was installed in the keypress table,
        that signal is emitted too.
        Finally, the event is removed.
        """
        key = e.key()
        pf.debug(f'Key {key} pressed', pf.DEBUG.GUI)
        self.signals.WAKEUP.emit()
        signal = self.hotkey.get(key, None)
        if signal is not None:
            signal.emit()
        e.ignore()


    def XGeometry(self, border=True):
        """Get the main window position and size.

        Parameters
        ----------
        border: bool
            If True (default), the returned geometry includes the
            border frame. If set to False, the border is excluded.

        Returns
        -------
        tuple (x,y,w,h)
            A tuple of int with the top left position and the size
            of the window geometry.
        """
        if border:
            geom = self.frameGeometry()
        else:
            geom = self.geometry()
        return geom.getRect()


    def writeSettings(self):
        """Store the GUI settings

        This includes the GUI size and position
        """
        pf.debug('Store current settings', pf.DEBUG.CONFIG)
        # store the history and main window size/pos
        pf.prefcfg['gui/scripthistory'] = self.scripthistory.files
        pf.prefcfg['gui/apphistory'] = self.apphistory.files
        if not pf.options.geometry:
            # if geometry is specified, we do not store it
            pf.prefcfg.update({
                'size': (self.width(), self.height()),
                'pos': (self.x(), self.y()),
                'splitsize': (self.central.height(), self.console.height()),
            }, name='gui')


    def findDialog(self, name):
        """Find the Dialog with the specified name.

        Returns the list with matching dialogs, possibly empty.
        """
        return self.findChildren(widgets.Dialog, str(name))


    def closeDialog(self, name):
        """Close the Dialog with the specified name.

        Closest all the Dialogs with the specified caption
        owned by the GUI.
        """
        for w in self.findDialog(name):
            w.close()


    # TODO: This should go to a toolbar class
    def enableButtons(self, toolbar, buttons, enable):
        """Enable or disable a button in a toolbar.

        toolbar is a toolbar dict.
        buttons is a list of button names.
        For each button in the list:

        - If it exists in toolbar, en/disables the button.
        - Else does nothing
        """
        for b in buttons:
            if b in toolbar:
                toolbar[b].setEnabled(enable)


    def reloadActionButtons(self):
        for b in self.actions:
            self.toolbar.removeAction(self.actions[b].defaultAction())
        self.actions = toolbar.addActionButtons(self.toolbar)


    def startRun(self):
        """Change the GUI when an app/script starts running.

        This method enables/disables the parts of the GUI that should or
        should not be available while a script is running
        It is called by the application executor.
        """
        self.drawlock.allow()
        if pf.options.canvas:
            pf.canvas.update()
        self.enableButtons(self.actions, ['ReRun'], False)
        self.enableButtons(self.actions, ['Play', 'Step', 'Continue', 'Stop'], True)
        # by default, we run the script in the current GUI viewport
        if pf.options.canvas:
            pf.canvas = self.viewports.current
        pf.app.processEvents()


    def stopRun(self):
        """Change the GUI when an app/script stops running.

        This method enables/disables the parts of the GUI that should or
        should not be available when no script is being executed.
        It is called by the application executor when an application stops.
        """
        self.drawlock.release()
        pf.canvas.update()
        self.enableButtons(self.actions, ['Play', 'ReRun'], True)
        self.enableButtons(self.actions, ['Step', 'Continue', 'Stop'], False)
        # acknowledge viewport switching
        pf.canvas = self.viewports.current
        pf.app.processEvents()


    def cleanup(self):
        """Cleanup the GUI (restore default state)."""
        pf.debug('GUI cleanup', pf.DEBUG.GUI)
        self.drawlock.release()
        pf.canvas.cancel_selection()
        pf.canvas.cancel_draw()
        draw.clear_canvas()
        self.resetCursor()


    def onExit(self, func):
        """Register a function for execution on exit of the GUI.

        Parameters
        ----------
        func: callable
            A function to be called on exit of the GUI. There is
            no guaranteed order of execution of the exit functions.
        """
        if not callable(func):
            raise ValueError('func should be a callable')
        self.on_exit.add(func)


    def closeEvent(self, event):
        """Override the close event handler.

        We override the default close event handler for the main
        window, to allow the user to cancel the exit, and to save
        the latest settings.
        """
        #
        # DEV: things going wrong during the event handler are hard to debug!
        # You can add those things to a function and add the function to a
        # menu for testing. At the end of the file helpMenu.py there is an
        # example (commented out). Or set a gui/dooze value in the config.
        #
        from pyformex import script
        self.cleanup()
        if pf.options.gui:
            script.force_finish()
        if exitDialog():
            self.drawlock.free()
            pf.debug("Executing registered exit functions", pf.DEBUG.GUI)
            for f in self.on_exit:
                pf.debug(f, pf.DEBUG.GUI)
                f()
            self.writeSettings()
            self.saveConsoleHistory()
            # allow user to see result before shutting down
            dooze = pf.cfg['gui/dooze']
            if dooze > 0:
                print(f"Exiting in {dooze} seconds")
                draw.sleep(dooze)
            # redirect stdout/stdin back to original
            sys.stdout.flush()
            sys.stderr.flush()
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            event.accept()
        else:
            event.ignore()


    def run(self):
        """Go into interactive mode until the user exits"""
        try:
            # Make the workdir the current dir
            os.chdir(pf.cfg['workdir'])
            pf.debug(f"Setting workdir to {pf.cfg['workdir']}", pf.DEBUG.INFO)
        except Exception:
            # Save the current dir as workdir
            Settings.updateSettings({'workdir': Path.cwd(), '_save_': True})
        # correctly display the current workdir
        self.setcurdir()
        pf.interactive = True
        if easter_egg:
            pf.debug("Show easter egg", pf.DEBUG.INFO)
            try:
                draw.playScript(easter_egg, encoding='egg')
            except Exception:
                pass

        pf.debug("Start main loop", pf.DEBUG.INFO)
        now = datetime.datetime.now()
        pf.verbose(3, f"GUI startup time = {now - pf.start_time}")
        res = pf.app.exec_()
        pf.debug(f"Exit main loop with value {res}", pf.DEBUG.INFO)
        return res


    def fullScreen(self, onoff=None):
        """Toggle the canvas full screen mode.

        Fullscreen mode hides all the components of the main window, except
        for the central canvas, maximizes the main window, and removes the
        window decorations, thus leaving only the OpenGL canvas on the full
        screen. (Currently there is also still a small border remaining.)

        This mode is activated by pressing the F5 key. A second F5 press
        will revert to normal display mode.
        """
        hide = [self.statusbar, self.menu] + self.toolbars
        if self.console:
            hide.append(self.console)
        if onoff is None:
            onoff = not self.fullscreen

        if onoff:
            # goto fullscreen
            for w in hide:
                w.hide()
            self.boxlayout.setContentsMargins(0, 0, 0, 0)
            self.showFullScreen()
        else:
            # go to normal mode
            for w in hide:
                w.show()
            self.boxlayout.setContentsMargins(*pf.cfg['gui/boxmargins'])
            self.showNormal()

        self.update()
        self.fullscreen = onoff
        pf.app.processEvents()


    def enableToolbars(self, enable=True):
        """En/disable the toolbars."""
        for tb in self.toolbars:
            tb.setEnabled(enable)


def exitDialog():
    """Show the exit dialog to the user.

    """
    confirm = pf.cfg['gui/exitconfirm']

    if confirm == 'never':
        return True

    if confirm == 'smart' and (pf.PF.filename is None or pf.PF.hits == 0):
        return True

    print(f"Project variable changes: {pf.PF.hits}")
    print(f"pyFormex globals: {list(pf.PF.keys())}")

    save_opts = ['To current project file', 'Under another name', 'Do not save']
    res = draw.askItems(
        [draw._I('info', itemtype='label', value="You have unsaved global variables. What shall I do?"),
          draw._I('save', itemtype='vradio', choices=save_opts, text='Save the current globals'),
          draw._I('reopen', pf.cfg['openlastproj'], text="Reopen the project on next startup"),
          ],
        caption='pyFormex exit dialog')

    if not res:
        # Cancel the exit
        return False

    save = save_opts.index(res['save'])
    if save == 0:
        File.saveProject()
    elif save == 1:
        File.saveAsProject()

    if not res['reopen']:
        File.closeProject(save=False, clear=False)

    return True


def xwininfo(*, windowid=None, name=None):
    """Get information about an X window.

    Returns the information about an X11 window as obtained from
    the ``xwininfo`` command, but parsed as a dict. The window can
    be specified by its id or by its name. If neither is provided,
    the user needs to interactively select a window by clicking the
    mouse in that window.

    Parameters
    ----------
    windowid: str, optional
        A hex string with the window id.
    name: str
        The window name, usually displayed in the top border decoration.
    check_only: bool
        If True, only check whether the window exists, but do not return
        the info.

    Returns
    -------
    dict
        Return all the information obtained from calling
        ``xwininfo`` for the specified or picked window.
        If a window id or name is specified that does not exist,
        an empty dict is returned.

    Notes
    -----
    The window id of the pyFormex main window can be obtained from
    pf.GUI.winId(). The name of the window is pf.Version().
    """
    if windowid is not None:
        args = f" -id {windowid}"
    elif name is not None:
        args = f" -name '{name}'"
    else:
        raise ValueError("Either windowid or name have to be specified")

    P = process.run(f"xwininfo {args}")
    res = {}
    if not P.returncode:
        for line in P.stdout.split('\n'):
            s = line.split(':')
            if len(s) < 2:
                s = s[0].strip().split(' ')
            if len(s) < 2:
                continue
            elif len(s) > 2:
                if s[0] == 'xwininfo':
                    s = s[-2:]  # remove the xwininfo string
                    t = s[1].split()
                    s[1] = t[0]  # windowid
                    name = ' '.join(t[1:]).strip().strip('"')
                    res['Window name'] = name
            if s[0][0] == '-':
                s[0] = s[0][1:]
            res[s[0].strip()] = s[1].strip()

    return res


def pidofxwin(windowid):
    """Returns the PID of the process that has created the window.

    Remark: Not all processes store the PID information in the way
    it is retrieved here. In many cases (X over network) the PID can
    not be retrieved. However, the intent of this function is just to
    find a dangling pyFormex process, and this should probably work on
    a normal desktop configuration.
    """
    import re
    #
    # We need a new shell here, otherwise we get a 127 exit.
    #
    P = process.run(f"xprop -id '{windowid}' _NET_WM_PID", shell=True)
    m = re.match(r"_NET_WM_PID\(.*\)\s*=\s*(?P<pid>\d+)", P.stdout)
    if m:
        pid = m.group('pid')
        return int(pid)

    return None


def findOldProcesses(max=16):
    """Find old pyFormex GUI processes still running.

    There is a maximum to the number of processes that can be detected.
    16 will suffice largely, because there is no sane reason to open that many
    pyFormex GUI's on the same screen.

    Returns the next available main window name, and a list of
    running pyFormex GUI processes, if any.
    """
    windowname = pf.Version()
    if pf.options.gl3:
        windowname += '--gl3'
    count = 0
    running = []

    while count < max:
        info = xwininfo(name=windowname)
        if info:
            name = info['Window name']
            windowid = info['Window id']
            if name == windowname:
                pid = pidofxwin(windowid)
            else:
                pid = None
            # pid control needed for invisible windows on ubuntu
            if pid:
                running.append((windowid, name, pid))
                count += 1
                windowname = f"{pf.Version()} ({count})"
            else:
                break
        else:
            break

    return windowname, running


def killProcesses(pids):
    """Kill the processes in the pids list."""
    warning = f"""..

Killing processes
-----------------
I will now try to kill the following processes::

    {pids}

You can choose the signal to be sent to the processes:

- KILL (9)
- TERM (15)

We advice you to first try the TERM(15) signal, and only if that
does not seem to work, use the KILL(9) signal.
"""
    actions = ['Cancel the operation', 'KILL(9)', 'TERM(15)']
    answer = draw.ask(warning, actions)
    if answer == 'TERM(15)':
        utils.killProcesses(pids, 15)
    elif answer == 'KILL(9)':
        utils.killProcesses(pids, 9)

########################
# Main application
########################


class Application(QtWidgets.QApplication):
    """The interactive Qt application

    Sets the default locale to 'C' and rejects thousands separators.
    This is the only sensible thing to do for processing numbers in
    an international scientific community.

    Overrides some QApplication methods for convenience (usually to
    allow simple strings as input).
    """
    forbidden_styles = ['gtk2']   # causes segmentation fault

    def __init__(self, args=sys.argv[:1]):
        if len(args) != 1:
            pf.debug(f"Arguments passed to the QApplication: {args}",
                     pf.DEBUG.INFO)
        # Make sure numbers are always treated correctly on in/out
        # The idiots that think otherwise, perhaps never use files
        # as interface between programs.
        locale = QtCore.QLocale.c()
        locale.setNumberOptions(QtCore.QLocale.RejectGroupSeparator)
        QtCore.QLocale.setDefault(locale)
        # Initialize the QApplication
        super().__init__(args)
        pf.debug(f"Arguments left after starting QApplication: {args}",
                 pf.DEBUG.INFO)
        # Set application attributes"
        self.setOrganizationName("pyformex.org")
        self.setOrganizationDomain("pyformex.org")
        self.setApplicationName("pyFormex")
        self.setApplicationVersion(pf.__version__)
        # Set appearance
        pf.debug("Setting Appearance", pf.DEBUG.GUI)
        self.setAppearance()
        # Quit application on aboutToQuit or lastWindowClosed signals
        self.aboutToQuit.connect(self.quit)
        self.lastWindowClosed.connect(self.quit)

    def maxSize(self):
        """Return the maximum available screensize"""
        return qtutils.Size(self.screens()[0].availableSize())


    def currentStyle(self):
        """Return the application style in use"""
        return self.style().metaObject().className()[1:-5]

    def getStyles(self):
        """Return the available styles, removing the faulty ones."""
        return [s.lower() for s in QtWidgets.QStyleFactory().keys()
                if s not in Application.forbidden_styles]

    def setStyle(self, style):
        """Set the application style.

        style is a string, one of those returned by :meth:`getStyles`
        """
        if style.lower() not in self.getStyles():
            print(f"Can not set style: {style}")
            return
        super().setStyle(style)

    def setFont(self, font):
        """Set the main application font.

        font is either a QFont or a string resulting from the
        QFont.toString() method
        """
        if isinstance(font, str):
            f = QtGui.QFont()
            f.fromString(font)
            font = f
        super().setFont(font)


    def setFontFamily(self, family):
        """Set the main application font family to the given family."""
        font = self.font()
        font.setFamily(family)
        self.setFont(font)


    def setFontSize(self, size):
        """Set the main application font size to the given point size."""
        font = self.font()
        font.setPointSize(int(size))
        self.setFont(font)


    def setAppearance(self):
        """Set all the GUI appearance elements.

        Sets the GUI appearance from the current configuration values
        'gui/style', 'gui/font', 'gui/fontfamily', 'gui/fontsize'.
        """
        style = pf.cfg['gui/style']
        font = pf.cfg['gui/font']
        family = pf.cfg['gui/fontfamily']
        size = pf.cfg['gui/fontsize']
        if style:
            self.setStyle(style)
        if font or family or size:
            if not font:
                font = self.font()
                if family:
                    font.setFamily(family)
                if size:
                    font.setPointSize(size)
            self.setFont(font)


def showSplash():
    """Show the splash screen"""
    pf.debug("Loading the splash image", pf.DEBUG.GUI)
    splash = None
    splash_path = pf.cfg['gui/splash']
    if splash_path.exists():
        pf.debug(f"Loading splash {splash_path}", pf.DEBUG.GUI)
        splashimage = QPixmap(splash_path)
        splash = QtWidgets.QSplashScreen(splashimage)
        splash.setFont(QtGui.QFont("Helvetica", 20))
        splash.showMessage(pf.Version(),
                           QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop,
                           QtCore.Qt.red)
        splash.show()
    return splash


# TODO: some things could be moved in Application or Gui class
def createGUI():
    """Create the Qt application and GUI.

    A (possibly empty) list of command line options should be provided.
    Qt wil remove the recognized Qt and X11 options.
    """
    pf.app = Application()
    pf.X11 = pf.app.platformName() in ('xcb', )

    # Set OpenGL format and check if we have DRI
    qtgl.setOpenGLFormat()
    dri = qtgl.hasDRI()

    # Check for existing pyFormex processes
    pf.debug("Checking for running pyFormex", pf.DEBUG.INFO)
    if pf.X11:
        windowname, running = findOldProcesses()
    else:
        windowname, running = "UNKOWN", []
    pf.debug(f"{windowname}, {running}", pf.DEBUG.INFO)


    while len(running) > 0:
        if len(running) >= 16:
            print(f"Too many open pyFormex windows: {len(running)} --- bailing out")
            return -1

        pids = [i[2] for i in running if i[2] is not None]
        warning = """..

pyFormex is already running on this screen
------------------------------------------
A main pyFormex window already exists on your screen.

If you really intended to start another instance of pyFormex, you
can just continue now.

The window might however be a leftover from a previously crashed pyFormex
session, in which case you might not even see the window anymore, nor be able
to shut down that running process. In that case, you would better bail out now
and try to fix the problem by killing the related process(es).

If you think you have already killed those processes, you may check it by
rerunning the tests.
"""
        actions = ['Really Continue', 'Rerun the tests', 'Bail out and fix the problem']
        if pids:
            warning += f"""

I have identified the process(es) by their PID as::

{pids}

If you trust me enough, you can also have me kill this processes for you.
"""
            actions[2:2] = ['Kill the running processes']

        if dri:
            answer = draw.ask(warning, actions)
        else:
            warning += """
I have detected that the Direct Rendering Infrastructure
is not activated on your system. Continuing with a second
instance of pyFormex may crash your XWindow system.
You should seriously consider to bail out now!!!
"""
            answer = draw.showWarning(warning, actions)


        if answer == 'Really Continue':
            break  # OK, Go ahead

        elif answer == 'Rerun the tests':
            windowname, running = findOldProcesses()  # try again

        elif answer == 'Kill the running processes':
            killProcesses(pids)
            windowname, running = findOldProcesses()  # try again

        else:
            return -1  # I'm out of here!

    splash = showSplash()

    # create GUI, show it, run it
    pf.debug("Creating the GUI", pf.DEBUG.GUI)
    if splash is not None:
        splash.showMessage("Creating the GUI");
    if pf.options.geometry:
        w, h, x, y = splitXgeometry(pf.options.geometry)
        size = (w, h)
        pos = (x, y)
        splitsize = (3*h//4, h//4)
    else:
        size = pf.cfg['gui/size']
        pos = pf.cfg['gui/pos']
        splitsize = pf.cfg['gui/splitsize']

    # Create the GUI
    pf.GUI = Gui(windowname, size, pos, splitsize)

    # update interpreter locals
    pf.interpreter.locals.update(draw.Globals())

    # setup the console
    pf.GUI.console.clear()
    pf.GUI.console.writecolor(f"""\
{pf.fullVersion()}   (C) Benedict Verhegghe

pyFormex comes with ABSOLUTELY NO WARRANTY. This is free software, and you are welcome to redistribute it under the conditions of the GNU General Public License, version 3 or later. See Help->License or the file COPYING for details.
""")

    # Set interaction functions

    def show_warning(message, category, filename, lineno, file=None, line=None):
        """Replace the default warnings.showwarning

        We display the warnings using our interactive warning widget.
        This feature can be turned off by setting
        cfg['warnings/popup'] = False
        """
        message = str(message)
        # NOTE: the following will expand our short message identifier
        # with the expanded message text from messages.py
        full_message = warnings.formatwarning(message, category, filename, lineno, line)
        print(full_message)
        res, check = draw.showMessage(
            full_message, level='warning',
            check="Do not show this warning anymore in this and future sessions")
        utils.filterWarning(message, category=category, save=check[0])

    if pf.cfg['warnings/popup']:
        warnings.showwarning = show_warning


    pf.warning = draw.showWarning
    pf.error = draw.showError


    # setup the canvas
    if pf.options.canvas:
        if splash is not None:
            splash.showMessage("Creating the canvas");
        pf.debug("Setting the canvas", pf.DEBUG.GUI)
        pf.app.processEvents()
        pf.GUI.viewports.changeLayout(1)
        pf.GUI.viewports.setCurrent(0)
        pf.canvas.setRenderMode(pf.cfg['draw/rendermode'])
        draw.reset()
        # set canvas background
        # (does not work before a draw.reset, do not know why)
        pf.canvas.setBackground(color=pf.cfg['canvas/bgcolor'],
                                image=pf.cfg['canvas/bgimage'])
        pf.canvas.update()

    # fix button states
    toolbar.perspective_button.update_status()


    # setup the status bar
    pf.debug("Setup status bar", pf.DEBUG.GUI)
    if pf.options.canvas:
        pf.GUI.addCoordsTracker()
        pf.GUI.toggleCoordsTracker(pf.cfg['gui/coordsbox'])
    pf.debug(f"Using window name {pf.GUI.windowTitle()}", pf.DEBUG.GUI)

    # Script/App menu
    if splash is not None:
        splash.showMessage("Loading script/app menu")
    pf.GUI.scriptmenu = appMenu.createAppMenu(
        parent=pf.GUI.menu, before='help', mode='script')
    pf.GUI.appmenu = appMenu.createAppMenu(
        parent=pf.GUI.menu, before='help')

    # Create databases
    createDatabases()
    # Link them in Globals menu
    Globals._init_(pf.GUI.database, pf.GUI.selection['geometry'])

    # Load configured plugin menus
    if splash is not None:
        splash.showMessage("Loading plugins");
    plugins.loadConfiguredPlugins()

    # show current application/file
    if splash is not None:
        splash.showMessage("Load current application");
    appname = pf.cfg['curfile']
    pf.GUI.setcurfile(appname)

    # Last minute menu modifications can go here

    # cleanup
    if splash is not None:
        splash.showMessage("Set status bar");
    #pf.GUI.addStatusBarButtons()

    pf.debug("Showing the GUI", pf.DEBUG.GUI)
    if splash is not None:
        splash.showMessage("Show the GUI");

    pf.GUI.show()

    if pf.DEBUG.GUI in pf.options.debuglevel:
        pf.debug(', '.join(
            (qtutils.sizeReport(pf.GUI, 'main:'),
             qtutils.sizeReport(pf.GUI.box, 'box:'),
             qtutils.sizeReport(pf.GUI.central, 'central:'),
             qtutils.sizeReport(pf.GUI.console, 'console'),
             )
        ), pf.DEBUG.GUI)

    if splash is not None:
        # remove the splash window
        splash.finish(pf.GUI)

    pf.debug("Update", pf.DEBUG.GUI)
    pf.GUI.update()

    if pf.cfg['gui/fortune']:
        P = process.run(pf.cfg['fortune'])
        if P.returncode == 0:
            draw.showInfo(P.stdout)

    # display startup warning
    if pf.cfg['gui/startup_warning']:
        utils.warn(pf.cfg['gui/startup_warning'])

    # Enable the toolbars
    pf.GUI.enableToolbars()

    #pf.app.setQuitOnLastWindowClosed(False)
    pf.debug("ProcessEvents", pf.DEBUG.GUI)
    pf.app_started = True
    pf.app.processEvents()

    ##### GUI ready ########
    if pf.options.runall:
       from pyformex.appsdir.RunAll import runAll
       runAll(count=pf.options.runall, shuffle=True)
       # TODO: should we continue or exit here?
       pf.GUI.close()
       pf.app.quit()

    # load last project
    #  TODO
    if pf.cfg['openlastproj'] and pf.cfg['curproj']:
        fn = Path(pf.cfg['curproj'])
        if fn.exists():
            proj = File.readProjectFile(fn)
            if proj:
                File.setProject(proj)
    #
    pf.debug("GUI Started", pf.DEBUG.GUI)
    return 0


def createDatabases():
    """Create unified database objects for all menus."""
    from pyformex.plugins import objects
    from pyformex.geometry import Geometry
    from pyformex.formex import Formex
    from pyformex.mesh import Mesh
    from pyformex.trisurface import TriSurface
    from pyformex.curve import PolyLine, BezierSpline
    from pyformex.plugins.nurbs import NurbsCurve
    pf.GUI.database = objects.Objects()
    pf.GUI.drawable = objects.DrawableObjects()
    pf.GUI.selection = {
        'geometry': objects.DrawableObjects(clas=Geometry),
        # 'formex': objects.DrawableObjects(clas=Geometry, allowed=Formex),
        # 'mesh': objects.DrawableObjects(clas=Geometry, allowed=Mesh),
        # 'surface': objects.DrawableObjects(clas=Geometry, allowed=TriSurface)),
        'polyline': objects.DrawableObjects(clas=PolyLine),
        'nurbs': objects.DrawableObjects(clas=NurbsCurve),
        'curve': objects.DrawableObjects(clas=BezierSpline),
        }
    pf.GS = pf.GUI.selection['geometry']



#### End
