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
"""pyFormex C library module initialisation.

This tries to load the compiled libraries, and replaces those that failed
to load with the (slower) Python versions, if possible.
"""

import pyformex as pf
__all__ = ['misc', 'nurbs', 'accelerated']

misc = nurbs = None
accelerated = []


def checkVersion(module):
    pf.debug("Succesfully loaded the pyFormex compiled module %s" % module.__name__, pf.DEBUG.LIB)
    pf.debug("  Module version is %s" % module.__version__, pf.DEBUG.LIB)
    if not module.__version__ == pf.__version__:
        target = 'lib3'
        raise RuntimeError("Incorrect acceleration module version (have %s, required %s)\nIf you are running pyFormex directly from sources, this might mean you have to run 'make %s' in the top directory of your pyFormex source tree.\nElse, this probably means pyFormex was not correctly installed." % (module.__version__, pf.__version__, target))
    accelerated.append(module)


accelerate = gui = False
if pf.options:
    # testing for not False makes other values than T/F (like None) pass
    # test for existence of these is for sphinx
    accelerate = pf.options.uselib is not False
    gui = hasattr(pf.options, 'gui') and pf.options.gui


if accelerate:

    try:
        from pyformex.lib import misc_c as misc
        checkVersion(misc)
    except ImportError:
        pf.debug("Error while loading the pyFormex compiled misc library", pf.DEBUG.LIB)

    try:
        from pyformex.lib import nurbs_c as nurbs
        checkVersion(nurbs)
    except ImportError:
        pf.debug("Error while loading the pyFormex compiled nurbs library", pf.DEBUG.LIB)

# Load Python libraries if acceleration libraries failed

if misc is None:
    pf.debug("Using the (slower) Python misc functions", pf.DEBUG.LIB)
    from pyformex.lib import misc_e as misc

if nurbs is None:
    pf.debug("Using the (slower) Python nurbs functions", pf.DEBUG.LIB)
    from pyformex.lib import nurbs_e as nurbs

pf.debug("Accelerated: %s" % accelerated, pf.DEBUG.LIB|pf.DEBUG.INFO)
pf.debug(misc, pf.DEBUG.LIB)
pf.debug(nurbs, pf.DEBUG.LIB)

# make sure we could at least import one version
assert(misc is not None)

# End
