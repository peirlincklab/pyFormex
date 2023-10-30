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
"""Klein bottle

This example creates and displays a Quad4 Mesh model of a Klein bottle.
A Klein bottle is a non-orientable (single sided) surface without boundary.
The surface is self intersecting.

The geometry is created by computing the position of the nodes from
mathematical formulas.

"""
_name = 'KleinBottle'
_level = 'beginner'
_topics = ['geometry', 'surface', 'mesh']
_techniques = ['dialog', 'bkcolor', 'transparency']

from pyformex.gui.draw import *
from pyformex.elements import Quad4

# TODO: we should add a fuse parameter and make fuse=True the default
def KleinBottle(nu=128, nv=64, ru=(0.,1.), rv=(0.,1.)):
    """A Quad4 Mesh representing a Klein bottle.

    A Klein bottle is a borderless non-orientable surface. In 3D the
    surface is self-intersecting.

    Parameters
    ----------
    nu: int
        Number of elements along the longitudinal axis of the bottle.
    nv: int
        Number of elements along the circumference of the bottle.
    ru: tuple of floats
        The relative range of the longitudinal parameter. The default
        covers the full range [0., pi].
    rv: tuple of floats
        The relative range of the circumferential parameter. The default
        covers the full range [0., 2*pi].

    Returns
    -------
    :class:`Mesh`
        A Mesh of eltype Quad4 representing a Klein bottle.
        The Mesh has nu * nv elements and (nu+1) * (nv+1) nodes.
        The Mesh is not fused and will contain double nodes at the
        ends of the full parameter ranges. Use :meth:`Mesh.fuse` and
        :meth:`Mesh.compact` to remove double nodes.

    Notes
    -----
    One can check that the surface has no border from::

        KleinBottle().fuse().compact().getBorder()

    which returns an empty list.

    The non-orientability and self-intersection of the surface can be
    checked from transforming the Klein bottle to a :class:`TriSurface`
    and then using the :meth:`~TriSurface.check`.
    For the non-fused bottle, this will report
    'orientable but self-intersecting'. For the fused bottle, the report
    will say 'not an orientable manifold'.

    """
    u = np.linspace(ru[0]*pi, ru[1]*pi, nu+1)
    v = np.linspace(rv[0]*2*pi, rv[1]*2*pi, nv+1)

    x = np.sum(
        [np.outer(a * np.cos(u) ** i * np.sin(u) ** j, np.cos(v) ** k
        ) for a, i, j, k in zip(
            [2 / 5, 2 / 3, -4, 12, -8],
            [1, 2, 1, 5, 7],
            [0, 1, 1, 1, 1],
            [1, 1, 0, 0, 0])], axis=0)

    y = np.sum(
        [np.outer(a * np.cos(u) ** i * np.sin(u) ** j, np.cos(v) ** k
        ) for a, i, j, k in zip(
            [-4, 1 / 5, -1 / 5, 1 / 3, -1 / 3, -16 / 5, 16 / 5, -16 / 3, 16 / 3],
            [0, 0, 2, 1, 3, 4, 6, 5, 7],
            [2, 1, 1, 2, 2, 1, 1, 2, 2],
            [0, 1, 1, 1, 1, 1, 1, 1, 1])], axis=0)

    z = np.sum(
        [np.outer(a * np.cos(u) ** i * np.sin(u) ** j, np.sin(v) ** k
        ) for a, i, j, k in zip(
            [2 / 5, 2 / 3],
            [0, 1],
            [0, 1],
            [1, 1])], axis=0)

    xyz = np.stack([x, y, z], axis=-1).reshape(-1,3)
    elems = Quad4.els(nv,nu)
    return Mesh(xyz,elems)


def run():
    """Main script"""
    clear()
    smooth()
    view('front')
    transparent()

    res = askItems(caption=_name, store=_name+'_data', items=[
        _I('nu', 128, text="#elements (longitudinal)"),
        _I('nv', 64, text="#elements (circumferential)"),
        _I('bottle', text="Geometry", itemtype='hradio',
           choices=['full bottle', 'half bottle']),
        _I('color', 1, min=0, max=15, text="Front color index"),
        _I('bkcolor', 3, min=0, max=15, text="Back color index"),
    ])

    if res:
        M = KleinBottle(
            nu = res['nu'], nv=res['nv'],
            rv = (0.0, 1.0) if res['bottle'].startswith('full') else (0.5, 1.0),
        )
        draw(M, color=res['color'], bkcolor=res['bkcolor'])
        export({_name:M})


if __name__ == '__draw__':
    run()

# End
