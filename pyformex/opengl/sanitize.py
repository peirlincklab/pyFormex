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
"""Sanitize data before rendering.

The pyFormex drawing functions were designed to require a minimal knowledge
of OpenGL and rendering principles in general. They allow the user to specify
rendering attributes in a simple, user-friendly, sometimes even sloppy way.
This module contains some functions to sanitize the user input into the more
strict attributes required by the OpenGl rendering engine.

These functions are generally not intended for direct used by the user, but
for use in the opengl rendering functions.
"""
import numpy as np

import pyformex as pf
from pyformex import colors
from pyformex import arraytools as at

### Sanitize settings ###############################################

def saneFloat(value):
    """Return a float value or None.

    If value can be converted to float, the float is returned, else None.
    """
    try:
        value = float(value)
    except Exception:
        value = None
    return value


saneLineWidth = saneFloat


def saneLineStipple(stipple):
    """Return a sane line stipple tuple.

    A line stipple tuple is a tuple (factor,pattern) where
    pattern defines which pixels are on or off (maximum 16 bits),
    factor is a multiplier for each bit.
    """
    try:
        stipple = [int(i) for i in stipple]
    except Exception:
        stipple = None
    return stipple


def saneColor(color=None):
    """Return a sane color array derived from the input color.

    A sane color is one that will be usable by the draw method.
    The input value of color can be either of the following:

    - None: indicates that the default color will be used,
    - a single color value in a format accepted by colors.GLcolor,
    - a tuple or list of such colors,
    - a (3,) shaped array of RGB values, ranging from 0.0 to 1.0,
    - an (n,3) shaped array of RGB values,
    - a (4,) shaped array of RGBA values, ranging from 0.0 to 1.0,
    - an (n,4) shaped array of RGBA values,
    - an (n,) shaped array of integer color indices. TODO: disallow!

    The return value is one of the following:
    - None, indicating no color (current color will be used),
    - a float array with shape (3/4,), indicating a single color,
    - a float array with shape (n,3/4), holding a collection of colors,
    - an integer array with shape (n,), holding color index values.

    !! Note that a single color can not be specified as integer RGB values.
    A single list of integers will be interpreted as a color index !
    Turning the single color into a list with one item will work though.
    [[0, 0, 255]] will be the same as ['blue'], while
    [0, 0, 255] would be a color index with 3 values.

    Examples
    --------
    >>> print(saneColor('red'))
    [1.  0.  0.]
    >>> print(saneColor('grey90'))
    [0.898 0.898 0.898]
    >>> saneColor(['red', 'green', 'blue'])
    array([[1.,  0.,  0.],
           [0.,  1.,  0.],
           [0.,  0.,  1.]])
    >>> saneColor([['red', 'green', 'blue'], ['cyan', 'magenta', 'yellow']])
    array([[[1.,  0.,  0.],
            [0.,  1.,  0.],
            [0.,  0.,  1.]],
           [[0.,  1.,  1.],
            [1.,  0.,  1.],
            [1.,  1.,  0.]]])
    """
    if color is None:
        # no color: use canvas color
        return None

    color = np.asarray(color)
    if color.dtype.kind in 'iu':
        raise ValueError("Integer input is ambiguous and not allowed")

    if color.dtype.kind != 'f':
        # Convert to colors
        try:
            color = at.mapArray(colors.GLcolor, color)
        except Exception:
            print("Could not convert input to colors:")
            print(color)
            return None

    if color.shape[-1] == 3 or color.shape[-1] == 4:
        # Looks like we have a sane color array
        return color.astype(np.float32)

    print(f"Invalid color array shape: color.shape")
    return None


def saneColorSet(color=None, colormap=None, *, shape=(1,)):
    """Return a sane set of colors.

    A sane set of colors is one that guarantees correct use by the
    draw functions. This means either

    - no color (None)
    - a single color
    - at least as many colors as the shape argument specifies
    - a color index with at least as many colors as the shape argument
      specifies, and a colormap with enough colors to satisfy the index.

    Parameters
    ----------
    color: colors_like
        One or more valid color designations. This can be anything that
        is valid input for saneColor. These can be the real colors (if float)
        or indices into a colormap (if int).
    colormap: list
        A list of colors to be used as the color map if colors are indices
        instead of the colors themselves.
    shape: tuple
        A tuple specifying the shape of the color array to return.
        The tuple should have 1 or 2 dimensions: (nelems,) or (nelems, nplex).
        The tuple should not contain the number of color components.

    Returns
    -------
    color: array
        Either a float32 array with shape ``shape + (3,)`` holding 3 RGB color
        components, or an int32 array with shape ``shape``, holding indices
        into the colormap.
    colormap: None | array
        None if color returns real colors, or a float32 array of shape
        (ncolors, 3), where ncolors is guaranteed to be larger than the
        maximum index returned in color.

    Examples
    --------
    No color always remains no color

    >>> saneColorSet(None, shape=(2,))
    (None, None)

    Single color remains single color

    >>> saneColorSet('red', shape=(2,))
    (array([1., 0., 0.]), None)
    >>> saneColorSet(colors.red, shape=(3,2))
    (array([1., 0., 0.]), None)
    >>> saneColorSet(1, colors.palette, shape=(2,))
    (array([1., 0., 0.]), None)
    >>> saneColorSet(1, colors.palette, shape=(3,2))
    (array([1., 0., 0.]), None)

    A set (tuple, list or array) of colors is expanded to match shape

    >>> saneColorSet(('red',), shape=(2,))
    (array([[1., 0., 0.],
           [1., 0., 0.]]), None)
    >>> saneColorSet((colors.red, colors.green), shape=(3,2))
    (array([[[1., 0., 0.],
            [1., 0., 0.]],
    <BLANKLINE>
           [[0., 1., 0.],
            [0., 1., 0.]],
    <BLANKLINE>
           [[1., 0., 0.],
            [1., 0., 0.]]]), None)
    >>> saneColorSet((1,), colors.palette, shape=(2,))
    (array([1., 0., 0.]), None)
    >>> saneColorSet((1, 2), colors.palette, shape=(3,2))
    (array([[1, 1],
           [2, 2],
           [1, 1]]), array([[0.4, 0.4, 0.4],
           [1. , 0. , 0. ],
           [0. , 1. , 0. ]]))

    """
    if color is None:
        return None, None

    if at.isInt(shape):  # make sure we get a tuple
        shape = (shape, )
    color = np.asarray(color)
    pf.debug(
        f"SANECOLORSET: color {color.shape}, {color.dtype} to shape {shape}",
        pf.DEBUG.DRAW)

    if color.dtype.kind in 'iu':
        # color index
        color = color.astype(np.int32)
        if colormap is None:
            # we need a color map: use the default
            colormap = pf.canvas.settings.colormap
        #print(f"{colormap.shape=}")
        colormap = saneColor(colormap)
        #print(f"{colormap.shape=}")
        ncolors = color.max() + 1
        colormap = at.resizeArray(colormap, (ncolors, colormap.shape[1]))
        if color.ndim == 0:
            # a scalar color index is converted to a single color
            color, colormap = colormap[color], None
        elif color.size == 1:
            # a single color index is also converted to a single color
            color, colormap = colormap[color.flat[0]], None
        else:
            #print(f"Before resize: {color.shape}")
            while color.ndim < 2:
                color = at.addAxis(color, 1)
            #return color.shape, shape
            color = at.resizeArray(color, shape)
            #print(f"After resize: {color.shape}")
    else:
        # direct color
        color = saneColor(color)
        colormap = None
        shape += (3,)
        if color.ndim > 1:
            #print(f"Before resize: {color.shape}")
            while color.ndim < len(shape):
                color = at.addAxis(color, 1)
            #return color.shape, shape
            color = at.resizeArray(color, shape)
            #print(f"After resize: {color.shape}")
    # else:
    #     print(color)
    #     raise ValueError("Invalid color input")
    #return color.ndim, color.shape, color.dtype

    pf.debug("SANECOLORSET RESULT: %s" % str(color.shape), pf.DEBUG.DRAW)
    return color, colormap


### End
