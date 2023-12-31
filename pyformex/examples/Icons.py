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

"""Icons

Create an icon file from a pyFormex model rendering.

This application was used to create some of the toolbar icons for pyFormex
"""
_level = 'normal'
_topics = ['geometry']
_techniques = ['image', 'icon']

from pyformex.gui.draw import *
from pyformex.gui.image import saveIcon
from pyformex.simple import rectangle
from pyformex.examples.Cube import cube_quad

def icon_smooth():
    view('iso')
    F = cube_quad(color='Face')
    draw(F)
    smooth()
    zoom(0.8)


def icon_wirenone():
    view('front')
    F = rectangle(2, 2)
    draw(F, color=red)
    smooth()
    zoomAll()
    zoomIn()
    zoomIn()


def icon_wireborder():
    view('front')
    F = rectangle(2, 2)
    draw(F, color=red)
    B = F.toMesh().getBorderMesh()
    draw(B, color=black, linewidth=2, ontop=True, opak=True, nolight=True)
    smooth()
    zoomAll()
    zoomIn()
    zoomIn()


def icon_wireall():
    view('front')
    F = rectangle(2, 2)
    draw(F, color=red, linewidth=2)
    smoothwire()
    zoomAll()
    zoomIn()
    zoomIn()


def icon_clock():
    from pyformex.examples.Clock import AnalogClock
    view('front')
    F = AnalogClock()
    F.draw()
    F.drawTime(11, 55)


def icon_run():
    view('front')
    F = Formex('3:016045').trl([-0.3, 0., 0.])
    draw(F)


def icon_rerun():
    icon_run()
    A = Arc(radius=1.5, angles=(45., 135.)).setProp(1)
    B = A.scale(0.8)
    MA = A.approx().toMesh()
    MB = B.approx().toMesh()
    C = MA.connect(MB)
    draw(C)
    D = F.scale(0.7).rotate(-45).setProp(1).trl(A.coords[0].scale(0.9))
    draw(D)
    E = C.rotate(180)
    F = D.rotate(180)
    draw([E, F])
    zoomAll()


def icon_reset():
    T = Formex([[(0, 0), (-3, 0), (-3, 3)]])
    draw(T, color='steelblue')
    x = Coords([(-2, 2), (-1, 3), (3, 3), (3, 0)])
    draw(x)
    P = BezierSpline(control=x)
    x = Coords([(3, 0), (3, -1), (3, -2), (1, -3)])
    draw(x)
    P1 = BezierSpline(control=x)
    draw([P, P1], color='indianred')
    zoomAll()


def icon_script():
    icon_run()
    from pyformex.examples import FontForge
    okfonts = [f for f in FontForge.fonts if 'Sans' in f and 'Oblique' in f]
    res = askItems([
        _I('fontname', None, choices=okfonts),
        ])
    if res:
        fontname = res['fontname']
        curve = FontForge.charCurve(fontname, 'S')
        curve = curve.scale(2.5/curve.sizes()[1]).centered()
        FontForge.drawCurve(curve, color=red, fill=True, with_border=False, with_points=False)
        print(curve.bbox())
    zoomAll()


def available_icons():
    """Create a list of available icons.

    The icon name is the second part of the 'icon_' function names.
    """
    icons = [i[5:] for i in globals().keys() if i.startswith('icon_') and callable(globals()[i])]
    return sorted(icons)


def run():

    resetAll()
    flat()
    bgcolor('white')  # Make sure we have a one color background


    res = askItems([
        _I('icon', text='Icon Name', choices=_avail_icons),
        _I('save', False, text='Save Icon'),
        ])

    if not res:
        return

    icon = res['icon']
    save = res['save']

    create = globals()['icon_'+icon]
    create()


    if save:
        saveIcon(icon)


_avail_icons = available_icons()


if __name__ == '__draw__':
    run()
# End
