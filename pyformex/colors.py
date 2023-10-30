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
"""Playing with colors.

This module defines some colors and color conversion functions.
It also defines a default palette of colors.

The following table shows the built-in colors, with their name,
RGB values in 0..1 range and luminance.

>>> for k,v in PF_colors.items():
...     print(f"{k:15s} = {v} -> {luminance(v):.3f}")
                red = (1.0, 0.0, 0.0) -> 0.213
              green = (0.0, 1.0, 0.0) -> 0.715
               blue = (0.0, 0.0, 1.0) -> 0.072
               cyan = (0.0, 1.0, 1.0) -> 0.787
            magenta = (1.0, 0.0, 1.0) -> 0.285
             yellow = (1.0, 1.0, 0.0) -> 0.928
            darkred = (0.5, 0.0, 0.0) -> 0.046
          darkgreen = (0.0, 0.5, 0.0) -> 0.153
           darkblue = (0.0, 0.0, 0.5) -> 0.015
           darkcyan = (0.0, 0.5, 0.5) -> 0.169
        darkmagenta = (0.5, 0.0, 0.5) -> 0.061
         darkyellow = (0.5, 0.5, 0.0) -> 0.199
      pyformex_pink = (1.0, 0.2, 0.4) -> 0.246
              black = (0.0, 0.0, 0.0) -> 0.000
           darkgrey = (0.4, 0.4, 0.4) -> 0.133
         mediumgrey = (0.6, 0.6, 0.6) -> 0.319
          lightgrey = (0.8, 0.8, 0.8) -> 0.604
     lightlightgrey = (0.9, 0.9, 0.9) -> 0.787
              white = (1.0, 1.0, 1.0) -> 1.000
"""

import numpy as np

import pyformex as pf
import pyformex.arraytools as at


# TODO: this should be lazyloaded !
X11_colors = {}

def loadX11Colors(filename):
    """Load the X11 colors"""
    with open(filename) as f:
        for line in f:
            s = line.strip().split()
            name = ''.join(s[3:]).lower()
            try:
                X11_colors[name] = tuple(int(i) for i in s[:3])
            except Exception:
                pass

loadX11Colors("/etc/X11/rgb.txt")


# TODO: This should become a Color class

def GLcolor(color):
    """Convert a color to an OpenGL RGB color.

    Parameters
    ----------
    color: :term:`color_like`
        Data specifying an RGB color. This can be any of the following:

        - a single int: returns the palette color with that index (modulo
          the palette length
        - a float: returns the grey color with that value
        - a string with the name of one of the built-in PF_colors
        - a string specifying the X11 name of the color
        - a hex string '#RGB' with 1 to 4 hexadecimal digits per color
        - a tuple or list of 3 integer values in the range 0..255
        - a tuple or list of 3 float values in the range 0.0..1.0
        - a QColor or any data that can be used to create a QColor

    Returns
    -------
    tuple | ndarray
        A tuple of three RGB float values, normally in the range 0.0..1.0.

    Warning
    -------
    There is currently no check that the result is in the range 0.0..1.0,
    because OpenGL allows to make clever use of values exceeding these
    limits. The values will be clipped at render time.

    Raises
    ------
    ValueError: If the input is not one of the accepted data.

    Examples
    --------
    >>> GLcolor(2)
    (0.0, 1.0, 0.0)
    >>> GLcolor('red')
    (1.0, 0.0, 0.0)
    >>> GLcolor('indianred')
    (0.8039..., 0.3607..., 0.3607...)
    >>> GLcolor('grey90')
    (0.8980...,  0.8980...,  0.8980...)
    >>> print(GLcolor('#ff0000'))
    (1.0, 0.0, 0.0)
    >>> GLcolor("zorro")
    (0.0, 0.0, 0.0)
    >>> GLcolor(red)
    (1.0, 0.0, 0.0)
    >>> GLcolor([200,200,255])
    (0.7843..., 0.7843..., 1.0)
    >>> GLcolor(np.array([200,200,255], dtype=np.uint8))
    (0.7843..., 0.7843..., 1.0)
    >>> GLcolor([1.,1.,1.])
    (1.0, 1.0, 1.0)
    >>> GLcolor(0.6)
    (0.6, 0.6, 0.6)
    >>> at.mapArray(GLcolor, ['red'])
    array([[1.,  0.,  0.]])
    >>> at.mapArray(GLcolor, ['red', 'green'])
    array([[1.,  0.,  0.],
           [0.,  1.,  0.]])
    >>> at.mapArray(GLcolor, [['red', 'green'], ['cyan','magenta']])
    array([[[1.,  0.,  0.],
            [0.,  1.,  0.]],
           [[0.,  1.,  1.],
            [1.,  0.,  1.]]])
    """
    from pyformex.gui import QtGui

    col = color

    if at.isInt(col):
        # single int value: convert to current palette color
        return palette[col % len(palette)]
    elif at.isFloat(col):
        # single float value: convert to a grey value
        return grey(col)
    elif isinstance(col, str):
        if col in PF_colors:
            # string defined in PF_colors:
            return PF_colors[col]
        elif col in X11_colors:
            # str defined in X11_colors:
            col = X11_colors[col]
        else:
            # Try conversion to QColor
            col = QtGui.QColor(col)

    # Convert QColor to (r,g,b) tuple (0..255)
    if isinstance(col, QtGui.QColor):
        col = (col.red(), col.green(), col.blue())

    # Convert to an array and check type
    col = np.atleast_1d(col)
    if col.dtype.kind in 'ui':
        col = col / 255
        # print(f"{col=}\n{col.dtype=}")
    if col.dtype.kind == 'f' and col.size == 3:
        return tuple(col)
    else:
        raise ValueError(f"GLcolor: invalid input {color} (type {type(color)})")


def GLcolor4(color, alpha=0.5):
    """Like GLcolor with alpha.

    Returns tuple of shape (4,)
    If color does not contain alpha, adds 0.5
    """
    try:
        color = GLcolor(color)
        return *color, alpha
    except Exception as e:
        # probably a 4 component color?
        color = np.asarray(color)
        if color.dtype.kind in 'ui':
            color = color / 255
        if len(color) == 4:
            return tuple(color)
        else:
            raise e


def QTcolor(color):
    from pyformex.gui import QtGui
    return QtGui.QColor.fromRgbF(*GLcolor(color))


def RGBcolor(color):
    """Return an RGB (0-255) tuple for a color

    color can be anything that is accepted by GLcolor.

    Returns the corresponding RGB colors as a numpy array of type uint8
    and shape (..,3).

    Example:

      >>> RGBcolor(red)
      array([255,   0,   0], dtype=uint8)
    """
    col = np.array(GLcolor(color))*255
    return col.round().astype(np.uint8)


def RGBAcolor(color, alpha=0.5):
    """Return an RGBA (0-255) tuple for a color and alpha value.

    color can be anything that is accepted by GLcolor.

    Returns the corresponding RGBA colors as a numpy array of type uint8
    and shape (..., 4).

    Examples
    --------
    >>> RGBAcolor(yellow)
    array([255, 255,   0, 128], dtype=uint8)
    >>> RGBAcolor('yellow')
    array([255, 255,   0, 128], dtype=uint8)
    >>> RGBAcolor((1., 1., 0.))
    array([255, 255,   0, 128], dtype=uint8)
    >>> RGBAcolor((1., 1., 0., 0.5))
    array([255, 255,   0, 128], dtype=uint8)
    >>> RGBAcolor((255, 255, 0))
    array([255, 255,   0, 128], dtype=uint8)
    >>> RGBAcolor((255, 255, 0, 128))
    array([255, 255,   0, 128], dtype=uint8)
    >>> RGBAcolor(yellow, 1.0)
    array([255, 255,   0, 255], dtype=uint8)
    >>> RGBAcolor((255, 255, 255, 255))
    array([255, 255, 255, 255], dtype=uint8)
    """
    col = np.array(GLcolor4(color, alpha))*255
    return col.round().astype(np.uint8)


def WEBcolor(color):
    """Return an RGB hex string for a color

    color can be anything that is accepted by GLcolor.
    Returns the corresponding WEB color, which is a hexadecimal string
    representation of the RGB components.

    Example:

      >>> WEBcolor(red)
      '#ff0000'
    """
    col = RGBcolor(color)
    return "#%02x%02x%02x" % tuple(col)


def colorName(color):
    """Return a string designation for the color.

    color can be anything that is accepted by GLcolor.
    In the current implementation, the returned color name is the
    WEBcolor (hexadecimal string).

    Example:

      >>> colorName('red')
      '#ff0000'
      >>> colorName('#ffddff')
      '#ffddff'
      >>> colorName([1.,0.,0.5])
      '#ff0080'
    """
    return WEBcolor(color)


def luminance(color, gamma=True):
    """Compute the luminance of a color.

    Returns a floating point value in the range 0..1 representing the
    luminance of the color. The higher the value, the brighter the color
    appears to the human eye.

    This can for example be used to derive a good contrasting
    foreground color to display text on a colored background.
    Values lower than 0.5 contrast well with white, larger value
    contrast better with black.

    Examples
    --------
    >>> print([f"{luminance(c):0.2f}" for c in ['black','red','green','blue']])
    ['0.00', '0.21', '0.72', '0.07']
    >>> print(luminance(np.array([black,red,green,blue])))
    [0.     0.2126 0.7152 0.0722]
    """
    if not isinstance(color, np.ndarray):
        color = np.array(GLcolor(color))
    if color.dtype.kind in 'ui' :
        color = color / 255
    color = color.astype(np.float32)

    if gamma:
        color = np.where(color > 0.04045,
                         ((color+0.055)/1.055) ** 2.4, color/12.92)

    R, G, B = color[..., 0], color[..., 1], color[..., 2]
    return 0.2126 * R + 0.7152 * G + 0.0722 * B


def closestColorName(color):
    """Return the closest color name."""
    pass


def RGBA(rgb, alpha=1.0):
    """Adds an alpha channel to an RGB color"""
    return GLcolor(rgb)+(alpha,)


def GREY(val, alpha=1.0):
    """Returns a grey OpenGL color of given intensity (0..1)"""
    return (val, val, val, 1.0)

def grey(i):
    return (i, i, i)


PF_colors = {
    'red'            : (1.0, 0.0, 0.0),
    'green'          : (0.0, 1.0, 0.0),
    'blue'           : (0.0, 0.0, 1.0),
    'cyan'           : (0.0, 1.0, 1.0),
    'magenta'        : (1.0, 0.0, 1.0),
    'yellow'         : (1.0, 1.0, 0.0),
    'darkred'        : (0.5, 0.0, 0.0),
    'darkgreen'      : (0.0, 0.5, 0.0),
    'darkblue'       : (0.0, 0.0, 0.5),
    'darkcyan'       : (0.0, 0.5, 0.5),
    'darkmagenta'    : (0.5, 0.0, 0.5),
    'darkyellow'     : (0.5, 0.5, 0.0),
    'pyformex_pink'  : (1.0, 0.2, 0.4),
    'black'          : grey(0.0),
    'darkgrey'       : grey(0.4),
    'mediumgrey'     : grey(0.6),
    'lightgrey'      : grey(0.8),
    'lightlightgrey' : grey(0.9),
    'white'          : grey(1.0),
}

def setPalette(colors):
    # Change the palette with a list of colors
    global palette
    palette = dict([(k, GLcolor(k)) for k in colors])


# make the PF-colors available as names
globals().update(PF_colors)

# Set default palette
palette = [PF_colors[k] for k in (
    'darkgrey',     #  0
    'red',          #  1
    'green',        #  2
    'blue',         #  3
    'cyan',         #  4
    'magenta',      #  5
    'yellow',       #  6
    'white',        #  7
    'black',        #  8
    'darkred',      #  9
    'darkgreen',    # 10
    'darkblue',     # 11
    'darkcyan',     # 12
    'darkmagenta',  # 13
    'darkyellow',   # 14
    'lightgrey',    # 15
)]

Palette = {
    'default': palette,
    'dark': [c for c in palette if luminance(c) < 0.5],
    'light': [c for c in palette if luminance(c) > 0.5],
    }


# End
