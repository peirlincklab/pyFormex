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

"""Test the fonts on the system for use in text drawing.

The script will loop over all detected monotype fonts and
display the full texture image of that font.

The save option should probably be refined (overwrite existing?)
and put into the dialog.

"""


from pyformex.gui.draw import *
from pyformex.opengl.actors import *
from pyformex.opengl.textext import *

do_save = ack("Save the generated texturefonts to pyformex/fonts? Only do so if you know what you're doing!")


def run():
    clear()
    lights(False)
    interactive = True
    for f in utils.listMonoFonts():
        run1(f, save=do_save)
        if interactive:
            ans = ask("Quit, Continue (silent) with all fonts, or show Next font?", ["Quit", "Continue", "Next"])
            if ans == "Quit":
                break
            elif ans == "Continue":
                interactive = False
        else:
            sleep(1)


def run1(f, save=False):
    clear()
    print(f)
    font = FontTexture(f, 24, save=save)
    nrows, ncols = font.layout
    x, y = 20, pf.canvas.getSize()[1] - 20
    drawText(f, (x, y), font=font, size=24)
    c = np.arange(32, 128).reshape(nrows, ncols)
    a = [''.join([chr(c) for c in range(32+i*ncols, 32+(i+1)*ncols)]) for i in range(nrows)]
    #print(a)
    for ai in a:
        y -= 32
        drawText(ai, (x, y), font=font, size=24)
    for size in (12, 18, 24, 32, 40, 48):
        y -= size+8
        drawText("This is a sample at size %s" % size, (x, y), font=font, size=size)


# You can also run on a single font:
#run1('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',save=True)
#run1('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Oblique.ttf',save=True)

run()
