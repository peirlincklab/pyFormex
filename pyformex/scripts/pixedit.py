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

"""A simple pixel editor.

This pixel editor was created for quickly creating and editing
simple pyFormex icons. At the same time it is a nice illustration
of the power of the pyFormex functionality. And maybe, some day, it
may become a full featured pixeld editor.

Currently it is mainly used for editing XPM type B/W icons.
Executing the script does the following:

- ask the user to select an XPM file
- read the XPM file
- draw the image on real pixel size in the lower left corner
- draw the image enlarged on an editable pixel grid
- allow the user to edit the image (see below)
- ask the user for an XPM file to save the edited icon

Editing
-------
In edit mode, pyFormex goes in a pick('element') mode. Clicking on a
pixel or selecting a rectangle of pixels will change their color index
to 0. Holding down the SHIFT key while picking will change the color
index to 1. In pyFormex XPM icons color index 0 is black and 1 is
transparent. Changing this can currently only be done through the
pyFormex console.

Console
-------
Running the pixedit script creates a PixelEditor instance which becomes
available in the console under the name 'pixed'. From there a lot of
extra functionality can be excuted. The most important are::

  pixed.read_xpm(pixfile)  # read an XPM file
  pixed.drawImage()  # draw the small icon
  pixed.draw()       # draw the editable grid
  pixed.edit()       # start an edit cycle
  pixed.save_xpm()   # save the icon to file

You have also full access to the pixels and the color palette:

  - pixed.colors: uint8 array (width, height) with the pixel color indices
  - pixed.colormap: uint8 array (ncolors, 3 or 4) with the colors in RGB(A)
  - pixed.trl: dict with characters as keys and the corresponding color index
    as values (needed for storing in XPM format).

It is thus possible to programmatorically change the image from the console.
With two viewports it is even easy to simultaneously work on two icons and
copy pixels from one image to the other.

Todo
----
There is a lot of room for adding extra interactive functionality. Perhaps
the most important would be to change/add colors.

Trivia
------
pixedit was created especially to create icons for the quick query and pick
buttons in the toolbar.
"""
from pyformex.gui import QtGui
from pyformex.plugins.imagearray import *
from PIL import Image
from pyformex import colors
from pyformex.gui.qtcanvas import SHIFT, CTRL
clear()

import re

class PixelEditor:
    space_replacement = ".,_-~aeiouO0"

    def __init__(self):
        self.clear()

    def clear(self):
        self.filename = None
        self.width = None
        self.height = None
        self.ncolors = None
        self.bpp = None
        self.trl = None
        self.colors = None
        self.colormap = None

    def hasNone(self):
        return isinstance(self.colormap, np.ndarray) and self.colormap.shape[1] == 4

    def read_xpm(self, fn):
        self.clear()
        self.filename = Path(fn)
        with open(fn, 'r') as fil:
            self.width = self.height = self.ncolors = self.bpp = None
            line = fil.readline()
            if not line[:9] == "/* XPM */":
                raise ValueError("Not a valid XPM file")
            for line in fil:
                m = re.match(r'"([0-9]*) ([0-9]*) ([0-9]*) ([0-9]*)', line)
                if m:
                    self.width, self.height, self.ncolors, self.bpp = (
                        int(i) for i in m.groups())
                    break
            if self.width is None:
                raise ValueError("Not a valid XPM file")
            if self.ncolors > 256 or self.bpp != 1:
                raise ValueError("Can not read this XPM file")

            self.colormap = np.zeros((self.ncolors,3), dtype=np.uint8)
            self.trl = {}
            col = 0
            for line in fil:
                if line.startswith('/*'):
                    continue
                line = line.strip('",};\n')
                code = line[0]
                colortype, colorname = line[2:].split()[:2]
                if colortype != 'c':
                    raise ValueError("Can not read this XPM file")
                self.trl[code] = col
                if colorname.lower() == 'none':
                    # Transparent image
                    if self.colormap.shape[1] == 3:
                        # Add an alpha
                        self.colormap = at.growAxis(self.colormap, 1, 1, 255)
                        self.colormap[col] = 0
                else:
                    self.colormap[col, :3] = colors.RGBcolor(colorname)
                col += 1
                if col == self.ncolors:
                    break
            self.color = np.zeros((self.width, self.height), dtype=np.uint8)
            row = 0
            for line in fil:
                if line.startswith('/*'):
                    continue
                line = line.strip('",};\n')
                if len(line) != self.width:
                    raise ValueError("Not a proper XPM file")
                self.color[row] = [self.trl.get(c, 0) for c in line]
                row += 1
                if row == self.height:
                    return self.color, self.colormap
            raise ValueError("Not a proper XPM file")


    def format_xpm(self):
        """Format the image in xpm format"""
        xpm = ['/* XPM */',
               'static char *dummy[]={',
               f'"{self.width} {self.height} {self.ncolors} {self.bpp}",']
        for c in self.trl:
            i = self.trl[c]
            col = self.colormap[i]
            if self.hasNone() and col[3]==0:
                name = 'None'
                col = ()
            else:
                col = tuple(col[:3])
                name = colors.colorName(col)
            xpm.append(f'"{c} c {name}",')
        itrl = dict((self.trl[k], k) for k in self.trl)
        for row in self.color:
            crow = [itrl[i] for i in row]
            xpm.append(f'"{"".join(crow)}",')
        xpm[-1] = xpm[-1].replace(',', '};\n')
        return '\n'.join(xpm)


    def save_xpm(self, fn=None):
        """Save the image in xpm format"""
        fn = Path(fn) if fn else self.filename
        fn = askFilename(fn, 'xpm')
        if not fn:
            return
        if fn.exists():
            if not ack(f"Overwrite {self.filename}?"):
                return
        self.from_gl()
        with open(fn, 'w') as fil:
            n =fil.write(self.format_xpm())
        print(f"Wrote {fn} ({n} bytes)")


    def __str__(self):
        s = f"""\n
PixelEditor: {self.filename=}
  {self.width=}, {self.height=}, {self.ncolors=}, {self.bpp=}
  {self.trl=}
  colors:
"""
        for c in self.trl:
            i = self.trl[c]
            col = self.colormap[i]
            if self.hasNone() and col[3]==0:
                name = 'None'
                col = ()
            else:
                col = tuple(col[:3])
                name = colors.colorName(col)
            s += f"    {i}: {c} c {name} {col}\n"
        return s

    def drawImage(self):
        qim = QtGui.QImage(self.filename)
        self.actor_im = drawImage(qim, x=20, y=20)

    def to_gl(self):
        """Convert xpm colors to opengl colors"""
        self.glcolor = np.flipud(self.color).reshape(-1)
        self.glcolormap = self.colormap.astype(np.float32) / 255

    def from_gl(self):
        """Put gl colors back in color format"""
        self.color = np.flipud(self.glcolor.reshape(self.width, self.height))
        self.colormap = (self.glcolormap * 255).astype(np.uint8)

    def draw(self):
        """Draw the pixel editor"""
        pf.canvas.camera.unlock()
        ny, nx = self.color.shape
        self.mesh = Mesh(eltype='quad4').subdivide(nx, ny)
        self.to_gl()
        flatwire()
        transparent(self.glcolormap.shape[1] == 4)
        self.mesh.attrib(color=self.glcolor, colormap=self.glcolormap)
        self.actor = draw(self.mesh)
        view('front')
        pf.canvas.camera.lockview()

    def change_pixel(self, canvas):
        picked = canvas.picked
        if canvas.mod == SHIFT:
            color = 1
        else:
            color = 0
        if 0 in picked:
            sel = picked[0]
            print(sel)
            print(self.glcolor.shape)
            self.glcolor[sel] = color
            newactor = draw(self.mesh)
            undraw(self.actor)
            self.actor = newactor

    def edit(self):
        pick('element', func=self.change_pixel)

    def done(self):
        clear()
        pf.canvas.camera.unlock()


if 'pixfile' not in globals():
    pixfile = pf.cfg['icondir']
pixfile = askFilename(pixfile, 'xpm')
if not pixfile:
    exit()
pixed = PixelEditor()
pixed.read_xpm(pixfile)
pixed.drawImage()
pixed.draw()
pixed.edit()
pixed.save_xpm()
