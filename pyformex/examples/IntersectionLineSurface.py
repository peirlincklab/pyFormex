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
"""IntersectionLineSurface

Find the intersection points of a set lines with a TriSurface.
This example teaches how to recognize the intersection points
with a specific line.
"""

_level = 'normal'
_topics = ['surface']
_techniques = ['intersection']

from pyformex.gui.draw import *
from pyformex.trisurface import *
from pyformex.simple import sphere, regularGrid


def run():

    clear()
    transparent()

    nquad = 1
    nsphere = 5

    S = sphere(nsphere)

    #Creating the points to define the intersecting lines
    R = regularGrid([0., 0., 0.], [0., 1., 1.], [1, nquad, nquad])
    L0 = Coords(R.reshape(-1, 3)).trl([-2., -1./2, -1./2]).fuse()[0]
    L1 = L0.trl([4., 0., 0.])

    P, X = S.intersectionWithLines(L0, L1, method='line',  atol=1e-5)

    # Retrieve the index of the points and the corresponding lines and hit triangles
    id_pts = X[:, 0]
    id_intersected_line = X[:, 1]
    id_hit_triangle = X[:, 2]

    hitsxline = at.inverseIndex(id_intersected_line.reshape(-1, 1))
    Nhitsxline = (hitsxline>-1).sum(axis=1)

    ptsok = id_pts[hitsxline[np.where(hitsxline>-1)]]
    hittriangles = id_hit_triangle[hitsxline[np.where(hitsxline>-1)]]


    colors = ['red', 'green', 'blue', 'cyan']
    [draw(Formex([[p0, p1]]), color=c, linewidth=2, alpha=0.7)
     for p0, p1, c in zip(L0, L1, colors)]

    id=0
    for icolor, nhits in enumerate(Nhitsxline):
        for i in range(nhits):
            draw(P[ptsok][id], color=colors[icolor], marksize=5, alpha=1)
            draw(S.select([hittriangles[id]]), ontop=True, color=colors[icolor])
            id+=1
    draw(S, alpha=0.3)




if __name__ == '__draw__':
    run()
# End
