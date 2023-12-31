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
#
"""DataInterpolation

This example demonstrates how to use the external 'calpy' module
to interpolate data on a Mesh.

The Mesh is a 4 by 3 grid of 'Quad8' elements. Random data, shown as colors,
are generated for all the Gauss integration points (GP) of the elements.
These data are then inter-/extrapolated to yield nodal data for all elements.
Finally, nodal data are averaged to yield single sets of data at the nodes.

The same technique can be used if the data are given at other points
than the GP or need to be interpolated at other points.

The application shows two viewports. In the left viewport element per
element interpolation is shown. The right viewport shows the result of the
nodal averaging.
"""
_level = 'advanced'
_topics = ['mesh', 'postprocess']
_techniques = ['calpy', 'color']

from pyformex.gui.draw import *

# First, we need to import calpy. If you do not have calpy,
# download it from ftp://bumps.ugent.be/pub/calpy
# and compile/install it

def run():

    # Locate calpy and load interface
    from pyformex.plugins import calpy_itf
    try:
        Q = calpy_itf.QuadInterpolator
    except Exception:
        print("NO CALPY: I'm out of here!")
        return


    # Now, let's create a grid of 'quad8' elements
    # size of the grid
    nx, ny = 4, 3
    # plexitude
    nplex = 4
    clear()
    flatwire()
    M = Formex('4:0123').replicm((nx, ny)).toMesh().convert('quad%s'%nplex, fuse=True)
    #draw(M,color=yellow)

    # Create the Mesh interpolator
    gprule = (3, 1)  # integration rule: minimum (1,1),  maximum (5,5)
    Q = calpy_itf.QuadInterpolator(M.nelems(), M.nplex(), gprule)

    # Define some random data at the GP.
    # We use 3 data per GP, because we will use the data directly as colors
    ngp = np.prod(gprule)  # number of datapoints per element
    data = np.random.rand(M.nelems(), ngp, 3)
    print("Number of data points per element: %s" % ngp)
    print("Original element data: %s" % str(data.shape))
    # compute the data at the nodes, per element
    endata = Q.GP2Nodes(data)
    print("Element nodal data: %s" % str(endata.shape))
    # compute nodal averages
    nodata = Q.NodalAvg(M.elems+1, endata, M.nnodes())
    print("Average nodal data: %s" % str(nodata.shape))
    # extract the colors per element
    colors = nodata[M.elems]
    print("Color data: %s" % str(colors.shape))
    layout(2)

    viewport(0)
    clear()
    smoothwire()
    lights(False)
    draw(M, color=endata)
    drawNumbers(M.coords)
    drawText("Per element interpolation", (20, 20))

    viewport(1)
    clear()
    smoothwire()
    lights(False)
    draw(M, color=colors)
    drawNumbers(M.coords)
    drawText("Averaged nodal values", (20, 20))

if __name__ == '__draw__':
    run()
# End
