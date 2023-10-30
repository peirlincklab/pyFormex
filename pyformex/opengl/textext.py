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

This module uses textures on quads to render text on an OpenGL canvas.
It is dependent on freetype and the Python bindings freetype-py.
"""
from itertools import cycle

import numpy as np

import pyformex as pf
from pyformex import Path
from pyformex import utils
from pyformex import arraytools as at
from pyformex.coords import Coords
from pyformex.formex import Formex
from .drawable import Actor
from .texture import Texture
from .gl import GL
from pyformex.plugins.imagearray import array2image, image2array

__all__ = ['FontTexture', 'Text', 'TextArray', 'Mark']


class FontTexture(Texture):
    """A Texture class for text rendering.

    The FontTexture class is a texture containing the most important
    characters of a font. This texture can then be used to draw text
    on geometry. In the current implementation only the characters with
    ASCII ordinal in the range 32..127 are put in the texture.

    Parameters
    ----------
    filename: str or Path
        The name of the font file to be used. It should be the
        full path of an existing monospace font on the system.
    size: float
        Intended font height. The actual height might differ a bit.
    save: bool
        If True and ``filename`` is a font file (.ttf), the generated
        texture image will be saved as a .png image for later reload.
    """
    # This is how we store the 96 character textures
    layout = (3, 32)

    def __init__(self, filename, size, save=False):
        """Initialize a FontTexture"""
        nrows, ncols = FontTexture.layout
        filename = Path(filename)
        if not filename.is_absolute():
            filename = pf.cfg['fontsdir'] / filename
        if not filename.exists():
            raise ValueError("Font file %s does not exist" % filename)

        if filename.suffix == '.ttf':
            # generate texture from .ttf file
            image = self.generateFromFont(filename, size, save=False)

            if save:
                stem = filename.stem
                fn = pf.cfg['fontsdir'] / (stem+'.%sx%s.png'%(nrows, ncols))
                if not fn.exists():
                    print("Saving Font Texture: %s" % fn)
                    array2image(image, str(fn))

        elif filename.suffix == '.png':
            stem = filename.stem
            if not stem.endswith("%sx%s" % FontTexture.layout):
                raise ValueError("Invalid layout for font %s" % filename)
            image = image2array(filename, flip=False)  # ! no flipping for fonts

        self.height = image.shape[0] / nrows
        self.width = image.shape[1] / ncols
        pf.debug("Image size %s, w%s, h%s, type %s" % (image.shape, self.width, self.height, image.dtype), pf.DEBUG.FONT)

        Texture.__init__(self, image, format=GL.GL_ALPHA, texformat=GL.GL_ALPHA)


    def generateFromFont(self, filename, size, save=False):
        """Initialize a FontTexture"""
        from pyformex import freetype as ft   # lazy loading
        pf.debug("Creating FontTexture(%s) in size %s" % (filename, size), pf.DEBUG.FONT)
        # Load font  and check it is monospace
        face = ft.Face(str(filename))
        try:
            face.set_char_size(int(size*64))
        except Exception:
            raise RuntimeError("Can not load font '%s' at size %s" % (filename, size))
        if not face.is_fixed_width:
            raise RuntimeError("Font is not monospace")

        # Determine largest glyph size
        width, height, ascender, descender = 0, 0, 0, 0
        for c in range(32, 128):
            face.load_char(chr(c), ft.FT_LOAD_RENDER | ft.FT_LOAD_FORCE_AUTOHINT)
            bitmap    = face.glyph.bitmap
            width     = max(width, bitmap.width)
            ascender  = max(ascender, face.glyph.bitmap_top)
            descender = max(descender, bitmap.rows-face.glyph.bitmap_top)
            #print("chr %s; ord %s; width %s, ascender %s, descender %s" % (
            #    chr(c), c, bitmap.width, face.glyph.bitmap_top, bitmap.rows-face.glyph.bitmap_top))
        height = ascender+descender
        #print("width %s, ascender %s, descender %s, height %s" % (
        #    width, ascender, descender, height ))

        # Generate texture data
        nrows, ncols = FontTexture.layout
        image = np.zeros((height*nrows, width*ncols), dtype=np.ubyte)
        for j in range(nrows):
            for i in range(ncols):
                k = 32+j*ncols+i
                face.load_char(chr(k), ft.FT_LOAD_RENDER | ft.FT_LOAD_FORCE_AUTOHINT)
                bitmap = face.glyph.bitmap
                x = i*width  + face.glyph.bitmap_left
                y = j*height + ascender - face.glyph.bitmap_top
                #print("%s %s:  %s  %s, %s" % (k,chr(k),face.glyph.bitmap_left,x,y))
                image[y:y+bitmap.rows, x:x+bitmap.width].flat = bitmap.buffer
        return image


    def activate(self, mode=None):
        """Bind the texture and make it ready for use.

        Returns the texture id.
        """
        GL.glEnable(GL.GL_BLEND)
        Texture.activate(self, filtr=1)


    def texCoords(self, char):
        """Return the texture coordinates for a character or string.

        Parameters
        ----------
        char: int | str
            If an integer, it should be in the range 32..127 (printable ASCII
            characters). If a string, all its characters
            should be ASCII printable characters (have an ordinal value in the
            range 32..127).

        Returns
        -------
        tuple | array
            If ``char`` is an int, returns a tuple with the texture coordinates
            in the FontTexture corresponding with the specified character.
            This is a sequence of four (x,y) pairs corresponding respectively
            holding the lower left, lower right, upper right, upper left corners
            of the character in the texture. Note that values for the lower
            corners are higher than those for the upper corners. This is
            because the FontTextures are stored from top to bottom (as in images
            files), while opengl coordinates are from bottom to top.

            If `char` is a string of length `ntext`, returns a float array with
            shape (ntext,4,2) holding the texture coordinates needed to display
            the given text on a grid of quad4 elements.
        """
        nrows, ncols = FontTexture.layout
        if at.isInt(char):
            dx, dy = 1./ncols, 1./nrows
            k = char-32
            x0, y0 = (k%ncols)*dx, (k//ncols)*dy
            return (x0, y0+dy), (x0+dx, y0+dy), (x0+dx, y0), (x0, y0)

        else:
            return np.array([self.texCoords(ord(c)) for c in char])


    default_font = None
    @classmethod
    def default(clas, size=24):
        """Set and return the default FontTexture.

        """
        if clas.default_font is None:
            default_font_file ='NotoSansMono-Condensed.3x32.png'
            default_font_size = 24
            clas.default_font = FontTexture(default_font_file, default_font_size)
        return clas.default_font


#
# TODO: Docstring of Text should be extended (include grid parameter),
# or TextArray should be merged into Text.
#
class Text(Actor):
    """A text drawn at a 2D or 3D position.

    Parameters
    ----------
    text: string
        The text to display. If not a str, the string
        representation of the object will be drawn. Newlines in the string
        are supported. After a newline, the remainder of the string is continued
        from a lower vertical position and the initial horizontal position.
        The vertical line offset is determined from the font.
    pos: tuple
        Position where render the text: either a 2D (x,y) or a 3D (x,y,z) tuple.
        If 2D, the values are measured in pixels. If 3D, it is a point in
        global 3D space. The text is drawn in 2D, inserted at the specified
        position.
    gravity: str, optional
        Specifies the adjustment of the text with respect to the insert position.
        It can be a combination of one of the characters 'N or 'S' to specify
        the vertical positon, and 'W' or 'E' for the horizontal.
        The default(empty) string centers the text.
    size: float, optional
        The height of the font. This is the displayed height.
        The used font can have a different height and is scaled accordingly.
    width: float, optional
        The width of the font. This is the displayed width of a single
        character (currently only monospace fonts are supported).
        The default is set from the ``size`` parameter and the aspect ratio
        of the font.
        Setting this to a different value allows the creation of condensed and
        expanded font types. Condensed fonts are often used to save space.
    font: :class:`FontTexture` or string, optional.
        The font to be used. If a string, it is the filename of an monospace
        font file existing on the system.
    lineskip: float, loptional
        The distance in pixels between subsequent baselines
        in case of multi-line text. Multi-line text results when the input
        ``text`` contains newlines.
    grid: Geometry, optional
        A grid geometry for rendering the text upon as a Texture.
        The default is a grid of rectangles of size (``width``,``size``) which
        are juxtaposed horizontally. Each rectangle will be rendered with a
        single character on it.
    colors: list, optional
        A list of N color specifications, allowing to draw the subsequent
        strings in different colors. If provided, it overrides a ``color``
        parameter specified in kargs. If all strings are to be displayed with
        the same color, the ``color`` parameter instead.
    **kargs:
        Other parameters (like color) to be passed to the Actor initalization.
    """

    def __init__(self, text, pos, gravity=None, size=18, width=None, font=None,
                 lineskip=1.0, grid=None, texmode=4, rotate=None, colors=None,
                 **kargs):
        """Initialize the Text actor."""

        # split the string on newlines
        text = str(text).split('\n')

        # set pos and offset3d depending on pos type (2D vs 3D rendering)
        pos = at.checkArray(pos)
        if pos.shape[-1] == 2:
            rendertype = 2
            pos = [pos[0], pos[1], 0.]
            offset3d = None
        else:
            rendertype = 1
            offset3d = Coords(pos)
            pos = [0., 0., 0.]
            if offset3d.ndim > 1:
                if offset3d.shape[0] != len(text[0]):
                    raise ValueError("Length of text(%s) and pos(%s) should match!" % (len(text), len(pos)))
                # Flag vertex offset to shader
                rendertype = -1

        # set the font characteristics
        if font is None:
            font = FontTexture.default(size)
        if isinstance(font, str):
            font = FontTexture(font, size)
        if width is None:
            #print("Font %s / %s" % (font.height,font.width))
            aspect = float(font.width) / font.height
            width = size * aspect
        self.width = width

        # set the alignment
        if gravity is None:
            gravity = 'E'
        else:
            gravity = gravity.upper()
        alignment = ['0', '0', '0']
        if 'W' in gravity:
            alignment[0] = '+'
        elif 'E' in gravity:
            alignment[0] = '-'
        if 'S' in gravity:
            alignment[1] = '+'
        elif 'N' in gravity:
            alignment[1] = '-'
        alignment = ''.join(alignment)

        # record the lengths of the lines, join all characters
        # together, create texture coordinates for all characters
        # create a geometry grid for the longest line
        lt = [len(t) for t in text]
        text = ''.join(text)
        texcoords = font.texCoords(text)
        if grid is None:
            grid = Formex('4:0123').replic(max(lt))
        grid = grid.scale([width, size, 0.])
        if rotate is not None:
            grid = grid.rotate(rotate)

        color = kargs.pop('color',pf.cfg['canvas/textcolor'])
        if colors is None:
            colors = [ color ]
        # cycle line colors if not enough
        colors = cycle(colors)

        # create the actor for the first line
        l = lt[0]
        g = grid.select(range(l)).align(alignment, pos)
        Actor.__init__(self, g, rendertype=rendertype, texture=font,
                       texmode=texmode, texcoords=texcoords[:l],
                       opak=False, ontop=True, mode='flat', offset3d=offset3d,
                       color=next(colors), **kargs)

        for k in lt[1:]:
            # lower the canvas y-value
            pos[1] -= font.height * lineskip
            g = grid.select(range(k)).align(alignment, pos)
            C = Actor(g, rendertype=rendertype, texture=font,
                      texmode=texmode, texcoords=texcoords[l:l+k],
                      opak=False, ontop=True, mode='flat', offset3d=offset3d,
                      color=next(colors), **kargs)
            self.children.append(C)
            # do next line
            l += k


class TextArray(Text):
    """An array of texts drawn at a 2D or 3D positions.

    The text is drawn in 2D, inserted at the specified (2D or 3D) position,
    with alignment specified by the gravity (see class :class:`Text`).

    Parameters
    ----------
    text: list of str
        A list containing N strings to be displayed. If an item is
        not a string, the string representation of the object will be drawn.
    pos: float array
        Either an [N,2] or [N,3] shaped array with the 2D or 3D positions
        where to display the strings. If 2D, the values are measured in pixels.
        If 3D, it is a point in the global 3D space.
    prefix: str, optional
        If specified, it is prepended to all drawn strings.
    colors: list, optional
        A list of N color specifications, allowing to draw the subsequent
        strings in different colors. If provided, it overrides a ``color``
        parameter specified in kargs. If all strings are to be displayed with
        the same color, the ``color`` parameter instead.
    **kargs:
        Other parameters (like color) to be passed to the Actor initalization.
    """

    def __init__(self, val, pos, prefix='', colors=None, **kargs):
        # Make sure we have strings
        val = [str(i) for i in val]
        pos = at.checkArray(pos, shape=(len(val), -1))
        if len(val) != pos.shape[0]:
            raise ValueError("val and pos should have same length")

        # concatenate all strings
        val = [prefix+str(v) for v in val]
        cs = at.cumsum0([len(v) for v in val])
        val = ''.join(val)
        nc = cs[1:] - cs[:-1] # lengths of the strings including prefix
        pos = [at.multiplex(p, n, 0) for p, n in zip(pos, nc)]
        pos = np.concatenate(pos, axis=0)
        pos = at.multiplex(pos, 4, 1)

        # multiplex the colors
        if colors is not None:
            if isinstance(colors, str) and colors == 'range':
                colors = np.arange(len(val))
            mcolors = []
            for n,c in zip(nc, cycle(colors)):
                mcolors.extend([c] * n)
            kargs['color'] = mcolors

        # Create the grids for the strings
        F = Formex('4:0123')
        grid = Formex.concatenate([F.replic(n) for n in nc])

        # Create a text with the concatenation
        Text.__init__(self, val, pos=pos, grid=grid, **kargs)


class Mark(Actor):
    """A 2D drawing inserted at a 3D position of the scene.

    The minimum attributes and methods are:

    - `pos` : 3D point where the mark will be drawn
    """

    def __init__(self, pos, tex, size, opak=False, ontop=True, **kargs):
        self.pos = pos
        F = Formex([[[0, 0], [1, 0], [1, 1], [0, 1]]]).scale(size).align('000')
        Actor.__init__(self, F, rendertype=1, texture=tex, texmode=4, offset3d=pos, opak=opak, ontop=ontop, mode='flat', **kargs)


# End
