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
"""Baumkuchen Vault

"""


_level = 'beginner'
_topics = ['structure']
_techniques = ['color', 'bump']

from pyformex.gui.draw import *

def run():
    global a1, a2, a3, a4
    clear()
    smoothwire()
    m = 12  # number of cells in direction 0
    n = 36  # number of cells in direction 1
    k = 7  # number of vaults in direction 0
    e1 = 30  # elevation of the major arcs
    e2 = 5  # elevation of the minor arcs

    beam = False  # Set True for using beam elements

    if beam:
        # Create a grid of beam elements
        a1 = Formex('l:2').replicm((m+1, n)) + \
             Formex('l:1').replicm((m, n+1))
    else:
        # Create a grid of quad elements
        a1 = Formex('4:0123').replicm((m, n))

    draw(a1, view='front')
    p = np.array(a1.center())
    p[2] = e1
    f = lambda x: 1-(x/18)**2/2
    a2 = a1.bump(2, p, f, 1)
    draw(a2, view='bottom', color='red')
    p[2] = e2
    a3 = a2.bump(2, p, lambda x: 1-(x/6)**2/2, 0)
    draw(a3, view='bottom', color='green')
    # Replicate the structure in x-direction
    a4 = a3.replicate(k, dir=0, step=m)
    draw(a4, view='bottom', color='blue')

if __name__ == '__draw__':
    run()
# End
