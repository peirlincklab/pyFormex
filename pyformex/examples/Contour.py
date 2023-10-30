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

"""Contour

This example demonstrates the use of the freetype library to render text
as 3D objects. Most Linux installations have freetype installed.
The Python bindings to freetype by Nicolas P. Rougier are included
with pyFormex.
"""
_level = 'advanced'
_topics = ['text']
_techniques = ['contour', 'font']

from pyformex.gui.draw import *
from pyformex import curve
from pyformex import freetype as ft


# TODO: put this is a separate module
# TODO: make a Contours class, having multiple Contour objects with same Coords

class FontOutline():
    """A class for font outlines.

    """
    def __init__(self, filename, size):
        """Initialize a FontOutline"""
        print("Creating FontOutline(%s) in size %s" % (filename, size))
        face = ft.Face(str(filename))
        face.set_char_size(int(size*64))
        # if not face.is_fixed_width:
        #     raise RuntimeError("Font is not monospace")
        self.face = face

    def outline(self, c):
        """Return the outlines for glyph i"""
        self.face.load_char(c, ft.FT_LOAD_RENDER | ft.FT_LOAD_FORCE_AUTOHINT)
        return self.face.glyph.outline


def pointsToContour(points, tags):
    if tags[0] & 1 == 0:
        raise ValueError("First point should be on curve!")
    elems = []
    elem = []

    def store():
        if elem:
            elem.append(i)
            if len(elem) > 4:
                raise ValueError(
                    f"Too many points ({len(elem)}) in stroke {len(elems)}")
            elems.append(elem)

    for i, t in enumerate(tags):
        if t & 1:
            store()
            elem = []
        elem.append(i)
    i = 0
    store()
    return curve.Contour(Coords(points), elems)


def outlineToCurves(outline):
    out = List([])
    i = 0
    for k in outline.contours:
        j = k+1
        C = pointsToContour(outline.points[i:j], outline.tags[i:j])
        print(C)
        i = j
        out.append(C)
    return out


def glyphCurves(font, c):
    """Returns a glyph as a list of curves.

    Parameters
    ----------
    font: :term:`path_like` or FontOutline
        The path of a font file that can be read by FreeType. It is
        normally a .ttf file.
    c: char
        The character for which to return the outline curves.

    Returns
    -------
    list:
        A list of :class:`Curve` instances.

    """
    if not isinstance(font, FontOutline):
        font = FontOutline(font, 24)
    CO = font.outline(c)
    return outlineToCurves(CO)


def drawChar(font, c):
    CO = font.outline(c)
    O = outlineToCurves(CO)
    clear()
    draw(O.approx(chordal=0.001), clear=True)
    X = Coords(CO.points)
    draw(X)
    drawNumbers(X)


def setFont(font, size=24):
    """Set the global font to the specified font file"""
    global the_font
    the_font = FontOutline(font, 24)


def on_font_change(item):
    """Change the global font to the value of the input item"""
    setFont(item.value())


def on_char_change(item):
    """Draw the current character of the input item"""
    drawChar(the_font, item.value())


def run():
    fonts = utils.listMonoFonts() + [ pf.cfg['datadir'] / 'blippok.ttf' ]
    default = utils.defaultMonoFont()
    setFont(default)

    choices = [chr(i) for i in range(32, 127)]
    res = askItems([
        _I('font', choices=fonts, value=default, func=on_font_change),
        _I('char', choices=choices, itemtype='push', value='@',
           func=on_char_change, count=16),
        ])
    if not res:
        return
    default = res['font']
    setFont(default)
    c = res['char']
    drawChar(the_font, c)


if __name__ == '__draw__':
    clear()
    reset()
    smooth()
    lights(False)
    run()


# End
