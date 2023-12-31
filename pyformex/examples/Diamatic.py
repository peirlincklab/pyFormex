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
"""Diamatic dome

"""


_level = 'beginner'
_topics = ['structure', 'domes']
_techniques = ['color', 'circulize']

from pyformex.gui.draw import *


def run():
    wireframe()

    u = 3.     # modular length
    n = 6      # number of modules in one sector
    r = 36.    # radius of the dome

    # Topology for 1 sector
    T = Formex('l:164', 3).replic2(n, n, 1, 1, 0, 1, 0, -1)


    # 4 sectors
    m = 4
    angle = 360./m
    # circulize sector
    D = T.scale(u).circulize(m)
    D = D.mapd(2, lambda d: sqrt(r**2-d**2), [0, 0, 0], [0, 1])
    dome1=D.rosette(m, angle)
    clear()
    draw(dome1)

    # 6 sectors
    m = 6
    angle = 360./m
    a = sqrt(3.)/2
    D = T.shear(0, 1, 0.5).scale([1, a, 1])
    #D = T.replic2(n,n,1,a,0,1,0.5,-1)
    D = D.scale(u).circulize(m)
    D = D.mapd(2, lambda d: sqrt(r**2-d**2), [0, 0, 0], [0, 1])
    dome2=D.rosette(m, angle)

    clear()
    draw(dome2)

    # 8 sectors
    m = 8
    angle = 360./m
    a = sqrt(2.)/2
    T = Formex([[[0, 0], [1, 0]], [[1, 0], [a, a]], [[a, a], [0, 0]]], 3)
    D = T.replic2(n, n, 1, a, 0, 1, a, -1)
    # circulize sector
    D = D.scale(u).circulize(m)
    D = D.mapd(2, lambda d: sqrt(r**2-d**2), [0, 0, 0], [0, 1])
    dome3=D.rosette(m, angle)

    clear()
    draw(dome3)

    # circulize1
    m = 6
    angle = 360./m
    T = Formex('l:127', 3)
    D = T.replic2(n, n, 1, 1, 0, 1, 1, -1)
    D = D.scale(u).circulize1()
    D = D.mapd(2, lambda d: sqrt(r**2-d**2), [0, 0, 0], [0, 1])
    dome4=D.rosette(m, angle)

    clear()
    draw(dome4)

    clear()
    dome4.setProp(1)
    draw(dome2+dome4)

    clear()
    d=1.1*r
    draw(dome1+dome2.translate([d, 0, 0])+dome3.translate([0, -d, 0])+dome4.translate([d, -d, 0]))

if __name__ == '__draw__':
    run()
# End
