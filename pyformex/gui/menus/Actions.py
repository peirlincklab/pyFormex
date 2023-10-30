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
"""Menus for the pyFormex GUI.

This modules implements specialized classes and functions for building
the pyFormex GUI menu system.
"""
import pyformex as pf
from pyformex import utils
from pyformex import script
from pyformex.gui import (
    QtGui, QtCore, Signal,
    toolbar, image, draw,
    )

# The menu actions can be simply function names instead of strings, if the
# functions have already been defined here.

def printwindow():
    #pf.app.syncX()
    r = pf.GUI.XGeometry()
    print(f"Qt geom(w,h,x,y): {r}")


_geometry=None

def saveGeometry():
    global _geometry
    _geometry = pf.GUI.saveGeometry()

def restoreGeometry():
    pf.GUI.restoreGeometry(_geometry)

def closeLogFile():
    if draw.logfile:
        draw.logfile.close()
        draw.logfile = None

def openLogFile():
    fn = draw.askFilename(filter=['*.log', '*'])
    if fn:
        closeLogFile()
        draw.logfile = open(fn, 'w')


def printSysPath():
    import sys
    print(sys.path)


def printModules():
    import sys
    print(sorted(sys.modules.keys()))


def printLastCommand():
    """Print a nice report of the outcome of the last command"""
    print('=' * 8 + " LAST COMMAND REPORT " + '=' * 21)
    print(utils.last_command)
    print('=' * 50)


def saveBoard():
    extra = [draw._I('contents', choices=['all', 'commands', 'output'])]
    res = draw.askFile(filter=['*.txt', '*'], extra=extra)
    if res:
        pf.GUI.console.save(res['filename'], res['contents'])


def clearBoard():
    pf.GUI.console.clear()


def toggleConsole(onoff=None):
    if pf.GUI.console:
        if onoff is None:
            onoff = not pf.GUI.console.isVisible()
        pf.GUI.console.setVisible(onoff)
        pf.GUI.update()


def toggleConsoleInput(onoff=None):
    if pf.GUI.console:
        if onoff is None:
            onoff = not pf.GUI.console.inpedit.isVisible()
        pf.GUI.console.promptdisp.setVisible(onoff)
        pf.GUI.console.inpedit.setVisible(onoff)


MenuData = ('Actions', [
    ('Play', draw.play),
    ('Rerun', draw.replay),
    ## ('Step',draw.step),
    ('Continue', draw.fforward),
    ('Stop', draw.raiseExit),
    ("---", None),
    ('Console', [
        ('Save Output', saveBoard),
        ('Clear Output', clearBoard),
        ('Toggle Console', toggleConsole),
        ('Toggle Input Area', toggleConsoleInput),
        ]),
    ("---", None),
    ('Open Log File', openLogFile),
    ('Close Log File', closeLogFile),
    ('Print Config', script.printConfig),
    ('Print Last Command', printLastCommand),
    ('Print Loaded Apps', script.printLoadedApps),
    ('Print sys.path', printSysPath),
    ('Print loaded modules', printModules),
    ('Print Bbox', draw.printbbox),
    ('Print Viewport Settings', draw.printviewportsettings),
    ('Print Window Geometry', printwindow),
    ## ('Reset Picking Mode',resetPick),
    ('Save Geometry', saveGeometry),
    ('Restore Geometry', restoreGeometry),
    ('Toggle Input Timeout', toolbar.timeout),
    ('Reset GUI', draw.resetGUI),
   ])


# End
