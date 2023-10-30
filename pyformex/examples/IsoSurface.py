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

"""IsoSurface

This example illustrates the use of the isosurface plugin to construct
isosurface through a set of data
"""

_level = 'beginner'
_topics = ['surface']
_techniques = ['isosurface', 'timer']

from pyformex.gui.draw import *
from pyformex import elements
from pyformex.plugins import isosurface as sf
from pyformex.plugins import imagearray as ia


def loadImage(file, grey=True):
    """Load a grey image into a numpy array"""
    im = ia.image2array(file)
    return im


def loadImages(files, glmode=True):
    images = [loadImage(f) for f in files]
    images = np.dstack(images)
    if images.dtype.kind == 'u':
        images = images/255.
    return images


def run():
    clear()
    smooth()

    options = ["Cancel", "Image files", "DICOM files", "Generated from function"]
    ans = ask("This IsoSurface example can either reconstruct a surface from a series of 2D images, or it can use data generated from a function. Use which data?", options)
    ans = options.index(ans)

    tet = False

    if ans == 0:
        return

    elif ans in [1, 2]:
        fn = askFilename(mode='multi')
        if not fn:
            return

        if len(fn) == 1:
            files = Path(utils.NameSequence(fn[0])).glob()
        else:
            files = fn

        print(files)

        # skip some files?
        res = askItems([('file_step', 1)])
        if not res:
            return

        step = res['file_step']
        if step > 1:
            files = files[::step]
            print(files)

        with busyCursor():
            if ans == 1:
                data = loadImages(files)
                scale = ones(3)
            else:
                data, scale = ia.dicom2numpy(files)
                print(f"Spacing: {scale}")
                # normalize
                dmin, dmax = data.min(), data.max()
                data = (data-dmin).astype(float32)/(dmax-dmin)

        # level at which the isosurface is computed
        res = askItems([
            _I('isolevel', 0.5),
            _I('algorithm', itemtype='hradio', choices=['cubes', 'tetrahedrons']),
            ])
        if not res:
            return

        level = res['isolevel']
        if level <= 0.0 or level >= 1.0:
            level = data.mean()

        tet = res['algorithm'] == 'tetrahedrons'

    else:
        # data space: create a grid to visualize
        if ack("Large model (takes some time)?"):
            nx, ny, nz = 100, 150, 200  # for time testing
        else:
            nx, ny, nz = 6, 8, 10
        F = elements.Hex8.toFormex().repm([nz, ny, nx]).setProp(1)
        #draw(F,mode='wireframe')

        # function to generate data: the distance from the origin
        dist = lambda x, y, z: sqrt(x*x+y*y+z*z)
        # a bit more spectacular:
        dist = lambda x, y, z: sin(sqrt(x*y*z)/20)
        data = np.fromfunction(dist, (nz+1, ny+1, nx+1))
        scale = np.ones(3)

        # level at which the isosurface is computed
        level = 0.5*data.max()

    print(f"Image Data: {data.shape}, {data.dtype}")
    print(f"Pixel Spacing: {scale}")
    print(f"{data.min()=:.6f}, {data.max()=:.6f}")
    print(f"iso{level=:.6f}")

    fast = True

    # Compute the isosurface
    with busyCursor():
        with Timer() as t:
            tri = sf.isosurface(data, level, nproc=4, tet=tet)
        ntri = len(tri)
        print(f"Got {ntri} triangles in {t.mem:.6f} seconds")
        if ntri > 0:
            S = TriSurface(tri).scale(scale[::-1])
            draw(S, color=blue, bkcolor=red)
            export({'isosurf': S})


# The following is to make it work as a script
if __name__ == '__draw__':
    run()


# End
