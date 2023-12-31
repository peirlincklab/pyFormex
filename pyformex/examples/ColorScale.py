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

"""ColorScale

Example showing the use of the 'colorscale' plugin.
"""

_level = 'normal'
_topics = ['FEA']
_techniques = ['dialog', 'color']

import pyformex as pf
from pyformex import colors
from pyformex.gui.draw import *
from pyformex.gui.colorscale import ColorScale, Palette
from pyformex.opengl.decors import ColorLegend

input_data = [
    _C('', [
        _I('valrange', text='Value range type', choices=['Minimum-Medium-Maximum', 'Minimum-Maximum']),
        _I('maxval', 12.0, text='Maximum value'),
        _I('medval', 0.0, text='Medium value'),
        _I('minval', -6.0, text='Minimum value'),
        _I('palet', text='Predefined color palette', value='RAINBOW',
            choices=list(Palette.keys())),
        _G('custom', text='Custom color palette', items=[
            _I('paltype', text='Palette type', choices=['3-color', '2-color']),
            _I('maxcol', [1., 0., 0.], text='Maximum color', itemtype='color'),
            _I('medcol', [1., 1., 0.], text='Medium color', itemtype='color'),
            _I('mincol', [1., 1., 1.], text='Minimum color', itemtype='color'),
            ], check=False),
        _I('maxexp', 1.0, text='High exponent'),
        _I('minexp', 1.0, text='Low exponent'),
        _I('ncolors', 200, text='Number of colors'),
    ]),
    _C('', [
        _T('Grid/Label', [
            _I('ngrid', -1, text='Number of grid intervals'),
            _I('linewidth', 1.5, text='Line width'),
            _I('nlabel', -1, text='Number of label intervals'),
            _I('dec', 2, text='Decimals'),
            _I('scale', 0, text='Scaling exponent'),
            _I('lefttext', True, text='Text left of colorscale'),
            _I('textsize', 18, text='Text height'),
            _I('textcolor', pf.canvas.settings['fgcolor'], text='Text color',
                itemtype='color'),
            _I('header', 'Currently not displayed', text='Header',
                enabled=False),
            _I('gravity', 'Notused', text='Gravity', enabled=False),
            ]),
        _T('Position/Size', [
            _I('autosize', True, text='Autosize'),
            _I('size', (100, 600), text='Size'),
            _I('autopos', True, text='Autoposition'),
            _I('position', [100, 50], text='Position'),
            ]),
        ]),
    ]
input_enablers = [
    ('valrange', 'Minimum-Medium-Maximum', 'medval'),
    ('paltype', '3-color', 'medcol'),
    ('custom', False, 'palet'),
    ('autosize', False, 'size'),
    ('autopos', False, 'position'),
    ]


dialog = None
def show():
    """Accept the data and draw according to them"""
    global medval, medcol, palet, paltype, minexp, grid, nlabels, dialog

    if not dialog.validate():
        return
    clear()
    lights(False)
    pf.PF['_ColorScale_data_'] = dialog.results

    res = dialog.results
    globals().update(res)

    if valrange == 'Minimum-Maximum':
        medval = None
        minexp = None

    if custom:
        palet = tuple(colors.GLcolor(i) for i in (mincol, medcol, maxcol))
        if paltype == '2-color':
            palet = (palet[0], None, palet[2])

    mw, mh = pf.canvas.getSize()
    x, y = position
    if autosize:
        h = int(0.9*(mh-y))
        w = min(0.1*mw, 100)
    else:
        w, h = size
    if autopos:
        x = 100

    # ok, now draw it
    drawColorScale(palet, minval, maxval, medval, maxexp, minexp, ncolors, dec, scale, ngrid, linewidth, nlabel, lefttext, textsize, colors.GLcolor(textcolor), x, y, w, h)


def drawColorScale(palet, minval, maxval, medval, maxexp, minexp, ncolors, dec, scale, ngrid, linewidth, nlabel, lefttext, textsize, textcolor, x, y, w, h):
    """Draw a color scale with the specified parameters"""
    CS = ColorScale(palet, minval, maxval, midval=medval, exp=maxexp, exp2=minexp)
    CLA = ColorLegend(CS, ncolors, x, y, w, h, ngrid=ngrid, linewidth=linewidth, nlabel=nlabel, size=textsize, dec=dec, scale=scale, lefttext=lefttext, textcolor=textcolor)
    drawActor(CLA)


def close():
    global dialog
    ## pf.PF['ColorScale_data'] = dialog.results
    if dialog:
        dialog.close()
        dialog = None
    # Release script lock
    scriptRelease(__file__)


def timeOut():
    """What to do on a Dialog timeout event.

    As a policy, all pyFormex examples should behave well on a
    dialog timeout.
    Most users can simply ignore this.
    """
    show()
    close()


def atUnload():
    print("Unloading? Wait, I want to close the dialog first")
    close()

dialog = None
def run():
    global dialog

    # This is another way to avoid multiple executions.
    if dialog:
        return

    clear()

    # Create the modeless dialog widget
    dialog = Dialog(input_data, enablers=input_enablers, caption='ColorScale Dialog', actions = [('Close', close), ('Show', show)], default='Show')

    # Update its data from stored values
    if '_ColorScale_data_' in pf.PF:
        dialog.updateData(pf.PF['_ColorScale_data_'])

    # Show the dialog and let the user have fun
    dialog.show(timeoutfunc=timeOut)

    # Block other scripts
    scriptLock(__file__)


if __name__ == '__draw__':
    run()

# End
