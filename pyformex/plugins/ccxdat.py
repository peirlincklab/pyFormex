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

"""
Interface with Calculix FE result files (.dat).

"""
import re

import numpy as np

import pyformex.arraytools as at

from pyformex.plugins.fe_post import FeResult
from pyformex.mesh import Mesh


_re_float = re.compile(r"[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?")
_re_header = re.compile(
    r" *(?P<name>[^ ]+) *\(.*\) +for set (?P<set>[^ ]+) *and time *(?P<time>[^ ]+)")


######################### functions #############################

def skipBlankLine(fil):
    line = next(fil).strip()
    if len(line) > 0:
        raise ValueError("Expected a blank line")


# TODO: this could be speeded up as done in tetgen.py
def readDispl(fil, nnodes, nres):
    """Read displacements from a Calculix .dat file"""
    values = np.zeros((nnodes, nres), dtype=at.Float)
    for line in fil:
        if len(line.strip()) == 0:
            break
        s = line.split()
        i = int(s[0])
        x = [float(f) for f in s[1:]]
        values[i-1] = x
    return values


def readStress(fil, nelems, ngp, nres):
    """Read stresses from a Calculix .dat file"""
    values = np.zeros((nelems, ngp, nres), dtype=at.Float)
    for line in fil:
        if len(line.strip()) == 0:
            break
        s = line.split()
        i, j = [int(v) for v in s[:2]]
        x = [float(v) for v in s[2:]]
        values[i-1, j-1] = x
    return values



def readResults(fn, DB, nnodes, nelems, ngp):
    """Read Calculix results file for nnodes, nelems, ngp

    Add results to the specified DB
    """
    fil = open(fn, 'r')

    result = {}
    step = 1
    for line in fil:
        m = _re_header.match(line)
        if m:
            m = m.groupdict()
            name = m['name'][:5]
            setname = m['set']
            time = m['time']
            print("Match %s %s %s" % (name, setname, time))
            skipBlankLine(fil)
            if name == 'displ':
                result[name] = readDispl(fil, nnodes, 3)
            elif name == 'stres':
                result[name] = readStress(fil, nelems, ngp, 6)
        if 'displ' in result and 'stres' in result:
            addFeResult(DB, step, time, result)
            result = {}
            step += 1

    return result


def createResultDB(model):
    """Create a results database for the given FE model"""
    DB = FeResult()
    DB.nodes = model.coords
    DB.nnodes = model.coords.shape[0]
    DB.nodid = np.arange(DB.nnodes)
    DB.elems = dict(enumerate(model.elems))
    DB.nelems = model.celems[-1]
    DB.Finalize()
    return DB


def addFeResult(DB, step, time, result):
    """Add an FeResult for a time step to the result DB

    This is currently 2D only
    """
    print("Storing result for step %s, time %s" % (step, time))
    DB.Increment(step, 0)
    DB.R['TIME'] = time
    if 'displ' in result:
        DB.datasize['U'] = result['displ'].shape[1]
        DB.R['U'] = result['displ']
    if 'stres' in result:
        try:
            stress = result['stres']
            # CALCULIX HAS NO 2D: keep only half of GP's
            ngp = stress.shape[1]//2
            stress = stress[:, :ngp, :]
            print("Reduced stresses: %s" % str(stress.shape))
            mesh = Mesh(DB.nodes, DB.elems[0], eltype='quad4')
            gprule = [2, 2]
            stress = computeAveragedNodalStresses(mesh, stress, gprule)
            DB.datasize['S'] = result['stres'].shape[1]
            DB.R['S'] = stress
        except Exception:
            print("Error importing stresses")
    return DB


def computeAveragedNodalStresses(M, data, gprule):
    """Compute averaged nodal stresses from GP stresses in 2D quad8 mesh"""


    ############################
    # Load the needed calpy modules
    from pyformex.plugins import calpy_itf
    calpy_itf.check()

    gprule = (2, 2)  # integration rule: minimum (1,1),  maximum (5,5)
    Q = calpy_itf.QuadInterpolator(M.nelems(), M.nplex(), gprule)
    ngp = np.prod(gprule)  # number of datapoints per element
    print("Number of data points per element: %s" % ngp)
    print("Original element data: %s" % str(data.shape))
    # compute the data at the nodes, per element
    endata = Q.GP2Nodes(data)
    print("Element nodal data: %s" % str(endata.shape))
    # compute nodal averages
    nodata = Q.NodalAvg(M.elems+1, endata, M.nnodes())
    print("Average nodal data: %s" % str(nodata.shape))
    # extract the colors per element

    return nodata

# End
