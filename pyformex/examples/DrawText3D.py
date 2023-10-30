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
"""DrawText3D

This example illustrates the drawing of a text in full 3D. The text is
displayed on a Formex grid and can be manipulated and transformed by
the usual pyFormex methods.
"""

_level = 'normal'
_topics = ['text']
_techniques = ['dialog', 'font', 'text']

from pyformex.gui.draw import *
from pyformex.gui import QtGui
from pyformex.opengl.textext import FontTexture

def sameLength(text):
    """Make sure all strings hat the same length

    in: list of str
    out: list of str with all same length
    """
    maxlen = max([len(s) for s in text])
    return [s + ' '*(maxlen-len(s)) for s in text[::-1]]


def draw3DText(text, font=None, ftsize=10, color=None, texmode=2, ontop=True):
    if isinstance(text, str):
        text = text.split('\n')
    text = sameLength(text)
    nrows = len(text)
    ncols = len(text[0])
    text = ''.join(text)
    #print(text, ncols, nrows)
    G = Formex('4:0123').replicm((ncols,nrows))
    if font is None:
        font = 'NotoSansMono-Condensed.3x32.png'
    ft = FontTexture(font, 24)
    tc = ft.texCoords(text)
    if color is None:
        color = pf.canvas.settings.bgcolor
    draw(G, color=color, texture=ft, texcoords=tc, texmode=texmode, ontop=ontop)
    zoom(2)


def run():
    clear()
    flat()
    fonts = utils.listMonoFonts()
    center = (pf.canvas.width()//2, pf.canvas.height()//2)
    res = askItems([
        _I('text', 'pyFormex\nrules\nthe world!', itemtype='text'),
        _I('font', choices=fonts),
        ])
    if res:
        print(res)
        draw3DText(**res)

if __name__ == '__draw__':
    run()
# End
