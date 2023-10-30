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
"""pyFormex GUI module initialization.

This module is intended to form a single access point to the Python
wrappers for the QT libraries, which form the base of the pyFormex GUI.
By using a single access point, we can better deal with API changes
in the wrappers.

All pyFormex modules accessing QT libraries should do this by importing
from this module.

This module also detects the underlying windowing system.
Currently, the pyFormex GUI is only guaranteed on X11.
For other systems, a warning will be printed that some things may not work.
"""
import sys

import pyformex as pf
from pyformex import Path
from pyformex import utils

BINDINGS = ('pyside2', 'pyqt5')
bindings = pf.cfg['gui/bindings'].lower()

if bindings in BINDINGS:
    utils.Module.require(bindings)
else:
    # Try using any existing bindings
    bindings = ''
    for b in BINDINGS:
        if utils.Module.has(b):
            bindings = b
            break

if bindings == 'pyside2':
    from PySide2 import QtCore, QtGui, QtOpenGL, QtWidgets
    from PySide2.QtCore import Signal, Slot

elif bindings == 'pyqt5':
    from PyQt5 import QtCore, QtGui, QtOpenGL, QtWidgets
    from PyQt5.QtCore import pyqtSignal as Signal
    from PyQt5.QtCore import pyqtSlot as Slot

else:
    bindings = ''

if not bindings:
    raise ValueError("\n"+"*"*40+"\nThe pyFormex GUI requires Python bindings for the Qt libraries.\n These are available as PySide2 or PyQt5.\nI could not find neither of them, so I can not continue.\nInstall one of these bindings for Python3 (including its OpenGL component)\nand then retry."+"\n"+"*"*40)


if bindings == 'pyside2':
    def QByteArrayToStr(self):
        """Convert a QByteArray to a Python3 str"""
        return str(self)[2:-1]
    QtCore.QByteArray.toStr = QByteArrayToStr


# Some Qt wrappers

class QPixmap(QtGui.QPixmap):
    def __init__(self, *args):
        if isinstance(args[0], Path):
            args = (str(args[0]),) + args[1:]
        QtGui.QPixmap.__init__(self, *args)


class QImage(QtGui.QImage):
    def __init__(self, *args):
        if isinstance(args[0], Path):
            args = (str(args[0]),) + args[1:]
        QtGui.QImage.__init__(self, *args)


# End
