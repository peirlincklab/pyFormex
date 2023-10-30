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
"""signals.py: Definition of our own signals used in the GUI communication.

Signals are treated by the normal Qt machine. They can be emitted from
anywhere, causing attached functions to be executed.
"""


from pyformex.gui import QtCore
from pyformex.gui import Signal


class Signals(QtCore.QObject):
    """A class with all custom signals in pyFormex.

    Custom signals are instances of the gui.Signal function, and should
    be defined inside a class derived from QtCore.QObject.

    The following signals are currently defined:

    - CANCEL: cancel the operation, undoing it
    - DONE: accept and finish the operation
    - REDRAW: redraw a preview state
    - WAKEUP: wake up from a sleep state
    - TIMEOUT: terminate what was going on
    - SAVE: save current rendering
    - FULLSCREEN: toggle fullscreen mode
    - VALIDATED: the dialog data were validated
    - RECTANGLE: a rectangle has been picked
    """
    CANCEL = Signal()
    DONE   = Signal()
    REDRAW = Signal()
    WAKEUP = Signal()
    TIMEOUT = Signal()
    SAVE = Signal()
    FULLSCREEN = Signal()
    VALIDATED = Signal()


# End
