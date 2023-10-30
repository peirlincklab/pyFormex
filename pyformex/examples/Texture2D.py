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

"""Texture

This example demonstrates the possibilities of drawing with a 2D texture.

It prompts the user to select an image file, and then draws the selected
as a texture on a set of squares in each of the colors of the default
colormap, and in each of the supported texture modes. The number next to
the 'G' character in the rendering represents the mode.
The blending of G3 can be interactively adjusted using the ObjectDialog.

Draw with texture
.................
Drawing a 2D texture on a Mesh of quad4 elements is as easy as::

   draw(M,texture=image)

where image is a numpy array with rgba values. The image will be added
on each element. By default the image will be modulated with the object
color. You should add color=white to view the image unaltered.

Texture mode
............
The blending of the texture image with the object color can be done in
different ways, selectable by adding an argument `texmode`:

- `texmode = 0`: the image colors replace the object color. Because texture
  is added after the lighting has been computed, object lighting will be
  destroyed in this mode.
- `texmode = 1`: the image colors are modulated with the object's color. This
  is the default mode. Use a white object color to get the original image
  colors.
- `texmode = 2`: this mode is prefered when the texture has transparency.
  The result is a mix of object and image colors, with a weight depending
  on the image's alpha channel. If the image has no alpha channel, this
  produces the same result as mode 0.
- `texmode = 3`: this mode produces a mix of object and image colors, weighed
  by the object's alpha value. The result is as if the object is a colored
  glass, and the image is behind it.

Limitations
...........
Currently there can only be one texture in a scene.

"""


_level = 'beginner'
_topics = ['color']
_techniques = ['texture', 'image']

from pyformex.gui.draw import *
from pyformex.plugins.imagearray import image2array

imagefile = pf.cfg['pyformexdir'] / 'data' / 'butterfly.png'


def drawNames(F):
    for Fi in F:
        drawText(Fi.attrib.name, Fi.bbox()[0] + (-0.5, 0.5, 0.), color=black)


def run():
    global imagefile
    reset()
    clear()
    flat()

    imagefile = askImageFile(imagefile)
    if not imagefile:
        return

    image = image2array(imagefile, 'RGBA')
    if image is None:
        return

    image = np.flipud(image)

    palette = pf.canvas.settings.colormap
    ncolors = len(palette)
    F = Formex('4:0123').replicm((ncolors, 1)).setProp(np.arange(ncolors)).toMesh()
    G = [F.trl(1, (1+i)*F.sizes()[1]) for i in range(4)]
    for i in range(4):
        G[i].attrib(name='G%s'%i, texture=image, texmode=i, alpha=0.5)
    drawNames(G)
    draw([F, G])

if __name__ == '__draw__':
    run()
# End
