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
"""Decorations for the OpenGL canvas.

This module contains a collection of predefined decorations that
can be useful additions to a geometry scene rendering.
"""
import numpy as np

import pyformex as pf
from pyformex import simple
from pyformex.formex import Formex
from pyformex import colors
from .drawable import Actor
from .textext import FontTexture
from .sanitize import saneLineWidth


__all__ = ['BboxActor', 'Rectangle', 'Line', 'Lines', 'Grid2D', 'ColorLegend',
            'Grid']

### Decorations ###############################################


class BboxActor(Actor):
    """Create a bounding box actor.

    A bounding box is a hexaeder in global axes. The hexaeder is
    drawn in wireframe mode with default color black.

    Parameters
    ----------
    bbox: :term:`coords_like`
        A Coords with two points: the minimal and maximal coordinates
        of the bounding box to be drawn.
    **kargs: keyword parameters
        Keyword parameters like in the :func:`draw` funnction.
        The `mode`, `lighting`, `opak` parameters are fixed and can not be
        used.

    Returns
    -------
    :class:`Actor`
        An Actor representing a bounding box.
    """
    def __init__(self, bbox, **kargs):
        F = simple.cuboid(*bbox)
        Actor.__init__(self, F, mode='wireframe', lighting=False, opak=True, **kargs)


class Rectangle(Actor):
    """A 2D-rectangle on the canvas."""
    def __init__(self, x1, y1, x2, y2, **kargs):
        F = Formex([[[x1, y1], [x2, y1], [x2, y2], [x1, y2]]])
        Actor.__init__(self, F, rendertype=2, **kargs)


class Line(Actor):
    """A 2D-line on the canvas.

    Parameters:

    - `x1, y1, x2, y2`: floats: the viewport coordinates of the
      endpoints of the line
    - `kargs`: keyword arguments to be passed to the :class:`Actor`.
    """
    def __init__(self, x1, y1, x2, y2, **kargs):
        F = Formex([[[x1, y1], [x2, y2]]])
        Actor.__init__(self, F, rendertype=2, **kargs)


class Lines(Actor):
    """A collection of straight lines on the canvas.

    Parameters:

    - `data`: data that can initialize a 2-plex Formex: the viewport coordinates
      of the 2 endpoints of the n lines. The third coordinate is ignored.
    - `kargs`: keyword arguments to be passed to the :class:`Actor`.

    """
    def __init__(self, data, color=None, linewidth=None, **kargs):
        """Initialize a Lines."""
        F = Formex(data)
        Actor.__init__(self, F, rendertype=2, **kargs)


class Grid2D(Actor):
    """A 2D-grid on the canvas."""
    def __init__(self, x1, y1, x2, y2, nx=1, ny=1, lighting=False, rendertype=2, **kargs):
        F = Formex([[[x1, y1], [x1, y2]]]).replic(nx+1, step=float(x2-x1)/nx, dir=0) + \
            Formex([[[x1, y1], [x2, y1]]]).replic(ny+1, step=float(y2-y1)/ny, dir=1)
        Actor.__init__(self, F, rendertype=rendertype, lighting=lighting, **kargs)


class ColorLegend(Actor):
    """A labeled colorscale legend.

    When showing the distribution of some variable over a domain by means
    of a color encoding, the viewer expects some labeled colorscale as a
    guide to decode the colors. The ColorLegend decoration provides
    such a color legend. This class only provides the visual details of
    the scale. The conversion of the numerical values to the matching colors
    is provided by the :class:`~gui.colorscale.ColorScale` class.

    Parameters:

    - `colorscale`: a :class:`~gui.colorscale.ColorScale` instance providing
      conversion between numerical values and colors
    - `ncolors`: int: the number of different colors to use.
    - `x,y,w,h`: four integers specifying the position and size of the
      color bar rectangle
    - `ngrid`: int: number of intervals for the grid lines to be shown.
      If > 0, grid lines are drawn around the color bar and between the
      ``ngrid`` intervals.
      If = 0, no grid lines are drawn.
      If < 0 (default), the value is set equal to the number of colors
      or to 0 if this number is higher than 50.
    - `linewidth`: float: width of the grid lines. If not specified, the
      current canvas line width is used.
    - `nlabel`: int: number of intervals for the labels to be shown.
      If > 0, labels will be displayed at `nlabel` interval borders, if
      possible. The number of labels displayed thus will be ``nlabel+1``,
      or less if the labels would otherwise be too close or overlapping.
      If 0, no labels are shown.
      If < 0 (default), a default number of labels is shown.
    - `size`: font size to be used for the labels
    - `font`: font to be used for the labels. It can be a
      :class:`~opengl.textext.FontTexture` or a string with the path to a monospace
      .ttf font. If unspecified, the default font is used.
    - `dec`: int: number of decimals to be used in the labels
    - `scale`: int: exponent of 10 for the scaling factor of the label values.
      The displayed values will be equal to the real values multiplied with
      ``10**scale``.
    - `lefttext`: bool: if True, the labels will be drawn to the left of the
      color bar. The default is to draw the labels at the right.

    Some practical guidelines:

    - Large numbers of colors result in a quasi continuous color scheme.
    - With a high number of colors, grid lines disturb the image, so either
      use ``ngrid=0`` or ``ngrid=`` to only draw a border around the colors.
    - With a small number of colors, set ``ngrid = len(colorlegend.colors)``
      to add gridlines between each color.
      Without it, the individual colors in the color bar may seem to be not
      constant, due to an optical illusion. Adding the grid lines reduces
      this illusion.
    - When using both grid lines and labels, set both ``ngrid`` and ``nlabel``
      to the same number or make one a multiple of the other. Not doing so
      may result in a very confusing picture.
    - The best practice is to either use a low number of colors (<=20) and
      the default ``ngrid`` and ``nlabel``, or to use a high number of colors
      (>=200) and the default values or a low value for ``nlabel``.

    The `ColorScale` example script provides opportunity to experiment with
    different settings.
    """
    def __init__(self, colorscale, ncolors, x, y, w, h, ngrid=0, linewidth=None, nlabel=-1, size=18, font=None, textcolor=None, dec=2, scale=0, lefttext=False, **kargs):
        """Initialize the ColorLegend."""
        from pyformex.gui import colorscale as cs
        self.cl = cs.ColorLegend(colorscale, ncolors)
        self.x = float(x)
        self.y = float(y)
        self.w = float(w)
        self.h = float(h)
        self.ngrid = int(ngrid)
        if self.ngrid < 0:
            self.ngrid = ncolors
            if self.ngrid > 50:
                self.ngrid = 0
        self.linewidth = saneLineWidth(linewidth)
        self.nlabel = int(nlabel)
        if self.nlabel < 0:
            if self.ngrid > 0:
                self.nlabel = self.ngrid
            else:
                self.nlabel = ncolors
        self.dec = dec   # number of decimals
        self.scale = 10 ** scale  # scale all numbers with 10**scale
        self.lefttext = lefttext
        self.xgap = 4  # hor. gap between color bar and labels
        self.ygap = 4  # (min) vert. gap between labels

        F = simple.rectangle(1, ncolors, self.w, self.h).trl([self.x, self.y, 0.])
        Actor.__init__(self, F, rendertype=2, lighting=False, color=self.cl.colors, **kargs)

        if self.ngrid > 0:
            F = simple.rectangle(1, self.ngrid, self.w, self.h).trl([self.x, self.y, 0.])
            G = Actor(F, rendertype=2, lighting=False, color=colors.black, linewidth=self.linewidth, mode='wireframe')
            self.children.append(G)

        # labels
        # print("LABELS: %s" % self.nlabel)
        if self.nlabel > 0:
            from .import textext

            if font is None:
                font = FontTexture.default()
            elif isinstance(font, str):
                font = FontTexture(font, size)
            self.font = font
            fh = self.font.height
            pf.debug("FONT HEIGHT %s" % fh, pf.DEBUG.DRAW)

            if textcolor is None:
                textcolor = pf.canvas.settings['fgcolor']

            if self.lefttext:
                x = F.coords[0, 0, 0] - self.xgap
                gravity = 'W'
            else:
                x = F.coords[0, 1, 0] + self.xgap
                gravity = 'E'

            # minimum label distance
            dh = fh + self.ygap
            da = self.h / self.nlabel

            # Check if labels will fit
            if da < dh and self.nlabel == ncolors:
                # reduce number of labels
                self.nlabel = int(self.h/dh)
                da = self.h / self.nlabel

            vals = cs.ColorLegend(colorscale, self.nlabel).limits
            #print("VALS",vals)

            ypos = self.y + da * np.arange(self.nlabel+1)

            yok = self.y - 0.01*dh
            for (y, v) in zip(ypos, vals):
                #print(y,v,yok)
                if y >= yok:
                    t = textext.Text(("%%.%df" % self.dec) % (v*self.scale), (x, y), size=size, gravity=gravity, color=textcolor)
                    self.children.append(t)
                    yok = y + dh


def Grid(nx=(1, 1, 1), ox=(0.0, 0.0, 0.0), dx=(1.0, 1.0, 1.0),
         planes='b', lines='b', planecolor=colors.white, linecolor=colors.black,
         alpha=0.3, name='_grid_', **kargs):
    """Creates a (set of) grid(s) in (some of) the coordinate planes.

    Parameters
    ----------
    nx: tuple of int
        A tuple of three ints, specifying the number of divisions of the
        grid in the three coordinate directions. A zero value may be specified
        to avoid the grid to extend in that direction. Thus, setting the last
        value to zero will result in a planar grid in the xy-plane.
    ox: tuple of float
        The coordinates of the origin of the grid.
    dx: tuple of float
        The step size in each coordinate direction.
    plane: str
        One of 'first', 'box', 'all', 'no'. The string can be shortened to
        the first character.  Specifies how many planes to draw in each
        direction: 'first' only draws the first, 'box' draws the first and the
        last, 'all' draws all planes, 'no' draws no planes.
    lines: str
        One of 'first', 'box', 'all', 'no'. The string can be shortened to
        the first character.  Specifies how many lines to draw in each
        direction: 'first' only draws the first, 'box' draws the first and the
        last, 'all' draws all lines, 'no' draws no lines.
    plane_color: :term:`color_like`
        The color to use for drawing the planes
    line_color: :term:`color_like`
        The color to use for drawing the lines
    alpha: float
        Alpha transparency value (0.0 <= alpha <= 1.0)
    name: str
        Base name for the attributes set on the items in the returned List.

    Returns
    -------
    :class:`List`
        A List with up to two Meshes: the planes and the lines. The Meshes
        come with the following :class:`~attributes.Attributes` set:

        - name: the provided name with '_planes_' or '_lines_' appended.
        - color: the provided plane or line color
        - alpha: the provided alpha value for the planes, 0.6 for the lines.
        - mode: 'flat'
        - lighting: False

        The user can of course change these before drawing the List.

    """
    from pyformex import simple
    from pyformex.olist import List
    from pyformex.mesh import Mesh
    G = List()

    planes = planes[:1].lower()
    P = []
    L = []
    for i in range(3):
        n0, n1, n2 = np.roll(nx, i)
        d0, d1, d2 = np.roll(dx, i)
        if n0*n1:
            if planes != 'n':
                M = simple.rectangle(b=n0*d0, h=n1*d1)
                if n2:
                    if planes == 'b':
                        M = M.replic(2, dir=2, step=n2*d2)
                    elif planes == 'a':
                        M = M.replic(n2+1, dir=2, step=d2)
                P.append(M.rollAxes(-i).toMesh())
            if lines != 'n':
                M = Formex('l:1').scale(n0*d0).replic(n1+1, dir=1, step=d1) + \
                    Formex('l:2').scale(n1*d1).replic(n0+1, dir=0, step=d0)
                if n2:
                    if lines == 'b':
                        M = M.replic(2, dir=2, step=n2*d2)
                    elif lines == 'a':
                        M = M.replic(n2+1, dir=2, step=d2)

                L.append(M.rollAxes(-i).toMesh())

    if P:
        M = Mesh.concatenate(P)
        M.attrib(name=f'{name}_planes_', mode='flat', lighting=False,
                 color=planecolor, alpha=alpha, **kargs)
        G.append(M)
    if L:
        M = Mesh.concatenate(L)
        M.attrib(name=f'{name}_lines_', mode='flat', lighting=False,
                 color=linecolor, alpha=0.6, **kargs)
        G.append(M)

    return G.trl(ox)



# End
