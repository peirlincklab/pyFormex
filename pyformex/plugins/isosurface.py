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
#
"""Isosurface: surface reconstruction algorithms

This module contains

"""
import numpy as np

from pyformex.lib import misc
from pyformex.multi import multitask, cpu_count, splitar


def isosurface(data, level, nproc=-1, tet=0):
    """Create an isosurface through data at given level.

    Parameters
    ----------
    data: :term:`array_like`
        An (nx,ny,nz) shaped float array of data values at points with
        coordinates equal to their indices. This defines a 3D volume
        [0,nx-1], [0,ny-1], [0,nz-1].
    level: float
        The data value for which the isosurface is to be constructed.
    nproc: int
        The number of parallel processes to use. On multiprocessor machines
        this may be used to speed up the processing. If <= 0 , the number of
        processes will be set equal to the number of available processors,
        to achieve a maximal speedup.
    tet: int
        If zero (default), a marching cubes algiorithm is used. If nonzero,
        a marching tetrahedrons algorithm is used. The latter is slower and
        produces a lot more triangles, but results in a smoother surface.
        The tetraeders algorithm is currently only available in the compiled
        pyFormex library.

    Returns
    -------
    array:
        An (ntr,3,3) float array defining the triangles of the isosurface.
        The result may be empty (if level is outside the data range).

    Notes
    -----
    Currently only a marching cubes algorithm is used. Marching tetraeders
    is not implemented yet.
    """
    if nproc is None:
        nproc = -1
    if nproc < 1:
        nproc = cpu_count()

    if nproc == 1:
        # Perform single process isosurface (accelerated)
        data = data.astype(np.float32)
        level = np.float32(level)
        tri = misc.isosurface(data, level, tet)

    else:
        # Perform parallel isosurface
        # 1. Split in blocks (and remember shift)
        datablocks = splitar(data, nproc, close=True)
        shift = (np.array([d.shape[0] for d in datablocks]) - 1).cumsum()
        # 2. Solve blocks independently
        tasks = [(isosurface, (d, level, 1, tet)) for d in datablocks]
        tri = multitask(tasks, nproc)
        # 3. Shift and merge blocks
        for t, s in zip(tri[1:], shift[:-1]):
            t[:, :, 2] += s
        tri = np.concatenate(tri, axis=0)

    return tri


def isoline(data, level, nproc=-1):
    """Create an isocontour through data at given level.

    Parameters
    ----------
    data: :term:`array_like`
        An (nx,ny) shaped array of data values at points with
        coordinates equal to their indices. This defines a 2D area
        [0,nx-1], [0,ny-1].
    level: float
        The data value for which the isocontour is to be constructed.
    nproc: int
        The number of parallel processes to use. On multiprocessor machines
        this may be used to speed up the processing. If <= 0 , the number of
        processes will be set equal to the number of available processors,
        to achieve a maximal speedup.

    Returns
    -------
    array:
        An (nseg,2,2) float array defining the 2D coordinates of the
        segments of the isocontour.
        The result may be empty (if level is outside the data range).
    """
    if nproc is None:
        nproc = -1
    if nproc < 1:
        nproc = cpu_count()

    if nproc == 1:
        # Perform single process isoline (accelerated)
        data = data.astype(np.float32)
        level = np.float32(level)
        seg = misc.isoline(data, level)

    else:
        # Perform parallel isoline
        # 1. Split in blocks (and remember shift)
        datablocks = splitar(data, nproc, close=True)
        shift = (np.array([d.shape[0] for d in datablocks]) - 1).cumsum()
        # 2. Solve blocks independently
        tasks = [(isoline, (d, level, 1)) for d in datablocks]
        seg = multitask(tasks, nproc)
        # 3. Shift and merge blocks
        for t, s in zip(seg[1:], shift[:-1]):
            t[:, :, 1] += s
        seg = np.concatenate(seg, axis=0)

    return seg


# End
