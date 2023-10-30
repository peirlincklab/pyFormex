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
"""ColoredText

This example illustrates the drawing of text on the 2D OpenGL canvas.
It also shows how to generate random values and how to remove 2D decorations
from the canvas.

The application starts with the generation of (n,8) random numbers between
0.0 and 1.0, and where n is the number of text strings that will be displayed.
The 8 random numbers for each case are use as follows:

- 0, 1: the relative position on the canvas viewport,
- 2: the relative font size, ranging from 12 to 48,
- 3, 4, 5: the color (resp. red, green and blue components),
- 6: the text to be shown, selected from a list of predefined texts,
- 7: the font to be used, also selected from a list of fonts.

The texts are shown one by one, with a small pause between.
During the display of the first half of the set of texts,
the previous text is removed after each new one is shown.
During the second half, all texts remain on the canvas.
"""


_level = 'normal'
_topics = ['text']
_techniques = ['color', 'random', 'animation']

from pyformex.gui.draw import *
from pyformex.opengl.textext import *

def run():
    n = 40
    T = ['Python', 'NumPy', 'OpenGL',
         'Qt5', 'PySide2',
         'PIL', 'pyFormex']
    fonts = utils.listMonoFonts()

    ftmin, ftmax = 12, 48
    rotmin, rotmax = -90., +90.

    R = np.random.random((n, 9))
    w, h = pf.canvas.width(), pf.canvas.height()
    a = R[:, :2] * np.array([w, h]).astype(int)
    size = (ftmin + R[:, 2] * (ftmax-ftmin)).astype(int)
    colors = R[:, 3:6]
    t = (R[:, 6] * len(T)).astype(int)
    f = (R[:, 7] * len(fonts) - 0.5).astype(int).clip(0, len(fonts)-1)
    rot = rotmin + R[:, 8] * (rotmax-rotmin)
    clear()

    bgcolor(white)
    lights(False)
    TA = None


    for i in range(n):
        TB = drawText(T[t[i]], a[i], font=fonts[f[i]], size=size[i],
                      color=list(colors[i]), rotate=rot[i])
        sleep(0.4)
        breakpt()
        if i < n//2:
            undecorate(TA)
        TA = TB

if __name__ == '__draw__':
    run()
# End
