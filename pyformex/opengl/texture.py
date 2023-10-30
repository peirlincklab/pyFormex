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
"""Texture rendering.

This module defines tools for texture rendering in pyFormex.
"""
import numpy as np

import pyformex as pf
from .gl import GL

### Textures ###############################################


class Texture():
    """An OpenGL 2D Texture.

    Parameters
    ----------
    image: :term:`array_like` or :term:`path_like`
        Image data: either raw image data (unsigned byte RGBA data) or
        the name of an image file with such data.
    format:
        Format of the image data.
    texformat:
        Format of the texture data.

    """
    # This fails on mesa: probably too early
    #max_texture_units = GL.glGetIntegerv(GL.GL_MAX_TEXTURE_UNITS)
    #active_textures =

    def __init__(self, image, mode=1, format=GL.GL_RGBA, texformat=GL.GL_RGBA):
        self.texid = None
        if isinstance(image, str):
            from pyformex.plugins.imagearray import image2array
            image = image2array(image, 'RGBA')
        else:
            image = np.asarray(image)
        s = "Texture: type %s, size %s" % (image.dtype, image.shape)
        image = np.require(image, dtype='ubyte', requirements='C')
        pf.debug(s+"; Converted to: type %s, size %s" % (image.dtype, image.shape), pf.DEBUG.IMAGE)
        # if len(image.shape) != 3 or image.shape[2] != 4:
        #     raise ValueError("Invalid texture array shape: expected (ny, nx, 4)")
        ny, nx = image.shape[:2]

        # Generate a texture id
        self.texid = GL.glGenTextures(1)
        self.texun = None
        # Make our new texture the current 2D texture
        GL.glEnable(GL.GL_TEXTURE_2D)
        #GL.glTexEnvf(GL.GL_TEXTURE_ENV,GL.GL_TEXTURE_ENV_MODE,GL.GL_MODULATE)
        # select texture unit 0
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texid)
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
        # Copy the texture data into the current texture
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, texformat, nx, ny, 0,
                        format, GL.GL_UNSIGNED_BYTE, image)
        self.mode = mode


    def activate(self, mode=None, filtr=0):
        """Render-time texture environment setup"""
        if mode is None:
            mode = self.mode
        texmode = {0: GL.GL_REPLACE,
                    1: GL.GL_MODULATE,
                    2: GL.GL_DECAL,
                    }[mode]
        texfiltr = {0: GL.GL_NEAREST,
                     1: GL.GL_LINEAR,
                     }[filtr]

        # Configure the texture rendering parameters
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glTexEnvf(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, texmode)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, texfiltr)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, texfiltr)
        # Re-select the texture
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texid)


    def bind(self):
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texid)


    def __del__(self):
        if self.texid:
            GL.glDeleteTextures(self.texid)


### End
