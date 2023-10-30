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
"""Mapping numerical values into colors.

This module contains some definitions useful in the mapping of
numerical values into colors. This is typically used to provide
a visual representation of numerical values (e.g. a temperature plot).
See the 'postproc' plugin for some applications in the representation
of results from Finite Element simulation programs.

- ColorScale: maps scalar float values into colors.
- ColorLegend: subdivides a ColorScale into a number of subranges (which
  are graphically represented by the pyformex.opengl.decors.ColorLegend
  class).
- Palette: a dict with some predefined palettes that can be used to create
  ColorScale instances. The values in the dict are tuples of three colors,
  the middle one possibly being None (see ColorScale initialization for
  more details). The keys are strings that can be used in the ColorScale
  initialization instead of the corresponding value.
  Currently, the following palettes are defined:
  'RAINBOW', 'IRAINBOW', 'HOT', 'RGB', 'BGR', RWB', 'BWR', 'RWG', 'GWR',
  'GWB', 'BWG', 'BW', 'WB', 'PLASMA', 'VIRIDIS', 'INFERNO', 'MAGMA'.

"""

from pyformex import colors
from pyformex.arraytools import stuur
import numpy as np

# predefined color palettes
Palette = {
    'RAINBOW': ((-2., 0., 2.), (0., 2., 0.), (2., 0., -2.)),
    'IRAINBOW': ((2., 0., -2.), (0., 2., 0.), (-2., 0., 2.)),
    'HOT': ((0., 0., -2), (1., 0., -1), (1., 2., 1.)),
    'RGB': (colors.red, colors.green, colors.blue),
    'BGR': (colors.blue, colors.green, colors.red),
    'RWB': (colors.red, colors.white, colors.blue),
    'BWR': (colors.blue, colors.white, colors.red),
    'RWG': (colors.red, colors.white, colors.green),
    'GWR': (colors.green, colors.white, colors.red),
    'GWB': (colors.green, colors.white, colors.blue),
    'BWG': (colors.blue, colors.white, colors.green),
    'BW': (colors.black, None, colors.white),
    'WB': (colors.white, colors.grey(0.5), colors.black),
            # could be None or grey(0.5)
    # From matplotlib:
    'PLASMA': ((0.050383, 0.029803, 0.527975),
               (0.794549, 0.275770, 0.473117),
               (0.940015, 0.975158, 0.131326)),
    'VIRIDIS': ((0.267004, 0.004874, 0.329415),
                (0.128729, 0.563265, 0.551229),
                (0.993248, 0.906157, 0.143936)),
    'INFERNO': ((0.001462, 0.000466, 0.013866),
                (0.735683, 0.215906, 0.330245),
                (0.988362, 0.998364, 0.644924)),
    'MAGMA': ((0.001462, 0.000466, 0.013866),
                (0.716387, 0.214982, 0.47529),
                (0.987053, 0.991438, 0.749504)),
}


class ColorScale():
    """Mapping floating point values into colors.

    The ColorScale maps a range of float values minval..maxval or
    minval..midval..maxval into the corresponding color from the
    specified palette.

    Parameters:

    - `palet`: the color palette to be used. It is either a string or
      a tuple of three colors.  If a string, is should be one of the keys of
      the colorscale.Palette dict (see above). The full list of available
      strings can be seen in the `ColorScale` example.
      If a tuple of three colors, the middle one may
      be specified as None, in which case it will be set to the mean value
      of the two other colors. Each color is a tuple of 3 float values,
      corresponding to the RGB components of the color. Although OpenGL
      RGB values are limited to the range 0.0 to 1.0, it is perfectly legal
      to specify color component values outside this range here. OpenGL
      will however clip the resulting colors to the 0..1 range. This
      feature can effectively be used to construct color ranges displaying
      a wider variation of colors. for example, the built in 'RAINBOW'
      palette has a value ((-2., 0., 2.), (0., 2., 0.), (2., 0., -2.)).
      After clipping these will correspond to the colors blue, yellow, red
      respecively.
    - `minval`: float: the minimum value of the scalar range. This value and
      all lower values will be mapped to the first color of the palette.
    - `maxval`: float: the maximum value of the scalar range. This value and
      all higher values will be mapped to the last (third) color of the palette.
    - `midval`: float: a value in the scalar range that will correspond to
      the middle color of the palette. It defaults to the mean value of
      `minval` and `maxval`. It can be specified to allow unequal scaling
      of both subranges of the scalar values. This is often used to set
      a middle value 0.0 when the values can have both negative and positive
      values but with rather different maximum values in both directions.
    - `exp`, `exp2`: float: exponent to allow non-linear mapping. The defaults
      provide a linear mapping between numerical values and colors, or
      rather a bilinear mapping if the (midval,middle color) is not a linear
      combination of the endpoint mappings. Still, there are cases where the
      user wants a nonlinear mapping, e.g. to have more visual accuracy in the
      higher or lower (absolute) values of the (sub)range(s). Therefore, the
      values are first linearly scaled to the -1..1 range, and then mapped
      through the nonlinear function :func:`arraytools.stuur`.
      The effect is that with
      both exp > 1.0, more colors are used in the neighbourhood of the lowest
      value, while with exp < 1.0, more colors are use around the highest
      value. When both `exp` and `exp2`, the first one holds for the upper
      halfrange, the second for the lower one. Setting both values > 1.0
      thus has the effect of using more colors around the `midval`.

    See example: ColorScale

    """

    def __init__(self, palet='RAINBOW', minval=0., maxval=1., midval=None, exp=1.0, exp2=None):
        """Initialize the ColorScale.

        """
        if isinstance(palet, str):
            self.palet = Palette.get(palet.upper(), Palette['RGB'])
        else:
            self.palet = palet
        if self.palet[1] is None:
            first, last = self.palet[0], self.palet[2]
            self.palet = (first, tuple(0.5*(p+q) for p, q in zip(first, last)), last)
            print(self.palet)
        self.xmin = minval
        self.xmax = maxval
        if midval is None:
            self.x0 = 0.5*(minval+maxval)
        else:
            self.x0 = midval
        self.exp = exp
        self.exp2 = exp2


    def scale(self, val):
        """Scale a value to the range -1...1.

        Parameters:

        - `val`: float: numerical value to be scaled.

        If the ColorScale has only one exponent, values in the range
        self.minval..self.maxval are scaled to the range -1..+1.

        If two exponents were specified, scaling is done independently in
        the intervals minval..midval and midval..maxval, mapped resp. using
        exp2 and exp onto the intervals -1..0 and 0..1.
        """
        if self.exp2 is None:
            return stuur(val, [self.xmin, self.x0, self.xmax], [-1., 0., 1.], self.exp)

        if val < self.x0:
            return stuur(val, [self.xmin, (self.x0+self.xmin)/2, self.x0], [-1., -0.5, 0.], self.exp2)
        else:
            return stuur(val, [self.x0, (self.x0+self.xmax)/2, self.xmax], [0., 0.5, 1.0], self.exp)


    def color(self, val):
        """Return the color representing a value val.

        Parameters:

        - `val`: float: numerical value to be scaled.

        The returned color is a tuple of three float RGB values. Values
        may be out of the range 0..1 if any of the palette defining colors
        is.

        The resulting color is obtained by first scaling the value to the
        -1..1 range using the `scale` method, and then using that result
        to linearly interpolate between the color values of the palette.
        """
        x = self.scale(val)
        c0 = self.palet[1]
        if x == 0.:
            return c0
        if x < 0:
            c1 = self.palet[0]
            x = -x
        else:
            c1 = self.palet[2]
        return tuple([(1.-x)*p + x*q for p, q in zip(c0, c1)])


class ColorLegend():
    """A colorlegend divides a ColorScale in a number of subranges.

    Parameters:

    - `colorscale`: a :class:`ColorScale` instance
    - `n`: a positive integer

    For a :class:`ColorScale` without ``midval``, the full range is divided
    in ``n`` subranges; for a scale with ``midval``, each of the two ranges
    is divided in ``n/2`` subranges. In each case the legend has ``n``
    subranges limited by ``n+1`` values. The ``n`` colors of the legend
    correspond to the middle value of each subrange.

    See also :class:`opengl.decors.ColorLegend`.
    """

    def __init__(self, colorscale, n):
        """Initialize the color legend."""
        self.cs = colorscale
        n = int(n)
        r = float(n)/2
        m = (n+1)//2
        vals = [(self.cs.xmin*(r-i)+self.cs.x0*i)/r for i in range(m)]
        val2 = [(self.cs.xmax*(r-i)+self.cs.x0*i)/r for i in range(m)]
        val2.reverse()
        if n % 2 == 0:
            vals += [self.cs.x0]
        vals += val2
        midvals = [(vals[i] + vals[i+1])/2 for i in range(n)]
        self.limits = vals
        self.colors = [self.cs.color(v) for v in midvals]
        self.underflowcolor = None
        self.overflowcolor = None


    def overflow(self, oflow=None):
        """Raise a runtime error if oflow is None, else return oflow."""
        if oflow is None:
            raise RuntimeError("Value outside colorscale range")
        else:
            return oflow


    def color(self, val):
        """Return the color representing a value val.

        The color is that of the subrange holding the value. If the value
        matches a subrange limit, the lower range color is returned.
        If the value falls outside the colorscale range, a runtime error
        is raised, unless the corresponding underflowcolor or overflowcolor
        attribute has been set, in which case this attirbute is returned.
        Though these attributes can be set to any not None value, it will
        usually be set to some color value, that will be used to show
        overflow values.
        The returned color is a tuple of three RGB values in the range 0-1.
        """
        i = 0
        while self.limits[i] < val:
            i += 1
            if i >= len(self.limits):
                return self.overflow(self.overflowcolor)
        if i==0:
            return self.overflow(self.underflowcolor)
        return self.colors[i-1]


if __name__ == '__main__':

    for palet in ['RGB', 'BW']:
        CS = ColorScale(palet, -50., 250.)
        for x in [-50+10.*i for i in range(31)]:
            print(x, ": ", CS.color(x))

    CS = ColorScale('RGB', -50., 250., 0.)
    CL = ColorLegend(CS, 5)
    print(CL.limits)
    for x in [-45+10.*i for i in range(30)]:
        print(x, ": ", CL.color(x))
    CL.underflowcolor = black
    CL.overflowcolor = white

    print(CL.color(-55))
    print(CL.color(255))

# End
