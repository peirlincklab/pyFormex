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

"""Voxelize

This example illustrates the use of the gtsinside program to create a
voxelization of a closed surface.
"""
_level = 'advanced'
_topics = ['surface']
_techniques = ['voxelize', 'image']
_name = 'Voxelize'
_data = _name + '_data'

from pyformex.gui.draw import *
from pyformex.plugins.imagearray import saveGreyImage, array2image
from pyformex import simple

filename = pf.cfg['datadir'] / 'horse.off'


def createSurface(surface, filename, grade, **kargs):
    """Create and draw a closed surface from input data

    """
    if surface == 'file':
        S = TriSurface.read(filename).centered()
    elif surface == 'sphere':
        S = simple.sphere(ndiv=grade)

    draw(S)

    if not S.isClosedManifold():
        warning("This is not a closed manifold surface. Try another.")
        return None
    return S


# TODO: this should be merged with opengl.drawImage3D
def showGreyImage(a):
    """Draw pixel array on the canvas"""
    F = Formex('4:0123').repm([a.shape[1], a.shape[0]], [0, 1], [1., 1.]).setProp(a)
    return draw(F)

def saveGreyImage(a, f, flip=True):
    """Save a 2D int array as a grey image.

    Parameters:

    - `a`: int array (nx,ny) with values in the range 0..255. These are
      the grey values of the pixels.
    - `f`: filename
    - `flip`: by default, the vertical axis is flipped, so that images are
      stored starting at the top. If your data already have the vertical axis
      downwards, use flip=False.

    """
    a = at.checkArray(a, ndim=2, kind='u', allow='i').astype(np.uint8)
    array2image(a, f)
    # c = np.flipud(a)
    # c = np.dstack([c, c, c])
    # im = numpy2qimage(c)
    # im.save(f)


def saveScan(scandata, surface, filename, showimages=False, **kargs):
    """Save the scandata for the surface"""
    dirname = askDirname(caption="Directory where to store the images")
    if not dirname:
        return
    chdir(dirname)
    if not checkWorkdir():
        print("Could not open directory for writing. I have to stop here")
        return

    if surface == 'sphere':
        name = 'sphere'
    else:
        name = utils.projectName(filename)
    fs = utils.NameSequence(name, '.png')

    if showimages:
        clear()
        flat()
        A = None
    for frame in scandata:
        if showimages:
            B = showGreyImage(frame*7)
            undraw(A)
            A = B

        saveGreyImage(frame*255, next(fs))


def run():
    resetAll()
    clear()
    smooth()
    lights(True)

    res = askItems(caption=_name, store=_data, items=[
        _G('Model', [
            _I('surface', choices=['file', 'sphere']),
            _I('filename', filename, text='Image file', itemtype='filename',
               filter='surface', mode='exist'),
            _I('grade', 8),
        ]),
        _G('Scan', [
            _I('resolution', 100),
        ]),
    ], enablers = [
        ('surface', 'file', 'filename', ),
        ('surface', 'sphere', 'grade', ),
    ])
    if not res:
        return

    S = createSurface(**res)
    if S:
        nmax = res['resolution']
        with busyCursor():
            vox, P = S.voxelize(nmax, return_formex=True)
        scale = P.sizes() / np.array(vox.shape)
        origin = P.bbox()[0]
        print("Box size: %s" % P.sizes())
        print("Data size: %s " % np.array(vox.shape))
        print("Scale: %s" % scale)
        print("Origin: %s" % P.bbox()[0])
        draw(P, marksize=5)
        transparent()
        saveScan(vox, showimages=True, **res)


# The following is to make it work as a script
if __name__ == '__draw__':
    run()


# End
