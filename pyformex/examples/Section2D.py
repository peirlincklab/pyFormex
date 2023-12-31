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
"""Section2D

Computing geometrical properties of plane sections.

"""


_level = 'normal'
_topics = ['geometry', 'section2d']
_techniques = []

from pyformex.gui.draw import *
from pyformex.plugins.section2d import *
from pyformex import simple
from pyformex.mydict import CDict


def showaxes(C, angle, size, color):
    H = simple.shape('plus').scale(0.6*size).rot(angle/at.DEG).trl(C)
    draw(H, color=color)


def square_example(scale=[1., 1., 1.]):
    P = Formex([[[1, 1]]]).rosette(4, 90).scale(scale)
    return sectionize.connectPoints(P, close=True)

def rectangle_example():
    return square_example(scale=[2., 1., 1.])

def circle_example():
    return simple.circle(5., 5.)

def close_loop_example():
    # one more example, originally not a closed loop curve
    F = Formex('l:11').replic(2, 1, 1) + Formex('l:2').replic(2, 2, 0)
    M = F.toMesh()
    draw(M, color='green')
    drawNumbers(M, color=red)
    drawNumbers(M.coords, color=blue)

    print("Original elements:", M.elems)
    conn = M.elems.chained()
    if len(conn) > 1:
        print("This curve is not a closed circumference")
        return None

    sorted = conn[0]
    print("Sorted elements:", sorted)

    showInfo('Click to continue')
    clear()
    M = Mesh(M.coords, sorted)
    drawNumbers(M)
    return M.toFormex()

def run():
    clear()
    flat()
    reset()
    examples = {'Square': square_example,
                 'Rectangle': rectangle_example,
                 'Circle': circle_example,
                 'CloseLoop': close_loop_example,
                 }

    res = askItems([
        _I('example', text='Select an example', choices=list(examples.keys())),
        ])
    if res:
        F = examples[res['example']]()
        if F is None:
            return
        draw(F)
        S = sectionChar(F)
        S.update(extendedSectionChar(S))
        print(CDict(S))
        G = Formex([[[S['xG'], S['yG']]]])
        draw(G, bbox='last')
        showaxes([S['xG'], S['yG'], 0.], S['alpha'], F.dsize(), 'red')

if __name__ == '__draw__':
    run()
# End
