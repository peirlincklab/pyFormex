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
"""Core

Print the list of symbols that are defined in the pyFormex core language.
These symbols are globally available when running a script/app.
"""
from pyformex.gui.draw import *

header = f"""\
These are the identifiers imported in the pyFormex core language
with the scriptmode set to '{pf.cfg['scriptmode']}'.
The scriptmode can be changed in the Settings menu.
In the future, the 'strict' mode may be further restricted.
"""

def run():
    keys = sorted(globals().keys())
    print(header)
    print(keys)
    print(f"There are {len(keys)} identifiers in total.")

if __name__ == '__draw__':
    run()
# End
