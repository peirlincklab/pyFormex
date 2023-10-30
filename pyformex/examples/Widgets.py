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

"""Widgets

"""


_level = 'beginner'
_topics = ['dialog']
_techniques = []

from pyformex.gui.draw import *

def run():
    print(error("This is a simulated error, to demonstrate how an error message would be shown to the user.\nJust click OK and the error will go away."))

    print(warning("""
<h1>This is a warning.</h1>
A warning draws attention of the user on special conditions.<br/>
Remark that we can use plain text or html.
"""))

    print(showInfo("""..

A text in ReST
==============

- The lowest level of message box is the *info* level.
  It just displays information for the user.
- ReST text is automatically detected if it starts with '..'.

"""))

    print(ask("Answer this question with yes or no", ['Yes', 'No']))


    print(selectItems(["a", "ccc", "bb", "dddd"], sort=True))

if __name__ == '__draw__':
    run()
# End
