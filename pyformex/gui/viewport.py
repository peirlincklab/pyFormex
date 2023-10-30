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
"""Multiple OpenGL viewports in a Qt widget.

This module provides the MultiCanvas class which allows for multiple
OpenGL viewports in a single Qt OpenGL widget.
"""
import pyformex as pf
from pyformex import arraytools as at
from pyformex import utils
from pyformex.gui import QtWidgets
from . import toolbar

if not pf.sphinx:
    if pf.options.mgl:
        from opengl3.mglcanvas import *
    else:
        from .qtcanvas import *

###########################################################################
#####    Multiple Viewports    #######

@utils.pzf_register
class MultiCanvas(QtWidgets.QGridLayout):
    """An OpenGL canvas with multiple viewports.

    The MultiCanvas implements a central QT widget containing one or more
    QtCanvas widgets.
    """
    def __init__(self, parent=None):
        """Initialize the multicanvas."""
        QtWidgets.QGridLayout.__init__(self)
        self.setContentsMargins(0, 0, 0, 0)
        self.all = []
        self.links = {}
        self.current = None
        self.ncols = 2
        self.rowwise = True
        self.pos = None
        self.rstretch = None
        self.cstretch = None
        self.parent = parent


    def __getitem__(self, i):
        return self.all[i]


    def changeLayout(self, nvps=None, ncols=None, nrows=None, pos=None, rstretch=None, cstretch=None, reset=False):
        """Change the lay-out of the viewports on the OpenGL widget.

        nvps: number of viewports
        ncols: number of columns
        nrows: number of rows
        pos: list holding the position and span of each viewport
        [[row,col,rowspan,colspan],...]
        rstretch: list holding the stretch factor for each row
        cstretch: list holding the stretch factor for each column
        (rows/columns with a higher stretch factor take more of the
        available space)
        Each of this parameters is optional.

        If a number of viewports is given, viewports will be added
        or removed to match the requested number.
        By default they are laid out rowwise over two columns.

        If ncols is an int, viewports are laid out rowwise over ncols
        columns and nrows is ignored. If ncols is None and nrows is an int,
        viewports are laid out columnwise over nrows rows. Alternatively,
        the pos argument can be used to specify the layout of the viewports.
        """
        # add or remove viewports to match the requested number
        if at.isInt(nvps):
            while len(self.all) > (0 if reset else nvps):
                self.removeView()
            while len(self.all) < nvps:
                self.addView()
        # get the new layout definition
        if at.isInt(ncols):
            rowwise = True
            pos = None
        elif at.isInt(nrows):
            ncols = nrows
            rowwise = False
            pos = None
        elif isinstance(pos, list) and len(pos) == len(self.all):
            ncols = None
            rowwise = None
        else:
            return
        # remove the viewport widgets
        for w in self.all:
            self.removeWidget(w)
        # assign the new layout arguments
        self.ncols = ncols
        self.rowwise = rowwise
        self.pos = pos
        self.rstretch = rstretch
        self.cstretch = cstretch
        # add the viewport widgets
        for w in self.all:
            self.showWidget(w)


    def newView(self, shared=True, settings=None):
        """Create a new viewport.

        If shared is True, and the MultiCanvas already has one or more
        viewports, the new viewport will share display lists and textures
        with the first viewport. Since pyFormex is not using display
        lists (anymore) and textures are needed to display text, the value
        defaults to True, and all viewports will share the same textures,
        unless a viewport is created with a specified value for shared:
        it can either be another viewport to share textures with, or a
        value False or None to not share textures with any viewport. In the
        latter case you will not be able to use text display, unless you
        initialize the textures yourself.

        settings: can be a legal CanvasSettings to initialize the viewport.
        Default is to copy settings of the current viewport.

        Returns the created viewport, which is an instance of QtCanvas.
        """
        if not isinstance(shared, QtCanvas):
            if shared and len(self.all) > 0:
                shared = self.all[0]
            else:
                shared = None

        # Now shared should be a QtCanvas or None
        pf.debug("New viewport sharing textures with %s" % shared, pf.DEBUG.DRAW)
        if settings is None:
            try:
                settings = self.current.settings
            except Exception:
                settings = {}
        #pf.debug("Create new viewport with settings:\n%s"%settings, pf.DEBUG.CANVAS)
        ##
        ## BEWARE: shared should be positional, settings should be keyword !
        canv = QtCanvas(self.parent, shared, settings=settings)
        #print(canv.settings)
        return(canv)


    def addView(self):
        """Add a new viewport to the widget"""
        canv = self.newView()
        if len(self.all) > 0:
            # copy default settings from previous
            canv.resetDefaults(self.all[-1].settings)
        self.all.append(canv)
        self.showWidget(canv)
        canv.initializeGL()   # Initialize OpenGL context and camera
        self.setCurrent(canv)


    def setCurrent(self, canv):
        """Make the specified viewport the current one.

        canv can be either a viewport or viewport number.
        """
        if at.isInt(canv) and canv in range(len(self.all)):
            canv = self.all[canv]
        if canv == self.current:
            pass
        elif canv in self.all:
            if self.current:
                self.current.focus = False
                self.current.updateGL()
            self.current = canv
            # Only show focus if more than 1
            self.current.focus = len(pf.GUI.viewports.all) > 1 and pf.cfg['gui/showfocus']
            self.current.updateGL()
            toolbar.updateViewportButtons(self.current)
        pf.canvas = self.current


    def viewIndex(self, view):
        """Return the index of the specified view"""
        return self.all.index(view)


    def currentView(self):
        """Return the index of the current view"""
        return self.all.index(self.current)


    def showWidget(self, w):
        """Show the view w."""
        ind = self.all.index(w)
        if self.pos is None:
            row, col = divmod(ind, self.ncols)
            if not self.rowwise:
                row, col = col, row
            rspan, cspan = 1, 1
        elif ind < len(self.pos):
            row, col, rspan, cspan = self.pos[ind]
        else:
            return
        self.addWidget(w, row, col, rspan, cspan)
        w.raise_()
        # set the stretch factors
        if self.rstretch is not None:
            for i in range(row, row+rspan):
                if i >= len(self.rstretch):
                    self.rstretch.append(1)
                self.setRowStretch(i, self.rstretch[i])
        if self.cstretch is not None:
            for i in range(col, col+cspan):
                if i >= len(self.cstretch):
                    self.cstretch.append(1)
                self.setColumnStretch(i, self.cstretch[i])


    def removeView(self):
        """Remove the last view"""
        if len(self.all) > 1:
            w = self.all.pop()
            lastnr = len(self.all)
            if lastnr in self.links:
                del self.links[lastnr]
            if self.pos is not None:
                self.pos = self.pos[:-1]
            if self.current == w:
                self.setCurrent(self.all[-1])
            self.removeWidget(w)
            w.close()
            # Remove focus rectangle if only one left
            if len(self.all) == 1:
                self.current.focus = False
            # set the stretch factors
            pos = [self.getItemPosition(self.indexOf(w)) for w in self.all]
            if self.rstretch is not None:
                row = max([p[0]+p[2] for p in pos])
                for i in range(row, len(self.rstretch)):
                    self.setRowStretch(i, 0)
                self.rstretch = self.rstretch[:row]
            if self.cstretch is not None:
                col = max([p[1]+p[3] for p in pos])
                for i in range(col, len(self.cstretch)):
                    self.setColumnStretch(i, 0)
                self.cstretch = self.cstretch[:col]


##     def setCamera(self,bbox,view):
##         self.current.setCamera(bbox,view)

    def updateAll(self):
         pf.debug("UPDATING ALL VIEWPORTS", pf.DEBUG.GUI)
         for v in self.all:
             v.update()
         pf.app.processEvents()

    def printSettings(self):
        for i, v in enumerate(self.all):
            print("""
## VIEWPORTS ##
Viewport %s;  Current:%s;  Settings:
%s
""" % (i, v == self.current, v.settings))


    def linkScene(self, vp, to):
        vp0 = self.all[to]
        vp1 = self.all[vp]
        vp1.scene = vp0.scene
        vp0.zoomAll()
        vp1.zoomAll()
        vp0.updateGL()
        vp1.updateGL()
        pf.app.processEvents()


    # TODO: We should probably limit linking to the changelayout case
    def link(self, vp, to):
        """Link viewport vp to to"""
        nvps = len(self.all)
        vp = checkInt(vp, 0, nvps-1)
        to = checkInt(to, 0, nvps-1)
        # resolve links
        while to != vp and to in self.links:
            to = self.links[to]
        if to == vp:
            raise ValueError("Can not link viewport to itself")
        print("Link viewport %s to %s" % (vp, to))
        self.links[vp] = to
        tovp = self.all[to]
        oldvp = self.all[vp]
        utils.warn('warn_viewport_linking')
        newvp = self.newView(shared=True)
        self.all[vp] = newvp
        self.removeWidget(oldvp)
        oldvp.close()
        self.showWidget(newvp)
        newvp.scene = tovp.scene
        #newvp.scene.actors = to.scene.actors
        newvp.show()
        newvp.setCamera()
        newvp.redrawAll()
        #newvp.updateGL()
        pf.app.processEvents()


    def settings(self):
        """Return the full configuration needed to restore the MultiCanvas"""
        d = {
            'gui_size': qtutils.Size(pf.GUI),
            'central_size': qtutils.Size(pf.GUI.central),
            'nvps': len(self.all),
            'rowwise': self.rowwise,
            'ncols': self.ncols,
            'current': self.viewIndex(self.current),
#            'canvas': self.viewIndex(pf.canvas),
            }
        for i, vp in enumerate(self.all):
            d[f'canvas{i}'] = dict(vp.settings)
            d[f'camera{i}'] = vp.camera.settings()
        return d


    def loadConfig(self, config):
        """Reset the viewports size, layout and cameras from a dict"""
        size = config['gui_size']
        if size:
            pf.GUI.resize(*size)
        size = config['central_size']
        if size:
            pf.GUI.central.resize(*size)
        nvps = config['nvps']
        rowwise = config['rowwise']
        ncols = config['ncols']
        nrows = None
        if not rowwise:
            ncols, nrows = nrows, ncols
        self.changeLayout(nvps = nvps, ncols=ncols, nrows=nrows)
        for i in range(len(self.all)):
            Ci = config[f'canvas{i}']
            canvas = self.all[i]
            canvas.settings.update(Ci)
            Ci = config[f'camera{i}']
            canvas.camera.loadConfig(Ci)
        current = config['current']
        if current:
            self.setCurrent(current)
        self.update()

    ###################
    ## PZF interface ##

    def pzf_dict(self):
        return { 'kargs:p': self.settings() }

    @classmethod
    def pzf_load(clas, **kargs):
        return kargs


    ## DEPRECATED ##

    # Deprecated old canvas/camera saving format   2023-01
    # TODO: remove after 2023-08


    @utils.deprecated('camera_save')
    def save(self, filename):
        """Save the canvas settings to file"""
        d = self.settings()
        open(filename, 'w').write(f"{d!r}\n")


    @utils.deprecated('camera_save')
    def load(self, filename):
        """Load the canvas settings from file"""
        f = open(filename, 'r')
        t = f.read()
        d = eval(t)
        self.loadConfig(d)

# End
