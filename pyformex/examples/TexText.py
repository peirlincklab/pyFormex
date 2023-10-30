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
"""Text rendering on the OpenGL canvas.

This example illustrates some of the possibilities of text drawing
using textures.
"""

_level = 'normal'
_topics = ['Text']
_techniques = ['texture']

import pyformex as pf
from pyformex.gui.draw import *
from pyformex.opengl.textext import *
from pyformex.plugins.imagearray import image2array

def run():
    #
    # TODO: RESETALL does not properly layout the canvas in the viewport
    # caused by reset Viewport
    # add a viewport + reset layout does fix it
    #resetAll()
    clear()
    view('front')
    smooth()
    #ft = FontTexture.default()
    ft = FontTexture('NotoSansMono-Condensed.3x32.png', 24)
    ftrows, ftcols = FontTexture.layout

    # - draw a rectangle with shape like the FontTexture.layout
    # - use the full character set in the default font as a texture
    # - the font textures are currently upside down, therefore we need
    #   to specify texcoords to flip the image
    F = Formex('4:0123').centered().scale(10).scale([ftcols, ftrows, 1]).toMesh()
    A = draw(F, color=yellow, texture=ft,
             texcoords=np.array([[0, 1], [1, 1], [1, 0], [0, 0]]), texmode=2)

    # - draw 10x2 squares
    # - fill with specific text
    # - put this object on top
    G = Formex('4:0123').replicm((10, 2)).scale(10).rot(30).trl([10, 10, 0])
    text = [' pyFormex ', '  rules!  ']
    text = text[1] + text[0]
    #tc = FontTexture.default().texCoords(text)
    tc = ft.texCoords(text)
    draw(G, color=pyformex_pink, texture=ft, texcoords=tc, texmode=2, ontop=True)


    # draw a cross at the center of the square
    # pos is 3D, therefore values are world coordinates
    decorate(Text('+', pos=(0, 0, 0), gravity='', size=40, color=red))

    # draw a string using the default_font texture
    # pos is 2D, therefore values are pixel coordinates
    decorate(Text("Hegemony!", pos=(40, 60), size=30, offset=(0.0, 0.0, 1)))
    decorate(Text("Hegemony!", (0, 0), size=20, color=red, gravity='NE'))
    decorate(Text("Hegemony!", (10, 30), size=20, color=red))

    # use a TextArray to draw text at the corners of the square
    corners = F.coords[F.elems[0]]
    U = TextArray(["Lower left corner", "Lower right corner"], pos=corners[:2], size=18, gravity='S')
    decorate(U)
    V = TextArray(["Upper right corner", "Upper left corner"], pos=corners[2:], size=18, gravity='N')
    decorate(V)

    #drawViewportAxes3D((0.,0.,0.),color=blue)

    # draw a cross at the upper corners using an image file
    imagefile = pf.cfg['datadir'] / 'mark_cross.png'
    image = image2array(imagefile, 'RGBA')
    X = Formex('4:0123').scale(40).toMesh().align('000')
    # at the upper left corner using direct texture drawing techniques
    draw(X, texture=image, texcoords=np.array([[0, 1], [1, 1], [1, 0], [0, 0]]), texmode=0, rendertype=-1, opak=False, ontop=True, offset3d=[corners[3], corners[3], corners[3], corners[3]])
    # at the upper right corner, using a Mark
    drawActor(Mark(corners[2], image, size=40, color=red))

if __name__ == '__draw__':
    run()

# End
