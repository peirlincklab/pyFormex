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
"""Tools to access files from the web

This module provides some convenience functions to access files from the
web. It is currently highly biased to downloading 3D models from archive3d.net,
unzipping the files, and displaying the .3ds models included.

"""

import pyformex as pf
from pyformex import utils
from pyformex import Path
from pyformex.gui.draw import busyCursor


def download(url, tgt):
    """Download a file with a known url to tgt.

    """
    import requests
    with open(tgt, 'wb') as f:
        f.write(requests.get(url).content)


def find3ds(fn):
    """List the .3ds files in a zip file"""
    files = [Path(f) for f in utils.zipList(fn)]
    return [f for f in files if f.lsuffix == '.3ds']


def show3ds(fn):
    """Import and show a 3ds file

    Import a 3ds file, render it, and export it to the GUI
    """
    fn = Path(fn)
    from pyformex.plugins.vtk_itf import import3ds
    from pyformex.gui.draw import draw, export
    name = fn.stem
    geom = import3ds(fn)
    draw(geom)
    export({name: geom})


def show3dzip(fn):
    """Show the .3ds models in a zip file.

    fn: a zip file containing one or more .3ds models.
    """
    print("Zip file %s" % fn)
    for f in find3ds(fn):
        print("Extracting %s" % f)
        utils.zipExtract(fn, members=[f])
        show3ds(f)


def download3d(fid, fn):
    """Download a file from archive3d.net by id number."""
    url = "http://archive3d.net/?a=download&do=get&id=%s" % fid
    download(url, fn)


def show3d(fid):
    """Show a model from the archive3d.net database.

    fid: string: the archive3d id number
    """
    path = pf.cfg['downloaddir'] / 'archive3d'
    path.mkdir(exist_ok=True)
    fn = path / fid
    if not fn.exists():
        with busyCursor():
            download3d(fid, fn)
    show3dzip(fn)


# End
