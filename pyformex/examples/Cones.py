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
"""Cones

"""


_level = 'normal'
_topics = ['geometry']
_techniques = ['connect', 'dialog']

from pyformex.gui.draw import *

from pyformex import simple
from pyformex.gui import widgets


def cone(r0, r1, h, t=360., nr=1, nt=24, diag=None):
    """Constructs a Formex which is (a sector of) a
    circle / (truncated) cone / cylinder.

    r0,r1,h are the lower and upper radius and the height of the truncated
    cone. All can be positive, negative or zero.
    Special cases:
    r0 = r1 : cylinder
    h = 0 : (flat) circle
    r0 = 0 or r1 = 0 : untruncated cone

    Only a sector of the structure, with opening angle t, is modeled.
    The default results in a full circumference.

    The cone is modeled by nr elements in height direction and nt elements in
    circumferential direction.

    By default, the result is a 4-plex Formex whose elements are quadrilaterals
    (some of which may collapse into triangles).
    If diag='up' or diag = 'down', all quads are divided by an up directed
    diagonal and a plex-3 Formex results.
    """
    B = simple.rectangle(nt, nr, 1., 1., diag=diag)  # grid with size 1x1
    B = B.map(lambda x, y, z: [x, y, r0-y*(r0-r1)])  # translate and tilt it
    B = B.scale([t, h, 1.])             # scale to fit parameters
    return B.cylindrical(dir=[2, 0, 1])  # roll it into a cone


def cone1(r0, r1, h, t=360., nr=1, nt=24, diag=None):
    """Constructs a Formex which is (a sector of) a
    circle / (truncated) cone / cylinder.

    r0,r1,h are the lower and upper radius and the height of the truncated
    cone. All can be positive, negative or zero.
    Special cases:
    r0 = r1 : cylinder
    h = 0 : (flat) circle
    r0 = 0 or r1 = 0 : untruncated cone

    Only a sector of the structure, with opening angle t, is modeled.
    The default results in a full circumference.

    The cone is modeled by nr elements in height direction and nt elements in
    circumferential direction.

    By default, the result is a 4-plex Formex whose elements are quadrilaterals
    (some of which may collapse into triangles).
    If diag='up' or diag = 'down', all quads are divided by an up directed
    diagonal and a plex-3 Formex results.
    """
    r0, r1, h, t = [float(f) for f in (r0, r1, h, t)]
    p = Formex(simple.regularGrid([r0, 0., 0.], [r1, h, 0.], [0, nr, 0]).reshape(-1, 3))
    #draw(p,color=red)
    a = (r1-r0)/h
    if a != 0.:
        p = p.shear(0, 1, a)
    #draw(p)
    q = p.rotate(t/nt, axis=1)
    #draw(q,color=green)
    if diag == 'u':
        F = connect([p, p, q], bias=[0, 1, 1]) + \
            connect([p, q, q], bias=[1, 2, 1])
    elif diag == 'd':
        F = connect([q, p, q], bias=[0, 1, 1]) + \
            connect([p, p, q], bias=[1, 2, 1])
    else:
        F = connect([p, p, q, q], bias=[0, 1, 1, 0])

    F = Formex.concatenate([F.rotate(i*t/nt, 1) for i in range(nt)])
    return F


from pyformex.simple import rectangle

r0=3.   # bottom radius
r1=1.   # top radius
h=5.    # height
t=360.  # degrees (180. = half)
nr=2    # number of elements along height
nt=12   # number of elements along circumference
diag=''

def run():
    items = [
        _I(n, globals()[n]) for n in ['r0', 'r1', 'h', 't', 'nr', 'nt']
        ] + [
        _I('diag', diag, itemtype='radio', choices=['', 'u', 'd'])
        ]
    dialog = Dialog(items)

    while not dialog.result() == Dialog.TIMEOUT:
        res = dialog.getResults()
        if not res:
            break

        globals().update(res)
        F = cone(r0, r1, h, t, nr, nt, diag)
        G = cone1(r0, r1, h, t, nr, nt, diag).swapAxes(1, 2).trl(0, 2*max(r0, r1))
        G.setProp(1)
        H = F+G
        clear()
        smoothwire()
        draw(H)
        return


if __name__ == '__draw__':
    run()
# End
