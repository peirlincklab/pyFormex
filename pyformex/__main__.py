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

"""pyFormex startup module

Running this module from the Python3 interpreter will start the
pyFormex program::

    python3 __main__.py

Parameters can be passed to pyFormex if you precede them with a '--'
option::

    python3 __main__.py -- --help

However, pyFormex comes with an executable (called pyformex or
pyformex-VERSION) that simplifies the startup::

    pyformex --help
"""
import os
import sys

# Get the pyformex dir and put it on the head of sys.path
# This has to be done *before* importing pyformex, so it
# can only be done here.

_bindir = sys.path[0]

# In case we execute the pyformex script from inside the
# pyformex package dir: add the parent to the front of sys.path
# to pick up the package here instead of from default path

if _bindir.endswith('pyformex'):
    sys.path[0] = os.path.dirname(_bindir)

try:
    import pyformex as pf
except ImportError as e:
    print(e)
    raise ImportError("""
#######################################################################
##  The pyformex package could not be imported.
##  This probably means that pyFormex was not properly installed.
#######################################################################
""")

# set the pyformex executable
if len(sys.argv) > 1:
    pf.executable = pf.Path(sys.argv[1])
    common = pf.executable.commonprefix(pf.pyformexdir)
    if common == '/':
        raise RuntimeError(
            f"You started pyFormex from {pf.executable} "
            f"but imported the pyformex package from {pf.pyformexdir}. "
            f"This is not a normal situation! Either start the program "
            f"from another directory, or use the pyformex/pyformex script "
            f"if you want to use the pyformex package from {pf.pyformexdir}.")

###################################################################
## Run pyFormex
###############

if __name__ == "__main__":
    from pyformex import main
    res = main.run(sys.argv[2:])
    #sys.exit(res)

# End
