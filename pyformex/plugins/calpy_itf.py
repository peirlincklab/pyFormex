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

"""Calpy interface for pyFormex.

Currently this is only used to detect the installation of calpy and
add the path of the calpy module to sys.path.

Importing this module will automatically check the availabilty of calpy
and set the sys.path accordingly.
"""
import sys
import numpy as np

import pyformex as pf
from pyformex import utils

calpy_path = None  # never tried to detect
#calpy_path = pf.cfg['pyformexdir'] / 'lib' / 'calpy'

def detect(trypaths=None):
    """Check if we have calpy and if so, add its path to sys.path."""
    #print("DETECTING CALPY")
    global calpy_path

    calpy = utils.External.has('calpy')
    if not calpy:
        return

    print("You have calpy version %s" % calpy)
    path = ''
    calpy = calpy.split('-')[0]  # trim the version trailer
    if utils.External.check('calpy', '0.3.4-rev3') >= 0:
        P = utils.command('calpy3 --whereami')
        if not P.returncode:
            path = P.stdout.splitlines()[0]
            pf.debug("I found calpy in %s" % path)
    if not path:
        if trypaths is None:
            trypaths = ['/usr/local/lib', '/usr/local']
        for p in trypaths:
            path = path(p) / 'calpy-%s' % calpy
            if path.exists():
                pf.debug('path exists: %s' % path)
                break
            else:
                pf.debug('path does not exist: %s' % path)
                path = ''
    if path:
        #path += '/calpy'
        print("I found calpy in '%s'" % path)
        sys.path.append(path)

    calpy_path = path


def check(trypaths=None):
    #print("CHECKING CALPY")
    if calpy_path is None:
        detect(trypaths)

    else:
        if not calpy_path in sys.path:
            sys.path.append(calpy_path)

    try:
        import calpy
    except ImportError:
        pass

    if utils.Module.has('calpy', check=True):
        return True
    else:
        pf.warning("Sorry, I can not run this example, because you do not have calpy installed (at least not in a place where I can find it).")
        return False



if __name__ == '__main__':
    print(__doc__)
else:
    pf.debug("Loading plugin %s" % __file__)

    if check():

        from calpy import plane
        class QuadInterpolator(plane.Quad):
            """A class to interface with calpy's Quad class.

            We want to use the calpy interpolation facilities without
            having to set up a full model for calpy processing.
            This class just sets the necessary data to make the
            interpolation methods (GP2Nodes, NodalAcc, NodalAvg) work.

            Parameters:

            - `nelems`: number of elements
            - `nplex`: plexitude of the elements (supported is 4 to 9)
            - `gprule`: gauss integration rule
            """
            class Model:
                """A dummy class to keep calpy happy."""
                option = 'dummy'
                tempfilename = 'dummy'

            def __init__(self, nelems, nplex, gprule):
                from numpy import array
                plane.Quad.__init__(self, 'myQuad', gprule, self.Model)
                self.nnod = nplex
                self.nelems = nelems
                self.natCoords = np.array([1, 1, -1, 1, -1, -1, 1, -1, 0, 1, -1, 0, 0, -1, 1, 0, 0, 0], dtype=float).reshape((9, 2))[:self.nnod, :]


    else:

        print("Could not import calpy")


### End
