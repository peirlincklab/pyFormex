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
"""GeomFile

Test the GeomFile export and import
"""
_level = 'normal'
_topics = ['geometry']
_techniques = ['color', 'geomfile']

from pyformex.gui.draw import *
from pyformex.examples.Cube import cube_quad


def run():

    colormode = [None, 'Single', 'Face', 'Full']
    n = len(colormode)
    obj = {}
    layout(2*n, 4)
    for vp, color in enumerate(colormode):
        viewport(vp)
        clear()
        reset()
        smooth()
        view('iso')
        obj[str(color)] = o = cube_quad(color)
        draw(o)

    if checkWorkdir():
        indir = pf.cfg['workdir']
    else:
        tmpdir = utils.TempDir()
        indir = tmpdir.path

    filewrite.writePGF(indir / 'test.pgf', obj)

    oobj = readGeometry(indir / 'test.pgf')
    for vp, color in enumerate(colormode[:4]):
        viewport(vp+n)
        clear()
        reset()
        smooth()
        view('iso')
        draw(oobj[str(color)])


if __name__ == '__draw__':
    run()
# End
